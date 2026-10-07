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
- Business identity (company particulars a profile may require on outbound mail): the values are a
  deployment fact (``Settings.business_identities``), looked up ONLY by ``ctx.tenant_id``. They are copied
  into read-only mappings when ``Settings`` is built, never printed, and reach the send-service only as a
  tenant-scoped provider (``TenantIdentities``) that ``prepare`` consults for the RFQ's own tenant. An
  incomplete or invalid identity is a ``Conflict`` before anything is stored or sent. Construction refuses
  wiring that would lose the requirement, that differs from the profile's footer wording, or that allows
  more recipients than the profile's limit (see ``PurchasingService._check_wiring``).
- ``prepare_rfqs`` builds and reads back the message for every selected vendor (``SendService.check_prepare``,
  a dry run) before it adds the first RFQ row: a message that cannot be built is a ``Conflict`` that leaves
  nothing behind (no orphan row, no event, no cache entry).
"""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import inspect
import io
import json
import os
import re
import secrets
import threading
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Protocol, TypeVar

from aiplat.ctx import Ctx, Forbidden, Role, require
from aiplat.profile import ResolvedProfile, load_profile
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
from components.evidence.log import CHAIN_KEY_ENV, EVT_APPROVAL_TOKEN_ISSUED, PII_KEY_ENV, EventLog
from components.imports.safety import clean_text, neutralise
from components.parts.equivalence.catalogue import normalise_mpn
from components.parts.equivalence.engine import classify_offered, find_candidates, is_offerable
from components.parts.families.registry import get_family, is_family_enabled, list_families
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
    substitution_subject,
)
from components.rfq.comparison import compare
from components.rfq.quotes.extractors import LLMQuoteExtractor, RegexQuoteExtractor
from components.rfq.quotes.grounding import INJECTION_FLAG, ground
from components.rfq.quotes.normalise import is_quarantined, normalise_quote
from components.rfq.quotes.verify_quote import (
    ATTENTION_FLAG,
    REVIEW_FLAG,
    finding_payload,
    flags_for,
    verify_quote,
)
from components.rfq.workflow import Workflow, WorkflowError
from components.send_service import SendError, SendService
from components.send_service.message import (
    DEFAULT_IDENTITY_LABELS,
    ReadOnlyMap,
    has_visible_text,
    is_plain_line,
    render_footer,
    validate_identity_pairs,
)
from components.send_service.service import TenantIdentities
from components.suppliers import SupplierStore, is_stop_request
from components.verify.config import VerifyConfig
from components.verify.findings import Finding
from components.verify.history import PriceHistory

from .mvp import MvpOps
from .service_port import Conflict, NotFound, TextRfqDraft
from .views import (
    ApprovalLinkView,
    AuditView,
    DecisionResult,
    ImportSummary,
    OpenQuestion,
    PendingApproval,
    PreparedRFQ,
    QuestionField,
    QuoteView,
    RequestDetail,
    RequestView,
    RFQView,
    SendResult,
    StopAck,
    VendorRef,
)

S = RequestState
T = TypeVar("T")

EVT_REQUEST_CREATED = "request.created"
EVT_CANDIDATES = "candidates.found"
EVT_RFQ_PREPARED = "rfq.prepared"
EVT_QUOTE_INGESTED = "quote.ingested"
EVT_QUOTE_VERIFIED = "quote.verified"  # verification findings for an ingested quote (flags only)
EVT_VENDOR_UPSERTED = "vendor.upserted"
EVT_CSV_IMPORT = "import.csv"
EVT_VENDOR_CONTACT_CHANGED = "vendor.contact_changed"
EVT_VENDOR_CONTACT_CONFIRMED = "vendor.contact_confirmed"
EVT_KILL_SWITCH = "send.kill_switch"
EVT_QUOTE_RFQ_LINKED = "quote_rfq.linked"
# M4: a quote carrying any of these can only proceed with a human approval (approver != requester).
FORCE_APPROVAL_FLAGS = frozenset({
    "condition_not_new", "condition_unrecognised", "currency_assumed_usd", "freight_unknown",
    "buyer_entered", "tax_basis_unknown", "currency_ambiguous",
    REVIEW_FLAG,  # a verification finding (readings disagree, number check failed) needs a person
})
# Shown on the approval link but do not, by themselves, force an approval.
INFORMATIONAL_FLAGS = frozenset({"tax_basis_assumed", "lead_time_working_days_assumed",
                                ATTENTION_FLAG})
REFUSE_FLAGS = frozenset({"validity_expired"})  # cannot be selected at all
QUARANTINE_EXTRA = frozenset({"vendor_pending_callback"})  # R12 callback not yet confirmed
MAX_SOURCE_CHARS = 200_000
MAX_ANSWER_CHARS = 80
INGEST_STATES = frozenset({S.RFQ_SENT, S.QUOTES_COLLECTING, S.COMPARISON_READY, S.QUOTE_SELECTED})
SENDABLE_STATES = frozenset({S.RFQ_DRAFTED, S.RFQ_APPROVED, S.RFQ_SENT, S.QUOTES_COLLECTING})

IdGenerator = Callable[[str], str]


def default_ids(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6)}"


def check_site(site: object) -> None:
    """The ship-to ``site`` goes into the RFQ body, so it is held to the message layer's one-line rule
    (``is_plain_line``): no control or line-break character (a line break could add lines such as a
    forged "Phone:" to the message) and no zero-width or bidirectional one (the body refuses those, so
    a site holding one would fail late, at ``prepare_rfqs``). ``None`` means no site. Raises
    ``Conflict`` without echoing the value."""
    if site is not None and not is_plain_line(site):
        raise Conflict(
            "site must be one line of plain text (no control, line-break, zero-width or "
            "bidirectional characters)")


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
    daily_approval_threshold: Decimal | None = None  # tenant/day aggregate; default = approval_threshold
    reply_token_ttl: timedelta = timedelta(days=90)
    # Deployment-profile derived (None / "" = not set: filled from the profile when one is given).
    profile_tag: str = ""  # "<id>@<digest12>", stamped on every audit event
    enabled_families: tuple[str, ...] | None = None  # None = every registered family
    tiers_enabled: tuple[str, ...] | None = None  # None = ("A", "B")
    base_currency: str = "USD"
    raw_email_days: int = 90
    tax_name: str | None = None  # None = taken from the profile (RFQ wording)
    rfq_ask_tax_basis: bool = False  # the RFQ asks the supplier to state the tax basis
    # Business identity ("company particulars") on outbound RFQs. The VALUES are a deployment fact:
    # tenant_id -> field -> value, looked up ONLY by the authenticated tenant and never taken from a
    # request or model output. Which fields, their labels and whether they are required come from the
    # profile (`legal.business_identity`); `identity_labels` maps field -> label (defaults apply).
    # The values are copied into read-only mappings (`ReadOnlyMap`: picklable, repr shows counts only) at
    # construction (a later change to the mapping the deployer passed in changes nothing) and are left out
    # of the repr.
    business_identities: Mapping[str, Mapping[str, str]] = field(default_factory=dict, repr=False)
    identity_fields: tuple[str, ...] = ()
    identity_labels: Mapping[str, str] = field(default_factory=dict)
    identity_required: bool = False
    # Supplier guard (api-contract-mvp.md section 1): a one-to-one RFQ to a supplier recorded as an
    # individual (sole trader, partnership) is refused unless this is on. Counsel has not confirmed that
    # such messages are outside direct marketing, so it is off by default. Not one of the hard rules.
    allow_individual_subscribers: bool = False

    def __post_init__(self) -> None:
        if len(set(self.identity_fields)) != len(self.identity_fields) or any(
            f not in DEFAULT_IDENTITY_LABELS for f in self.identity_fields
        ):
            raise ValueError("identity_fields must be distinct, known identity fields")
        if self.identity_required and not self.identity_fields:
            raise ValueError("identity_required needs at least one of identity_fields")
        # Copies, so nothing the deployer still holds can change what is required or rendered later.
        object.__setattr__(self, "identity_fields", tuple(self.identity_fields))
        object.__setattr__(self, "business_identities", _freeze_identities(self.business_identities))
        object.__setattr__(self, "identity_labels", ReadOnlyMap(self.identity_labels))

    def identity_label(self, name: str) -> str:
        """The line label for one identity field: the profile's wording, else the default."""
        return self.identity_labels.get(name) or DEFAULT_IDENTITY_LABELS[name]

    def tenant_identities(self) -> TenantIdentities:
        """The tenants' company-particulars lines as a frozen, tenant-scoped provider: for each
        tenant the listed fields in order, under the labels in force. A field whose value shows no
        letter or digit counts as missing and is left out."""
        lines: dict[str, list[tuple[str, str]]] = {}
        for tenant_id, values in self.business_identities.items():
            pairs = [
                (self.identity_label(name), values[name].strip())
                for name in self.identity_fields if has_visible_text(values.get(name))
            ]
            if pairs:
                lines[tenant_id] = pairs
        return TenantIdentities(lines)

    def ensure_identity_not_weaker_than(self, profile: ResolvedProfile) -> None:
        """Raise ``ValueError`` if these settings drop or reword what a profile that REQUIRES the
        business-identity block asks for: the requirement itself, any of its fields or its labels.
        Settings can only add to a profile's requirement, never remove it."""
        bi = profile.profile.legal.business_identity
        if not bi.required:
            return
        problems: list[str] = []
        if not self.identity_required:
            problems.append("the requirement is switched off")
        dropped = [name for name in bi.fields if name not in self.identity_fields]
        if dropped:
            problems.append("fields dropped: " + ", ".join(dropped))
        reworded = [n for n, label in bi.effective_labels().items() if self.identity_label(n) != label]
        if reworded:
            problems.append("labels reworded: " + ", ".join(reworded))
        if problems:
            raise ValueError(
                "settings cannot weaken the profile's business-identity requirement ("
                + "; ".join(problems) + ")")

    @classmethod
    def from_profile(cls, profile: ResolvedProfile, **deployment_kwargs: Any) -> Settings:
        """Settings derived from a resolved profile. ``deployment_kwargs`` (alias address, buyer
        names, approvers, ...) are deployment facts and win over derived values, with one exception:
        they can ADD to a business-identity requirement but never drop or reword the one a profile
        requires (``ValueError``), as ``with_profile_defaults`` already guarantees."""
        p = profile.profile
        derived: dict[str, Any] = {
            "approval_threshold": p.approvals.threshold,
            "daily_approval_threshold": p.approvals.daily_aggregate_threshold,
            "send_approval_ttl": timedelta(minutes=p.approvals.send_approval_ttl_minutes),
            "substitution_ttl": timedelta(hours=p.approvals.substitution_ttl_hours),
            "max_vendors": p.comms.max_vendors,
            "down_now_max_vendors": p.comms.down_now_max_vendors,
            "reply_token_ttl": timedelta(days=p.comms.reply_token_ttl_days),
            "profile_tag": profile.short(),
            "enabled_families": tuple(p.parts.enabled_families),
            "tiers_enabled": tuple(p.tiers.enabled),
            "base_currency": p.money.base_currency,
            "raw_email_days": p.retention.raw_email_days,
            "tax_name": p.tax.name,
            "rfq_ask_tax_basis": p.tax.ask_basis_in_rfq,
            "identity_fields": tuple(p.legal.business_identity.fields),
            "identity_labels": p.legal.business_identity.effective_labels(),
            "identity_required": p.legal.business_identity.required,
        }
        settings = cls(**{**derived, **deployment_kwargs})
        settings.ensure_identity_not_weaker_than(profile)
        return settings

    def with_profile_defaults(self, profile: ResolvedProfile) -> Settings:
        """Fill only the unset profile-derived fields of explicitly given settings. The business
        identity policy is merged, never replaced: explicit settings can ADD fields or a requirement
        but cannot drop what the profile requires or reword the profile's labels."""
        p = profile.profile
        bi = p.legal.business_identity
        return replace(
            self,
            profile_tag=self.profile_tag or profile.short(),
            enabled_families=(self.enabled_families if self.enabled_families is not None
                              else tuple(p.parts.enabled_families)),
            tiers_enabled=(self.tiers_enabled if self.tiers_enabled is not None
                           else tuple(p.tiers.enabled)),
            identity_fields=tuple(dict.fromkeys([*bi.fields, *self.identity_fields])),
            identity_labels={**self.identity_labels, **bi.effective_labels()},
            identity_required=self.identity_required or bi.required,
            tax_name=self.tax_name or p.tax.name,
            rfq_ask_tax_basis=self.rfq_ask_tax_basis or p.tax.ask_basis_in_rfq,
        )


