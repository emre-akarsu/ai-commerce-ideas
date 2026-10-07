"""Postgres persistence for the stage-2 data (migration 0004; docs/architecture/stage1-contract.md).

Every store hands out tenant-bound capabilities (``for_tenant``) or takes the tenant on each call;
all access goes through ``tenant_session`` so ``app.tenant_id`` is bound per transaction and RLS
applies. Components never import this module; it imports components.

* ``PgOfferStore`` satisfies the ``TenantOffers`` protocol the quote pipeline expects. A tenant
  sees the shared
  platform offers (table ``shared_offers``, SELECT-only for ``app_user``) plus its own private ones
  (RLS table ``offers``). Money and quantities are stored as strings and rebuilt as ``Decimal``;
  every offer is re-validated on read (rule 5). ``PgSharedOfferWriter`` is the platform-only write
  path and needs an admin engine, never the application engine.
* ``PgApprovedMatchStore`` implements ``components.matching.approvals.ApprovedMatchStore``.
* ``PgImportStore`` keeps append-only ``ImportSummary`` rows. Shared (tenant-less) summaries are
  platform data and are not accepted by the tenant store.
* ``PgTemplateStore`` keeps ``kit-template/1`` documents: max 30 per tenant, same name and scope
  replaces. A 31st distinct template is refused (``TemplateLimitError``), not silently dropping an
  older one as the browser-local store does.
* ``PgQuoteSnapshotStore`` keeps versioned, insert-only snapshots (no UPDATE grant).
"""

from __future__ import annotations

import json
import re
import threading
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Connection, Engine, delete, func, insert, select, text, update
from sqlalchemy.exc import DBAPIError

from components.core.domain import UoM
from components.core.ports import Clock
from components.matching.approvals import ApprovalRecord
from components.matching.embedding import HashingEmbedder, cosine
from components.matching.similarity import cosine_counts, trigrams
from components.pricebook import ImportSummary
from components.pricing import (
    DeliveryTerms,
    DeliveryTier,
    DuplicateOfferError,
    Offer,
    OfferFilter,
    OfferValidationError,
    PackSize,
    Price,
    PricePer,
    PriceType,
    PricingConfig,
    Provenance,
    SharedOfferWriter,
    SourceKind,
    StockStatus,
    TenantScopeError,
    Tranche,
    VatBasis,
    Visibility,
)
from components.pricing.text import check_id
from components.pricing.units import Unit

from . import models as m
from .session import tenant_session

MAX_TEMPLATES = 30
TEMPLATE_FORMAT = "kit-template/1"
_UNIQUE = "23505"
_RLS_OR_PRIV = "42501"


class TemplateLimitError(ValueError):
    """The tenant already holds the maximum number of kit templates."""


class TemplateValidationError(ValueError):
    """The document is not a valid kit-template/1."""


def _sqlstate(exc: DBAPIError) -> str | None:
    return getattr(exc.orig, "sqlstate", None)


def _lock(conn: Connection, key: str) -> None:
    conn.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 0))"), {"k": key}
    )


# ---------------------------------------------------------------- offer codec (money as strings)


