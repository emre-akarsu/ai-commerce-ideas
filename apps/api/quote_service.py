"""The quote pipeline behind the API: kit -> matching -> pricing -> quote, price book, options.

Built from `components.job_kits`, `matching`, `pricing`, `quoting` and `pricebook`, with the
jurisdiction behaviour taken from the resolved deployment profile through `PricingConfig` and
`GatePolicy` (the way scripts/export_demo_data.py and scripts/demo_quote.py do). Time comes from an
injected `Clock`; nothing here sends, orders or fetches anything: request drafts and RFQ messages
are text (R1). Every state change (a quote saved, a match approved, a template saved or deleted)
appends a hash-chained event through the `EventSink` (rule 6).

The synthetic demo catalogue and price files are seeded ONLY when `demo=True`; they are fictional
merchants with invented prices, labelled as such in every document. Without it the catalogue and
the offer store start empty.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Protocol

import yaml
from employees.purchasing.service_port import Conflict, NotFound

from aiplat.ctx import Ctx
from aiplat.profile import ResolvedProfile
from components.core.ports import Clock
from components.evidence import EventLog
from components.job_kits import JobKitLibrary, KitError, ResolvedKit, load_library
from components.matching.approvals import signature
from components.matching.catalogue import load_catalogue
from components.matching.classification import load_classification
from components.matching.engine import MatchingEngine
from components.matching.index import CatalogIndex
from components.matching.models import CheckOutcome, OrderLine
from components.matching.ontology import default_data_dir, load_ontology
from components.matching.policy import GatePolicy
from components.pricebook import (
    ImportSummary,
    MerchantInfo,
    PriceBookError,
    RequestContext,
    RequestTemplate,
    RfqMode,
    RfqTemplate,
    build_price_book,
    draft_requests,
    draft_rfq_messages,
    price_books_ui,
    rfq_for_gaps,
    summaries_from_reports,
)
from components.pricing import PricingConfig
from components.quoting import (
    OptionsConfig,
    OptionsError,
    QuoteResult,
    QuotingContext,
    QuotingError,
    approve_match,
    build_quote,
    order_lines_from_kit,
    quote_draft_ui,
    quote_options,
    quote_options_ui,
)
from components.quoting.identity import carries_identity, is_named
from components.quoting.loading import load_price_files, specs_from_manifest

from .quote_store import (
    ApprovedMatchStore,
    ImportStore,
    InMemoryApprovedMatchStore,
    InMemoryImportStore,
    InMemoryOfferStore,
    InMemoryQuoteSnapshotStore,
    InMemoryTemplateStore,
    OfferStore,
    QuoteSnapshot,
    QuoteSnapshotStore,
    TemplateStore,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "profiles" / "data"
DEMO_LABEL = ("SYNTHETIC/ILLUSTRATIVE DEMO DATA: fictional merchants, invented prices and invented "
              "reviewer decisions; not real prices, not a supplier quote; nothing is sent or "
              "ordered")
# Invented buyers of the two synthetic demo tenants (same table as scripts/export_demo_data.py).
DEMO_BUYERS = {
    "demo-tenant-a": ("Alex Example", "Example Bathrooms Ltd (fictional)"),
    "demo-tenant-b": ("Sam Sample", "Sample Fitters Ltd (fictional)"),
}
LINE_STATE_TO_CHOICE = {"include": "needed", "not_needed": "not_needed", "have": "already_have"}
NOTE_MAX = 500
_CONTROL = re.compile(r"[\x00-\x1f\x7f<>]")


class QuoteInputError(Exception):
    """The caller's input cannot be resolved or quoted (HTTP 422)."""


class QuoteUnavailableError(Exception):
    """The deployment has no data for this profile (HTTP 503)."""


class EventSink(Protocol):
    def append(self, tenant_id: str, kind: str, subject_id: str,
               payload: Mapping[str, Any]) -> None: ...


class EventLogSink:
    """Default adapter: the existing hash-chained `EventLog`. `payload["actor"]` is the actor."""

    def __init__(self, log: EventLog) -> None:
        self._log = log

    def append(self, tenant_id: str, kind: str, subject_id: str,
               payload: Mapping[str, Any]) -> None:
        actor = str(payload.get("actor") or "system")
        self._log.append(tenant_id, subject_id, actor, kind, payload)