def _freeze_identities(values: object) -> Mapping[str, Mapping[str, str]]:
    """A deep, read-only copy of ``tenant_id -> field -> value``. Only text values of known identity
    fields are kept (anything else counts as missing), so what the deployer passed in is never held by
    reference and later changes to it cannot reach a prepared message. ``None`` means no identities."""
    if values is None:
        values = {}
    if not isinstance(values, Mapping):
        raise ValueError("business_identities must map tenant ids to {field: value} mappings")
    frozen: dict[str, Mapping[str, str]] = {}
    for tenant_id, fields in values.items():
        if isinstance(tenant_id, str) and isinstance(fields, Mapping):
            frozen[tenant_id] = ReadOnlyMap({
                name: value for name, value in fields.items()
                if name in DEFAULT_IDENTITY_LABELS and isinstance(value, str)
            })
    return ReadOnlyMap(frozen)


class ProfileStampedLog:
    """Event-log wrapper: every appended event carries ``profile`` = ``<id>@<digest12>`` (audit).
    Everything else (reads, chain verification, redaction) is delegated unchanged."""

    def __init__(self, inner: Any, tag: str) -> None:
        self._inner = inner
        self.profile_tag = tag

    def append(self, tenant_id: str, request_id: str | None, actor: str, etype: str,
               payload: Mapping[str, Any] | None = None, *args: Any, **kwargs: Any) -> Event:
        stamped = {**(payload or {}), "profile": self.profile_tag}
        return self._inner.append(tenant_id, request_id, actor, etype, stamped, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def _takes(fn: Callable[..., Any], name: str) -> bool:
    try:
        return name in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


def _tiers_enabled(settings: Settings) -> frozenset[str]:
    return frozenset(settings.tiers_enabled if settings.tiers_enabled is not None else ("A", "B"))


@dataclass(frozen=True)
class _Draft:
    """An RFQ ready to be stored but not stored yet. ``is_new`` says whether it is added or saved over
    the vendor's existing draft."""

    vendor: Vendor
    rfq: RFQ
    is_new: bool


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
    *,
    request_id: str | None = None,
    quote_id: str | None = None,
) -> None:
    """R2: the PO part number must be an approved Tier-A candidate or carry a SubstitutionApproval
    for exactly this candidate, quote version and (when given) request id and quote id.
    Raises ``Conflict`` otherwise."""
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
            and _bound_to(a, request_id, quote_id, quote_version)
        ):
            return
    raise Conflict("R2: part number is not an approved Tier-A candidate and has no substitution approval")


def _bound_to(a: Approval, request_id: str | None, quote_id: str | None, quote_version: int) -> bool:
    if request_id is None and quote_id is None:
        return True
    assert a.candidate_mpn is not None
    return hmac.compare_digest(
        a.mime_hash, substitution_subject(a.candidate_mpn, quote_version, request_id, quote_id))


def csv_cell(value: object) -> str:
    """Neutralise spreadsheet formulas (R7) with the single shared sanitiser (imports.safety)."""
    return neutralise(str(value))


def _total(quote: Quote, quantity: int) -> Decimal:
    assert quote.unit_price_each is not None
    return quote.unit_price_each * Decimal(quantity) + (quote.freight or Decimal(0))


# ---------------------------------------------------------------- the service


def _open_question_details(r: Request) -> list[OpenQuestion]:
    """For each open question sentence, the attribute fields an answer must be keyed by. A sentence several
    attributes share (the three dimensions) lists them all; the family question answers ``family``."""
    out: list[OpenQuestion] = []
    spec = get_family(r.family) if r.family else None
    for text in r.open_questions:
        fields: list[QuestionField] = []
        if spec is None:
            fields.append(QuestionField(attribute="family", allowed_values=list(list_families())))
        else:
            for attr, q in spec.questions.items():
                if q == text:
                    fields.append(QuestionField(
                        attribute=attr, allowed_values=list(spec.allowed_values.get(attr, ()))))
        out.append(OpenQuestion(text=text, fields=fields))
    return out


