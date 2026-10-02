# ruff: noqa: E501
"""PurchasingService: the purchasing pack's application service (implements PurchasingServicePort).

Everything the hard rules need is enforced here, in code:
- R1: mail goes out only via ``SendService.send`` with an ``Approval`` this service obtains from the
  approval service for an authenticated human and bound to the exact ``mime_hash``. The service has
  no transport; the planner (graph.py) has no import path to any of this.
- R2: ``check_r2`` before any PO draft. R3: tiers come from the parts engine, reasons from the
  templated comparison. R4: <= 2 questions then ESCALATED. R5/R9: Decimal money, caps checked.
- R6 (vendor content untrusted): quarantined extractor + grounding + inert text; nothing a vendor
  writes can change recipients, amounts, rules or state. R7: no link fetching exists.
- Hard rule 6 (every state change is a hash-chained Event): ``Request.state`` is only ever written
  by ``Workflow.transition``. Derived facts (candidates, the selected quote) are read back from
  the audit log, so this service keeps no hidden state besides the prepared-message cache.
- Tenant isolation: every object is reached through ``Store.for_tenant(ctx.tenant_id)``; foreign or
  unknown ids raise ``NotFound``. Tenant and user come from ``Ctx`` only.
"""

from __future__ import annotations

import csv
import hmac
import io
import re
import secrets
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Protocol, TypeVar

from aiplat.ctx import Ctx, Forbidden, Role, require
from components.core.domain import (
    RFQ,
    Approval,
    ApprovalKind,
    Candidate,
    Comparison,
    Event,
    ExtractedQuote,
    PurchaseOrderDraft,
    Quote,
    Request,
    RequestState,
    Tier,
    Vendor,
)
from components.core.fakes import RecordingTransport
from components.core.ports import Clock, Extractor, LLMProvider
from components.core.store import NotFoundError, Store, TenantIsolationError, TenantStore
from components.evidence.log import EVT_APPROVAL_TOKEN_ISSUED, EventLog
from components.parts.equivalence.catalogue import normalise_mpn
from components.parts.equivalence.engine import classify_offered, find_candidates, is_offerable
from components.parts.families.registry import get_family, list_families
from components.parts.spec.intake import parse_request_text
from components.parts.spec.normaliser import NormalisedSpec, normalise
from components.purchase_orders.approvals import (
    ApprovalAction,
    ApprovalError,
    ApprovalService,
    CapError,
    CapPolicy,
    TokenClaims,
    TokenError,
    quote_fingerprint,
)
from components.purchase_orders.approvals.service import (
    NotHumanApprover,
    SeparationOfDuties,
    TokenApproverMismatch,
    TokenExpired,
    TokenReplayed,
)
from components.rfq.comparison import compare
from components.rfq.quotes.extractors import LLMQuoteExtractor, RegexQuoteExtractor
from components.rfq.quotes.grounding import INJECTION_FLAG, ground
from components.rfq.quotes.normalise import is_quarantined, normalise_quote
from components.rfq.workflow import Workflow, WorkflowError
from components.send_service import FOOTER_TEMPLATE, SendError, SendService
from components.send_service.message import render_footer

from .service_port import Conflict, NotFound
from .views import (
    ApprovalLinkView,
    AuditView,
    DecisionResult,
    ImportSummary,
    PendingApproval,
    PreparedRFQ,
    QuoteView,
    RequestDetail,
    RequestView,
    RFQView,
    SendResult,
    VendorRef,
)

S = RequestState
T = TypeVar("T")

EVT_REQUEST_CREATED = "request.created"
EVT_CANDIDATES = "candidates.found"
EVT_RFQ_PREPARED = "rfq.prepared"
EVT_QUOTE_INGESTED = "quote.ingested"
EVT_VENDOR_UPSERTED = "vendor.upserted"
EVT_CSV_IMPORT = "import.csv"
MAX_SOURCE_CHARS = 200_000
MAX_ANSWER_CHARS = 80
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
INGEST_STATES = frozenset({S.RFQ_SENT, S.QUOTES_COLLECTING, S.COMPARISON_READY, S.QUOTE_SELECTED})
SENDABLE_STATES = frozenset({S.RFQ_DRAFTED, S.RFQ_APPROVED, S.RFQ_SENT, S.QUOTES_COLLECTING})

IdGenerator = Callable[[str], str]


def default_ids(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6)}"


# ---------------------------------------------------------------- configuration and ports


@dataclass(frozen=True)
class Settings:
    """Deployment configuration. Never taken from a request or from model output."""

    alias_address: str = "rfq@alias.example"
    reply_to_domain: str = "buyer.example"
    buyer_phone: str = "+1 555 010 0100"  # illustrative placeholder
    buyer_names: Mapping[str, str] = field(default_factory=dict)  # user_id -> display name
    approvers: tuple[str, ...] = ("user:approver-1",)
    approval_threshold: Decimal = Decimal("500")
    send_approval_ttl: timedelta = timedelta(minutes=30)
    substitution_ttl: timedelta = timedelta(hours=24)
    max_vendors: int = 4  # spec 4a
    down_now_max_vendors: int = 2
    max_csv_bytes: int = 1_000_000


@dataclass(frozen=True)
class ApprovalLinkNotice:
    """What the notification channel needs to deliver one approval link to its approver."""

    tenant_id: str
    request_id: str
    approver: str
    action: str
    token: str


class ApprovalNotifier(Protocol):
    def notify(self, notice: ApprovalLinkNotice) -> None: ...


