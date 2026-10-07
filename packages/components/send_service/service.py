"""The send-service: the ONLY module that holds or calls the mail transport (R1, ADR-003).

``prepare`` builds the final bytes (buyer identity, Reply-To, optional business-identity lines,
non-removable R8 footer) and hashes them. ``send`` accepts them only with an ``Approval`` that this
process's approval service registered for exactly those bytes. Every check below happens BEFORE
``transport.deliver`` and any failure raises a specific ``SendRefused`` subclass without touching
the transport. Refused sends do not consume the approval; once the transport has been called, the
approval is spent for good (at-most-once: a failed delivery is ambiguous, so a human must approve
again).

What is trusted: only the raw bytes and the registered Approval. The ``PreparedMessage`` metadata
(``to``, ``tenant_id``, ...) is never used for a decision; everything is re-derived from the bytes
the human approved, and the tenant comes from the Approval (never from the caller). That includes
the sanitiser's rules: ``prepare`` reads back what it built (a footer, a required identity line or
a text that would not survive a parse is refused), and ``send`` re-asserts the character rules on
the bytes it is given (``UnsafeText``), so bytes that did not come from ``prepare`` get the same
treatment.

Company particulars (business identity) belong to a tenant. A deployment hands the send-service an
``IdentityProvider`` (``TenantIdentities`` is the frozen, tenant-scoped implementation); ``prepare``
then derives the lines from the RFQ's own tenant and refuses any other pairs its caller passes.
Build the service with ``SendService.from_profile`` so the profile's footer and required labels
cannot be forgotten.
"""

from __future__ import annotations

import secrets
import threading
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

from components.core.domain import RFQ, Approval, ApprovalKind, Vendor
from components.core.ports import Clock, MailTransport
from components.core.store import (
    NotFoundError,
    Store,
    TenantIsolationError,
    TenantStore,
)
from components.evidence.log import (
    EVT_SEND_DELIVERED,
    EVT_SEND_FAILED,
    EVT_SEND_FOLLOWUP,
    EVT_SEND_REFUSED,
    UNATTRIBUTED_TENANT,
    EventLog,
)
from components.purchase_orders.approvals.service import CapError, CapPolicy

from .errors import (
    ApprovalExpired,
    CapRefused,
    DomainMismatch,
    DuplicateSend,
    FollowUpCancelled,
    FooterMissing,
    HashMismatch,
    IdentityMissing,
    KillSwitchEngaged,
    MalformedMessage,
    NonceReplayed,
    RecipientLimitExceeded,
    RecipientNotVendor,
    SendRefused,
    StandingRuleViolation,
    TenantMismatch,
    TransportFailure,
    UnknownApproval,
    UnsafeText,
    VendorMissing,
    VendorOptedOut,
    WrongApprovalKind,
)
from .message import (
    DEFAULT_IDENTITY_LABELS,
    FOOTER_TEMPLATE,
    NO_FOLLOW_UPS,
    REQUIRED_FOOTER_CLAUSES,
    FollowUpSchedule,
    MessagePurpose,
    ParsedMessage,
    PreparedMessage,
    ReadOnlyMap,
    as_identity_pairs,
    build_message,
    clean_identity_pairs,
    has_footer,
    identity_pairs,
    missing_identity_labels,
    parse_message,
    sha256_hex,
    unfilled_identity_labels,
    unsafe_text_fields,
    validate_identity_labels,
    validate_identity_pairs,
)
from .state import (
    FollowUpPlan,
    FollowUpPlans,
    InMemoryFollowUpPlans,
    InMemorySpentApprovals,
    SpentApprovals,
)

if TYPE_CHECKING:  # type-only: the send-service has no run-time dependency on the profile package
    from aiplat.profile import ResolvedProfile

__all__ = [
    "DEFAULT_IDENTITY_LABELS",
    "FOOTER_TEMPLATE",
    "NO_FOLLOW_UPS",
    "FollowUpSchedule",
    "IdentityProvider",
    "KillSwitch",
    "MessagePurpose",
    "ParsedMessage",
    "PreparedMessage",
    "SendService",
    "TenantIdentities",
]

DEFAULT_MAX_RECIPIENTS = 4  # spec 4a
DOWN_NOW_MAX_RECIPIENTS = 2
FOLLOW_UP_BODY = (
    "Following up on my earlier request below. Please send your quote or let us know if you "
    "cannot supply this item."
)


class IdentityProvider(Protocol):
    """Where the send-service reads a tenant's company particulars (an optional collaborator).

    ``identity_for(tenant_id)`` must return ONLY that tenant's ordered ``(label, value)`` lines, and
    nothing for a tenant it does not know. When configured, it is the only source of lines for
    ``prepare``."""

    def identity_for(self, tenant_id: str) -> Sequence[tuple[str, str]]: ...