class SpendBook(Protocol):
    """Approved-but-undrafted spend ("committed", for the daily approval-threshold aggregate) and the
    cap reservation of a PO draft ("reserved"), per (tenant, request). Known-gaps H2: in memory by
    default; a multi-process deployment injects the shared (Postgres) one. ``pop_*`` take the entry
    exactly once, so a release cannot be applied twice by two processes."""

    def set_committed(self, tenant_id: str, request_id: str, day: date, amount: Decimal) -> None: ...

    def pop_committed(self, tenant_id: str, request_id: str) -> None: ...

    def committed_today(self, tenant_id: str, day: date, *, exclude_request: str | None) -> Decimal: ...

    def set_reserved(
        self, tenant_id: str, request_id: str, day: date, amount: Decimal, currency: str
    ) -> None: ...

    def pop_reserved(self, tenant_id: str, request_id: str) -> tuple[date, Decimal, str] | None: ...


class InMemorySpendBook:
    def __init__(self) -> None:
        self._committed: dict[tuple[str, str], tuple[date, Decimal]] = {}
        self._reserved: dict[tuple[str, str], tuple[date, Decimal, str]] = {}
        self._lock = threading.Lock()

    def set_committed(self, tenant_id: str, request_id: str, day: date, amount: Decimal) -> None:
        with self._lock:
            self._committed[(tenant_id, request_id)] = (day, amount)

    def pop_committed(self, tenant_id: str, request_id: str) -> None:
        with self._lock:
            self._committed.pop((tenant_id, request_id), None)

    def committed_today(self, tenant_id: str, day: date, *, exclude_request: str | None) -> Decimal:
        with self._lock:
            return sum((amt for (tid, rid), (d, amt) in self._committed.items()
                        if tid == tenant_id and d == day and rid != exclude_request), Decimal(0))

    def set_reserved(
        self, tenant_id: str, request_id: str, day: date, amount: Decimal, currency: str
    ) -> None:
        with self._lock:
            self._reserved[(tenant_id, request_id)] = (day, amount, currency)

    def pop_reserved(self, tenant_id: str, request_id: str) -> tuple[date, Decimal, str] | None:
        with self._lock:
            return self._reserved.pop((tenant_id, request_id), None)