@dataclass
class InMemoryNotifier:
    """Dev/test notifier: collects notices instead of emailing them."""

    notices: list[ApprovalLinkNotice] = field(default_factory=list)

    def notify(self, notice: ApprovalLinkNotice) -> None:
        self.notices.append(notice)

    def token_for(self, approver: str, action: str) -> str:
        for n in reversed(self.notices):
            if n.approver == approver and n.action == action:
                return n.token
        raise KeyError((approver, action))


# ---------------------------------------------------------------- pure helpers


def check_r2(
    mpn: str,
    quote_version: int,
    candidates: Iterable[Candidate],
    substitutions: Iterable[Approval],
    now: datetime,
) -> None:
    """R2: the PO part number must be an approved Tier-A candidate or carry a SubstitutionApproval
    for exactly this candidate and quote version. Raises ``Conflict`` otherwise."""
    wanted = normalise_mpn(mpn)
    if wanted and any(
        c.tier is Tier.A and is_offerable(c) and normalise_mpn(c.mpn) == wanted for c in candidates
    ):
        return
    for a in substitutions:
        if (
            a.kind is ApprovalKind.SUBSTITUTION
            and a.candidate_mpn is not None
            and normalise_mpn(a.candidate_mpn) == wanted
            and a.quote_version == quote_version
            and now < a.expires_at
        ):
            return
    raise Conflict("R2: part number is not an approved Tier-A candidate and has no substitution approval")


def csv_cell(value: object) -> str:
    """Neutralise spreadsheet formulas (R7): any cell that could start one is prefixed with '."""
    text = str(value)
    return "'" + text if text.startswith(FORMULA_PREFIXES) else text


def _total(quote: Quote, quantity: int) -> Decimal:
    assert quote.unit_price_each is not None
    return quote.unit_price_each * Decimal(quantity) + (quote.freight or Decimal(0))


# ---------------------------------------------------------------- the service


