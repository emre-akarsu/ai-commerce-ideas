# ruff: noqa: E501
"""Buy-side RFQ MVP operations of the purchasing service (docs/architecture/api-contract-mvp.md).

A mixin for ``PurchasingService`` so ``service.py`` stays readable. It adds, all tenant-scoped and all
audited through the event log (hard rule 6: no status is written here; the one state change, returning a
request to its open questions, goes through ``Workflow`` via the service's ``_move``):

- supplier profile, admin attestation, suppression and the ``rfqs/prepare`` guards (FR-SU-2..4);
- vendor CSV import (FR-SU-1);
- the assumption ledger (FR-IN-4);
- setup readiness and go-live, which is RECORDED, NOT ENFORCED (FR-AD-1);
- the evidence export (FR-AU-2).

Nothing here sends mail, holds a transport or reads a vendor's text as an instruction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from aiplat.ctx import Ctx, Role, require
from aiplat.profile import ResolvedProfile
from components.core.domain import Attribute, AttrSource, Request, RequestState, Vendor
from components.core.ports import Clock
from components.core.store import NotFoundError, TenantIsolationError, TenantStore
from components.imports.safety import clean_text
from components.parts.families.registry import get_family
from components.parts.spec.normaliser import MAX_QUESTIONS
from components.suppliers import (
    Assumption,
    Money,
    SupplierProfile,
    SupplierStore,
    Verification,
    confidence_label,
    parse_vendor_csv,
)
from components.suppliers.models import AccountType, ContactKind

from .service_port import Conflict, NotFound
from .views import (
    AssumptionView,
    AuditExport,
    RejectedRowView,
    RequestDetail,
    SetupItem,
    SetupView,
    SupplierProfileView,
    VendorImportResult,
    VendorView,
    VerificationView,
)

S = RequestState

EVT_SUPPLIER_ATTESTED = "supplier.attested"
EVT_SUPPLIER_VERIFICATION_RESET = "supplier.verification_reset"
EVT_SUPPLIER_PROFILE_SET = "supplier.profile_set"
EVT_SUPPLIER_SUPPRESSED = "supplier.suppressed"
EVT_SUPPLIER_UNSUPPRESSED = "supplier.unsuppressed"
EVT_VENDORS_IMPORTED = "import.vendors"
EVT_ASSUMPTION_CREATED = "assumption.created"
EVT_ASSUMPTION_CONFIRMED = "assumption.confirmed"
EVT_ASSUMPTION_INVALIDATED = "assumption.invalidated"
EVT_SETUP_GO_LIVE = "setup.go_live"
# Event names written by service.py that the setup checks read back (pinned by a test).
EVT_RFQ_PREPARED_NAME = "rfq.prepared"
EVT_KILL_SWITCH_NAME = "send.kill_switch"

GATE_PREPARE = "rfqs/prepare"
GATE_QUOTE_BASIS = "quote_comparison"
MAX_IMPORT_ROWS = 2000
SENDING_DOMAIN_DETAIL = "confirm SPF, DKIM and DMARC for the alias domain"
MANUAL_SETUP_ITEMS = frozenset({"sending_domain"})  # shown, never checked here
_PROFILE_FIELDS = (
    "account_number", "account_type", "credit_days", "delivery_threshold",
    "quote_validity_days", "contact_kind",
)


def _vendor_label(vendor: Vendor) -> str:
    return clean_text(vendor.name, limit=80)


def assumption_view(a: Assumption) -> AssumptionView:
    return AssumptionView(
        id=a.id, request_id=a.request_id, statement=a.statement, source=a.source,
        confidence=a.confidence, status=a.status, critical=a.critical, gate=a.gate,
        created_at=a.created_at, resolved_by=a.resolved_by, resolved_at=a.resolved_at)


def assumption_rows_for(
    attributes: Mapping[str, Attribute], *, critical_names: frozenset[str],
) -> list[tuple[str, Attribute, str, bool]]:
    """The attributes of a spec that were NOT stated by the user and so need a ledger row:
    ``(name, attribute, ledger source, critical)``. A rule default is a ``default_template``; a model
    inference is a ``model_inference`` and is ALWAYS critical (R3: it can never satisfy a critical
    attribute, and nothing but a person confirms it). Values looked up from a standard for a
    designation the user typed, and values the user typed, are not assumptions."""
    rows: list[tuple[str, Attribute, str, bool]] = []
    for name, attr in sorted(attributes.items()):
        if attr.source is AttrSource.RULE:
            rows.append((name, attr, "default_template", name in critical_names))
        elif attr.source is AttrSource.MODEL_INFERENCE:
            rows.append((name, attr, "model_inference", True))
    return rows


class MvpOps:
    """Mixed into ``PurchasingService``; the attributes below are provided by it."""

    if TYPE_CHECKING:
        _suppliers: SupplierStore
        _log: Any
        _clock: Clock
        _settings: Any
        _profile: ResolvedProfile | None
        _identities: Any
        _send: Any
        _ids: Callable[[str], str]

        def _ts(self, tenant_id: str) -> TenantStore: ...
        @staticmethod
        def _get(repo: Any, obj_id: str) -> Any: ...
        def _load_request(self, ctx: Ctx, request_id: str) -> Request: ...
        def _emit(self, ctx_tenant: str, request_id: str | None, actor: str, etype: str,
                  payload: Mapping[str, Any]) -> Any: ...
        def _move(self, request: Request, to: RequestState, actor: str,
                  payload: Mapping[str, Any] | None = None) -> None: ...
        def _detail(self, request: Request) -> RequestDetail: ...

    # ------------------------------------------------------------ supplier profile

    def _sup(self, tenant_id: str) -> Any:
        return self._suppliers.for_tenant(tenant_id)

    def _profile_of(self, tenant_id: str, vendor_id: str) -> SupplierProfile:
        found = self._sup(tenant_id).profiles.find(vendor_id)
        return found if found is not None else SupplierProfile(tenant_id=tenant_id, vendor_id=vendor_id)

    def _save_profile(self, profile: SupplierProfile) -> SupplierProfile:
        repo = self._sup(profile.tenant_id).profiles
        if repo.find(profile.vendor_id) is None:
            return repo.add(profile)  # type: ignore[no-any-return]
        return repo.save(profile)  # type: ignore[no-any-return]

    def _vendor_of(self, tenant_id: str, vendor_id: str) -> Vendor:
        vendor: Vendor = self._get(self._ts(tenant_id).vendors, vendor_id)
        return vendor

    @staticmethod
    def _vendor_view(v: Vendor, p: SupplierProfile) -> VendorView:
        ver = p.verification
        return VendorView(
            **v.model_dump(),
            profile=SupplierProfileView(
                account_number=p.account_number, account_type=p.account_type,
                credit_days=p.credit_days, delivery_threshold=p.delivery_threshold,
                quote_validity_days=p.quote_validity_days, contact_kind=p.contact_kind,
                verification=VerificationView(
                    state=ver.state, attested_by=ver.attested_by, attested_at=ver.attested_at,
                    note=ver.note),
                suppressed=p.suppressed))

    def list_vendor_views(self, ctx: Ctx) -> list[VendorView]:
        require(ctx, Role.BUYER)
        profiles = {p.vendor_id: p for p in self._sup(ctx.tenant_id).profiles.list()}
        return [
            self._vendor_view(v, profiles.get(v.id) or SupplierProfile(
                tenant_id=ctx.tenant_id, vendor_id=v.id))
            for v in self._ts(ctx.tenant_id).vendors.list()]

    def get_vendor_view(self, ctx: Ctx, vendor_id: str) -> VendorView:
        require(ctx, Role.BUYER)
        vendor = self._vendor_of(ctx.tenant_id, vendor_id)
        return self._vendor_view(vendor, self._profile_of(ctx.tenant_id, vendor.id))

    def set_supplier_profile(
        self, ctx: Ctx, vendor_id: str, *, account_number: str | None = None,
        account_type: AccountType | None = None, credit_days: int | None = None,
        delivery_threshold: Money | None = None, quote_validity_days: int | None = None,
        contact_kind: ContactKind = "unknown",
    ) -> VendorView:
        """Set the six editable fields (all of them: a field left out is cleared). ``verification`` and
        ``suppressed`` cannot be set here."""
        require(ctx, Role.BUYER)
        vendor = self._vendor_of(ctx.tenant_id, vendor_id)
        current = self._profile_of(ctx.tenant_id, vendor.id)
        wanted: dict[str, Any] = {
            "account_number": account_number, "account_type": account_type,
            "credit_days": credit_days, "delivery_threshold": delivery_threshold,
            "quote_validity_days": quote_validity_days, "contact_kind": contact_kind}
        self._check_threshold_currency(delivery_threshold)
        try:
            updated = SupplierProfile.model_validate({
                **current.model_dump(), **{
                    k: (v.model_dump() if isinstance(v, Money) else v) for k, v in wanted.items()}})
        except ValidationError as exc:
            fields = sorted({str(e["loc"][0]) for e in exc.errors() if e.get("loc")})
            raise Conflict("invalid profile field(s): " + ", ".join(fields)) from exc
        changed = [f for f in _PROFILE_FIELDS if getattr(updated, f) != getattr(current, f)]
        saved = self._save_profile(updated)
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_SUPPLIER_PROFILE_SET, {
            "vendor_id": vendor.id, "changed": changed, "via": "profile"})
        return self._vendor_view(vendor, saved)

    def _check_threshold_currency(self, threshold: Money | None) -> None:
        if threshold is None or self._profile is None:
            return
        if threshold.currency not in self._profile.profile.money.accepted_currencies:
            raise Conflict("delivery_threshold: currency is not accepted by the active profile")

    def attest_vendor(self, ctx: Ctx, vendor_id: str, *, note: str | None = None) -> VendorView:
        """Admin attests that the supplier was checked. There is no second-person confirmation
        (listed in known-gaps.md)."""
        require(ctx, Role.ADMIN)
        vendor = self._vendor_of(ctx.tenant_id, vendor_id)
        current = self._profile_of(ctx.tenant_id, vendor.id)
        clean_note = clean_text(note, limit=200) if note else None
        saved = self._save_profile(current.model_copy(update={"verification": Verification(
            state="attested", attested_by=ctx.actor, attested_at=self._clock.now(),
            note=clean_note)}))
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_SUPPLIER_ATTESTED, {
            "vendor_id": vendor.id, "has_note": clean_note is not None})
        return self._vendor_view(vendor, saved)

    def _reset_verification(self, ctx: Ctx, vendor: Vendor, reason: str) -> None:
        current = self._profile_of(ctx.tenant_id, vendor.id)
        if current.verification.state != "attested":
            return
        self._save_profile(current.model_copy(update={"verification": Verification()}))
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_SUPPLIER_VERIFICATION_RESET, {
            "vendor_id": vendor.id, "reason": reason})

    def suppress_vendor(self, ctx: Ctx, vendor_id: str) -> VendorView:
        require(ctx, Role.BUYER)
        vendor = self._vendor_of(ctx.tenant_id, vendor_id)
        return self._vendor_view(vendor, self._suppress(ctx.tenant_id, vendor, ctx.actor, "manual"))

    def unsuppress_vendor(self, ctx: Ctx, vendor_id: str) -> VendorView:
        require(ctx, Role.ADMIN)
        vendor = self._vendor_of(ctx.tenant_id, vendor_id)
        current = self._profile_of(ctx.tenant_id, vendor.id)
        if not current.suppressed:
            return self._vendor_view(vendor, current)
        saved = self._save_profile(current.model_copy(update={"suppressed": False}))
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_SUPPLIER_UNSUPPRESSED, {"vendor_id": vendor.id})
        return self._vendor_view(vendor, saved)

    def _suppress(self, tenant_id: str, vendor: Vendor, actor: str, reason: str,
                  request_id: str | None = None) -> SupplierProfile:
        """Mark suppressed, stop the vendor's pending follow-ups (no further sends) and audit it.
        Already suppressed: nothing changes and nothing is appended."""
        current = self._profile_of(tenant_id, vendor.id)
        if current.suppressed:
            return current
        saved = self._save_profile(current.model_copy(update={"suppressed": True}))
        ts = self._ts(tenant_id)
        for rfq in ts.rfqs.list(lambda r: r.vendor_id == vendor.id):
            self._send.cancel_follow_ups(tenant_id, rfq.id)
        self._emit(tenant_id, request_id, actor, EVT_SUPPLIER_SUPPRESSED, {
            "vendor_id": vendor.id, "reason": reason})
        return saved

    def check_supplier_guards(self, tenant_id: str, vendors: list[Vendor]) -> None:
        """The ``rfqs/prepare`` guards, all ``Conflict`` and all before anything is stored."""
        for v in vendors:
            p = self._profile_of(tenant_id, v.id)
            if p.verification.state != "attested":
                raise Conflict(f"vendor not verified: {_vendor_label(v)}")
            if p.suppressed or v.opted_out:
                raise Conflict(f"vendor suppressed: {_vendor_label(v)}")
            if p.contact_kind == "individual" and not self._settings.allow_individual_subscribers:
                raise Conflict("individual subscriber: not enabled")

    def check_not_suppressed(self, tenant_id: str, vendor: Vendor) -> None:
        if self._profile_of(tenant_id, vendor.id).suppressed or vendor.opted_out:
            raise Conflict(f"vendor suppressed: {_vendor_label(vendor)}")

    # ------------------------------------------------------------ vendor CSV import

    def import_vendors(self, ctx: Ctx, data: bytes) -> VendorImportResult:
        require(ctx, Role.BUYER)
        if len(data) > self._settings.max_csv_bytes:
            raise Conflict("file too large")
        try:
            parsed = parse_vendor_csv(data, max_rows=MAX_IMPORT_ROWS)
        except ValueError as exc:
            raise Conflict(str(exc)) from exc
        repo = self._ts(ctx.tenant_id).vendors
        known = repo.list()
        created = updated = 0
        rejected = [RejectedRowView(row=r.row, reason=r.reason) for r in parsed.rejected]
        for row in parsed.rows:
            same = next((v for v in known if v.domain.lower() == row.domain
                         and v.contact_email.lower() == row.contact_email), None)
            clash = next((v for v in known if v is not same and (
                v.domain.lower() == row.domain or v.contact_email.lower() == row.contact_email)), None)
            if same is None and clash is not None:
                rejected.append(RejectedRowView(
                    row=row.row, reason="domain or contact_email belongs to an existing supplier "
                    "with a different contact: change contacts through the supplier record"))
                continue
            if same is None:
                vendor = Vendor(id=self._ids("v"), tenant_id=ctx.tenant_id, name=row.name,
                                domain=row.domain, contact_email=row.contact_email, phone=row.phone)
                repo.add(vendor)
                known.append(vendor)
                self._save_profile(SupplierProfile(
                    tenant_id=ctx.tenant_id, vendor_id=vendor.id,
                    account_number=row.account_number, account_type=row.account_type,
                    credit_days=row.credit_days, quote_validity_days=row.quote_validity_days,
                    contact_kind=row.contact_kind or "unknown"))
                self._emit(ctx.tenant_id, None, ctx.actor, "vendor.upserted", {
                    "vendor_id": vendor.id, "created": True, "opted_out": False,
                    "preferred": True, "via": "import"})
                created += 1
                continue
            self._update_from_row(ctx, same, row)
            updated += 1
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_VENDORS_IMPORTED, {
            "rows": len(parsed.rows) + len(parsed.rejected), "created": created,
            "updated": updated, "rejected": len(rejected)})
        return VendorImportResult(
            created=created, updated=updated, rejected=sorted(rejected, key=lambda r: r.row))

    def _update_from_row(self, ctx: Ctx, vendor: Vendor, row: Any) -> None:
        """A row for a supplier we already have changes its profile fields only, and only the ones the
        row fills in. Name, phone, domain, contact and verification are untouched."""
        current = self._profile_of(ctx.tenant_id, vendor.id)
        patch = {k: getattr(row, k) for k in (
            "account_number", "account_type", "credit_days", "quote_validity_days", "contact_kind")
            if getattr(row, k) is not None}
        saved = self._save_profile(current.model_copy(update=patch))
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_SUPPLIER_PROFILE_SET, {
            "vendor_id": vendor.id, "via": "import",
            "changed": [k for k in patch if getattr(saved, k) != getattr(current, k)]})

    # ------------------------------------------------------------ assumption ledger

    def _rows(self, tenant_id: str, request_id: str) -> list[Assumption]:
        return list(self._sup(tenant_id).assumptions.list(lambda a: a.request_id == request_id))

    def _assumption_views(self, tenant_id: str, request_id: str) -> list[AssumptionView]:
        return [assumption_view(a) for a in self._rows(tenant_id, request_id)]

    def _new_assumption(self, request: Request, *, statement: str, source: str, confidence: str,
                        critical: bool, gate: str | None, attribute: str | None = None,
                        value: str | None = None) -> Assumption:
        # Derived from the request id and a per-request count (rows are never deleted), not from the
        # service's id generator, so adding the ledger does not move any other generated id.
        n = len(self._rows(request.tenant_id, request.id)) + 1
        row = Assumption(
            id=f"asm-{request.id}-{n:03d}", tenant_id=request.tenant_id, request_id=request.id,
            statement=statement, source=source, confidence=confidence,  # type: ignore[arg-type]
            critical=critical, gate=gate, created_at=self._clock.now(), attribute=attribute,
            value=value)
        self._sup(request.tenant_id).assumptions.add(row)
        self._emit(request.tenant_id, request.id, "agent", EVT_ASSUMPTION_CREATED, {
            "assumption_id": row.id, "source": row.source, "critical": row.critical,
            "attribute": attribute, "gate": gate})
        return row

    def _record_assumptions(self, request: Request, attributes: Mapping[str, Attribute]) -> None:
        """Ledger rows for the spec's values the requester did not state (rule defaults, inferences).
        A value that already has a live (open or confirmed) row is not recorded twice."""
        if request.family is None:
            return
        fam = get_family(request.family)
        live = {(a.attribute, a.value) for a in self._rows(request.tenant_id, request.id)
                if a.attribute and a.status != "invalidated"}
        for name, attr, source, critical in assumption_rows_for(
                attributes, critical_names=frozenset(fam.critical_attributes)):
            if (name, attr.value) in live:
                continue
            unit = f" {attr.unit}" if attr.unit else ""
            self._new_assumption(
                request, source=source, confidence=confidence_label(attr.confidence),
                statement=clean_text(f"Assumed {name} = {attr.value}{unit}: {attr.source_ref}".strip(
                    " :"), limit=300),
                critical=critical, gate=GATE_PREPARE if critical else None,
                attribute=name, value=attr.value)

    def _record_quote_basis_assumption(self, request: Request) -> None:
        """The profile's quote-basis default is an assumption about what suppliers' prices include."""
        if self._profile is None:
            return
        tax = self._profile.profile.tax
        if tax.quote_basis_default == "unknown":
            return
        basis = "exclusive of" if tax.quote_basis_default == "ex_tax" else "inclusive of"
        self._new_assumption(
            request, source="default_template", confidence="medium", critical=False,
            gate=GATE_QUOTE_BASIS,
            statement=f"Quoted prices are assumed to be {basis} {tax.name} unless the supplier states otherwise.")

    def open_critical_count(self, tenant_id: str, request_id: str) -> int:
        return sum(1 for a in self._rows(tenant_id, request_id) if a.critical and a.status == "open")

    def check_assumptions_closed(self, tenant_id: str, request_id: str) -> None:
        n = self.open_critical_count(tenant_id, request_id)
        if n:
            raise Conflict(f"assumptions open: {n} critical assumption(s) unconfirmed")

    def list_assumptions(self, ctx: Ctx, request_id: str) -> list[AssumptionView]:
        require(ctx, Role.REQUESTER)
        request = self._load_request(ctx, request_id)
        return self._assumption_views(ctx.tenant_id, request.id)

    def _open_row(self, ctx: Ctx, request: Request, assumption_id: str) -> Assumption:
        try:
            row: Assumption = self._sup(ctx.tenant_id).assumptions.get(assumption_id)
        except (NotFoundError, TenantIsolationError) as exc:
            raise NotFound(assumption_id) from exc
        if row.request_id != request.id:
            raise NotFound(assumption_id)
        if row.status != "open":
            raise Conflict(f"assumption is already {row.status}")
        return row

    def _resolve(self, ctx: Ctx, row: Assumption, status: str, etype: str) -> None:
        self._sup(ctx.tenant_id).assumptions.save(row.model_copy(update={
            "status": status, "resolved_by": ctx.actor, "resolved_at": self._clock.now()}))
        self._emit(ctx.tenant_id, row.request_id, ctx.actor, etype, {
            "assumption_id": row.id, "critical": row.critical, "source": row.source,
            "attribute": row.attribute})

    def confirm_assumption(self, ctx: Ctx, request_id: str, assumption_id: str) -> RequestDetail:
        """A person confirms the row. Only an authenticated user reaches this; no code path confirms a
        row for the system (a ``model_inference`` row stays open until a person acts)."""
        require(ctx, Role.REQUESTER)
        request = self._load_request(ctx, request_id)
        row = self._open_row(ctx, request, assumption_id)
        self._resolve(ctx, row, "confirmed", EVT_ASSUMPTION_CONFIRMED)
        return self._detail(request)

    def invalidate_assumption(self, ctx: Ctx, request_id: str, assumption_id: str) -> RequestDetail:
        """The person says the assumption is wrong. For an attribute row the value is dropped and the
        request goes back to its open questions for that attribute (through the workflow); the row
        stays as history."""
        require(ctx, Role.REQUESTER)
        request = self._load_request(ctx, request_id)
        row = self._open_row(ctx, request, assumption_id)
        if row.attribute is not None:
            self._reopen_attribute(ctx, request, row.attribute)
        self._resolve(ctx, row, "invalidated", EVT_ASSUMPTION_INVALIDATED)
        return self._detail(request)

    def _reopen_attribute(self, ctx: Ctx, request: Request, name: str) -> None:
        if request.state not in (S.NEEDS_INFO, S.SPEC_CONFIRMED):
            raise Conflict(
                f"request is {request.state.value}: the assumption can no longer be invalidated here")
        assert request.family is not None
        fam = get_family(request.family)
        request.attributes = {k: v for k, v in request.attributes.items() if k != name}
        question = fam.questions.get(name)
        if question is None:  # not a required attribute: nothing to ask, the value is just dropped
            self._ts(request.tenant_id).requests.save(request)
            return
        self._move(request, S.SPEC_DRAFT, ctx.actor, {"step": "assumption_invalidated", "attribute": name})
        asking = [q for q in request.open_questions if q != question]
        new_total = request.questions_asked + (0 if question in request.open_questions else 1)
        if new_total > MAX_QUESTIONS:  # R4: bounded questions, then a defined outcome
            request.open_questions = []
            self._move(request, S.ESCALATED, "agent", {
                "reason": "spec incomplete after 2 questions", "missing": [name]})
            return
        request.open_questions = [*asking, question]
        request.questions_asked = new_total
        self._move(request, S.NEEDS_INFO, "agent", {"missing": [name]})

    # ------------------------------------------------------------ setup and go-live

    def _last_tenant_event(self, tenant_id: str, etype: str) -> Any:
        for e in reversed(self._log.events(tenant_id)):
            if e.type == etype:
                return e
        return None

    def _is_live(self, tenant_id: str) -> bool:
        return self._last_tenant_event(tenant_id, EVT_SETUP_GO_LIVE) is not None

    def _missing_identity(self, tenant_id: str) -> list[str]:
        s = self._settings
        have = {label for label, _ in self._identities.identity_for(tenant_id)}
        return [n for n in s.identity_fields if s.identity_label(n) not in have]

    def _setup_items(self, tenant_id: str) -> list[SetupItem]:
        items: list[SetupItem] = []
        prof = self._profile
        items.append(SetupItem(
            id="profile", label="Deployment profile", status="done" if prof else "todo",
            detail=f"{prof.profile.id}@{prof.digest[:12]}" if prof else "no profile loaded"))
        if self._settings.identity_required:
            missing = self._missing_identity(tenant_id)
            items.append(SetupItem(
                id="business_identity", label="Business identity on outbound messages",
                status="todo" if missing else "done",
                detail=("missing: " + ", ".join(missing)) if missing else "all required fields present"))
        attested = sum(1 for p in self._sup(tenant_id).profiles.list()
                       if p.verification.state == "attested")
        items.append(SetupItem(
            id="suppliers", label="At least one attested supplier",
            status="done" if attested else "todo", detail=f"{attested} attested"))
        kill = self._last_tenant_event(tenant_id, EVT_KILL_SWITCH_NAME)
        engaged = bool(kill and kill.payload.get("engaged"))
        items.append(SetupItem(
            id="kill_switch", label="Kill switch not engaged",
            status="blocked" if engaged else "done",
            detail="sending is stopped for this tenant" if engaged else "not engaged"))
        dry = self._last_tenant_event(tenant_id, EVT_RFQ_PREPARED_NAME) is not None
        items.append(SetupItem(
            id="dry_run", label="A request has reached a prepared RFQ",
            status="done" if dry else "todo",
            detail="a prepared RFQ exists" if dry else "prepare one RFQ end to end first"))
        items.append(SetupItem(
            id="sending_domain", label="Sending domain authentication", status="todo",
            detail=SENDING_DOMAIN_DETAIL))
        return items

    @staticmethod
    def _blocking(items: list[SetupItem]) -> list[str]:
        return [i.id for i in items if i.status != "done" and i.id not in MANUAL_SETUP_ITEMS]

    def get_setup(self, ctx: Ctx) -> SetupView:
        require(ctx, Role.ADMIN)
        items = self._setup_items(ctx.tenant_id)
        return SetupView(ready=not self._blocking(items), live=self._is_live(ctx.tenant_id),
                         items=items)

    def go_live(self, ctx: Ctx) -> SetupView:
        """Record the tenant as live when every checked item is done. RECORDED, NOT ENFORCED: sends are
        not blocked by ``live``. There is no second-person confirmation. See known-gaps.md."""
        require(ctx, Role.ADMIN)
        items = self._setup_items(ctx.tenant_id)
        blocking = self._blocking(items)
        if blocking:
            raise Conflict("not ready: " + ", ".join(blocking))
        if not self._is_live(ctx.tenant_id):
            self._emit(ctx.tenant_id, None, ctx.actor, EVT_SETUP_GO_LIVE, {
                "items": {i.id: i.status for i in items}, "enforced": False})
        return SetupView(ready=True, live=True, items=items)

    # ------------------------------------------------------------ evidence export

    def audit_export(self, ctx: Ctx, request_id: str | None = None) -> AuditExport:
        require(ctx, Role.ADMIN)
        if request_id is not None:
            self._get(self._ts(ctx.tenant_id).requests, request_id)
        events = self._log.events(ctx.tenant_id, request_id)
        public = [e.model_copy(update={"payload": {
            k: v for k, v in e.payload.items() if k != "_pii"}}) for e in events]
        return AuditExport(
            tenant=hashlib.sha256(f"tenant:{ctx.tenant_id}".encode()).hexdigest()[:16],
            generated_at=self._clock.now(),
            profile=self._settings.profile_tag, chain_valid=self._log.verify_chain(ctx.tenant_id),
            head_hash=self._log.head(ctx.tenant_id)[1], events=public, request_id=request_id)