class PurchasingService(MvpOps):
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
        reply_token_key: bytes | None = None,
        profile: ResolvedProfile | None = None,
        suppliers: SupplierStore | None = None,
        spend_book: SpendBook | None = None,
        shadow_extractor: Extractor | None = None,
        price_history: PriceHistory | None = None,
    ) -> None:
        self._suppliers = suppliers if suppliers is not None else SupplierStore()
        self._reply_key = reply_token_key if reply_token_key is not None else secrets.token_bytes(32)
        if len(self._reply_key) < 16:
            raise ValueError("reply_token_key must be at least 16 bytes")
        # Approved-but-undrafted spend and cap reservations per (tenant, request). In memory unless a
        # shared ``spend_book`` is injected (known-gaps H2).
        self._spend: SpendBook = spend_book if spend_book is not None else InMemorySpendBook()
        self._store = store
        self._log = event_log
        self._clock = clock
        self._send = send_service
        self._approvals = approval_service
        self._extractor = extractor
        self._settings = settings or Settings()
        self._profile = profile
        # Verification layer: a second, independent reader of every quote (findings only) and the
        # tenant's price history, when one is supplied. Thresholds come from the profile.
        self._shadow_extractor = shadow_extractor
        self._price_history = price_history
        self._verify_cfg = (VerifyConfig.from_mapping(profile.profile.verification.model_dump(mode="json"))
                            if profile is not None else VerifyConfig())
        self._check_wiring()
        self._identities = self._settings.tenant_identities()  # frozen, tenant-scoped copy
        if self._settings.profile_tag and not isinstance(event_log, ProfileStampedLog):
            event_log = ProfileStampedLog(event_log, self._settings.profile_tag)
            self._log = event_log
        self.notifier: ApprovalNotifier = notifier or InMemoryNotifier()
        self._ids = ids
        self._token_gen = token_gen
        self.llm = llm  # for the planner/graph; the service itself makes no model calls
        self._wf = Workflow(event_log, clock)
        self._prepared: dict[tuple[str, str], Any] = {}
        self._prepared_footers: dict[tuple[str, str], str] = {}  # footer as rendered at prepare time
        # prepare_rfqs reads the request's RFQ rows, checks every message and only then adds rows; two calls for
        # one request (a double click) must not interleave, or each adds a row for the same vendor. One lock per
        # request that is being prepared right now; the entry goes away with its last user.
        self._prepare_guard = threading.Lock()
        self._prepare_locks: dict[tuple[str, str], list[Any]] = {}

    def _check_wiring(self) -> None:
        """Refuse wiring that would lose what the settings or the profile call for. The settings may not
        be weaker than the profile they were given with; the send-service (whose send-time check is the
        backstop) must require every identity label the settings call for; and, given a profile, it must
        carry that profile's footer wording and must not allow more recipients than ``comms.max_vendors`` (a
        stricter limit is a legitimate local tightening, a looser one is refused). A send-service
        built with ``SendService.from_profile`` always satisfies all of this. The messages name the part
        that differs and never a value of company data."""
        if self._profile is not None:
            self._settings.ensure_identity_not_weaker_than(self._profile)
        absent = [label for label in _required_identity_labels(self._settings)
                  if label not in self._send.required_identity_labels]
        if absent:
            raise ValueError(
                "the send-service does not require the business-identity lines these settings call "
                f"for (labels missing: {', '.join(absent)}); build it with SendService.from_profile")
        if self._profile is not None:
            self._check_send_matches(self._profile)

    def _check_send_matches(self, profile: ResolvedProfile) -> None:
        p = profile.profile
        differs: list[str] = []
        if self._send.footer_template != p.legal.disclosure_footer:
            differs.append("the footer wording differs from legal.disclosure_footer")
        if self._send.max_recipients > p.comms.max_vendors:
            differs.append(
                f"the recipient limit {self._send.max_recipients} is higher than "
                f"comms.max_vendors {p.comms.max_vendors}")
        if differs:
            raise ValueError(
                "the send-service was not built from this profile (" + "; ".join(differs)
                + "); build it with SendService.from_profile")

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
            open_question_details=_open_question_details(r),
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
            assumptions=self._assumption_views(tid, request.id),
        )

    def _pending(self, request: Request) -> list[PendingApproval]:
        if request.state is not S.APPROVAL_PENDING:
            return []
        sel = self._selection(request.tenant_id, request.id)
        kind = "substitution" if sel.get("substitution") else "po"
        return [PendingApproval(kind=kind, request_id=request.id, quote_id=sel.get("quote_id"),
                                note="awaiting approver decision via approval link")]

    def _comparison(self, request: Request, quotes: list[Quote]) -> Comparison:
        # callback-pending quotes are quarantined: not even listed as candidates for recommendation
        quotes = [q for q in quotes if not QUARANTINE_EXTRA & set(q.flags)]
        extra: dict[str, Any] = {"profile": self._profile} if (
            self._profile is not None and _takes(compare, "profile")) else {}
        return compare(
            request.id, quotes, need_by=request.need_by, today=self._clock.now().date(),
            quantity=request.quantity or 1, **extra,
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
        check_site(site)
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
        self._record_quote_basis_assumption(request)
        self._apply_spec(request, normalise(text, questions_asked=0))
        return self._detail(request)

    def _apply_spec(self, request: Request, spec: NormalisedSpec) -> None:
        """Request is in SPEC_DRAFT. Record the spec and move to the next state (R4)."""
        request.family = spec.family
        request.attributes = dict(spec.attributes)
        if spec.family and not is_family_enabled(spec.family, self._settings.enabled_families):
            request.open_questions = []  # no guessing: never map to a family we do not handle
            self._move(request, S.ESCALATED, "agent", {
                "reason": "family not enabled in this deployment",
                "family": spec.family,
                "message": (f"This deployment does not handle {spec.family.replace('_', ' ')} "
                            "requests. A person will review it; nothing has been sent or ordered."),
            })
            return
        self._record_assumptions(request, spec.attributes)  # values the requester did not state
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

    def _offerable(self, c: Candidate) -> bool:
        return c.tier.value in _tiers_enabled(self._settings) and is_offerable(c)

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

    def _merge_answers(self, request: Request, answers: dict[str, str]) -> tuple[dict[str, Any], str | None]:
        from components.core.domain import Attribute, AttrSource

        family = request.family
        attrs = dict(request.attributes)
        if "family" in answers:
            if family is not None or answers["family"] not in list_families():
                raise Conflict("unknown or already-set family")
            if not is_family_enabled(answers["family"], self._settings.enabled_families):
                raise Conflict(f"family {answers['family']!r} is not enabled in this deployment")
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
        with self._one_prepare_at_a_time(ctx.tenant_id, request_id):  # in-process: see known-gaps.md
            return self._prepare_rfqs(
                ctx, request_id, vendor_ids=vendor_ids, candidate_mpns=candidate_mpns)

    @contextmanager
    def _one_prepare_at_a_time(self, tenant_id: str, request_id: str) -> Iterator[None]:
        """Serialise ``prepare_rfqs`` per request: only calls for the SAME request wait for each other."""
        key = (tenant_id, request_id)
        with self._prepare_guard:
            entry = self._prepare_locks.get(key)
            if entry is None:
                entry = self._prepare_locks[key] = [threading.Lock(), 0]
            entry[1] += 1
        try:
            with entry[0]:
                yield
        finally:
            with self._prepare_guard:
                entry[1] -= 1
                if entry[1] == 0:
                    del self._prepare_locks[key]

    def _prepare_rfqs(
        self, ctx: Ctx, request_id: str, *, vendor_ids: list[str],
        candidate_mpns: list[str] | None = None,
    ) -> list[PreparedRFQ]:
        request = self._load_request(ctx, request_id)
        if request.state not in (S.SPEC_CONFIRMED, S.RFQ_DRAFTED):
            raise Conflict(f"cannot prepare RFQs in state {request.state.value}")
        if not request.quantity:
            raise Conflict("quantity is required before an RFQ can be drafted")
        self.check_assumptions_closed(ctx.tenant_id, request.id)
        mpns = self._rfq_mpns(request, candidate_mpns)
        ts = self._ts(ctx.tenant_id)
        vendors = self._rfq_vendors(ts, request, list(dict.fromkeys(vendor_ids)))
        identity = self._business_identity(ctx)  # gate: nothing is stored if it refuses
        drafts = [self._draft_rfq(ctx, request, v, mpns) for v in vendors]
        self._check_messages(ctx, drafts, identity)  # last gate: nor if a message cannot be built
        out = [self._prepare_one(ctx, request, d, identity) for d in drafts]
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
            if self._callback_pending(request.tenant_id, v.id):
                raise Conflict(f"vendor {v.id} has an unconfirmed contact change (callback pending)")
            if not v.preferred:
                raise Conflict(f"vendor {v.id} is not a preferred vendor")
        self.check_supplier_guards(request.tenant_id, vendors)  # verified, not suppressed, not individual
        limit = (self._settings.down_now_max_vendors if request.down_now
                 else self._settings.max_vendors)
        existing = {r.vendor_id for r in self._rfqs(ts, request.id)}
        if len(existing | {v.id for v in vendors}) > limit:
            raise Conflict(f"at most {limit} vendors per request")
        return vendors

    def _business_identity(self, ctx: Ctx) -> list[tuple[str, str]]:
        """The ordered ``(label, value)`` company-particulars lines for the caller's tenant. The
        tenant comes from ``ctx`` only and the lines from the frozen, tenant-scoped provider. When the
        profile requires the block and any field is missing (absent, or showing no letter or digit)
        this raises ``Conflict`` naming the FIELDS (never values); a value that is present but invalid
        is a ``Conflict`` naming the LABEL. Both happen BEFORE anything is stored; otherwise the fields
        the tenant has are returned (possibly none)."""
        s = self._settings
        pairs = list(self._identities.identity_for(ctx.tenant_id))
        have = {label for label, _ in pairs}
        missing = [name for name in s.identity_fields if s.identity_label(name) not in have]
        if missing and s.identity_required:
            raise Conflict("business identity incomplete: missing " + ", ".join(missing))
        try:
            validate_identity_pairs(pairs)
        except SendError as exc:
            raise Conflict(f"cannot prepare message: {exc}") from exc
        return pairs

    def _draft_rfq(self, ctx: Ctx, request: Request, vendor: Vendor, mpns: list[str]) -> _Draft:
        """The RFQ to this vendor as it should be stored, NOT stored yet: a new one, or the existing
        draft with the new body and reply token. Writes nothing."""
        ts = self._ts(ctx.tenant_id)
        existing = next((r for r in self._rfqs(ts, request.id) if r.vendor_id == vendor.id), None)
        if existing is not None and existing.sent_message_id:
            raise Conflict(f"RFQ to {vendor.id} was already sent")
        cands = {c.mpn: c for c in self._candidates(request.tenant_id, request.id)}
        body = self._rfq_body(request, vendor, [cands[m] for m in mpns], self._settings)
        if existing is None:
            rfq = RFQ(id=self._ids("rfq"), tenant_id=ctx.tenant_id, request_id=request.id,
                      vendor_id=vendor.id, subject=f"RFQ: {mpns[0]} x{request.quantity}",
                      body=body, candidate_mpns=tuple(mpns))
            return _Draft(vendor, rfq.model_copy(update={"reply_token": self._issue_reply_token(rfq)}), True)
        return _Draft(vendor, existing.model_copy(update={
            "body": body, "candidate_mpns": tuple(mpns),
            "reply_token": self._issue_reply_token(existing)}), False)

    def _sender(self, ctx: Ctx) -> tuple[str, str, str, str]:
        """Who the message is from: (name, phone, alias address, reply-to address)."""
        name, reply_to = self._buyer(ctx)
        return name, self._settings.buyer_phone, self._settings.alias_address, reply_to

    def _check_messages(self, ctx: Ctx, drafts: list[_Draft], identity: list[tuple[str, str]]) -> None:
        """Build and read back every message (``SendService.check_prepare``, a dry run) BEFORE the first
        RFQ row is added, so a message that cannot be built (a sender name that would not survive a
        parse, a vendor name or a site the body refuses, ...) is a 409 that leaves nothing behind: no
        orphan RFQ row, no event, no cache entry."""
        sender = self._sender(ctx)
        for d in drafts:
            try:
                self._send.check_prepare(d.rfq, d.vendor, *sender, identity=identity)
            except SendError as exc:
                raise Conflict(f"cannot prepare message: {exc}") from exc

    def _prepare_one(self, ctx: Ctx, request: Request, draft: _Draft,
                     identity: list[tuple[str, str]]) -> PreparedRFQ:
        ts = self._ts(ctx.tenant_id)
        rfq, vendor = draft.rfq, draft.vendor
        if draft.is_new:
            ts.rfqs.add(rfq)
        else:
            ts.rfqs.save(rfq)
        name, phone, alias, reply_to = self._sender(ctx)
        try:
            prepared = self._send.prepare(rfq, vendor, name, phone, alias, reply_to, identity=identity)
            preview = self._send.preview(prepared)  # inside the try: a message that cannot be read is a 409
        except SendError as exc:
            raise Conflict(f"cannot prepare message: {exc}") from exc
        self._prepared[(ctx.tenant_id, rfq.id)] = prepared
        footer = render_footer(self._send.footer_template, name)
        self._prepared_footers[(ctx.tenant_id, rfq.id)] = footer
        self._emit(ctx.tenant_id, request.id, ctx.actor, EVT_RFQ_PREPARED, {
            "rfq_id": rfq.id, "vendor_id": vendor.id, "mime_hash": prepared.mime_hash})
        return PreparedRFQ(
            rfq_id=rfq.id, vendor=self._ref(vendor), to=prepared.to, subject=prepared.subject,
            body_preview=preview.text, mime_hash=prepared.mime_hash,
            footer=footer,
        )

    # ------------------------------------------------------------ templated text RFQs (quote to RFQ)

    _TEXT_LINK = re.compile(r"://|\bwww\.|<[^>]*>|\bhttps?\b|&#?\w+;", re.IGNORECASE)
    _TEXT_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
    _TEXT_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")
    _TEXT_MODES = ("per_supplier", "per_item")
    TEXT_SUBJECT_MAX = 200
    TEXT_BODY_MAX = 20000
    TEXT_LINES_MAX = 200

    def _check_text_rfq(
        self, ctx: Ctx, vendor_id: str, subject: str, body: str, line_refs: list[str],
        quote_ref: str, mode: str,
    ) -> tuple[Vendor, list[tuple[str, str]]]:
        """Every gate of a text RFQ, before anything is stored. The text is re-checked here and not
        trusted from the caller: no link, markup, entity or control character (a line break is
        allowed in the body only), bounded length."""
        require(ctx, Role.BUYER)
        if mode not in self._TEXT_MODES:
            raise Conflict("unknown mode")
        if not self._TEXT_REF.match(str(quote_ref)):
            raise Conflict("bad quote reference")
        if not 1 <= len(line_refs) <= self.TEXT_LINES_MAX or not all(
                isinstance(x, str) and self._TEXT_REF.match(x) for x in line_refs):
            raise Conflict("bad line references")
        for where, text, limit, multiline in (("subject", subject, self.TEXT_SUBJECT_MAX, False),
                                              ("body", body, self.TEXT_BODY_MAX, True)):
            if not isinstance(text, str) or not text.strip() or len(text) > limit:
                raise Conflict(f"{where}: empty or too long")
            if self._TEXT_CONTROL.search(text) or (not multiline and ("\n" in text or "\r" in text)):
                raise Conflict(f"{where}: control characters are not allowed")
            if self._TEXT_LINK.search(text):
                raise Conflict(f"{where}: links and markup are not allowed")
        ts = self._ts(ctx.tenant_id)
        try:
            vendor: Vendor = ts.vendors.get(vendor_id)
        except (NotFoundError, TenantIsolationError):
            raise Conflict(f"no verified supplier for {vendor_id!r}") from None
        if self._callback_pending(ctx.tenant_id, vendor.id):
            raise Conflict(f"vendor {vendor.id} has an unconfirmed contact change (callback pending)")
        if not vendor.preferred:
            raise Conflict(f"vendor {vendor.id} is not a preferred vendor")
        self.check_supplier_guards(ctx.tenant_id, [vendor])  # verified, not suppressed, not individual
        return vendor, self._business_identity(ctx)

    def check_text_rfq(
        self, ctx: Ctx, *, vendor_id: str, subject: str, body: str, line_refs: list[str],
        quote_ref: str, mode: str = "per_supplier",
    ) -> None:
        vendor, identity = self._check_text_rfq(ctx, vendor_id, subject, body, line_refs, quote_ref, mode)
        probe = RFQ(id="probe", tenant_id=ctx.tenant_id, request_id="probe", vendor_id=vendor.id,
                    subject=subject, body=body)
        self._check_messages(ctx, [_Draft(vendor, probe, True)], identity)

    def prepare_text_rfq(
        self, ctx: Ctx, *, vendor_id: str, subject: str, body: str, line_refs: list[str],
        quote_ref: str, mode: str = "per_supplier",
    ) -> PreparedRFQ:
        """One templated message (all of a supplier's lines, or one line) to one verified supplier.
        A new ``Request`` is the container (no part, no candidates, so it can never become a PO);
        the RFQ holds the exact text; the business identity, footer and ``mime_hash`` come from the
        send-service; the request moves SPEC_DRAFT, SPEC_CONFIRMED, RFQ_DRAFTED only through the
        workflow. Approval and sending stay ``approve_send`` (R1)."""
        vendor, identity = self._check_text_rfq(ctx, vendor_id, subject, body, line_refs, quote_ref, mode)
        now = self._clock.now()
        request = Request(
            id=self._ids("req"), tenant_id=ctx.tenant_id, requester=ctx.actor,
            raw_text=f"Quote request {quote_ref} to {vendor.id}", created_at=now)
        rfq = RFQ(id=self._ids("rfq"), tenant_id=ctx.tenant_id, request_id=request.id,
                  vendor_id=vendor.id, subject=subject, body=body)
        rfq = rfq.model_copy(update={"reply_token": self._issue_reply_token(rfq)})
        draft = _Draft(vendor, rfq, True)
        self._check_messages(ctx, [draft], identity)  # nothing is stored if the message cannot be built
        self._ts(ctx.tenant_id).requests.add(request)
        self._emit(ctx.tenant_id, request.id, ctx.actor, EVT_REQUEST_CREATED, {
            "instruction_flags": [], "criticality": False, "down_now": False})
        self._move(request, S.SPEC_DRAFT, "agent", {"step": "quote_rfq"})
        self._move(request, S.SPEC_CONFIRMED, "agent", {"step": "quote_rfq"})
        out = self._prepare_one(ctx, request, draft, identity)
        self._move(request, S.RFQ_DRAFTED, ctx.actor, {"rfq_ids": [rfq.id], "candidate_mpns": []})
        self._emit(ctx.tenant_id, request.id, ctx.actor, EVT_QUOTE_RFQ_LINKED, {
            "quote_ref": quote_ref, "mode": mode, "line_refs": list(line_refs),
            "rfq_id": rfq.id, "vendor_id": vendor.id, "mime_hash": out.mime_hash})
        return out

    def list_text_rfqs(self, ctx: Ctx, quote_ref: str) -> list[TextRfqDraft]:
        """Read-only: this tenant's prepared, unsent text RFQs linked to ``quote_ref``."""
        require(ctx, Role.BUYER)
        out: list[TextRfqDraft] = []
        for request in self._ts(ctx.tenant_id).requests.list():
            link = self._last_event(ctx.tenant_id, request.id, EVT_QUOTE_RFQ_LINKED)
            if link is None or link.payload.get("quote_ref") != quote_ref:
                continue
            for p in self.list_prepared_rfqs(ctx, request.id):
                if p.rfq_id == link.payload.get("rfq_id"):
                    out.append(TextRfqDraft(request.id, quote_ref, str(link.payload.get("mode")),
                                            list(link.payload.get("line_refs", [])), p))
        return out

    def list_prepared_rfqs(self, ctx: Ctx, request_id: str) -> list[PreparedRFQ]:
        """Read-only: the request's prepared, unsent RFQs, re-rendered from the very message objects
        ``approve_send`` verifies (so ``mime_hash`` is the one ``prepare_rfqs`` returned). An RFQ whose
        prepared message is no longer held (for example after a restart) is left out: prepare again."""
        require(ctx, Role.BUYER)
        ts = self._ts(ctx.tenant_id)
        request = self._load_request(ctx, request_id)
        vendors = {v.id: v for v in ts.vendors.list()}
        out: list[PreparedRFQ] = []
        for rfq in self._rfqs(ts, request.id):
            prepared = self._prepared.get((ctx.tenant_id, rfq.id))
            footer = self._prepared_footers.get((ctx.tenant_id, rfq.id))
            if rfq.sent_message_id or prepared is None or footer is None or rfq.vendor_id not in vendors:
                continue
            try:
                preview = self._send.preview(prepared)
            except SendError:
                continue
            out.append(PreparedRFQ(
                rfq_id=rfq.id, vendor=self._ref(vendors[rfq.vendor_id]), to=prepared.to,
                subject=prepared.subject, body_preview=preview.text, mime_hash=prepared.mime_hash,
                footer=footer))
        return out

    @staticmethod
    def _rfq_body(request: Request, vendor: Vendor, cands: list[Candidate],
                  settings: Settings | None = None) -> str:
        lines = [f"Hello {vendor.name},", "", "Please quote the following part(s):"]
        lines += [f"- {c.mpn} ({c.manufacturer})" for c in cands]
        lines += ["", f"Quantity: {request.quantity}"]
        if request.need_by:
            lines.append(f"Need by: {request.need_by.isoformat()}")
        if request.site:
            lines.append(f"Ship to: {request.site}")
        ask = ("unit price and unit of measure, currency, lead time, freight, "
               "quote validity, condition, and the exact manufacturer and part number you quote.")
        if settings is not None and settings.rfq_ask_tax_basis:
            tax = settings.tax_name or "tax"
            ask = ("unit price and unit of measure, currency, whether the price is exclusive or "
                   f"inclusive of {tax}, lead time, freight, quote validity, condition, "
                   "and the exact manufacturer and part number you quote.")
        lines += [
            "",
            f"Please reply with {ask}",
            "If you offer a different part, say so explicitly with its manufacturer and number.",
        ]
        return "\n".join(lines)

    def approve_send(self, ctx: Ctx, rfq_id: str, *, mime_hash: str) -> SendResult:
        require(ctx, Role.BUYER)
        ts = self._ts(ctx.tenant_id)
        rfq: RFQ = self._get(ts.rfqs, rfq_id)
        request = self._load_request(ctx, rfq.request_id)
        vendor = self._get(ts.vendors, rfq.vendor_id)
        self.check_not_suppressed(ctx.tenant_id, vendor)
        if self._profile_of(ctx.tenant_id, vendor.id).verification.state != "attested":
            raise Conflict(f"vendor not verified: {vendor.name}")  # verification can lapse after prepare
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

    # -- R12: signed reply tokens, vendor callback state

    def _sig(self, body: str) -> str:
        mac = hmac.new(self._reply_key, b"reply-token|" + body.encode("ascii"), hashlib.sha256)
        return base64.urlsafe_b64encode(mac.digest()[:16]).decode("ascii").rstrip("=")

    def _issue_reply_token(self, rfq: RFQ) -> str:
        """HMAC-signed value bound to tenant + rfq + vendor (+ expiry); carries no secret."""
        exp = int((self._clock.now() + self._settings.reply_token_ttl).timestamp())
        raw = json.dumps([rfq.tenant_id, rfq.id, rfq.vendor_id, exp], separators=(",", ":"))
        body = base64.urlsafe_b64encode(raw.encode()).decode("ascii").rstrip("=")
        return f"{body}.{self._sig(body)}"

    def _verify_reply_token(self, token: object) -> RFQ:
        """The RFQ the token was issued for, else ``NotFound`` (same error for every failure)."""
        try:
            if not isinstance(token, str) or token.count(".") != 1 or len(token) > 500:
                raise ValueError
            body, sig = token.split(".")
            if not hmac.compare_digest(sig, self._sig(body)):
                raise ValueError
            tenant, rfq_id, vendor_id, exp = json.loads(
                base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
            if int(exp) <= int(self._clock.now().timestamp()):
                raise ValueError
            rfq = self._ts(str(tenant)).rfqs.get(str(rfq_id))
            if rfq.vendor_id != vendor_id or rfq.tenant_id != tenant or rfq.reply_token != token:
                raise ValueError
        except (ValueError, TypeError, KeyError, NotFoundError, TenantIsolationError) as exc:
            raise NotFound("reply token") from exc
        return rfq

    def _callback_pending(self, tenant_id: str, vendor_id: str) -> bool:
        state = False
        for e in self._log.events(tenant_id):
            if e.payload.get("vendor_id") != vendor_id:
                continue
            if e.type == EVT_VENDOR_CONTACT_CHANGED:
                state = True
            elif e.type == EVT_VENDOR_CONTACT_CONFIRMED:
                state = False
        return state

    def confirm_vendor_contact(self, ctx: Ctx, vendor_id: str) -> None:
        """Admin records that the out-of-band callback to the vendor was made (R12)."""
        require(ctx, Role.ADMIN)
        self._get(self._ts(ctx.tenant_id).vendors, vendor_id)
        if not self._callback_pending(ctx.tenant_id, vendor_id):
            raise Conflict("no pending contact change for this vendor")
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_VENDOR_CONTACT_CONFIRMED,
                   {"vendor_id": vendor_id, "pending_callback": False})

    def set_kill_switch(self, ctx: Ctx, *, engaged: bool) -> None:
        """Admin only: stop (or resume) all outbound mail for the caller's tenant. Audited."""
        require(ctx, Role.ADMIN)
        self._send.set_kill_switch(ctx.tenant_id, engaged=engaged)
        self._emit(ctx.tenant_id, None, ctx.actor, EVT_KILL_SWITCH, {"engaged": bool(engaged)})

    # -- quote ingestion

    def ingest_quote(
        self, ctx: Ctx, request_id: str, *, vendor_id: str, source_text: str
    ) -> QuoteView:
        """Quote typed/pasted by an authenticated buyer. Carries no sender-authentication claim
        (flag ``buyer_entered`` forces a human approval at selection)."""
        require(ctx, Role.BUYER)
        ts = self._ts(ctx.tenant_id)
        request = self._load_request(ctx, request_id)
        vendor: Vendor = self._get(ts.vendors, vendor_id)
        rfq = next((r for r in self._rfqs(ts, request.id) if r.vendor_id == vendor.id), None)
        return self._ingest(request, vendor, rfq, source_text, buyer_entered=True, dmarc_ok=True)

    def ingest_inbound_reply(
        self, *, reply_token: str, from_domain: str, source_text: str, dmarc_aligned: bool
    ) -> QuoteView | StopAck:
        """Vendor reply from the trusted inbound adapter. Tenant/request/vendor come from the signed
        token only. A wrong sender domain or a failed DMARC alignment quarantines the quote (R12)."""
        rfq = self._verify_reply_token(reply_token)
        ts = self._ts(rfq.tenant_id)
        request: Request = self._get(ts.requests, rfq.request_id)
        vendor: Vendor = self._get(ts.vendors, rfq.vendor_id)
        domain_ok = isinstance(from_domain, str) and (
            from_domain.strip().lower().rstrip(".") == vendor.domain.strip().lower())
        if domain_ok and dmarc_aligned is True and is_stop_request(source_text):
            # A stop request from the vendor's own, authenticated domain suppresses the vendor and does nothing else:
            # no quote is read, no state moves, the text is not an instruction.
            self._suppress(rfq.tenant_id, vendor, "system", "stop_reply", request_id=request.id)
            return StopAck(vendor=self._ref(vendor))
        view = self._ingest(request, vendor, rfq, source_text, buyer_entered=False,
                            dmarc_ok=bool(dmarc_aligned is True and domain_ok))
        self._send.cancel_follow_ups(rfq.tenant_id, rfq.id)
        return view

    def _ingest(self, request: Request, vendor: Vendor, rfq: RFQ | None, source_text: str,
                *, buyer_entered: bool, dmarc_ok: bool) -> QuoteView:
        ts = self._ts(request.tenant_id)
        if rfq is None or not rfq.sent_message_id:
            raise Conflict("no sent RFQ to this vendor")
        if request.state not in INGEST_STATES:
            raise Conflict(f"cannot ingest quotes in state {request.state.value}")
        if not isinstance(source_text, str) or len(source_text) > MAX_SOURCE_CHARS:
            raise Conflict("quote text is missing or too large")
        extra = ["buyer_entered"] if buyer_entered else []
        if self._callback_pending(request.tenant_id, vendor.id):
            extra.append("vendor_pending_callback")
        quote, findings = self._build_quote(request, rfq, vendor, source_text, dmarc_ok, extra)
        existing = ts.quotes.find(quote.id)
        if existing is None:
            ts.quotes.add(quote)
        else:
            ts.quotes.save(quote)
        self._emit(request.tenant_id, request.id, "agent", EVT_QUOTE_INGESTED, {
            "quote_id": quote.id, "version": quote.version, "vendor_id": vendor.id,
            "flags": list(quote.flags), "offered_tier": quote.offered_tier.value,
            "buyer_entered": buyer_entered})
        if findings:
            self._emit(request.tenant_id, request.id, "agent", EVT_QUOTE_VERIFIED, {
                "quote_id": quote.id, "version": quote.version,
                "findings": finding_payload(findings)})
        self._advance_after_quote(request)
        return QuoteView(quote=quote, vendor=self._ref(vendor))

    def _build_quote(self, request: Request, rfq: RFQ, vendor: Vendor, text: str,
                     dmarc_aligned: bool, extra_flags: Iterable[str] = ()
                     ) -> tuple[Quote, tuple[Finding, ...]]:
        extra: list[str] = list(extra_flags)
        try:
            extracted = self._extractor.extract(text)
        except Exception:  # noqa: BLE001 - a failing extractor yields a blank, flagged quote
            extracted, extra = ExtractedQuote(), [*extra, "extraction_failed"]
        g = ground(extracted, text)
        prior = self._ts(request.tenant_id).quotes.find(self._quote_id_for(request, rfq))
        extra_kw: dict[str, Any] = {"profile": self._profile} if (
            self._profile is not None and _takes(normalise_quote, "profile")) else {}
        quote = normalise_quote(
            g.extracted, quote_id=prior.id if prior else self._ids("quote"),
            tenant_id=request.tenant_id, rfq_id=rfq.id, vendor_id=vendor.id,
            offered_tier=Tier.D, dmarc_aligned=dmarc_aligned,
            grounding_flags=[*g.flags, *extra], snippets=g.snippets,
            version=(prior.version + 1) if prior else 1, received_on=self._clock.now().date(),
            **extra_kw,
        )
        if quote.offered_mpn and request.family:
            tier = self._classify(request, quote.offered_mpn)
            quote = quote.model_copy(update={"offered_tier": tier})
        if quote.unit_price_each is not None and quote.freight is None \
                and "freight_unknown" not in quote.flags:
            quote = quote.model_copy(update={"flags": (*quote.flags, "freight_unknown")})
        findings = self._verify(quote, g.extracted, text, vendor, request)
        added = tuple(f for f in flags_for(findings) if f not in quote.flags)
        if added:
            quote = quote.model_copy(update={"flags": (*quote.flags, *added)})
        return quote, findings

    def _verify(self, quote: Quote, primary: ExtractedQuote, text: str, vendor: Vendor,
                request: Request) -> tuple[Finding, ...]:
        """Verification findings for a freshly built quote. They only add flags and an audit event:
        nothing here approves a quote, picks between two readings or fills a blank (R1, R3, R6)."""
        shadow: ExtractedQuote | None = None
        if self._shadow_extractor is not None:
            try:
                shadow = ground(self._shadow_extractor.extract(text), text).extracted
            except Exception:  # noqa: BLE001 - a failing second reader adds nothing
                shadow = None
        qty = Decimal(request.quantity) if request.quantity else None
        return verify_quote(quote, primary, shadow, cfg=self._verify_cfg,
                            history=self._price_history, merchant_id=vendor.id, quantity=qty)

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
        return is_quarantined(q) or INJECTION_FLAG in q.flags or bool(QUARANTINE_EXTRA & set(q.flags))

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
        forced = sorted(FORCE_APPROVAL_FLAGS & set(quote.flags))
        daily = self._settings.daily_approval_threshold or self._settings.approval_threshold
        over_daily = self._committed_today(request, exclude=True) + total > daily  # M5: no splitting
        needs_approval = (substitution or total > self._settings.approval_threshold
                          or over_daily or bool(forced))
        fp = quote_fingerprint(quote)
        self._move(request, S.QUOTE_SELECTED, ctx.actor, {
            "quote_id": quote.id, "quote_version": quote.version, "quote_hash": fp,
            "approval_required": needs_approval, "substitution": substitution,
            "approval_reasons": forced + (["daily_aggregate"] if over_daily else []),
            "total": total})
        self._spend.set_committed(request.tenant_id, request.id, self._clock.now().date(), total)
        if needs_approval:
            self._request_approval(request, quote, fp, total, force_separation=bool(forced) or over_daily)
        return self._detail(request)

    def _committed_today(self, request: Request, *, exclude: bool) -> Decimal:
        return self._spend.committed_today(
            request.tenant_id, self._clock.now().date(),
            exclude_request=request.id if exclude else None)

    def _check_selectable(self, request: Request, quote: Quote, ts: TenantStore) -> None:
        cmp = self._comparison(request, self._quotes(ts, request.id))
        if any(r.startswith(f"excluded:{quote.id}:") for r in cmp.reasons):
            raise Conflict("quote is excluded (flagged, quarantined or unusable)")
        if REFUSE_FLAGS & set(quote.flags):
            raise Conflict("quote validity has expired: ask the vendor for a current quote")
        if self._excluded_flags(quote):
            raise Conflict("quote is quarantined or flagged")
        if quote.offered_tier is Tier.D:
            raise Conflict("quote offers a Tier D part: engineering review required")
        if quote.offered_tier.value in ("A", "B") and \
                quote.offered_tier.value not in _tiers_enabled(self._settings):
            raise Conflict(f"Tier {quote.offered_tier.value} is not enabled in this deployment")
        if quote.unit_price_each is None or quote.currency is None or not quote.offered_mpn:
            raise Conflict("quote lacks price, currency or offered part number")

    def _request_approval(self, request: Request, quote: Quote, fp: str, total: Decimal,
                          *, force_separation: bool = False) -> None:
        above = force_separation or total > self._settings.approval_threshold
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
        qty = request.quantity
        total = quote.unit_price_each * Decimal(qty) if quote.unit_price_each is not None and qty else None
        note = ("substitution_review" if sel.get("substitution")
                else "quality_review" if sel.get("approval_reasons") else "")
        return ApprovalLinkView(
            request_id=request.id, quote_id=quote.id, vendor=self._ref(vendor),
            unit_price_each=quote.unit_price_each, currency=quote.currency,
            lead_time_days=quote.lead_time_days, quantity=qty, total=total,
            offered_mpn=clean_text(quote.offered_mpn, limit=80) if quote.offered_mpn else None,
            offered_tier=quote.offered_tier.value, flags=list(quote.flags),
            part_summary=self._part_summary(request), action_options=[claims.action.value],
            expires_at=claims.expires_at, note=note,
            tax_basis=quote.tax_basis, tax_rate=quote.tax_rate,
            unit_price_quoted=quote.unit_price_quoted,
            review_notes=sorted(INFORMATIONAL_FLAGS & set(quote.flags)))

    @staticmethod
    def _part_summary(request: Request) -> str:
        """Templated over attribute ids (R3): `family; name=value; ...`."""
        parts = [f"{k}={a.value}" for k, a in sorted(request.attributes.items())]
        return clean_text("; ".join([request.family or "unknown family", *parts]), limit=300)

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
                    ctx.tenant_id, ctx.actor,
                    self._canonical_mpn(ctx.tenant_id, request.id, quote.offered_mpn or ""),
                    quote.version, self._settings.substitution_ttl,
                    request_id=request.id, quote_id=quote.id)
                self._emit(ctx.tenant_id, request.id, ctx.actor, "approval.substitution_recorded", {
                    "approval_id": sub.id, "candidate_mpn": sub.candidate_mpn,
                    "quote_id": quote.id, "quote_version": quote.version})
            self._move(request, S.APPROVED, ctx.actor, {"quote_id": quote.id, "jti": claims.jti})
            return DecisionResult(request_id=request.id, decision="approved", state=request.state)
        self._move(request, S.DECLINED, ctx.actor, {"quote_id": quote.id, "jti": claims.jti})
        self._release(request)
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
                 self._clock.now(), request_id=request.id, quote_id=quote.id)
        total = _total(quote, qty)
        self._reserve(request, total, quote.currency)  # M5: spend is booked at draft time
        draft = PurchaseOrderDraft(
            id=self._ids("po"), tenant_id=ctx.tenant_id, request_id=request.id, quote_id=quote.id,
            quote_version=quote.version, vendor_id=quote.vendor_id,
            mpn=self._canonical_mpn(ctx.tenant_id, request.id, quote.offered_mpn),
            quantity=qty, unit_price_each=quote.unit_price_each, currency=quote.currency,
            total=total)
        ts.po_drafts.add(draft)
        self._move(request, S.PO_DRAFTED, ctx.actor, {
            "po_id": draft.id, "quote_id": quote.id, "quote_version": quote.version,
            "total": total, "currency": quote.currency})
        return draft

    def _canonical_mpn(self, tenant_id: str, request_id: str, offered: str) -> str:
        """The request's own candidate MPN when the offered part matches one (R2/L2), never the
        vendor's literal spelling; otherwise the offered MPN, whitespace-collapsed."""
        wanted = normalise_mpn(offered)
        for c in self._candidates(tenant_id, request_id):
            if wanted and normalise_mpn(c.mpn) == wanted:
                return c.mpn
        return " ".join(offered.split())

    def _reserve(self, request: Request, total: Decimal, currency: str) -> None:
        caps: CapPolicy | None = self._approvals.caps
        if caps is None:
            raise Conflict("spend caps are not configured")
        try:
            caps.reserve(request.tenant_id, total, currency=currency)
        except CapError as exc:
            raise Conflict(f"cap: {exc}") from exc
        self._spend.set_reserved(request.tenant_id, request.id, caps.today(), total, currency)

    def _release(self, request: Request) -> None:
        """Give back committed and reserved spend (declined / cancelled)."""
        self._spend.pop_committed(request.tenant_id, request.id)
        held = self._spend.pop_reserved(request.tenant_id, request.id)
        caps = self._approvals.caps
        if held is not None and caps is not None:
            day, amount, currency = held
            caps.release(request.tenant_id, amount, currency=currency, day=day)

    def cancel_po_draft(self, ctx: Ctx, request_id: str) -> None:
        """Cancel a drafted PO: the request is CANCELLED and its reserved spend released."""
        require(ctx, Role.BUYER)
        request = self._load_request(ctx, request_id)
        if request.state is not S.PO_DRAFTED:
            raise Conflict(f"no PO draft to cancel in state {request.state.value}")
        self._move(request, S.CANCELLED, ctx.actor, {"reason": "po_draft_cancelled"})
        self._release(request)

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
            changed = (current.contact_email, current.domain) != (vendor.contact_email, vendor.domain)
            if changed:
                require(ctx, Role.ADMIN)  # R12: remit-to/contact changes are admin-only
            saved = repo.save(vendor)
            if changed:  # the supplier is no longer the one that was checked
                self._reset_verification(ctx, saved, "domain_or_contact_changed")
            if changed:  # ... and quarantine the vendor's quotes until a callback is confirmed
                self._emit(ctx.tenant_id, None, ctx.actor, EVT_VENDOR_CONTACT_CHANGED, {
                    "vendor_id": saved.id, "old_domain": current.domain, "new_domain": saved.domain,
                    "pending_callback": True,
                    "_pii": {"old_contact": current.contact_email, "new_contact": saved.contact_email}})
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