class PurchasingService:
    def __init__(
        self,
        *,
        store: Store,
        event_log: EventLog,
        clock: Clock,
        send_service: SendService,
        approval_service: ApprovalService,
        extractor: Extractor,
        settings: Settings | None = None,
        notifier: ApprovalNotifier | None = None,
        ids: IdGenerator = default_ids,
        token_gen: Callable[[], str] = lambda: secrets.token_urlsafe(16),
        llm: LLMProvider | None = None,
    ) -> None:
        self._store = store
        self._log = event_log
        self._clock = clock
        self._send = send_service
        self._approvals = approval_service
        self._extractor = extractor
        self._settings = settings or Settings()
        self.notifier: ApprovalNotifier = notifier or InMemoryNotifier()
        self._ids = ids
        self._token_gen = token_gen
        self.llm = llm  # for the planner/graph; the service itself makes no model calls
        self._wf = Workflow(event_log, clock)
        self._prepared: dict[tuple[str, str], Any] = {}

    # ------------------------------------------------------------ infrastructure

    def _ts(self, tenant_id: str) -> TenantStore:
        return self._store.for_tenant(tenant_id)

    @staticmethod
    def _get(repo: Any, obj_id: str) -> Any:
        try:
            return repo.get(obj_id)
        except (NotFoundError, TenantIsolationError) as exc:
            raise NotFound(obj_id) from exc

    def _move(
        self, request: Request, to: RequestState, actor: str, payload: Mapping[str, Any] | None = None
    ) -> None:
        try:
            self._wf.transition(request, to, actor, payload)
        except WorkflowError as exc:
            raise Conflict(str(exc)) from exc
        self._ts(request.tenant_id).requests.save(request)

    def _emit(self, ctx_tenant: str, request_id: str | None, actor: str, etype: str,
              payload: Mapping[str, Any]) -> Event:
        return self._log.append(ctx_tenant, request_id, actor, etype, payload)

    def _load_request(self, ctx: Ctx, request_id: str) -> Request:
        request: Request = self._get(self._ts(ctx.tenant_id).requests, request_id)
        if ctx.role is Role.REQUESTER and request.requester != ctx.actor:
            raise NotFound(request_id)  # requesters only see their own requests
        return request

    def _events(self, tenant_id: str, request_id: str) -> list[Event]:
        return self._log.events(tenant_id, request_id)

    def _last_event(self, tenant_id: str, request_id: str, etype: str) -> Event | None:
        for e in reversed(self._events(tenant_id, request_id)):
            if e.type == etype:
                return e
        return None

    def _candidates(self, tenant_id: str, request_id: str) -> list[Candidate]:
        e = self._last_event(tenant_id, request_id, EVT_CANDIDATES)
        return [Candidate.model_validate(c) for c in e.payload["candidates"]] if e else []

    def _selection(self, tenant_id: str, request_id: str) -> dict[str, Any]:
        for e in reversed(self._events(tenant_id, request_id)):
            if e.type == "request.transition" and e.payload.get("to") == S.QUOTE_SELECTED.value:
                return dict(e.payload)
        raise Conflict("no quote selected")

    def _rfqs(self, ts: TenantStore, request_id: str) -> list[RFQ]:
        return ts.rfqs.list(lambda r: r.request_id == request_id)

    def _quotes(self, ts: TenantStore, request_id: str) -> list[Quote]:
        ids = {r.id for r in self._rfqs(ts, request_id)}
        return ts.quotes.list(lambda q: q.rfq_id in ids)

    def _buyer(self, ctx: Ctx) -> tuple[str, str]:
        name = self._settings.buyer_names.get(ctx.user_id, ctx.user_id)
        return name, f"{re.sub(r'[^A-Za-z0-9._-]', '', ctx.user_id)}@{self._settings.reply_to_domain}"

    # ------------------------------------------------------------ views

    @staticmethod
    def _view(r: Request) -> RequestView:
        return RequestView(
            id=r.id, state=r.state, family=r.family, attributes=dict(r.attributes),
            quantity=r.quantity, need_by=r.need_by, site=r.site, work_order_ref=r.work_order_ref,
            criticality=r.criticality, down_now=r.down_now, open_questions=list(r.open_questions),
            questions_asked=r.questions_asked, created_at=r.created_at,
        )

    @staticmethod
    def _ref(v: Vendor) -> VendorRef:
        return VendorRef(id=v.id, name=v.name)

    @staticmethod
    def _public(e: Event) -> Event:
        payload = {k: v for k, v in e.payload.items() if k != "_pii"}
        return e.model_copy(update={"payload": payload})

    def _detail(self, request: Request) -> RequestDetail:
        tid = request.tenant_id
        ts = self._ts(tid)
        rfqs = self._rfqs(ts, request.id)
        vendors = {v.id: v for v in ts.vendors.list()}
        quotes = self._quotes(ts, request.id)
        return RequestDetail(
            request=self._view(request),
            candidates=self._candidates(tid, request.id),
            rfqs=[
                RFQView(id=r.id, vendor=self._ref(vendors[r.vendor_id]), subject=r.subject,
                        sent_message_id=r.sent_message_id, candidate_mpns=list(r.candidate_mpns))
                for r in rfqs if r.vendor_id in vendors
            ],
            quotes=[
                QuoteView(quote=q, vendor=self._ref(vendors[q.vendor_id]))
                for q in quotes if q.vendor_id in vendors
            ],
            comparison=self._comparison(request, quotes) if quotes and request.quantity else None,
            events=[self._public(e) for e in self._events(tid, request.id)],
            pending_approvals=self._pending(request),
            chain_valid=self._log.verify_chain(tid),
        )

    def _pending(self, request: Request) -> list[PendingApproval]:
        if request.state is not S.APPROVAL_PENDING:
            return []
        sel = self._selection(request.tenant_id, request.id)
        kind = "substitution" if sel.get("substitution") else "po"
        return [PendingApproval(kind=kind, request_id=request.id, quote_id=sel.get("quote_id"),
                                note="awaiting approver decision via approval link")]

    def _comparison(self, request: Request, quotes: list[Quote]) -> Comparison:
        return compare(
            request.id, quotes, need_by=request.need_by, today=self._clock.now().date(),
            quantity=request.quantity or 1,
        )

    # ------------------------------------------------------------ requests / spec

    def create_request(
        self, ctx: Ctx, *, text: str, quantity: int | None = None, need_by: date | None = None,
        site: str | None = None, work_order_ref: str | None = None, down_now: bool = False,
        criticality: bool = False,
    ) -> RequestDetail:
        require(ctx, Role.REQUESTER)
        now = self._clock.now()
        parsed = parse_request_text(text, now.date())
        if quantity is not None and quantity <= 0:
            raise Conflict("quantity must be positive")
        request = Request(
            id=self._ids("req"), tenant_id=ctx.tenant_id, requester=ctx.actor, raw_text=text,
            quantity=quantity if quantity is not None else parsed.quantity,
            need_by=need_by or parsed.need_by, site=site, work_order_ref=work_order_ref,
            down_now=down_now or parsed.down_now,
            criticality=criticality or parsed.criticality_hint,  # text can only raise caution
            created_at=now,
        )
        self._ts(ctx.tenant_id).requests.add(request)
        self._emit(ctx.tenant_id, request.id, ctx.actor, EVT_REQUEST_CREATED, {
            "instruction_flags": list(parsed.raw_instruction_flags),
            "criticality": request.criticality, "down_now": request.down_now,
        })
        self._move(request, S.SPEC_DRAFT, "agent", {"step": "intake"})
        self._apply_spec(request, normalise(text, questions_asked=0))
        return self._detail(request)

    def _apply_spec(self, request: Request, spec: NormalisedSpec) -> None:
        """Request is in SPEC_DRAFT. Record the spec and move to the next state (R4)."""
        request.family = spec.family
        request.attributes = dict(spec.attributes)
        request.open_questions = list(spec.open_questions)
        request.questions_asked += len(spec.open_questions)
        if spec.escalate:
            request.open_questions = []
            self._move(request, S.ESCALATED, "agent",
                       {"reason": "spec incomplete after 2 questions", "missing": list(spec.missing)})
        elif spec.open_questions:
            self._move(request, S.NEEDS_INFO, "agent", {"missing": list(spec.missing)})
        else:
            self._move(request, S.SPEC_CONFIRMED, "agent", {"family": spec.family})
            self._find_candidates(request)

    def _find_candidates(self, request: Request) -> None:
        assert request.family is not None
        found = find_candidates(
            request.attributes, family=request.family, criticality=request.criticality
        )
        self._emit(request.tenant_id, request.id, "agent", EVT_CANDIDATES, {
            "candidates": [c.model_dump(mode="json") for c in found],
            "criticality": request.criticality,
        })
        if request.criticality and not any(self._offerable(c) for c in found):
            self._move(request, S.ESCALATED, "agent",
                       {"reason": "criticality: engineering review required (tier D)"})

    @staticmethod
    def _offerable(c: Candidate) -> bool:
        return c.tier in (Tier.A, Tier.B) and is_offerable(c)

    def list_requests(self, ctx: Ctx, *, state: str | None = None) -> list[RequestView]:
        require(ctx, Role.REQUESTER)
        wanted = RequestState(state) if state else None

        def keep(r: Request) -> bool:
            own = ctx.role is not Role.REQUESTER or r.requester == ctx.actor
            return own and (wanted is None or r.state is wanted)

        return [self._view(r) for r in self._ts(ctx.tenant_id).requests.list(keep)]

    def get_request(self, ctx: Ctx, request_id: str) -> RequestDetail:
        require(ctx, Role.REQUESTER)
        return self._detail(self._load_request(ctx, request_id))

    def answer_questions(self, ctx: Ctx, request_id: str, answers: dict[str, str]) -> RequestDetail:
        require(ctx, Role.REQUESTER)
        request = self._load_request(ctx, request_id)
        if request.state is not S.NEEDS_INFO:
            raise Conflict(f"request is {request.state.value}, not waiting for answers")
        attrs, family = self._merge_answers(request, answers)
        self._move(request, S.SPEC_DRAFT, ctx.actor, {"step": "answers", "keys": sorted(answers)})
        spec = normalise(
            "", existing=attrs, questions_asked=request.questions_asked, family=family
        )
        self._apply_spec(request, spec)
        return self._detail(request)

    @staticmethod
    def _merge_answers(request: Request, answers: dict[str, str]) -> tuple[dict[str, Any], str | None]:
        from components.core.domain import Attribute, AttrSource

        family = request.family
        attrs = dict(request.attributes)
        if "family" in answers:
            if family is not None or answers["family"] not in list_families():
                raise Conflict("unknown or already-set family")
            family = answers["family"]
        known: set[str] = set()
        if family:
            spec = get_family(family)
            known = set(spec.required_attributes) | set(spec.optional_attributes) | set(
                spec.critical_attributes)
        for key, value in answers.items():
            if key == "family":
                continue
            if key not in known:
                raise Conflict(f"unknown attribute {key!r}")
            clean = " ".join(str(value).split())[:MAX_ANSWER_CHARS]
            attrs[key] = Attribute(name=key, value=clean, source=AttrSource.USER_INPUT,
                                   source_ref="answer to clarifying question")
        return attrs, family

    # ------------------------------------------------------------ RFQ

    def prepare_rfqs(
        self, ctx: Ctx, request_id: str, *, vendor_ids: list[str],
        candidate_mpns: list[str] | None = None,
    ) -> list[PreparedRFQ]:
        require(ctx, Role.BUYER)
        request = self._load_request(ctx, request_id)
        if request.state not in (S.SPEC_CONFIRMED, S.RFQ_DRAFTED):
            raise Conflict(f"cannot prepare RFQs in state {request.state.value}")
        if not request.quantity:
            raise Conflict("quantity is required before an RFQ can be drafted")
        mpns = self._rfq_mpns(request, candidate_mpns)
        ts = self._ts(ctx.tenant_id)
        vendors = self._rfq_vendors(ts, request, list(dict.fromkeys(vendor_ids)))
        out = [self._prepare_one(ctx, request, v, mpns) for v in vendors]
        if request.state is S.SPEC_CONFIRMED:
            self._move(request, S.RFQ_DRAFTED, ctx.actor,
                       {"rfq_ids": [p.rfq_id for p in out], "candidate_mpns": mpns})
        return out

    def _rfq_mpns(self, request: Request, requested: list[str] | None) -> list[str]:
        offerable = [c for c in self._candidates(request.tenant_id, request.id) if self._offerable(c)]
        if not offerable:
            raise Conflict("no Tier A/B candidate: engineering review required")
        by_norm = {normalise_mpn(c.mpn): c.mpn for c in offerable}
        if requested is None:
            return [c.mpn for c in sorted(offerable, key=lambda c: (c.tier.value, c.mpn))]
        picked = []
        for m in requested:
            if normalise_mpn(m) not in by_norm:
                raise Conflict(f"{m!r} is not an offerable candidate of this request")
            picked.append(by_norm[normalise_mpn(m)])
        if not picked:
            raise Conflict("no candidate selected")
        return list(dict.fromkeys(picked))

    def _rfq_vendors(self, ts: TenantStore, request: Request, vendor_ids: list[str]) -> list[Vendor]:
        if not vendor_ids:
            raise Conflict("no vendors selected")
        vendors: list[Vendor] = [self._get(ts.vendors, vid) for vid in vendor_ids]
        for v in vendors:
            if v.opted_out:
                raise Conflict(f"vendor {v.id} has opted out")
            if not v.preferred:
                raise Conflict(f"vendor {v.id} is not a preferred vendor")
        limit = (self._settings.down_now_max_vendors if request.down_now
                 else self._settings.max_vendors)
        existing = {r.vendor_id for r in self._rfqs(ts, request.id)}
        if len(existing | {v.id for v in vendors}) > limit:
            raise Conflict(f"at most {limit} vendors per request")
        return vendors

    def _prepare_one(self, ctx: Ctx, request: Request, vendor: Vendor, mpns: list[str]) -> PreparedRFQ:
        ts = self._ts(ctx.tenant_id)
        existing = next((r for r in self._rfqs(ts, request.id) if r.vendor_id == vendor.id), None)
        if existing is not None and existing.sent_message_id:
            raise Conflict(f"RFQ to {vendor.id} was already sent")
        cands = {c.mpn: c for c in self._candidates(request.tenant_id, request.id)}
        body = self._rfq_body(request, vendor, [cands[m] for m in mpns])
        if existing is None:
            rfq = RFQ(id=self._ids("rfq"), tenant_id=ctx.tenant_id, request_id=request.id,
                      vendor_id=vendor.id, subject=f"RFQ: {mpns[0]} x{request.quantity}",
                      body=body, candidate_mpns=tuple(mpns), reply_token=self._token_gen())
            ts.rfqs.add(rfq)
        else:
            rfq = existing.model_copy(update={"body": body, "candidate_mpns": tuple(mpns)})
            ts.rfqs.save(rfq)
        name, reply_to = self._buyer(ctx)
        try:
            prepared = self._send.prepare(
                rfq, vendor, name, self._settings.buyer_phone, self._settings.alias_address, reply_to
            )
        except SendError as exc:
            raise Conflict(f"cannot prepare message: {exc}") from exc
        self._prepared[(ctx.tenant_id, rfq.id)] = prepared
        self._emit(ctx.tenant_id, request.id, ctx.actor, EVT_RFQ_PREPARED, {
            "rfq_id": rfq.id, "vendor_id": vendor.id, "mime_hash": prepared.mime_hash})
        return PreparedRFQ(
            rfq_id=rfq.id, vendor=self._ref(vendor), to=prepared.to, subject=prepared.subject,
            body_preview=self._send.preview(prepared).text, mime_hash=prepared.mime_hash,
            footer=render_footer(FOOTER_TEMPLATE, name),
        )

    @staticmethod
    def _rfq_body(request: Request, vendor: Vendor, cands: list[Candidate]) -> str:
        lines = [f"Hello {vendor.name},", "", "Please quote the following part(s):"]
        lines += [f"- {c.mpn} ({c.manufacturer})" for c in cands]
        lines += ["", f"Quantity: {request.quantity}"]
        if request.need_by:
            lines.append(f"Need by: {request.need_by.isoformat()}")
        if request.site:
            lines.append(f"Ship to: {request.site}")
        lines += [
            "",
            "Please reply with unit price and unit of measure, currency, lead time, freight, "
            "quote validity, condition, and the exact manufacturer and part number you quote.",
            "If you offer a different part, say so explicitly with its manufacturer and number.",
        ]
        return "\n".join(lines)

    def approve_send(self, ctx: Ctx, rfq_id: str, *, mime_hash: str) -> SendResult:
        require(ctx, Role.BUYER)
        ts = self._ts(ctx.tenant_id)
        rfq: RFQ = self._get(ts.rfqs, rfq_id)
        request = self._load_request(ctx, rfq.request_id)
        prepared = self._prepared.get((ctx.tenant_id, rfq.id))
        if rfq.sent_message_id:
            raise Conflict("RFQ was already sent")
        if request.state not in SENDABLE_STATES:
            raise Conflict(f"cannot send in state {request.state.value}")
        if prepared is None or not hmac.compare_digest(prepared.mime_hash, str(mime_hash)):
            raise Conflict("message changed or was never prepared: review the new hash")
        try:
            approval = self._approvals.issue_per_message_approval(
                ctx.tenant_id, ctx.actor, prepared.mime_hash, self._settings.send_approval_ttl,
                request_id=request.id,
            )
        except (NotHumanApprover, ValueError) as exc:
            raise Forbidden(str(exc)) from exc
        if request.state is S.RFQ_DRAFTED:
            self._move(request, S.RFQ_APPROVED, ctx.actor,
                       {"rfq_id": rfq.id, "approval_id": approval.id, "mime_hash": prepared.mime_hash})
        try:
            message_id = self._send.send(prepared, approval)
        except SendError as exc:
            raise Conflict(f"send refused: {exc.code}") from exc
        ts.rfqs.save(rfq.model_copy(update={"sent_message_id": message_id}))
        self._prepared.pop((ctx.tenant_id, rfq.id), None)
        if request.state is S.RFQ_APPROVED:
            self._move(request, S.RFQ_SENT, "system", {"rfq_id": rfq.id, "send_ref": message_id})
        return SendResult(message_id=message_id)

    # ------------------------------------------------------------ quotes

    def ingest_quote(
        self, ctx: Ctx, request_id: str, *, vendor_id: str, source_text: str, dmarc_aligned: bool
    ) -> QuoteView:
        require(ctx, Role.BUYER)
        ts = self._ts(ctx.tenant_id)
        request = self._load_request(ctx, request_id)
        vendor: Vendor = self._get(ts.vendors, vendor_id)
        rfq = next((r for r in self._rfqs(ts, request.id) if r.vendor_id == vendor.id), None)
        if rfq is None or not rfq.sent_message_id:
            raise Conflict("no sent RFQ to this vendor")
        if request.state not in INGEST_STATES:
            raise Conflict(f"cannot ingest quotes in state {request.state.value}")
        if not isinstance(source_text, str) or len(source_text) > MAX_SOURCE_CHARS:
            raise Conflict("quote text is missing or too large")
        quote = self._build_quote(request, rfq, vendor, source_text, bool(dmarc_aligned))
        existing = ts.quotes.find(quote.id)
        if existing is None:
            ts.quotes.add(quote)
        else:
            ts.quotes.save(quote)
        self._emit(ctx.tenant_id, request.id, "agent", EVT_QUOTE_INGESTED, {
            "quote_id": quote.id, "version": quote.version, "vendor_id": vendor.id,
            "flags": list(quote.flags), "offered_tier": quote.offered_tier.value})
        self._advance_after_quote(request)
        return QuoteView(quote=quote, vendor=self._ref(vendor))

    def _build_quote(self, request: Request, rfq: RFQ, vendor: Vendor, text: str,
                     dmarc_aligned: bool) -> Quote:
        extra: list[str] = []
        try:
            extracted = self._extractor.extract(text)
        except Exception:  # noqa: BLE001 - a failing extractor yields a blank, flagged quote
            extracted, extra = ExtractedQuote(), ["extraction_failed"]
        g = ground(extracted, text)
        prior = self._ts(request.tenant_id).quotes.find(self._quote_id_for(request, rfq))
        quote = normalise_quote(
            g.extracted, quote_id=prior.id if prior else self._ids("quote"),
            tenant_id=request.tenant_id, rfq_id=rfq.id, vendor_id=vendor.id,
            offered_tier=Tier.D, dmarc_aligned=dmarc_aligned,
            grounding_flags=[*g.flags, *extra], snippets=g.snippets,
            version=(prior.version + 1) if prior else 1, received_on=self._clock.now().date(),
        )
        if quote.offered_mpn and request.family:
            tier = self._classify(request, quote.offered_mpn)
            quote = quote.model_copy(update={"offered_tier": tier})
        return quote

    def _quote_id_for(self, request: Request, rfq: RFQ) -> str:
        ts = self._ts(request.tenant_id)
        found = ts.quotes.list(lambda q: q.rfq_id == rfq.id)
        return found[0].id if found else ""

    @staticmethod
    def _classify(request: Request, offered_mpn: str) -> Tier:
        assert request.family is not None
        try:
            tier, _ = classify_offered(
                offered_mpn, request.attributes, family=request.family,
                criticality=request.criticality,
            )
        except Exception:  # noqa: BLE001 - unclassifiable means engineering review
            return Tier.D
        return tier

    def _advance_after_quote(self, request: Request) -> None:
        ts = self._ts(request.tenant_id)
        if request.state is S.RFQ_SENT:
            self._move(request, S.QUOTES_COLLECTING, "agent", {"step": "first_quote"})
        if request.state is not S.QUOTES_COLLECTING:
            return
        sent = [r for r in self._rfqs(ts, request.id) if r.sent_message_id]
        usable = {q.rfq_id for q in self._quotes(ts, request.id) if not self._excluded_flags(q)}
        if sent and all(r.id in usable for r in sent):
            self._move(request, S.COMPARISON_READY, "agent", {"quotes": len(usable)})

    @staticmethod
    def _excluded_flags(q: Quote) -> bool:
        return is_quarantined(q) or INJECTION_FLAG in q.flags

    def get_comparison(self, ctx: Ctx, request_id: str) -> Comparison:
        require(ctx, Role.REQUESTER)
        request = self._load_request(ctx, request_id)
        return self._comparison(request, self._quotes(self._ts(ctx.tenant_id), request.id))

    # ------------------------------------------------------------ selection and approval links

    def select_quote(self, ctx: Ctx, request_id: str, quote_id: str) -> RequestDetail:
        require(ctx, Role.BUYER)
        ts = self._ts(ctx.tenant_id)
        request = self._load_request(ctx, request_id)
        quote: Quote = self._get(ts.quotes, quote_id)
        if quote.rfq_id not in {r.id for r in self._rfqs(ts, request.id)}:
            raise NotFound(quote_id)
        if request.state not in (S.QUOTES_COLLECTING, S.COMPARISON_READY):
            raise Conflict(f"cannot select a quote in state {request.state.value}")
        self._check_selectable(request, quote, ts)  # refuse before any state change
        if request.state is S.QUOTES_COLLECTING:
            self._move(request, S.COMPARISON_READY, ctx.actor, {"step": "buyer_proceeds"})
        qty = request.quantity or 1
        total = _total(quote, qty)
        substitution = quote.offered_tier is not Tier.A
        needs_approval = substitution or total > self._settings.approval_threshold
        fp = quote_fingerprint(quote)
        self._move(request, S.QUOTE_SELECTED, ctx.actor, {
            "quote_id": quote.id, "quote_version": quote.version, "quote_hash": fp,
            "approval_required": needs_approval, "substitution": substitution})
        if needs_approval:
            self._request_approval(request, quote, fp, total)
        return self._detail(request)

    def _check_selectable(self, request: Request, quote: Quote, ts: TenantStore) -> None:
        cmp = self._comparison(request, self._quotes(ts, request.id))
        if any(r.startswith(f"excluded:{quote.id}:") for r in cmp.reasons):
            raise Conflict("quote is excluded (flagged, quarantined or unusable)")
        if self._excluded_flags(quote):
            raise Conflict("quote is quarantined or flagged")
        if quote.offered_tier is Tier.D:
            raise Conflict("quote offers a Tier D part: engineering review required")
        if quote.unit_price_each is None or quote.currency is None or not quote.offered_mpn:
            raise Conflict("quote lacks price, currency or offered part number")

    def _request_approval(self, request: Request, quote: Quote, fp: str, total: Decimal) -> None:
        above = total > self._settings.approval_threshold
        eligible = [a for a in self._settings.approvers
                    if not (above and a.lower() == request.requester.lower())]
        if not eligible:
            raise Conflict("no eligible approver (approver must differ from requester)")
        notices = []
        try:
            for approver in eligible:
                for action in (ApprovalAction.APPROVE, ApprovalAction.DECLINE):
                    token = self._approvals.issue_approval_token(
                        tenant_id=request.tenant_id, approver=approver, action=action,
                        quote_version=quote.version, quote_hash=fp, requester=request.requester,
                        amount=total, request_id=request.id)
                    notices.append(ApprovalLinkNotice(
                        request.tenant_id, request.id, approver, action.value, token))
        except ApprovalError as exc:
            raise Conflict(str(exc)) from exc
        self._move(request, S.APPROVAL_PENDING, "system", {"approvers": eligible, "total": total})
        for n in notices:
            self.notifier.notify(n)

    def _peek(self, token: str) -> TokenClaims:
        """Decode a signed link WITHOUT consuming it (signature and structure are verified)."""
        try:
            return self._approvals._decode(token)  # noqa: SLF001 - see CONTRACT_CHANGES.md
        except TokenError as exc:
            raise NotFound("approval link") from exc

    def _link_context(self, claims: TokenClaims) -> tuple[Request, Quote, str]:
        tid = claims.tenant_id
        issued = next((e for e in self._log.events(tid)
                       if e.type == EVT_APPROVAL_TOKEN_ISSUED and e.payload.get("jti") == claims.jti),
                      None)
        if issued is None or issued.request_id is None:
            raise NotFound("approval link")
        ts = self._ts(tid)
        request: Request = self._get(ts.requests, issued.request_id)
        sel = self._selection(tid, request.id)
        try:
            quote = ts.quotes.get_version(sel["quote_id"], claims.quote_version)
        except (NotFoundError, TenantIsolationError) as exc:
            raise NotFound("approval link") from exc
        return request, quote, quote_fingerprint(quote)

    def get_approval_link(self, token: str) -> ApprovalLinkView:
        claims = self._peek(token)  # GET: validates, never consumes, never writes (R11)
        request, quote, fp = self._link_context(claims)
        try:
            self._approvals.verify_token(
                token, tenant_id=claims.tenant_id, approver=claims.approver, action=claims.action,
                quote_version=claims.quote_version, quote_hash=fp)
        except (TokenExpired, TokenReplayed) as exc:
            raise Conflict(str(exc)) from exc
        except TokenError as exc:
            raise NotFound("approval link") from exc
        if request.state is not S.APPROVAL_PENDING:
            raise Conflict("no approval is pending")
        vendor: Vendor = self._get(self._ts(claims.tenant_id).vendors, quote.vendor_id)
        sel = self._selection(claims.tenant_id, request.id)
        return ApprovalLinkView(
            request_id=request.id, quote_id=quote.id, vendor=self._ref(vendor),
            unit_price_each=quote.unit_price_each, currency=quote.currency,
            lead_time_days=quote.lead_time_days, action_options=[claims.action.value],
            expires_at=claims.expires_at,
            note="substitution_review" if sel.get("substitution") else "")

    def decide_approval_link(self, ctx: Ctx, token: str, action: str) -> DecisionResult:
        require(ctx, Role.BUYER)
        if action not in ("approve", "decline"):
            raise ValueError("action must be 'approve' or 'decline'")
        claims = self._peek(token)
        if claims.tenant_id != ctx.tenant_id:
            raise NotFound("approval link")  # never reveal another tenant's link
        request, quote, fp = self._link_context(claims)
        if request.state is not S.APPROVAL_PENDING:
            raise Conflict("no approval is pending")
        self._consume(ctx, token, action, claims, request, fp)
        sel = self._selection(ctx.tenant_id, request.id)
        if action == "approve":
            if sel.get("substitution"):
                sub = self._approvals.issue_substitution_approval(
                    ctx.tenant_id, ctx.actor, quote.offered_mpn or "", quote.version,
                    self._settings.substitution_ttl)
                self._emit(ctx.tenant_id, request.id, ctx.actor, "approval.substitution_recorded", {
                    "approval_id": sub.id, "candidate_mpn": sub.candidate_mpn,
                    "quote_id": quote.id, "quote_version": quote.version})
            self._move(request, S.APPROVED, ctx.actor, {"quote_id": quote.id, "jti": claims.jti})
            return DecisionResult(request_id=request.id, decision="approved", state=request.state)
        self._move(request, S.DECLINED, ctx.actor, {"quote_id": quote.id, "jti": claims.jti})
        return DecisionResult(request_id=request.id, decision="declined", state=request.state)

    def _consume(self, ctx: Ctx, token: str, action: str, claims: TokenClaims, request: Request,
                 fp: str) -> None:
        try:
            self._approvals.consume_token(
                token, tenant_id=ctx.tenant_id, approver=ctx.actor, action=action,
                quote_version=claims.quote_version, quote_hash=fp, request_id=request.id)
        except (TokenApproverMismatch, SeparationOfDuties) as exc:
            raise Forbidden(str(exc)) from exc
        except TokenError as exc:
            raise Conflict(str(exc)) from exc

    # ------------------------------------------------------------ PO

    def create_po_draft(self, ctx: Ctx, request_id: str) -> PurchaseOrderDraft:
        require(ctx, Role.BUYER)
        ts = self._ts(ctx.tenant_id)
        request = self._load_request(ctx, request_id)
        existing = ts.po_drafts.list(lambda d: d.request_id == request.id)
        if existing and request.state is S.PO_DRAFTED:
            return existing[0]
        sel = self._selection(ctx.tenant_id, request.id) if request.state in (
            S.APPROVED, S.QUOTE_SELECTED) else {}
        if request.state is S.APPROVED or (
            request.state is S.QUOTE_SELECTED and not sel.get("approval_required")
        ):
            pass
        else:
            raise Conflict(f"cannot draft a PO in state {request.state.value}")
        quote: Quote = ts.quotes.get_version(sel["quote_id"], int(sel["quote_version"]))
        assert quote.unit_price_each is not None and quote.currency and quote.offered_mpn
        qty = request.quantity or 0
        if qty <= 0:
            raise Conflict("quantity is required")
        check_r2(quote.offered_mpn, quote.version, self._candidates(ctx.tenant_id, request.id),
                 ts.approvals.list(lambda a: a.kind is ApprovalKind.SUBSTITUTION),
                 self._clock.now())
        total = _total(quote, qty)
        self._check_caps(ctx.tenant_id, total, quote.currency)
        draft = PurchaseOrderDraft(
            id=self._ids("po"), tenant_id=ctx.tenant_id, request_id=request.id, quote_id=quote.id,
            quote_version=quote.version, vendor_id=quote.vendor_id, mpn=quote.offered_mpn,
            quantity=qty, unit_price_each=quote.unit_price_each, currency=quote.currency,
            total=total)
        ts.po_drafts.add(draft)
        self._move(request, S.PO_DRAFTED, ctx.actor, {
            "po_id": draft.id, "quote_id": quote.id, "quote_version": quote.version,
            "total": total, "currency": quote.currency})
        return draft

    def _check_caps(self, tenant_id: str, total: Decimal, currency: str) -> None:
        caps: CapPolicy | None = self._approvals.caps
        if caps is None:
            raise Conflict("spend caps are not configured")
        try:
            caps.check(tenant_id, total, currency=currency)
        except CapError as exc:
            raise Conflict(f"cap: {exc}") from exc

    def po_csv(self, ctx: Ctx, request_id: str) -> str:
        require(ctx, Role.BUYER)
        ts = self._ts(ctx.tenant_id)
        request = self._load_request(ctx, request_id)
        drafts = ts.po_drafts.list(lambda d: d.request_id == request.id)
        if not drafts:
            raise Conflict("no PO draft yet")
        d = drafts[0]
        vendor: Vendor = self._get(ts.vendors, d.vendor_id)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["po_id", "request_id", "vendor_id", "vendor_name", "part_number", "quantity",
                    "unit_price_each", "currency", "total", "quote_id", "quote_version"])
        w.writerow([csv_cell(x) for x in (
            d.id, d.request_id, d.vendor_id, vendor.name, d.mpn, d.quantity, d.unit_price_each,
            d.currency, d.total, d.quote_id, d.quote_version)])
        return buf.getvalue()

    # ------------------------------------------------------------ vendors / audit / import

    def list_vendors(self, ctx: Ctx) -> list[Vendor]:
        require(ctx, Role.BUYER)
        return self._ts(ctx.tenant_id).vendors.list()

    def upsert_vendor(self, ctx: Ctx, vendor: Vendor) -> Vendor:
        require(ctx, Role.BUYER)
        vendor = vendor.model_copy(update={"tenant_id": ctx.tenant_id})  # tenant from ctx only
        repo = self._ts(ctx.tenant_id).vendors
        try:
            current = repo.find(vendor.id)
        except TenantIsolationError as exc:
            raise NotFound(vendor.id) from exc
        if current is None:
            saved = repo.add(vendor)
        else:
            if (current.contact_email, current.domain) != (vendor.contact_email, vendor.domain):
                require(ctx, Role.ADMIN)  # R12: remit-to/contact changes are admin-only
            saved = repo.save(vendor)
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_VENDOR_UPSERTED, {
            "vendor_id": saved.id, "created": current is None, "opted_out": saved.opted_out,
            "preferred": saved.preferred})
        return saved

    def audit(self, ctx: Ctx, request_id: str | None = None) -> AuditView:
        require(ctx, Role.ADMIN)
        if request_id is not None:
            self._get(self._ts(ctx.tenant_id).requests, request_id)
        events = self._log.events(ctx.tenant_id, request_id)
        return AuditView(events=[self._public(e) for e in events],
                         chain_valid=self._log.verify_chain(ctx.tenant_id))

    def import_csv(self, ctx: Ctx, data: bytes) -> ImportSummary:
        """Validates a parts/PO-history CSV (header must include ``part_number``). Rows are
        checked and counted only: persistence of imported history is not implemented yet."""
        require(ctx, Role.BUYER)
        if len(data) > self._settings.max_csv_bytes:
            raise Conflict("file too large")
        try:
            rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
        except (UnicodeDecodeError, csv.Error) as exc:
            raise Conflict("not a UTF-8 CSV file") from exc
        errors: list[dict[str, Any]] = []
        for i, row in enumerate(rows, start=2):
            pn = (row.get("part_number") or "").strip()
            if not pn or len(pn) > 80 or re.search(r"[\x00-\x1f\x7f]", pn):
                errors.append({"row": i, "error": "invalid part_number"})
        summary = ImportSummary(rows=len(rows), accepted=len(rows) - len(errors),
                                rejected=len(errors), errors=errors[:100])
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_CSV_IMPORT,
                   {"rows": summary.rows, "accepted": summary.accepted, "rejected": summary.rejected})
        return summary


