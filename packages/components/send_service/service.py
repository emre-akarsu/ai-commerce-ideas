"""The send-service: the ONLY module that holds or calls the mail transport (R1, ADR-003).

``prepare`` builds the final bytes (buyer identity, Reply-To, non-removable R8 footer) and hashes
them. ``send`` accepts them only with an ``Approval`` that this process's approval service
registered for exactly those bytes. Every check below happens BEFORE ``transport.deliver`` and any
failure raises a specific ``SendRefused`` subclass without touching the transport. Refused sends
do not consume the approval; once the transport has been called, the approval is spent for good
(at-most-once: a failed delivery is ambiguous, so a human must approve again).

What is trusted: only the raw bytes and the registered Approval. The ``PreparedMessage`` metadata
(``to``, ``tenant_id``, ...) is never used for a decision; everything is re-derived from the bytes
the human approved, and the tenant comes from the Approval (never from the caller).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

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
    FooterMissing,
    HashMismatch,
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
    VendorOptedOut,
    WrongApprovalKind,
)
from .message import (
    FOOTER_TEMPLATE,
    NO_FOLLOW_UPS,
    REQUIRED_FOOTER_CLAUSES,
    FollowUpSchedule,
    MessagePurpose,
    ParsedMessage,
    PreparedMessage,
    build_message,
    has_footer,
    parse_message,
    sha256_hex,
)

__all__ = [
    "FOOTER_TEMPLATE",
    "NO_FOLLOW_UPS",
    "FollowUpSchedule",
    "KillSwitch",
    "MessagePurpose",
    "ParsedMessage",
    "PreparedMessage",
    "SendService",
]

DEFAULT_MAX_RECIPIENTS = 4  # spec 4a
DOWN_NOW_MAX_RECIPIENTS = 2
FOLLOW_UP_BODY = (
    "Following up on my earlier request below. Please send your quote or let us know if you "
    "cannot supply this item."
)


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
class _FollowUpPlan:
    tenant_id: str
    request_id: str
    rfq_id: str
    vendor_id: str
    approval_id: str
    schedule: FollowUpSchedule
    sent_at: datetime
    original: ParsedMessage
    done: int = 0
    active: bool = True

    def due_at(self) -> datetime:
        return self.sent_at + self.schedule.interval * (self.done + 1)


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
    ) -> None:
        if not isinstance(footer_text, str) or any(
            clause.lower() not in footer_text.lower() for clause in REQUIRED_FOOTER_CLAUSES
        ):
            raise ValueError("footer must keep the mandated R8 clauses naming the buyer")
        if max_recipients < 1:
            raise ValueError("max_recipients must be >= 1")
        self._transport = transport
        self._clock = clock
        self._store = store
        self._log = event_log
        self._kill = kill_switch or KillSwitch()
        self._caps = caps
        self._max_recipients = max_recipients
        self._footer = footer_text
        self._lock = threading.RLock()
        self._spent: set[str] = set()  # approval ids / nonces handed to the transport
        self._plans: list[_FollowUpPlan] = []

    @property
    def footer_template(self) -> str:
        """The R8 disclosure footer template in force (default constant, or the profile's)."""
        return self._footer

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
    ) -> PreparedMessage:
        """Build the final bytes the human will approve. Recipient is always the vendor's
        registered contact; it is never a caller-supplied address."""
        if vendor.tenant_id != rfq.tenant_id:
            raise TenantMismatch("vendor and RFQ belong to different tenants")
        ts = self._store.for_tenant(rfq.tenant_id)
        stored = ts.vendors.find(vendor.id)
        if rfq.vendor_id != vendor.id or stored is None or stored != vendor:
            raise RecipientNotVendor("recipient is not the RFQ's registered vendor")
        if ts.rfqs.find(rfq.id) is None:
            raise MalformedMessage("RFQ is not stored for this tenant")
        self._check_vendor(vendor, vendor.contact_email)
        if purpose is MessagePurpose.RFQ and amount is not None:
            raise MalformedMessage("an RFQ message carries no amount")
        if purpose is MessagePurpose.PO and follow_up.count:
            raise MalformedMessage("purchase orders have no follow-up schedule")
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
        if approval.id in self._spent or approval.nonce in self._spent:
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
        # Point of no return: the approval is spent whatever the transport does.
        self._spent.update({approval.id, approval.nonce})
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
            self._plans.append(_FollowUpPlan(
                tenant, ctx.request_id, ctx.rfq.id, ctx.vendor.id, approval.id,
                ctx.parsed.follow_up, self._clock.now(), ctx.parsed,
            ))
        return message_id

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
        self, tenant: str | None, approval: object, mime_hash: str, exc: SendRefused
    ) -> None:
        payload: dict[str, object] = {"reason": exc.code, "mime_hash": mime_hash}
        if isinstance(approval, Approval):
            payload["approval_id"] = approval.id
        self._log.append(tenant or UNATTRIBUTED_TENANT, None, "system", EVT_SEND_REFUSED, payload)

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
            for plan in self._plans:
                if plan.tenant_id != tenant_id:
                    continue
                if not plan.active or plan.done >= plan.schedule.count or now < plan.due_at():
                    continue
                if self._kill.is_engaged(plan.tenant_id):
                    continue  # paused, not lost
                message_id = self._send_follow_up(plan)
                if message_id:
                    sent.append(message_id)
        return sent

    def _send_follow_up(self, plan: _FollowUpPlan) -> str | None:
        try:
            ts = self._store.for_tenant(plan.tenant_id)
            vendor = ts.vendors.get(plan.vendor_id)
            self._check_vendor(vendor, plan.original.to)
            if vendor.contact_email.lower() != plan.original.to.lower():
                raise RecipientNotVendor("vendor contact changed")
        except (SendRefused, NotFoundError):
            plan.active = False  # opted out or identity changed: cancelled for good
            return None
        orig = plan.original
        seq = plan.done + 1
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
        )
        plan.done = seq  # at-most-once per slot
        if plan.done >= plan.schedule.count:
            plan.active = False
        base = {"mime_hash": sha256_hex(raw), "approval_id": plan.approval_id,
                "vendor_id": plan.vendor_id, "rfq_id": plan.rfq_id, "seq": seq}
        try:
            message_id = self._transport.deliver(to=orig.to, subject="Re: " + orig.subject,
                                                 raw_mime=raw)
            if not isinstance(message_id, str) or not message_id.strip():
                raise ValueError("no message id")
        except Exception as exc:  # noqa: BLE001 - any transport problem stops this plan
            plan.active = False
            self._log.append(plan.tenant_id, plan.request_id, "system", EVT_SEND_FAILED,
                             {**base, "reason": "follow_up_transport_error",
                              "error_type": type(exc).__name__})
            return None
        self._log.append(plan.tenant_id, plan.request_id, "system", EVT_SEND_FOLLOWUP,
                         {**base, "message_id": message_id, "_pii": {"to": orig.to}})
        return message_id

    def cancel_follow_ups(self, tenant_id: str, rfq_id: str) -> int:
        """Stop pending follow-ups (e.g. a reply arrived). Tenant-scoped; returns plans stopped."""
        with self._lock:
            count = 0
            for plan in self._plans:
                if plan.active and plan.tenant_id == tenant_id and plan.rfq_id == rfq_id:
                    plan.active = False
                    count += 1
            return count