def _is_production() -> bool:
    return os.environ.get("ENV", "").strip().lower() in {"production", "prod"}


def _secret_from_env(name: str) -> bytes:
    value = os.environ.get(name, "")
    if value:
        if len(value) < 16:
            raise ValueError(f"{name} must be at least 16 characters")
        return value.encode("utf-8")
    if _is_production():
        raise RuntimeError(f"{name} is required when ENV is production")
    return secrets.token_bytes(32)


def _audit_log(clock: Clock, audit_key: bytes | None) -> EventLog:
    """Audit chain and personal-data keys come from configuration, never random in production (M1)."""
    chain = audit_key if audit_key is not None else _secret_from_env(CHAIN_KEY_ENV)
    pii_env = os.environ.get(PII_KEY_ENV, "")
    pii = pii_env.encode("utf-8") if pii_env else hmac.new(chain, b"pii-key", hashlib.sha256).digest()
    return EventLog(clock, pii_key=pii, chain_key=chain)


def _required_identity_labels(cfg: Settings) -> tuple[str, ...]:
    """Labels the send-service must find on every message (checked again at send time). Derived from
    the settings AFTER the profile's policy was merged in, so they can only ever add to the profile."""
    if not cfg.identity_required:
        return ()
    return tuple(cfg.identity_label(name) for name in cfg.identity_fields)