# ---------------------------------------------------------------- factories


def build_in_memory_service(
    *,
    clock: Clock | None = None,
    store: Store | None = None,
    event_log: EventLog | None = None,
    transport: Any | None = None,  # handed to the send-service only (any MailTransport)
    extractor: Extractor | None = None,
    llm: LLMProvider | None = None,
    use_llm_extractor: bool = False,
    settings: Settings | None = None,
    caps: CapPolicy | None = None,
    notifier: ApprovalNotifier | None = None,
    ids: IdGenerator = default_ids,
    token_gen: Callable[[], str] | None = None,
    approval_secret: bytes | None = None,
) -> PurchasingService:
    """Fully wired service on in-memory stores. The transport is handed to the send-service ONLY.
    Defaults are dev-safe: a recording transport (nothing leaves the process), a fresh random
    approval secret, caps from the manifest defaults. Pass fakes in tests."""
    from datetime import UTC

    class _SystemClock:
        def now(self) -> datetime:
            return datetime.now(UTC)

    cfg = settings or Settings()
    clk: Clock = clock or _SystemClock()
    st = store or Store()
    log = event_log or EventLog(clk)
    policy = caps or CapPolicy(Decimal("5000"), Decimal("15000"), clk)
    approvals = ApprovalService(
        clk, approval_secret or secrets.token_bytes(32), store=st, event_log=log, caps=policy,
        requester_threshold=cfg.approval_threshold)
    send = SendService(transport or RecordingTransport(), clk, st, log, caps=policy,
                       max_recipients=cfg.max_vendors)
    if extractor is None:
        extractor = (LLMQuoteExtractor(llm) if use_llm_extractor and llm is not None
                     else RegexQuoteExtractor())
    kwargs: dict[str, Any] = {} if token_gen is None else {"token_gen": token_gen}
    return PurchasingService(
        store=st, event_log=log, clock=clk, send_service=send, approval_service=approvals,
        extractor=extractor, settings=cfg, notifier=notifier, ids=ids, llm=llm, **kwargs)