class TenantIdentities:
    """A frozen, tenant-scoped set of company-particulars lines (an ``IdentityProvider``).

    Built once from ``tenant_id -> ordered (label, value) pairs``. Everything is copied into
    tuples and a read-only mapping (``ReadOnlyMap``) at construction, so changing what the
    caller passed in later (the outer mapping, an inner list, a list two tenants happened to
    share) changes nothing, and two tenants never share storage. Lookup is exact on
    ``tenant_id``. There is no way to list tenants or values through it, and its repr shows a
    count only. It can be pickled and copied (a deployment that starts workers by spawning needs
    that); the copy is rebuilt through the constructor. Values are not validated here:
    ``prepare`` validates what it renders and refuses a malformed line, naming the label, never
    the value."""

    __slots__ = ("_lines",)

    def __init__(self, lines: Mapping[str, Iterable[tuple[str, str]]]) -> None:
        frozen: dict[str, tuple[tuple[str, str], ...]] = {}
        for tenant_id, pairs in lines.items():
            if not isinstance(tenant_id, str) or not tenant_id.strip():
                raise ValueError("tenant ids must be non-empty text")
            if isinstance(pairs, (str, bytes, Mapping)) or not isinstance(pairs, Iterable):
                raise ValueError("a tenant's identity must be a sequence of (label, value) pairs")
            frozen[tenant_id] = tuple(self._pair(item) for item in pairs)
        self._lines: Mapping[str, tuple[tuple[str, str], ...]] = ReadOnlyMap(frozen)

    @staticmethod
    def _pair(item: object) -> tuple[str, str]:
        if (
            not isinstance(item, (list, tuple)) or len(item) != 2
            or not all(isinstance(part, str) for part in item)
        ):
            raise ValueError("identity lines must be (label, value) pairs of text")
        return (item[0], item[1])

    def identity_for(self, tenant_id: str) -> tuple[tuple[str, str], ...]:
        return self._lines.get(tenant_id, ()) if isinstance(tenant_id, str) else ()

    def __repr__(self) -> str:
        return f"TenantIdentities(tenants={len(self._lines)})"

    def __reduce__(self) -> tuple[Any, ...]:
        return (TenantIdentities, (dict(self._lines),))  # rebuilt, and so re-validated, when loaded


class KillSwitch:
    """Global and per-tenant stop for all outbound mail (spec section 7)."""

    def __init__(self) -> None:
        self._global = False
        self._tenants: set[str] = set()
        self._lock = threading.Lock()

    def engage(self, tenant_id: str | None = None) -> None:
        with self._lock:
            if tenant_id is None:
                self._global = True
            else:
                self._tenants.add(tenant_id)

    def release(self, tenant_id: str | None = None) -> None:
        with self._lock:
            if tenant_id is None:
                self._global = False
            else:
                self._tenants.discard(tenant_id)

    def is_engaged(self, tenant_id: str | None = None) -> bool:
        with self._lock:
            return self._global or (tenant_id is not None and tenant_id in self._tenants)


@dataclass
class _Context:
    """Facts re-derived from the bytes and the tenant's own records during ``send``."""

    parsed: ParsedMessage
    ts: TenantStore
    rfq: RFQ
    vendor: Vendor
    family: str | None
    request_id: str
    amount: Decimal | None = None
    extra: dict[str, object] = field(default_factory=dict)