def _caps_from_profile(prof: ResolvedProfile, clock: Clock, *, ledger: Any = None) -> CapPolicy:
    """Spend caps in the profile's base currency; unset profile caps keep the shipped defaults."""
    c = prof.profile.caps
    per_order = c.per_order_max or Decimal("5000")
    daily = c.daily_aggregate_max or max(Decimal("15000"), per_order)
    return CapPolicy(per_order, daily, clock, currency=prof.profile.money.base_currency, ledger=ledger)


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
    audit_key: bytes | None = None,
    profile: ResolvedProfile | None = None,
    suppliers: SupplierStore | None = None,
    shared: dict[str, Any] | None = None,
    price_history: PriceHistory | None = None,
) -> PurchasingService:
    """Fully wired service on in-memory stores. The transport is handed to the send-service ONLY.
    Defaults are dev-safe: a recording transport (nothing leaves the process), caps from the manifest
    defaults. Keys: the audit chain/PII key comes from ``audit_key`` or env ``AUDIT_CHAIN_KEY`` and the
    approval secret from ``approval_secret`` or env ``APPROVAL_SECRET``; when ENV=production a missing
    key RAISES (never a per-process random one, which would make the audit chain fail to verify
    across processes and restarts). Outside production a missing key falls back to an ephemeral one.
    ``shared`` (known-gaps H2) optionally swaps the process-local security state for shared stores, keys:
    ``cap_ledger``, ``token_store``, ``spent_approvals``, ``follow_up_plans``, ``kill_switch``,
    ``spend_book`` (see ``aidb.state.PgSharedState.as_kwargs``). Absent keys keep the in-memory default."""
    from datetime import UTC

    class _SystemClock:
        def now(self) -> datetime:
            return datetime.now(UTC)

    prof = profile or load_profile("us")  # "us" reproduces the pre-profile behaviour
    cfg = (settings.with_profile_defaults(prof) if settings is not None
           else Settings.from_profile(prof))
    clk: Clock = clock or _SystemClock()
    st = store or Store()
    log = ProfileStampedLog(event_log or _audit_log(clk, audit_key), cfg.profile_tag)
    secret = approval_secret or _secret_from_env("APPROVAL_SECRET")
    sh = dict(shared or {})
    policy = caps or _caps_from_profile(prof, clk, ledger=sh.get("cap_ledger"))
    approvals = ApprovalService(
        clk, secret, store=st, event_log=log, caps=policy,
        requester_threshold=cfg.approval_threshold, token_store=sh.get("token_store"))
    send = SendService.from_profile(
        prof, transport or RecordingTransport(), clk, st, log, caps=policy,
        max_recipients=cfg.max_vendors,
        required_identity_labels=_required_identity_labels(cfg),
        identity_provider=cfg.tenant_identities(), kill_switch=sh.get("kill_switch"),
        spent_approvals=sh.get("spent_approvals"), follow_up_plans=sh.get("follow_up_plans"))
    if extractor is None:
        extractor = (LLMQuoteExtractor(llm) if use_llm_extractor and llm is not None
                     else RegexQuoteExtractor())
    kwargs: dict[str, Any] = {} if token_gen is None else {"token_gen": token_gen}
    if use_llm_extractor and llm is not None:
        kwargs["shadow_extractor"] = RegexQuoteExtractor()  # the cheap second reader for the diff
    return PurchasingService(
        store=st, event_log=log, clock=clk, send_service=send, approval_service=approvals,
        extractor=extractor, settings=cfg, notifier=notifier, ids=ids, llm=llm,
        reply_token_key=hmac.new(secret, b"reply-token-key", hashlib.sha256).digest(),
        profile=prof, suppliers=suppliers, spend_book=sh.get("spend_book"),
        price_history=price_history, **kwargs)