@dataclass(frozen=True)
class Stores:
    offers: OfferStore
    approvals: ApprovedMatchStore
    imports: ImportStore
    templates: TemplateStore
    snapshots: QuoteSnapshotStore


@dataclass(frozen=True)
class DemoWorld:
    """What the demo build adds: the SYNTHETIC merchants of the manifest."""

    merchants: tuple[MerchantInfo, ...]

    def account_refs(self, tenant_id: str) -> dict[str, str]:
        """Invented account references, as scripts/export_demo_data.py makes them."""
        letter = tenant_id[-1].upper()
        ordered = sorted(self.merchants, key=lambda m: m.merchant_id)
        return {m.merchant_id: f"ACC-{letter}-{1001 + i}" for i, m in enumerate(ordered)}


@dataclass
class QuoteService:
    profile: ResolvedProfile
    clock: Clock
    events: EventSink
    stores: Stores
    engine_or_none: MatchingEngine | None
    pricing: PricingConfig
    library: JobKitLibrary | None
    request_template: RequestTemplate
    rfq_template: RfqTemplate
    demo: DemoWorld | None = None
    buyers: Mapping[str, tuple[str, str]] = field(default_factory=dict)

    # ------------------------------------------------------------------ plumbing

    @property
    def label(self) -> str | None:
        return DEMO_LABEL if self.demo is not None else None

    @property
    def engine(self) -> MatchingEngine:
        if self.engine_or_none is None:
            raise QuoteUnavailableError("no catalogue is loaded in this deployment")
        return self.engine_or_none

    def _ctx(self) -> QuotingContext:
        return QuotingContext(engine=self.engine, offers=self.stores.offers,
                              pricing=self.pricing, clock=self.clock)

    def _library(self) -> JobKitLibrary:
        if self.library is None:
            raise QuoteUnavailableError("no job-kit library for this deployment profile")
        return self.library

    def _resolve(self, scope_id: str, kit: Mapping[str, Any]) -> ResolvedKit:
        lib = self._library()
        values = {**kit.get("measurements", {}), **kit.get("allowances", {})}
        try:
            return lib.resolve(scope_id, kit.get("answers", {}), values, kit.get("choices", {}))
        except KitError as exc:
            raise QuoteInputError(str(exc)) from exc

    def _lines(self, scope_id: str, kit: Mapping[str, Any]) -> Any:
        resolved = self._resolve(scope_id, kit)
        states = kit.get("lines", {})
        choices = {k: LINE_STATE_TO_CHOICE[v] for k, v in states.items() if v != "include"}
        try:
            return resolved, order_lines_from_kit(resolved, choices)
        except QuotingError as exc:
            raise QuoteInputError(str(exc)) from exc

    def _quote(self, tenant_id: str, scope_id: str, kit: Mapping[str, Any]) -> QuoteResult:
        _, lines = self._lines(scope_id, kit)
        try:
            return build_quote(self._ctx(), tenant_id, lines)
        except QuotingError as exc:
            raise QuoteInputError(str(exc)) from exc

    def _snapshot(self, ctx: Ctx, snapshot_id: str) -> QuoteSnapshot:
        snap = self.stores.snapshots.for_tenant(ctx.tenant_id).get(snapshot_id)
        if snap is None or snap.tenant_id != ctx.tenant_id:
            raise NotFound(snapshot_id)
        return snap

    # ------------------------------------------------------------------ kits

    def resolve_kit(self, scope_id: str, kit: Mapping[str, Any]) -> dict[str, Any]:
        resolved = self._resolve(scope_id, kit)
        states = kit.get("lines", {})
        return resolved_kit_doc(resolved, states)

    # ------------------------------------------------------------------ quotes

    def create_quote(self, ctx: Ctx, scope_id: str, kit: dict[str, Any]) -> dict[str, Any]:
        quote = self._quote(ctx.tenant_id, scope_id, kit)
        doc = quote_draft_ui(quote)
        return self._save(ctx, scope_id, kit, doc, None, "quote_created", {})

    def _save(self, ctx: Ctx, scope_id: str, kit: dict[str, Any], doc: dict[str, Any],
              parent: str | None, kind: str | None, extra: Mapping[str, Any]
              ) -> dict[str, Any]:
        snap = QuoteSnapshot(ctx.tenant_id, scope_id, kit, doc, self.clock.now(), ctx.actor,
                             parent)
        new_id = self.stores.snapshots.for_tenant(ctx.tenant_id).add(snap)
        if kind is not None:  # a decision's snapshot follows its own match_approved event
            self.events.append(ctx.tenant_id, kind, new_id, {
                "actor": ctx.actor, "scope_id": scope_id, "quote_id": doc.get("quote_id"),
                "parent": parent, **extra})
        return {"id": new_id, "quote": doc}

    def get_quote(self, ctx: Ctx, quote_id: str) -> dict[str, Any]:
        snap = self._snapshot(ctx, quote_id)
        return {"id": snap.id, "quote": snap.quote}

    def options(self, ctx: Ctx, quote_id: str, *, budget: str | None, required_by: str | None,
                max_deliveries: int | None, preferred: Sequence[str]) -> dict[str, Any]:
        snap = self._snapshot(ctx, quote_id)
        quote = self._quote(ctx.tenant_id, snap.scope_id, snap.kit)
        try:
            config = OptionsConfig(
                budget_total=Decimal(budget) if budget is not None else None,
                required_by=date.fromisoformat(required_by) if required_by else None,
                max_deliveries=max_deliveries)
            result = quote_options(quote, self.pricing, self.clock, preferred=list(preferred),
                                   config=config)
        except (OptionsError, InvalidOperation, ValueError) as exc:
            raise QuoteInputError(f"options: {exc}") from exc
        return quote_options_ui(result)

    # ------------------------------------------------------------------ price book

    def _merchants(self, tenant_id: str) -> tuple[MerchantInfo, ...]:
        if self.demo is not None:
            return self.demo.merchants
        found = sorted({o.merchant_id for o in self.stores.offers.for_tenant(tenant_id).search()})
        try:
            return tuple(MerchantInfo(m, m) for m in found)
        except PriceBookError:
            return ()

    def _request_context(self, ctx: Ctx) -> RequestContext:
        name, company = self.buyers.get(ctx.tenant_id, (ctx.user_id, ctx.tenant_id))
        refs = (self.demo.account_refs(ctx.tenant_id)
                if self.demo and ctx.tenant_id in DEMO_BUYERS else {})
        return RequestContext(buyer_name=name, buyer_company=company, account_references=refs)

    def price_books(self, ctx: Ctx, quote_id: str | None) -> dict[str, Any]:
        quote = None
        if quote_id is not None:
            snap = self._snapshot(ctx, quote_id)
            quote = self._quote(ctx.tenant_id, snap.scope_id, snap.kit)
        merchants = self._merchants(ctx.tenant_id)
        book = build_price_book(
            self.stores.offers, ctx.tenant_id, merchants, self.pricing, self.clock, quote=quote,
            imports=self.stores.imports.for_tenant(ctx.tenant_id).list())
        rctx = self._request_context(ctx)
        drafts = draft_requests(self.request_template, book.merchants, rctx)
        names = {m.merchant_id: m.name for m in merchants}
        groups = rfq_for_gaps(book.gaps)
        rfq = {mode: draft_rfq_messages(self.rfq_template, groups, names, rctx, mode)
               for mode in (RfqMode.PER_SUPPLIER, RfqMode.PER_ITEM)}
        return price_books_ui(book, drafts, label=self.label,
                              rfq_per_supplier=rfq[RfqMode.PER_SUPPLIER],
                              rfq_per_item=rfq[RfqMode.PER_ITEM])

    # ------------------------------------------------------------------ decisions

    def decide(self, ctx: Ctx, quote_id: str, line_id: str, sku_id: str,
               note: str | None) -> dict[str, Any]:
        """A person approves one product for one review line. Refused when the product failed a
        deterministic check of the line (rule 3) or is not among the line's candidates, which
        would be a substitution needing its own approval (rule 2). Idempotent."""
        snap = self._snapshot(ctx, quote_id)
        quote = self._quote(ctx.tenant_id, snap.scope_id, snap.kit)
        result = next((r for r in quote.results if r.line_id == line_id), None)
        if result is None:
            raise NotFound(line_id)
        order = result.request.order_line
        parsed = self.engine.index.parser.parse(order)
        sig = signature(parsed)
        record = self.engine.store.lookup(ctx.tenant_id, sig) if sig else None
        if record is not None and sku_id in record.sku_ids:
            return {"id": snap.id, "quote": quote_draft_ui(quote)}  # already decided: no-op
        if result.bucket.value != "review":
            raise Conflict("the line is not waiting for a decision")
        self._vet_candidate(ctx.tenant_id, order, sku_id)
        item = self.engine.index.get(sku_id)
        if item is None:
            raise Conflict("unknown product")
        if is_named(parsed) and not carries_identity(parsed, item,
                                                     self.engine.index.ontology.normaliser):
            raise Conflict("this product does not carry the brand, MPN or GTIN the line names: "
                           "that is a substitution and needs a substitution approval")
        clean = _CONTROL.sub(" ", note or "").strip()[:NOTE_MAX]
        self.events.append(ctx.tenant_id, "match_approved", line_id, {
            "actor": ctx.actor, "quote_id": snap.id, "line_id": line_id, "sku_id": sku_id,
            "note": clean})
        try:
            approve_match(self._ctx(), ctx.tenant_id, result.request, sku_id, ctx.actor)
        except QuotingError as exc:
            raise Conflict(str(exc)) from exc
        after = self._quote(ctx.tenant_id, snap.scope_id, snap.kit)
        return self._save(ctx, snap.scope_id, snap.kit, quote_draft_ui(after), snap.id,
                          None, {})

    def _vet_candidate(self, tenant_id: str, order: OrderLine, sku_id: str) -> None:
        found = self.engine.match(tenant_id, order)
        cand = next((c for c in (*found.top, *found.group) if c.item.sku_id == sku_id), None)
        if cand is None:
            raise Conflict("this product is not a candidate for the line: choosing it would be a "
                           "substitution and needs a substitution approval")
        if any(c.outcome is CheckOutcome.FAIL for c in cand.checks):
            raise Conflict("this product failed a check of the line's attributes and cannot be "
                           "approved for it")

    # ------------------------------------------------------------------ templates

    def list_templates(self, ctx: Ctx) -> list[dict[str, Any]]:
        return self.stores.templates.for_tenant(ctx.tenant_id).list()

    def put_template(self, ctx: Ctx, doc: dict[str, Any]) -> dict[str, Any]:
        if self.library is not None and doc["scopeId"] not in self.library.scope_ids():
            raise QuoteInputError("unknown scope")
        saved = self.stores.templates.for_tenant(ctx.tenant_id).put(doc)
        self.events.append(ctx.tenant_id, "kit_template_saved", saved["id"], {
            "actor": ctx.actor, "name": saved["name"], "scope_id": saved["scopeId"]})
        return saved

    def delete_template(self, ctx: Ctx, template_id: str) -> None:
        if not self.stores.templates.for_tenant(ctx.tenant_id).delete(template_id):
            raise NotFound(template_id)
        self.events.append(ctx.tenant_id, "kit_template_deleted", template_id, {
            "actor": ctx.actor})