def _dec(value: object) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _s(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(UTC).isoformat()


def _when(value: object) -> datetime | None:
    return None if value is None else datetime.fromisoformat(str(value))


def _tranches_to_doc(tranches: Sequence[Tranche]) -> list[dict[str, int]]:
    return [{"packs": t.packs, "in_days": t.in_days} for t in tranches]


def _tranches_from_doc(doc: Mapping[str, Any]) -> tuple[Tranche, ...]:
    """Missing key: availability is unknown (documents written before tranches existed)."""
    rows = doc.get("availability", [])
    if not isinstance(rows, list) or not all(isinstance(r, Mapping) for r in rows):
        raise OfferValidationError("availability must be a list of {packs, in_days} objects")
    return tuple(Tranche(r["packs"], r["in_days"]) for r in rows)


def offer_to_doc(o: Offer) -> dict[str, Any]:
    p, d = o.price, o.delivery
    doc: dict[str, Any] = {
        "offer_id": o.offer_id, "sku_id": o.sku_id, "merchant_id": o.merchant_id,
        "source_kind": o.source_kind.value,
        "price": {
            "amount": str(p.amount), "currency": p.currency, "per": p.per.value,
            "uom": p.uom.value, "vat_basis": p.vat_basis.value, "vat_rate": _s(p.vat_rate),
        },
        "pack": {
            "quantity": str(o.pack.quantity),
            "unit": None if o.pack.unit is None else o.pack.unit.value,
        },
        "observed_at": _iso(o.observed_at),
        "provenance": {
            "source_id": o.provenance.source_id, "method": o.provenance.method,
            "synthetic": o.provenance.synthetic,
        },
        "licence": o.licence, "confidence": str(o.confidence), "source_ref": o.source_ref,
        "min_order_qty": o.min_order_qty, "order_multiple": o.order_multiple,
        "stock_status": o.stock_status.value, "lead_time_days": o.lead_time_days,
        "delivery": None if d is None else {
            "flat_fee": _s(d.flat_fee), "free_over": _s(d.free_over),
            "tiers": [{"min_spend": str(t.min_spend), "fee": str(t.fee)} for t in d.tiers],
            "vat_basis": None if d.vat_basis is None else d.vat_basis.value,
        },
        "valid_until": _iso(o.valid_until), "visibility": o.visibility.value,
        "tenant_id": o.tenant_id, "flags": list(o.flags), "price_type": o.price_type.value,
        "account_specific": o.account_specific, "tenant_attested": o.tenant_attested,
    }
    if o.availability:  # written only when known, so documents without it stay byte-identical
        doc["availability"] = _tranches_to_doc(o.availability)
    return doc


def offer_from_doc(doc: Mapping[str, Any]) -> Offer:
    """Rebuild and re-validate (the model's own checks run again)."""
    p, pk, d = doc["price"], doc["pack"], doc.get("delivery")
    delivery = None if d is None else DeliveryTerms(
        flat_fee=_dec(d["flat_fee"]), free_over=_dec(d["free_over"]),
        tiers=tuple(DeliveryTier(Decimal(t["min_spend"]), Decimal(t["fee"])) for t in d["tiers"]),
        vat_basis=None if d["vat_basis"] is None else VatBasis(d["vat_basis"]),
    )
    observed = _when(doc["observed_at"])
    assert observed is not None
    return Offer(
        offer_id=doc["offer_id"], sku_id=doc["sku_id"], merchant_id=doc["merchant_id"],
        source_kind=SourceKind(doc["source_kind"]),
        price=Price(Decimal(p["amount"]), p["currency"], PricePer(p["per"]), UoM(p["uom"]),
                    VatBasis(p["vat_basis"]), _dec(p["vat_rate"])),
        pack=PackSize(Decimal(pk["quantity"]), None if pk["unit"] is None else Unit(pk["unit"])),
        observed_at=observed,
        provenance=Provenance(**doc["provenance"]),
        licence=doc["licence"], confidence=Decimal(doc["confidence"]),
        source_ref=doc["source_ref"], min_order_qty=doc["min_order_qty"],
        order_multiple=doc["order_multiple"], stock_status=StockStatus(doc["stock_status"]),
        lead_time_days=doc["lead_time_days"], delivery=delivery,
        valid_until=_when(doc["valid_until"]), visibility=Visibility(doc["visibility"]),
        tenant_id=doc["tenant_id"], flags=tuple(doc["flags"]),
        price_type=PriceType(doc["price_type"]), account_specific=doc["account_specific"],
        tenant_attested=doc["tenant_attested"],
        availability=_tranches_from_doc(doc),
    )


def _offer_row(o: Offer) -> dict[str, Any]:
    return {
        "id": o.offer_id, "sku_id": o.sku_id, "merchant_id": o.merchant_id,
        "source_kind": o.source_kind.value, "observed_at": o.observed_at,
        "data": offer_to_doc(o),
    }


# ---------------------------------------------------------------- offers


class PgOfferRepository:
    """`OfferRepository` for one tenant: shared offers (read only) plus its own private ones."""

    def __init__(self, engine: Engine, tenant_id: str, config: PricingConfig) -> None:
        check_id(tenant_id, "tenant_id")
        self._engine = engine
        self._tenant = tenant_id
        self._config = config

    @property
    def tenant_id(self) -> str:
        return self._tenant

    def _load(self, data: Mapping[str, Any]) -> Offer:
        offer = offer_from_doc(data)
        self._config.check_offer(offer)
        return offer

    def add(self, offer: Offer) -> None:
        self.add_many([offer])

    def add_many(self, offers: Iterable[Offer]) -> int:
        """All or nothing: one transaction."""
        batch: list[Offer] = []
        for offer in offers:
            if not isinstance(offer, Offer):
                raise OfferValidationError("only Offer values can be stored")
            self._config.check_offer(offer)
            if offer.visibility is not Visibility.TENANT_PRIVATE or offer.tenant_id != self._tenant:
                raise TenantScopeError("a tenant may only add its own tenant-private offers")
            batch.append(offer)
        ids = [o.offer_id for o in batch]
        if len(set(ids)) != len(ids):
            raise DuplicateOfferError("duplicate offer ids in one batch")
        with tenant_session(self._engine, self._tenant) as conn:
            taken = conn.execute(
                select(m.shared_offers.c.id).where(m.shared_offers.c.id.in_(ids))
            ).first()
            if taken:
                raise DuplicateOfferError(f"offer {taken[0]} already exists")
            try:
                with conn.begin_nested():
                    for offer in batch:
                        conn.execute(
                            insert(m.offers).values(tenant_id=self._tenant, **_offer_row(offer))
                        )
            except DBAPIError as exc:
                if _sqlstate(exc) == _UNIQUE:
                    raise DuplicateOfferError("an offer in the batch already exists") from exc
                if _sqlstate(exc) == _RLS_OR_PRIV:
                    raise TenantScopeError("offer write rejected by row level security") from exc
                raise
        return len(batch)

    def get(self, offer_id: str) -> Offer | None:
        check_id(offer_id, "offer_id")
        with tenant_session(self._engine, self._tenant) as conn:
            for table in (m.offers, m.shared_offers):
                q = select(table.c.data).where(table.c.id == offer_id)
                if table is m.offers:
                    q = q.where(table.c.tenant_id == self._tenant)
                data = conn.execute(q).scalars().first()
                if data is not None:
                    return self._load(data)
        return None

    def search(self, flt: OfferFilter | None = None) -> tuple[Offer, ...]:
        criteria = flt or OfferFilter()
        found: list[Offer] = []
        with tenant_session(self._engine, self._tenant) as conn:
            for table in (m.shared_offers, m.offers):
                q = select(table.c.data)
                if table is m.offers:
                    q = q.where(table.c.tenant_id == self._tenant)
                if criteria.sku_ids is not None:
                    q = q.where(table.c.sku_id.in_(sorted(criteria.sku_ids)))
                if criteria.merchant_ids is not None:
                    q = q.where(table.c.merchant_id.in_(sorted(criteria.merchant_ids)))
                if criteria.source_kinds is not None:
                    kinds = sorted(k.value for k in criteria.source_kinds)
                    q = q.where(table.c.source_kind.in_(kinds))
                if criteria.observed_since is not None:
                    q = q.where(table.c.observed_at >= criteria.observed_since)
                q = q.order_by(table.c.id).limit(criteria.limit)
                found += [self._load(d) for d in conn.execute(q).scalars()]
        hits = sorted((o for o in found if criteria.matches(o)), key=lambda o: o.offer_id)
        return tuple(hits[: criteria.limit])

    def remove(self, offer_id: str) -> bool:
        check_id(offer_id, "offer_id")
        with tenant_session(self._engine, self._tenant) as conn:
            res = conn.execute(
                delete(m.offers).where(m.offers.c.tenant_id == self._tenant,
                                       m.offers.c.id == offer_id)
            )
            if res.rowcount:
                return True
            if conn.execute(
                select(m.shared_offers.c.id).where(m.shared_offers.c.id == offer_id)
            ).first():
                raise TenantScopeError("shared offers are managed by the platform, not a tenant")
            return False

    def count(self) -> int:
        with tenant_session(self._engine, self._tenant) as conn:
            own = conn.execute(
                select(func.count()).select_from(m.offers).where(
                    m.offers.c.tenant_id == self._tenant)
            ).scalar_one()
            shared = conn.execute(select(func.count()).select_from(m.shared_offers)).scalar_one()
        return int(own) + int(shared)


class PgOfferStore:
    """Satisfies `TenantOffers` (the quote pipeline's context). Use the app_user engine."""

    def __init__(self, engine: Engine, config: PricingConfig) -> None:
        self._engine = engine
        self._config = config

    def for_tenant(self, tenant_id: str) -> PgOfferRepository:
        return PgOfferRepository(self._engine, tenant_id, self._config)


class PgSharedOfferWriter:
    """Platform-only writer for ``shared_offers``. Needs the admin/owner engine (app_user has no
    INSERT on the table). Applies the same shareability rules as `SharedOfferWriter`."""

    def __init__(self, admin_engine: Engine, config: PricingConfig,
                 shareable_licences: frozenset[str] | None = None) -> None:
        self._engine = admin_engine
        self._config = config
        args: tuple[Any, ...] = (config, threading.RLock())
        self._rules = (
            SharedOfferWriter({}, {}, *args) if shareable_licences is None
            else SharedOfferWriter({}, {}, *args, shareable_licences)
        )

    def add_many_shared(self, offers: Iterable[Offer]) -> int:
        batch = list(offers)
        for offer in batch:
            if not isinstance(offer, Offer):
                raise OfferValidationError("only Offer values can be stored")
            self._config.check_offer(offer)
            self._rules._check_shareable(offer)  # noqa: SLF001
        ids = [o.offer_id for o in batch]
        if len(set(ids)) != len(ids):
            raise DuplicateOfferError("duplicate offer ids in one batch")
        with self._engine.begin() as conn:
            clash = conn.execute(
                select(m.offers.c.id).where(m.offers.c.id.in_(ids))
            ).first()
            if clash:
                raise DuplicateOfferError(f"offer {clash[0]} already exists")
            try:
                with conn.begin_nested():
                    for offer in batch:
                        conn.execute(insert(m.shared_offers).values(**_offer_row(offer)))
            except DBAPIError as exc:
                if _sqlstate(exc) == _UNIQUE:
                    raise DuplicateOfferError("a shared offer already exists") from exc
                raise
        return len(batch)

    def add_shared(self, offer: Offer) -> None:
        self.add_many_shared([offer])

    def remove_shared(self, offer_id: str) -> bool:
        check_id(offer_id, "offer_id")
        with self._engine.begin() as conn:
            res = conn.execute(delete(m.shared_offers).where(m.shared_offers.c.id == offer_id))
            return bool(res.rowcount)


# ---------------------------------------------------------------- approved matches


def _record_doc(r: ApprovalRecord) -> dict[str, Any]:
    return {
        "tenant_id": r.tenant_id, "signature": r.signature, "sku_ids": list(r.sku_ids),
        "approver": r.approver, "approved_at": _iso(r.approved_at), "line_text": r.line_text,
        "retrieval_text": r.retrieval_text,
    }


def _record_from(doc: Mapping[str, Any]) -> ApprovalRecord:
    approved = _when(doc["approved_at"])
    assert approved is not None
    return ApprovalRecord(
        tenant_id=doc["tenant_id"], signature=doc["signature"], sku_ids=tuple(doc["sku_ids"]),
        approver=doc["approver"], approved_at=approved, line_text=doc["line_text"],
        retrieval_text=doc["retrieval_text"],
    )


class PgApprovedMatchStore:
    """`components.matching.approvals.ApprovedMatchStore` in Postgres; every call is one tenant
    transaction, so another tenant's approvals are invisible and unwritable."""

    def __init__(self, engine: Engine, clock: Clock) -> None:
        self._engine = engine
        self._clock = clock
        self._embedder = HashingEmbedder()

    def approve(self, tenant_id: str, signature: str, line_text: str, retrieval_text: str,
                sku_ids: Sequence[str], approver: str) -> ApprovalRecord:
        if not tenant_id or not approver or not sku_ids or not signature:
            raise ValueError("tenant, signature, approver and at least one SKU are required")
        record = ApprovalRecord(tenant_id, signature, tuple(sku_ids), approver,
                                self._clock.now(), line_text, retrieval_text)
        doc = _record_doc(record)
        with tenant_session(self._engine, tenant_id) as conn:
            conn.execute(text(
                "INSERT INTO approved_matches (tenant_id, signature, data) "
                "VALUES (:t, :s, CAST(:d AS jsonb)) "
                "ON CONFLICT (tenant_id, signature) DO UPDATE "
                "SET data = EXCLUDED.data, updated_at = now()"
            ), {"t": tenant_id, "s": signature, "d": json.dumps(doc)})
        return record

    def lookup(self, tenant_id: str, signature: str) -> ApprovalRecord | None:
        with tenant_session(self._engine, tenant_id) as conn:
            data = conn.execute(
                select(m.approved_matches.c.data).where(
                    m.approved_matches.c.tenant_id == tenant_id,
                    m.approved_matches.c.signature == signature)
            ).scalars().first()
        return None if data is None else _record_from(data)

    def _all(self, tenant_id: str) -> list[ApprovalRecord]:
        with tenant_session(self._engine, tenant_id) as conn:
            rows = conn.execute(
                select(m.approved_matches.c.data).where(m.approved_matches.c.tenant_id == tenant_id)
            ).scalars().all()
        return [_record_from(d) for d in rows]

    def nearest(self, tenant_id: str, retrieval_text: str, k: int) -> list[ApprovalRecord]:
        tri, vec = trigrams(retrieval_text), self._embedder.embed(retrieval_text)

        def score(r: ApprovalRecord) -> float:
            return (cosine_counts(tri, trigrams(r.retrieval_text))
                    + cosine(vec, self._embedder.embed(r.retrieval_text)))

        return sorted(self._all(tenant_id), key=lambda r: (-score(r), r.signature))[:max(0, k)]

    def count(self, tenant_id: str) -> int:
        with tenant_session(self._engine, tenant_id) as conn:
            return int(conn.execute(
                select(func.count()).select_from(m.approved_matches).where(
                    m.approved_matches.c.tenant_id == tenant_id)
            ).scalar_one())


# ---------------------------------------------------------------- price imports (append-only)


class PgTenantImports:
    def __init__(self, engine: Engine, tenant_id: str) -> None:
        self._engine = engine
        self._tenant = tenant_id

    def add(self, summary: ImportSummary) -> ImportSummary:
        if not isinstance(summary, ImportSummary):
            raise TypeError("only ImportSummary values can be stored")
        if summary.tenant_id != self._tenant or summary.visibility != "tenant_private":
            raise TenantScopeError("a tenant may only record its own tenant-private imports")
        doc = {"merchant_id": summary.merchant_id, "tenant_id": summary.tenant_id,
               "visibility": summary.visibility, "offers": summary.offers,
               "quarantined": summary.quarantined}
        with tenant_session(self._engine, self._tenant) as conn:
            conn.execute(insert(m.price_imports).values(
                tenant_id=self._tenant, merchant_id=summary.merchant_id, data=doc))
        return summary

    def list(self) -> list[ImportSummary]:
        with tenant_session(self._engine, self._tenant) as conn:
            rows = conn.execute(
                select(m.price_imports.c.data).where(m.price_imports.c.tenant_id == self._tenant)
                .order_by(m.price_imports.c.seq)
            ).scalars().all()
        return [ImportSummary(**d) for d in rows]


class PgImportStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def for_tenant(self, tenant_id: str) -> PgTenantImports:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        return PgTenantImports(self._engine, tenant_id)


# ---------------------------------------------------------------- kit templates

_NAME_MAX = 80
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,95}")
_TRI = frozenset({"include", "not_needed", "have"})
_KEYS = frozenset({"format", "id", "name", "savedAt", "scopeId", "jobType", "answers",
                   "measurements", "allowances", "choices", "lines", "sample"})