def build_pg_service(
    profile: ResolvedProfile,
    engine: Any,
    shared_state: Any,
    event_store: EventLog,
    **kwargs: Any,
) -> PurchasingService:
    """The service over Postgres (known-gaps H2): its own stores (requests, vendors, RFQs, quotes,
    approvals, PO drafts, supplier profiles, assumptions) are ``PgServiceStore`` rows under RLS, and
    its security state is ``shared_state`` (``aidb.state.PgSharedState``), the audit log
    ``event_store`` (``aidb.repositories.PgEventStore``). ``engine`` must connect as ``app_user``.
    ``kwargs`` go to ``build_in_memory_service`` (keys, clock, transport, notifier, ...); ``store``,
    ``suppliers``, ``event_log`` and ``shared`` are fixed here and refused if passed. Still per
    process: the prepared-message cache, the approval notifier and in-process prepare locks."""
    clash = {"store", "suppliers", "event_log", "shared"} & kwargs.keys()
    if clash:
        raise TypeError(f"build_pg_service fixes {sorted(clash)}")
    from .pg_wiring import PgServiceStore

    pg = PgServiceStore(engine)
    return build_in_memory_service(
        profile=profile, store=pg, suppliers=pg,  # type: ignore[arg-type]
        event_log=event_store, shared=shared_state.as_kwargs(), **kwargs)