# --------------------------------------------------------------------------- documents


def resolved_kit_doc(kit: ResolvedKit, states: Mapping[str, str]) -> dict[str, Any]:
    """The resolved kit as plain JSON: Decimal quantities and values are strings (rule 5)."""
    return {
        "format": "resolved-kit/1", "scope_id": kit.scope_id, "version": kit.version,
        "label": kit.label, "status": kit.status, "ok": kit.ok,
        "answers": dict(kit.answers), "values": {k: str(v) for k, v in kit.values.items()},
        "modules": list(kit.modules),
        "lines": [{
            "id": x.id, "module": x.module, "description": x.description, "spec": x.spec,
            "unit": x.unit, "quantity": str(x.quantity), "quantity_formula": x.quantity_formula,
            "kind": x.kind, "forced_by": dict(x.forced_by) if x.forced_by else None,
            "option": ({"id": x.option.id, "label": x.option.label, "spec": x.option.spec}
                       if x.option else None),
            "state": states.get(x.id, "include"),
            "assumption_source": x.assumption_source,
        } for x in kit.lines],
        "assumptions": [{"kind": a.kind, "key": a.key, "value": a.value, "label": a.label,
                         "source": a.source} for a in kit.assumptions],
        "rule_results": [{"id": r.id, "applies": r.applies, "ok": r.ok,
                          "missing": list(r.missing), "clashing": list(r.clashing)}
                         for r in kit.rule_results],
    }