class SendService:
    def __init__(
        self,
        transport: MailTransport,
        clock: Clock,
        store: Store,
        event_log: EventLog,
        *,
        kill_switch: KillSwitch | None = None,
        caps: CapPolicy | None = None,
        max_recipients: int = DEFAULT_MAX_RECIPIENTS,
        footer_text: str = FOOTER_TEMPLATE,
        required_identity_labels: tuple[str, ...] = (),
        identity_provider: IdentityProvider | None = None,
        spent_approvals: SpentApprovals | None = None,
        follow_up_plans: FollowUpPlans | None = None,
    ) -> None:
        if not isinstance(footer_text, str) or any(
            clause.lower() not in footer_text.lower() for clause in REQUIRED_FOOTER_CLAUSES
        ):
            raise ValueError("footer must keep the mandated R8 clauses naming the buyer")
        if max_recipients < 1:
            raise ValueError("max_recipients must be >= 1")
        if identity_provider is not None and not callable(
            getattr(identity_provider, "identity_for", None)
        ):
            raise ValueError("identity_provider must offer identity_for(tenant_id)")
        self._transport = transport
        self._clock = clock
        self._store = store
        self._log = event_log
        self._kill = kill_switch or KillSwitch()
        self._caps = caps
        self._max_recipients = max_recipients
        self._footer = footer_text
        # Labels of the business-identity lines every message must carry (empty = none required).
        # This is an extra requirement: it never replaces or relaxes the R8 footer check.
        self._identity_labels = validate_identity_labels(required_identity_labels)
        self._identity_provider = identity_provider
        self._lock = threading.RLock()
        # Approval ids / nonces handed to the transport, and follow-up plans. In memory by default;
        # a multi-process deployment injects the shared (Postgres) ones (known-gaps H2).
        self._spent: SpentApprovals = spent_approvals or InMemorySpentApprovals()
        self._plans: FollowUpPlans = follow_up_plans or InMemoryFollowUpPlans()

    @classmethod
    def from_profile(
        cls,
        profile: ResolvedProfile,
        transport: MailTransport,
        clock: Clock,
        store: Store,
        event_log: EventLog,
        *,
        kill_switch: KillSwitch | None = None,
        caps: CapPolicy | None = None,
        max_recipients: int | None = None,
        required_identity_labels: Sequence[str] = (),
        identity_provider: IdentityProvider | None = None,
        spent_approvals: SpentApprovals | None = None,
        follow_up_plans: FollowUpPlans | None = None,
    ) -> SendService:
        """The send-service a deployment profile calls for: its R8 footer wording, its recipient
        limit (``comms.max_vendors`` unless ``max_recipients`` is given) and, when the profile
        requires the business-identity block, the effective label of every listed field.

        ``required_identity_labels`` can only ADD to the profile's labels, never replace or drop
        them. Every deployment that builds its own send-service (for example the worker's
        ``send_service_factory``) should use this instead of the constructor, so the send-time
        backstop cannot be lost by forgetting a keyword."""
        legal = profile.profile.legal
        identity = legal.business_identity
        profile_labels = tuple(identity.effective_labels().values()) if identity.required else ()
        extra = validate_identity_labels(required_identity_labels)  # a list/tuple of valid labels
        labels = tuple(dict.fromkeys([*profile_labels, *extra]))
        return cls(
            transport, clock, store, event_log, kill_switch=kill_switch, caps=caps,
            max_recipients=(
                profile.profile.comms.max_vendors if max_recipients is None else max_recipients
            ),
            footer_text=legal.disclosure_footer, required_identity_labels=labels,
            identity_provider=identity_provider, spent_approvals=spent_approvals,
            follow_up_plans=follow_up_plans,
        )

    @property
    def footer_template(self) -> str:
        """The R8 disclosure footer template in force (default constant, or the profile's)."""
        return self._footer

    @property
    def required_identity_labels(self) -> tuple[str, ...]:
        """Labels of the business-identity lines every message must carry (may be empty)."""
        return self._identity_labels

    @property
    def max_recipients(self) -> int:
        """How many distinct vendors one request may be sent to (before the down-now limit)."""
        return self._max_recipients

    @property
    def identity_provider(self) -> IdentityProvider | None:
        """The tenant-scoped source of company particulars, if one is configured."""
        return self._identity_provider

    # ------------------------------------------------------------------ prepare

    def prepare(
        self,
        rfq: RFQ,
        vendor: Vendor,
        buyer_name: str,
        buyer_phone: str,
        alias_address: str,
        reply_to: str,
        *,
        purpose: MessagePurpose = MessagePurpose.RFQ,
        amount: Decimal | None = None,
        currency: str | None = None,
        follow_up: FollowUpSchedule = NO_FOLLOW_UPS,
        identity: Sequence[tuple[str, str]] = (),
    ) -> PreparedMessage:
        """Build the final bytes the human will approve. Recipient is always the vendor's
        registered contact; it is never a caller-supplied address. ``identity`` holds the
        ``(label, value)`` business-identity lines; a required label that is absent or shows no
        letter or digit is refused with ``IdentityMissing`` (which names labels, never values).

        With an ``identity_provider`` the lines are the RFQ's own tenant's, whatever the caller
        passes: pairs that are not exactly those lines are refused with ``TenantMismatch``.

        The last step reads the bytes back: they are parsed as the approver and the send-time
        gate will parse them, and a footer, a required identity line or a text that would not
        survive that is refused with a ``MalformedMessage`` (naming the kind of field, never a
        value). So bytes ``prepare`` returns can pass the send-time content checks."""
        ts = self._known_parties(rfq, vendor)
        if ts.rfqs.find(rfq.id) is None:
            raise MalformedMessage("RFQ is not stored for this tenant")
        raw = self._build_checked(
            rfq, vendor, buyer_name, buyer_phone, alias_address, reply_to, purpose=purpose,
            amount=amount, currency=currency, follow_up=follow_up, identity=identity,
        )
        return PreparedMessage(
            mime_bytes=raw,
            mime_hash=sha256_hex(raw),
            to=vendor.contact_email,
            tenant_id=rfq.tenant_id,
            rfq_id=rfq.id,
            vendor_id=vendor.id,
            subject=rfq.subject,
            purpose=purpose,
        )

    def check_prepare(
        self,
        rfq: RFQ,
        vendor: Vendor,
        buyer_name: str,
        buyer_phone: str,
        alias_address: str,
        reply_to: str,
        *,
        identity: Sequence[tuple[str, str]] = (),
    ) -> None:
        """Dry run of ``prepare`` for an RFQ that is NOT stored yet: the same checks, the same
        build and the same read-back, and the same refusals, for the plain RFQ (no amount, no
        follow-up). It stores, audits and sends nothing, keeps nothing and returns nothing, so
        no caller can get bytes from it.

        A caller that is about to store an RFQ runs this first, so a message that cannot be
        built leaves no RFQ row behind. ``prepare`` itself still requires the RFQ to be stored."""
        self._known_parties(rfq, vendor)
        self._build_checked(
            rfq, vendor, buyer_name, buyer_phone, alias_address, reply_to,
            purpose=MessagePurpose.RFQ, amount=None, currency=None, follow_up=NO_FOLLOW_UPS,
            identity=identity,
        )

    def _known_parties(self, rfq: RFQ, vendor: Vendor) -> TenantStore:
        """Both belong to one tenant, and the vendor is the RFQ's registered vendor."""
        if vendor.tenant_id != rfq.tenant_id:
            raise TenantMismatch("vendor and RFQ belong to different tenants")
        ts = self._store.for_tenant(rfq.tenant_id)
        stored = ts.vendors.find(vendor.id)
        if rfq.vendor_id != vendor.id or stored is None or stored != vendor:
            raise RecipientNotVendor("recipient is not the RFQ's registered vendor")
        return ts

    def _build_checked(
        self,
        rfq: RFQ,
        vendor: Vendor,
        buyer_name: str,
        buyer_phone: str,
        alias_address: str,
        reply_to: str,
        *,
        purpose: MessagePurpose,
        amount: Decimal | None,
        currency: str | None,
        follow_up: FollowUpSchedule,
        identity: Sequence[tuple[str, str]],
    ) -> bytes:
        self._check_vendor(vendor, vendor.contact_email)
        if purpose is MessagePurpose.RFQ and amount is not None:
            raise MalformedMessage("an RFQ message carries no amount")
        if purpose is MessagePurpose.PO and follow_up.count:
            raise MalformedMessage("purchase orders have no follow-up schedule")
        pairs = self._tenant_identity(rfq.tenant_id, identity)  # read once; the checks below use it
        self._require_identity(unfilled_identity_labels(pairs, self._identity_labels))
        raw = build_message(
            subject=rfq.subject,
            body=rfq.body,
            to=vendor.contact_email,
            buyer_name=buyer_name,
            buyer_phone=buyer_phone,
            alias_address=alias_address,
            reply_to=reply_to,
            rfq_id=rfq.id,
            purpose=purpose,
            sent_at=self._clock.now(),
            footer_template=self._footer,
            reply_token=rfq.reply_token,
            amount=amount,
            currency=currency,
            follow_up=follow_up,
            identity=pairs,
        )
        self._read_back(raw)
        return raw

    def _read_back(self, raw: bytes) -> None:
        """Parse the bytes just built, as the approver (``preview``) and the send-time gate will,
        and refuse what would not come back. Names kinds of field only, never a value."""
        try:
            parsed = parse_message(raw)
        except MalformedMessage as exc:
            raise MalformedMessage(f"the message built here cannot be read back: {exc}") from exc
        if not has_footer(parsed, self._footer):
            raise MalformedMessage(
                "the footer would not survive being read back from the message "
                "(check the sender name and the footer wording)"
            )
        missing = missing_identity_labels(parsed, self._identity_labels)
        if missing:
            raise MalformedMessage(
                "business identity lines would not survive being read back: " + ", ".join(missing)
            )
        kinds = unsafe_text_fields(parsed, self._footer)
        if kinds:
            raise MalformedMessage(
                "the text would not pass the send-time text check, kinds: " + ", ".join(kinds)
            )

    def _tenant_identity(self, tenant_id: str, supplied: object) -> list[Any]:
        """The identity lines for ONE tenant. Without a provider these are the caller's pairs (the
        direct-caller and test path). With one they are the provider's lines for ``tenant_id``, and
        caller-supplied pairs are accepted only if, once cleaned, they are exactly those lines."""
        given = as_identity_pairs(supplied)
        if self._identity_provider is None:
            return given
        own = as_identity_pairs(self._identity_provider.identity_for(tenant_id))
        if given and clean_identity_pairs(given) != clean_identity_pairs(own):
            raise TenantMismatch("identity differs from the one configured for the RFQ's tenant")
        return own

    def preview(self, prepared: PreparedMessage) -> ParsedMessage:
        """What the approver sees: re-parsed from the exact bytes that will be hashed and sent."""
        return parse_message(prepared.mime_bytes)

    # ------------------------------------------------------------------ send

    def send(self, prepared: PreparedMessage, approval: Approval) -> str:
        """Deliver exactly the approved bytes once. Returns the transport's message id."""
        raw = prepared.mime_bytes if isinstance(prepared, PreparedMessage) else b""
        mime_hash = sha256_hex(raw) if isinstance(raw, bytes) else ""
        tenant: str | None = None
        try:
            with self._lock:
                tenant = self._authenticate(approval)
                ctx = self._verify(prepared, raw, mime_hash, approval, tenant)
                return self._deliver(ctx, prepared, raw, mime_hash, approval)
        except SendRefused as exc:
            self._audit_refusal(tenant, approval, mime_hash, exc)
            raise

    def _authenticate(self, approval: Approval) -> str:
        """Approval must be exactly the record the approval service registered (R1)."""
        if not isinstance(approval, Approval) or not approval.tenant_id:
            raise UnknownApproval("not an approval")
        try:
            registered = self._store.for_tenant(approval.tenant_id).approvals.find(approval.id)
        except TenantIsolationError as exc:
            raise TenantMismatch("approval id belongs to another tenant") from exc
        if registered is None or registered != approval:
            raise UnknownApproval("approval was not issued by the approval service")
        return approval.tenant_id

    def _verify(
        self, prepared: PreparedMessage, raw: bytes, mime_hash: str, approval: Approval, tenant: str
    ) -> _Context:
        if self._kill.is_engaged(tenant):
            raise KillSwitchEngaged("outbound mail is stopped")
        if not raw or prepared.mime_hash != mime_hash:
            raise HashMismatch("prepared message was altered after hashing")
        if approval.mime_hash != mime_hash:
            raise HashMismatch("approval does not cover these exact bytes")
        if self._clock.now() >= approval.expires_at:
            raise ApprovalExpired("approval has expired")
        if prepared.tenant_id and prepared.tenant_id != tenant:
            raise TenantMismatch("message was prepared for another tenant")
        parsed = parse_message(raw)
        if not has_footer(parsed, self._footer):
            raise FooterMissing("mandatory AI-disclosure footer is missing")
        self._require_identity(missing_identity_labels(parsed, self._identity_labels))
        self._require_plain_text(unsafe_text_fields(parsed, self._footer))
        if parsed.followup_seq is not None or parsed.in_reply_to is not None:
            raise MalformedMessage("follow-ups are sent by the schedule, not by approval")
        self._check_kind(approval, parsed)
        if self._already_used(tenant, approval):
            raise NonceReplayed("approval was already used")
        ctx = self._resolve(parsed, tenant)
        self._check_vendor(ctx.vendor, parsed.to)
        if approval.kind is ApprovalKind.STANDING:
            self._check_standing(ctx, approval)
        return ctx

    @staticmethod
    def _identity_refusal(missing: list[str]) -> IdentityMissing:
        """Names the missing labels only; never a value."""
        return IdentityMissing("business identity missing: " + ", ".join(missing))

    def _require_identity(self, missing: list[str]) -> None:
        if missing:
            raise self._identity_refusal(missing)

    @staticmethod
    def _require_plain_text(kinds: list[str]) -> None:
        """Bytes that did not come from ``prepare`` get the sanitiser's rules re-asserted here.
        Names the kinds of field only; never their text."""
        if kinds:
            raise UnsafeText(
                "text holds control, line-break or hidden characters in: " + ", ".join(kinds)
            )

    @staticmethod
    def _check_kind(approval: Approval, parsed: ParsedMessage) -> None:
        allowed = (
            {ApprovalKind.PO}
            if parsed.purpose is MessagePurpose.PO
            else {ApprovalKind.PER_MESSAGE, ApprovalKind.STANDING}
        )
        if approval.kind not in allowed:
            raise WrongApprovalKind(
                f"{approval.kind.value} approval cannot send a {parsed.purpose.value}"
            )

    def _resolve(self, parsed: ParsedMessage, tenant: str) -> _Context:
        ts = self._store.for_tenant(tenant)
        try:
            rfq = ts.rfqs.find(parsed.rfq_id)
            vendor = next(
                (v for v in ts.vendors.list() if v.contact_email.lower() == parsed.to.lower()),
                None,
            )
        except TenantIsolationError as exc:
            raise TenantMismatch("RFQ belongs to another tenant") from exc
        if rfq is None:
            raise MalformedMessage("message references an unknown RFQ")
        if vendor is None or vendor.id != rfq.vendor_id:
            raise RecipientNotVendor("recipient is not the registered vendor of this RFQ")
        try:
            request = ts.requests.get(rfq.request_id)
        except NotFoundError as exc:
            raise MalformedMessage("RFQ has no request") from exc
        return _Context(parsed, ts, rfq, vendor, request.family, rfq.request_id,
                        amount=parsed.amount)

    @staticmethod
    def _check_vendor(vendor: Vendor, to: str) -> None:
        if vendor.opted_out:
            raise VendorOptedOut("vendor has opted out of messages")
        if "@" not in to or to.rsplit("@", 1)[1].lower() != vendor.domain.lower():
            raise DomainMismatch("recipient domain differs from the vendor's registered domain")

    def _check_standing(self, ctx: _Context, approval: Approval) -> None:
        rule = ctx.ts.standing_rules.find(approval.rule_id) if approval.rule_id else None
        if rule is None:
            raise StandingRuleViolation("standing rule does not exist or was revoked")
        if self._clock.now() >= rule.expires_at:
            raise StandingRuleViolation("standing rule has expired")
        if rule.vendor_id != ctx.vendor.id:
            raise StandingRuleViolation("vendor is outside the standing rule")
        if (ctx.family or "").strip().lower() != rule.family.strip().lower():
            raise StandingRuleViolation("part family is outside the standing rule")
        if (ctx.amount or Decimal(0)) > rule.max_amount:
            raise StandingRuleViolation("amount exceeds the standing rule")
        if ctx.ts.rule_uses(rule.id) > rule.max_count:
            raise StandingRuleViolation("standing rule use count exceeded")

    def _already_used(self, tenant: str, approval: Approval) -> bool:
        if self._spent.is_spent(tenant, (approval.id, approval.nonce)):
            return True
        for event in self._log.events(tenant):
            if event.type in (EVT_SEND_DELIVERED, EVT_SEND_FAILED) and (
                event.payload.get("approval_id") == approval.id
            ):
                return True
        return False

    def _delivered(self, tenant: str, request_id: str) -> list[dict[str, object]]:
        return [
            dict(e.payload)
            for e in self._log.events(tenant, request_id)
            if e.type == EVT_SEND_DELIVERED
        ]

    def _check_limits(self, ctx: _Context, tenant: str, mime_hash: str) -> None:
        delivered = self._delivered(tenant, ctx.request_id)
        if any(p.get("mime_hash") == mime_hash for p in delivered):
            raise DuplicateSend("this exact message was already sent")
        if ctx.parsed.purpose is not MessagePurpose.RFQ:
            return
        vendors = {p.get("vendor_id") for p in delivered if p.get("purpose") == "rfq"}
        request = ctx.ts.requests.get(ctx.request_id)
        limit = self._max_recipients
        if request.down_now:
            limit = min(limit, DOWN_NOW_MAX_RECIPIENTS)
        if ctx.vendor.id not in vendors and len(vendors) >= limit:
            raise RecipientLimitExceeded(f"at most {limit} vendors per request")

    def _deliver(
        self, ctx: _Context, prepared: PreparedMessage, raw: bytes, mime_hash: str,
        approval: Approval,
    ) -> str:
        tenant = approval.tenant_id
        self._check_limits(ctx, tenant, mime_hash)
        if ctx.parsed.purpose is MessagePurpose.PO:
            if self._caps is None or ctx.parsed.amount is None or ctx.parsed.currency is None:
                raise CapRefused("purchase orders are only sent under configured spend caps")
            try:
                self._caps.reserve(tenant, ctx.parsed.amount, currency=ctx.parsed.currency)
            except CapError as exc:
                raise CapRefused(str(exc)) from exc
        self._spend(tenant, approval, ctx)
        base = self._base_payload(ctx, mime_hash, approval)
        try:
            message_id = self._transport.deliver(
                to=ctx.parsed.to, subject=ctx.parsed.subject, raw_mime=raw
            )
        except Exception as exc:
            self._log.append(tenant, ctx.request_id, "system", EVT_SEND_FAILED,
                             {**base, "reason": "transport_error",
                              "error_type": type(exc).__name__})
            raise TransportFailure("transport failed; delivery state unknown") from exc
        if not isinstance(message_id, str) or not message_id.strip():
            self._log.append(tenant, ctx.request_id, "system", EVT_SEND_FAILED,
                             {**base, "reason": "no_message_id"})
            raise TransportFailure("transport returned no message id")
        payload: dict[str, object] = {**base, "message_id": message_id,
                                      "_pii": {"to": ctx.parsed.to}}
        self._log.append(tenant, ctx.request_id, "system", EVT_SEND_DELIVERED, payload)
        if ctx.parsed.purpose is MessagePurpose.RFQ and ctx.parsed.follow_up.count:
            self._plans.add(FollowUpPlan(
                secrets.token_hex(8), tenant, ctx.request_id, ctx.rfq.id, ctx.vendor.id,
                approval.id, ctx.parsed.follow_up, self._clock.now(), ctx.parsed, raw=raw,
            ))
        return message_id

    def _spend(self, tenant: str, approval: Approval, ctx: _Context) -> None:
        """Point of no return: the approval is spent whatever the transport does. The claim is one
        atomic call on the (possibly shared) store, so of two processes holding the same approval
        exactly one gets here. The loser gives back any cap it reserved and sends nothing. If the
        store cannot answer, nothing is sent (the error propagates before the transport call)."""
        try:
            won = self._spent.claim(tenant, approval.id, (approval.id, approval.nonce))
        except BaseException:
            self._give_back_cap(tenant, ctx)
            raise
        if not won:
            self._give_back_cap(tenant, ctx)
            raise NonceReplayed("approval was already used")

    def _give_back_cap(self, tenant: str, ctx: _Context) -> None:
        if ctx.parsed.purpose is MessagePurpose.PO and self._caps is not None:
            if ctx.parsed.amount is not None and ctx.parsed.currency is not None:
                self._caps.release(tenant, ctx.parsed.amount, currency=ctx.parsed.currency)

    @staticmethod
    def _base_payload(ctx: _Context, mime_hash: str, approval: Approval) -> dict[str, object]:
        """Ids and hashes only: never the body, buyer contact details or the footer."""
        payload: dict[str, object] = {
            "mime_hash": mime_hash,
            "approval_id": approval.id,
            "approval_kind": approval.kind.value,
            "approver": approval.approver,
            "vendor_id": ctx.vendor.id,
            "rfq_id": ctx.rfq.id,
            "purpose": ctx.parsed.purpose.value,
        }
        if approval.rule_id:
            payload["rule_id"] = approval.rule_id
        if ctx.parsed.amount is not None:
            payload["amount"] = ctx.parsed.amount
            payload["currency"] = ctx.parsed.currency
        return payload

    def _audit_refusal(
        self, tenant: str | None, approval: object, mime_hash: str, exc: SendRefused,
        *, request_id: str | None = None, extra: Mapping[str, object] | None = None,
    ) -> None:
        payload: dict[str, object] = {"reason": exc.code, "mime_hash": mime_hash}
        if isinstance(approval, Approval):
            payload["approval_id"] = approval.id
        payload.update(extra or {})
        self._log.append(
            tenant or UNATTRIBUTED_TENANT, request_id, "system", EVT_SEND_REFUSED, payload
        )

    def _cancel_plan(
        self, plan: FollowUpPlan, seq: int, exc: SendRefused, mime_hash: str = ""
    ) -> None:
        """End a follow-up plan for good and say so in the audit trail. Every way a plan can end
        goes through here (opt-out, contact change, missing vendor, a follow-up that cannot be
        built or lost its identity block, a stop on request), so none is silent. It can only
        reduce sending: the plan is switched off before anything else, and nothing here calls
        the transport. ``seq`` is the slot that will not be sent; ``mime_hash`` is the follow-up
        that was built and not sent, if any."""
        if self._plans.deactivate(plan):  # only the caller that ended it audits it
            self._audit_plan_cancelled(plan, seq, mime_hash, exc)

    def _audit_plan_cancelled(
        self, plan: FollowUpPlan, seq: int, mime_hash: str, exc: SendRefused
    ) -> None:
        """A follow-up plan was cancelled for good. Ids and codes only (never content), enough
        for an auditor to tell WHICH plan and slot: request, RFQ, vendor, approval, sequence."""
        ids: dict[str, object] = {
            "request_id": plan.request_id, "rfq_id": plan.rfq_id,
            "vendor_id": plan.vendor_id, "approval_id": plan.approval_id, "seq": seq,
        }
        self._audit_refusal(
            plan.tenant_id, None, mime_hash, exc, request_id=plan.request_id, extra=ids
        )

    # ------------------------------------------------------------------ follow-ups (F4)

    def set_kill_switch(self, tenant_id: str, *, engaged: bool) -> None:
        """Engage or release the per-tenant stop (the caller audits and authorises it)."""
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id is required")
        (self._kill.engage if engaged else self._kill.release)(tenant_id)

    def run_due_follow_ups(self, tenant_id: str) -> list[str]:
        """Send pre-approved follow-ups that are due for ONE tenant. At most one per plan per call.

        The tenant is mandatory: a worker task for tenant A must never send tenant B's mail."""
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id is required to run follow-ups")
        sent: list[str] = []
        with self._lock:
            now = self._clock.now()
            for plan in self._plans.active_for_tenant(tenant_id):
                if plan.done >= plan.schedule.count or now < plan.due_at():
                    continue
                if self._kill.is_engaged(plan.tenant_id):
                    continue  # paused, not lost
                message_id = self._send_follow_up(plan)
                if message_id:
                    sent.append(message_id)
        return sent

    def _send_follow_up(self, plan: FollowUpPlan) -> str | None:
        seq = plan.done + 1
        try:
            vendor = self._store.for_tenant(plan.tenant_id).vendors.get(plan.vendor_id)
        except (NotFoundError, TenantIsolationError):
            # deleted, or the id now belongs to another tenant: this tenant has no such vendor
            self._cancel_plan(plan, seq, VendorMissing("the plan's vendor no longer exists"))
            return None
        try:
            self._check_vendor(vendor, plan.original.to)
            if vendor.contact_email.lower() != plan.original.to.lower():
                raise RecipientNotVendor("vendor contact changed")
        except SendRefused as exc:  # opted out, or the contact moved: cancelled for good
            self._cancel_plan(plan, seq, exc)
            return None
        orig = plan.original
        identity = identity_pairs(orig)  # carried over, so a follow-up never loses the block
        try:
            validate_identity_pairs(identity)
            raw = build_message(
                subject="Re: " + orig.subject,
                body=FOLLOW_UP_BODY,
                to=orig.to,
                buyer_name=orig.from_name,
                buyer_phone=orig.buyer_phone or "",
                alias_address=orig.from_addr,
                reply_to=orig.reply_to,
                rfq_id=orig.rfq_id,
                purpose=MessagePurpose.RFQ,
                sent_at=self._clock.now(),
                footer_template=self._footer,
                in_reply_to=orig.message_id,
                followup_seq=seq,
                identity=identity,
            )
        except MalformedMessage as exc:
            # Lines the sanitiser would never have produced, or a signature without a phone (only
            # possible for bytes built outside ``prepare``): cancel for good rather than raising on
            # every run and stalling the loop.
            self._cancel_plan(plan, seq, exc)
            return None
        missing = missing_identity_labels(parse_message(raw), self._identity_labels)
        if missing:  # fail closed: never send a follow-up lacking the block that is required
            self._cancel_plan(plan, seq, self._identity_refusal(missing), sha256_hex(raw))
            return None
        if not self._plans.claim_slot(plan, seq):  # at-most-once per slot, across processes
            return None
        base = {"mime_hash": sha256_hex(raw), "approval_id": plan.approval_id,
                "vendor_id": plan.vendor_id, "rfq_id": plan.rfq_id, "seq": seq}
        try:
            message_id = self._transport.deliver(to=orig.to, subject="Re: " + orig.subject,
                                                 raw_mime=raw)
            if not isinstance(message_id, str) or not message_id.strip():
                raise ValueError("no message id")
        except Exception as exc:  # noqa: BLE001 - any transport problem stops this plan
            self._plans.deactivate(plan)
            self._log.append(plan.tenant_id, plan.request_id, "system", EVT_SEND_FAILED,
                             {**base, "reason": "follow_up_transport_error",
                              "error_type": type(exc).__name__})
            return None
        self._log.append(plan.tenant_id, plan.request_id, "system", EVT_SEND_FOLLOWUP,
                         {**base, "message_id": message_id, "_pii": {"to": orig.to}})
        return message_id

    def cancel_follow_ups(self, tenant_id: str, rfq_id: str) -> int:
        """Stop pending follow-ups (e.g. a reply arrived). Tenant-scoped; returns plans stopped.
        Each plan stopped is audited (``follow_up_cancelled``); asking again stops, and audits,
        nothing."""
        with self._lock:
            count = 0
            for plan in self._plans.active_for_tenant(tenant_id):
                if plan.rfq_id == rfq_id and self._plans.deactivate(plan):
                    self._audit_plan_cancelled(
                        plan, plan.done + 1, "", FollowUpCancelled("stopped on request")
                    )
                    count += 1
            return count