def clean_template_name(raw: str) -> str:
    """Same rule as `cleanName` in apps/web/lib/kits/templates.ts."""
    out = re.sub(r"[\x00-\x1f<>]", " ", raw)
    return re.sub(r"\s+", " ", out).strip()[:_NAME_MAX]


def _str_map(doc: Mapping[str, Any], key: str, ok: Any) -> dict[str, Any]:
    value = doc.get(key, {})
    if not isinstance(value, dict) or not all(
        isinstance(k, str) and ok(v) for k, v in value.items()
    ):
        raise TemplateValidationError(f"{key} is not valid")
    return dict(value)


def validate_template(doc: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(doc, Mapping):
        raise TemplateValidationError("a template must be an object")
    extra = set(doc) - _KEYS
    if extra:
        raise TemplateValidationError(f"unknown fields: {sorted(extra)}")
    if doc.get("format") != TEMPLATE_FORMAT:
        raise TemplateValidationError(f"format must be {TEMPLATE_FORMAT}")
    tid, scope = doc.get("id"), doc.get("scopeId")
    if not isinstance(tid, str) or _ID_RE.fullmatch(tid) is None:
        raise TemplateValidationError("id must be a plain identifier")
    if not isinstance(scope, str) or not scope.strip() or len(scope) > 96:
        raise TemplateValidationError("scopeId is required")
    name = clean_template_name(doc["name"]) if isinstance(doc.get("name"), str) else ""
    if not name:
        raise TemplateValidationError("name is required")
    saved, job = doc.get("savedAt", ""), doc.get("jobType", "")
    if not isinstance(saved, str) or not isinstance(job, str):
        raise TemplateValidationError("savedAt and jobType must be text")
    is_str = lambda v: isinstance(v, str)  # noqa: E731
    out: dict[str, Any] = {
        "format": TEMPLATE_FORMAT, "id": tid, "name": name, "savedAt": saved, "scopeId": scope,
        "jobType": job,
        "answers": _str_map(doc, "answers", lambda v: isinstance(v, str | bool)),
        "measurements": _str_map(doc, "measurements", is_str),
        "allowances": _str_map(doc, "allowances", is_str),
        "choices": _str_map(doc, "choices", is_str),
        "lines": _str_map(doc, "lines", lambda v: v in _TRI),
    }
    if doc.get("sample") is True:
        out["sample"] = True
    return out


class PgTenantTemplates:
    def __init__(self, engine: Engine, tenant_id: str) -> None:
        self._engine = engine
        self._tenant = tenant_id

    def list(self) -> list[dict[str, Any]]:
        """Newest first (by savedAt, then id)."""
        t = m.kit_templates
        with tenant_session(self._engine, self._tenant) as conn:
            rows = conn.execute(
                select(t.c.data).where(t.c.tenant_id == self._tenant)
                .order_by(t.c.saved_at.desc(), t.c.id)
            ).scalars().all()
        return [dict(r) for r in rows]

    def get(self, template_id: str) -> dict[str, Any] | None:
        t = m.kit_templates
        with tenant_session(self._engine, self._tenant) as conn:
            data = conn.execute(
                select(t.c.data).where(t.c.tenant_id == self._tenant, t.c.id == template_id)
            ).scalars().first()
        return None if data is None else dict(data)

    def put(self, template: Mapping[str, Any]) -> dict[str, Any]:
        doc = validate_template(template)
        t = m.kit_templates
        scope = (t.c.tenant_id == self._tenant)
        with tenant_session(self._engine, self._tenant) as conn:
            _lock(conn, "aidb-kit-templates:" + self._tenant)
            same_name = conn.execute(
                select(t.c.id).where(scope, t.c.scope_id == doc["scopeId"], t.c.name == doc["name"])
            ).scalars().first()
            if same_name is not None and same_name != doc["id"]:
                conn.execute(delete(t).where(scope, t.c.id == same_name))
            exists = conn.execute(select(t.c.id).where(scope, t.c.id == doc["id"])).first()
            cols = {"name": doc["name"], "scope_id": doc["scopeId"], "saved_at": doc["savedAt"],
                    "data": doc}
            if exists:
                conn.execute(update(t).where(scope, t.c.id == doc["id"]).values(**cols))
            else:
                n = conn.execute(select(func.count()).select_from(t).where(scope)).scalar_one()
                if n >= MAX_TEMPLATES:
                    raise TemplateLimitError(f"at most {MAX_TEMPLATES} kit templates per tenant")
                conn.execute(insert(t).values(tenant_id=self._tenant, id=doc["id"], **cols))
        return doc

    def delete(self, template_id: str) -> bool:
        t = m.kit_templates
        with tenant_session(self._engine, self._tenant) as conn:
            res = conn.execute(
                delete(t).where(t.c.tenant_id == self._tenant, t.c.id == template_id))
            return bool(res.rowcount)


class PgTemplateStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def for_tenant(self, tenant_id: str) -> PgTenantTemplates:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        return PgTenantTemplates(self._engine, tenant_id)


# ---------------------------------------------------------------- quote snapshots


@dataclass(frozen=True)
class QuoteSnapshotRecord:
    id: str
    version: int
    created_at: datetime
    snapshot: dict[str, Any]


def _plain_json(doc: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(doc, Mapping):
        raise TypeError("a snapshot must be an object")
    out: dict[str, Any] = json.loads(json.dumps(doc, allow_nan=False))  # Decimal/float NaN fail
    return out


class PgTenantSnapshots:
    def __init__(self, engine: Engine, tenant_id: str) -> None:
        self._engine = engine
        self._tenant = tenant_id

    def add(self, snapshot: Mapping[str, Any], snapshot_id: str | None = None) -> str:
        """Insert a snapshot and return its id. A new id (generated unless given, or taken from the
        document's ``id``) starts at version 1; an existing id gets the next version. Rows are
        never updated or deleted (app_user has no such grant)."""
        doc = _plain_json(snapshot)
        sid = snapshot_id or (str(doc["id"]) if "id" in doc else uuid.uuid4().hex)
        check_id(sid, "snapshot id")
        q = m.quote_snapshots
        with tenant_session(self._engine, self._tenant) as conn:
            _lock(conn, f"aidb-snapshots:{self._tenant}:{sid}")
            last = conn.execute(
                select(func.max(q.c.version)).where(q.c.tenant_id == self._tenant, q.c.id == sid)
            ).scalar_one()
            conn.execute(insert(q).values(
                tenant_id=self._tenant, id=sid, version=(last or 0) + 1, data=doc))
        return sid

    def get(self, snapshot_id: str, version: int | None = None) -> QuoteSnapshotRecord | None:
        q = m.quote_snapshots
        stmt = select(q.c.id, q.c.version, q.c.created_at, q.c.data).where(
            q.c.tenant_id == self._tenant, q.c.id == snapshot_id)
        stmt = stmt.where(q.c.version == version) if version is not None else stmt.order_by(
            q.c.version.desc()).limit(1)
        with tenant_session(self._engine, self._tenant) as conn:
            row = conn.execute(stmt).first()
        return None if row is None else QuoteSnapshotRecord(row.id, row.version, row.created_at,
                                                            dict(row.data))

    def list(self, limit: int = 50) -> list[QuoteSnapshotRecord]:
        """Latest version of each snapshot, newest first."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit must be an integer between 1 and 1000")
        q = m.quote_snapshots
        latest = (
            select(q.c.id, func.max(q.c.version).label("v"))
            .where(q.c.tenant_id == self._tenant).group_by(q.c.id).subquery()
        )
        stmt = (
            select(q.c.id, q.c.version, q.c.created_at, q.c.data)
            .join(latest, (q.c.id == latest.c.id) & (q.c.version == latest.c.v))
            .where(q.c.tenant_id == self._tenant)
            .order_by(q.c.created_at.desc(), q.c.id).limit(limit)
        )
        with tenant_session(self._engine, self._tenant) as conn:
            rows = conn.execute(stmt).all()
        return [QuoteSnapshotRecord(r.id, r.version, r.created_at, dict(r.data)) for r in rows]


class PgQuoteSnapshotStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def for_tenant(self, tenant_id: str) -> PgTenantSnapshots:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        return PgTenantSnapshots(self._engine, tenant_id)


__all__ = [
    "MAX_TEMPLATES",
    "PgApprovedMatchStore",
    "PgImportStore",
    "PgOfferRepository",
    "PgOfferStore",
    "PgQuoteSnapshotStore",
    "PgSharedOfferWriter",
    "PgTemplateStore",
    "QuoteSnapshotRecord",
    "TemplateLimitError",
    "TemplateValidationError",
    "offer_from_doc",
    "offer_to_doc",
    "validate_template",
]