# --------------------------------------------------------------------------- construction


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def build_quote_service(
    profile: ResolvedProfile, *, clock: Clock, events: EventSink | None = None,
    demo: bool = False, stores: Stores | None = None,
) -> QuoteService:
    """Wire the pipeline from the resolved profile. `demo=True` seeds the SYNTHETIC catalogue and
    price files (InMemory stores only); otherwise the catalogue and offers start empty."""
    resolved = profile.profile.model_dump(mode="json")
    pricing = PricingConfig.from_mapping(resolved)
    policy = GatePolicy.from_mapping(resolved["matching"])
    market = profile.profile.id
    try:
        data = default_data_dir(market)
        registry = load_classification(data / "classification.yaml")
        ontology = load_ontology(data / "ontology", registry)
        items = load_catalogue(data / "catalogue_seed.yaml", ontology, registry) if demo else []
    except FileNotFoundError as exc:
        raise QuoteUnavailableError(f"no matching data for profile {market}") from exc
    own = stores or Stores(InMemoryOfferStore(pricing), InMemoryApprovedMatchStore(clock),
                           InMemoryImportStore(), InMemoryTemplateStore(),
                           InMemoryQuoteSnapshotStore())
    engine = (MatchingEngine(CatalogIndex(items, ontology), own.approvals, policy=policy)
              if items else None)  # an index cannot be empty: no catalogue, no matching
    kits = DATA / "job_kits" / market
    pb = DATA / "pricebook"
    world = _seed_demo(own, pricing) if demo else None
    return QuoteService(
        profile=profile, clock=clock, events=events or EventLogSink(EventLog(clock)), stores=own,
        engine_or_none=engine, pricing=pricing,
        library=load_library(kits) if kits.is_dir() else None,
        request_template=RequestTemplate.from_mapping(
            yaml.safe_load((pb / "request_templates.yaml").read_text(encoding="utf-8"))),
        rfq_template=RfqTemplate.from_mapping(
            yaml.safe_load((pb / "rfq_templates.yaml").read_text(encoding="utf-8"))),
        demo=world, buyers=DEMO_BUYERS if demo else {})


def _seed_demo(stores: Stores, pricing: PricingConfig) -> DemoWorld:
    if not isinstance(stores.offers, InMemoryOfferStore) or not isinstance(
            stores.imports, InMemoryImportStore):
        raise QuoteUnavailableError("the demo data can only be seeded into the in-memory stores")
    qdir = DATA / "quoting"
    manifest = _read_json(qdir / "manifest.json")
    texts = {f["file"]: (qdir / f["file"]).read_text(encoding="utf-8") for f in manifest["files"]}
    reports = load_price_files(stores.offers, specs_from_manifest(manifest, texts), pricing)
    by_source = {f["source_id"]: f["merchant_id"] for f in manifest["files"]}
    summaries: tuple[ImportSummary, ...] = summaries_from_reports(reports, by_source)
    for s in summaries:
        if s.tenant_id is None:
            stores.imports.add_shared(s)
        else:
            stores.imports.for_tenant(s.tenant_id).add(s)
    merchants = tuple(MerchantInfo(m["merchant_id"], m["name"]) for m in manifest["merchants"])
    return DemoWorld(merchants=merchants)
