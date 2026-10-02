"""Approvals: per-message approvals, standing pre-authorisations, signed approval links, caps.

Hard rules served here: R1 (human authorisation is the only way to obtain an ``Approval``),
R9 (Decimal caps: per order and daily aggregate), R11 (approval links bound to approver + quote
version/hash + action, single-use, short-lived; viewing a link never consumes it).

Trust model
- Every ``Approval`` this service mints is registered in the tenant-scoped store. The send-service
  accepts an Approval only if it is byte-for-byte identical to the registered one, so an Approval
  object forged elsewhere in the code base is worthless.
- Approvals are only ever issued for a *human* approver (never ``agent``, ``system`` or
  ``operator:*``; R10: operators cannot approve).
- Standing-rule use counts are consumed when the authorisation is minted, so minting many
  approvals up front cannot exceed ``max_count``.
"""

from __future__ import annotations

import hashlib
import hmac
import math
import re
import secrets
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any

from itsdangerous import BadData, URLSafeSerializer

from components.core.domain import Approval, ApprovalKind, Quote, StandingRule
from components.core.ports import Clock
from components.core.store import NotFoundError, Store
from components.evidence.log import (
    EVT_APPROVAL_ISSUED,
    EVT_APPROVAL_TOKEN_CONSUMED,
    EVT_APPROVAL_TOKEN_ISSUED,
    EVT_RULE_CREATED,
    EVT_RULE_REVOKED,
    EventLog,
    canonical_json,
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_NON_HUMAN = frozenset({"agent", "system", "operator", "planner", "bot", "service"})
MAX_RULE_COUNT = 10_000


# ---------------------------------------------------------------- errors


class ApprovalError(Exception):
    """Base class for approval-domain refusals."""


class NotHumanApprover(ApprovalError):  # noqa: N818 - reads as a refusal reason
    pass


class SeparationOfDuties(ApprovalError):  # noqa: N818
    """Approver equals requester above the approval threshold (R11)."""


class RuleError(ApprovalError):
    pass


class RuleNotUsable(RuleError):  # noqa: N818 - rule missing or revoked
    pass


class RuleExpired(RuleError):  # noqa: N818
    pass


class RuleLimitReached(RuleError):  # noqa: N818
    pass


class RuleScopeMismatch(RuleError):  # noqa: N818
    pass


class AmountOverRule(RuleError):  # noqa: N818
    pass


class TokenError(ApprovalError):
    pass


class TokenInvalid(TokenError):  # noqa: N818 - bad signature, malformed or never issued
    pass


class TokenExpired(TokenError):  # noqa: N818
    pass


class TokenReplayed(TokenError):  # noqa: N818
    pass


class TokenWrongAction(TokenError):  # noqa: N818
    pass


class TokenQuoteMismatch(TokenError):  # noqa: N818 - quote version or hash differs from the link
    pass


class TokenApproverMismatch(TokenError):  # noqa: N818
    pass


class TokenTenantMismatch(TokenError):  # noqa: N818
    pass


class CapError(ApprovalError):
    pass


class InvalidAmount(CapError, ValueError):  # noqa: N818
    pass


class PerOrderCapExceeded(CapError):  # noqa: N818
    pass


class DailyCapExceeded(CapError):  # noqa: N818
    pass


class CapCurrencyMismatch(CapError):  # noqa: N818
    pass


# ---------------------------------------------------------------- helpers


def is_human_actor(actor: object) -> bool:
    """True for identities that may authorise things. Agents, the system and operators may not."""
    if not isinstance(actor, str):
        return False
    normalised = actor.strip().lower()
    if not normalised:
        return False
    return re.split(r"[:@/\s-]", normalised, maxsplit=1)[0] not in _NON_HUMAN


def _require_human(actor: object, what: str) -> str:
    if not is_human_actor(actor):
        raise NotHumanApprover(f"{what} must be a human user, not an agent, system or operator")
    return str(actor)


def _norm_actor(actor: str) -> str:
    return actor.strip().lower()


def _money(value: object, name: str) -> Decimal:
    """Decimal only (R9): floats, ints and strings are refused; must be finite and >= 0."""
    if not isinstance(value, Decimal):
        raise InvalidAmount(f"{name} must be a Decimal, got {type(value).__name__}")
    if not value.is_finite():
        raise InvalidAmount(f"{name} must be finite")
    if value < 0:
        raise InvalidAmount(f"{name} must not be negative")
    return value


def _check_hash(value: object, name: str = "mime_hash") -> str:
    if not isinstance(value, str) or not _HEX64.match(value):
        raise ValueError(f"{name} must be a lowercase sha256 hex digest")
    return value


def _check_ttl(ttl: object, maximum: timedelta) -> timedelta:
    if not isinstance(ttl, timedelta) or ttl <= timedelta(0) or ttl > maximum:
        raise ValueError(f"ttl must be positive and at most {maximum}")
    return ttl


def _utc(now: datetime) -> datetime:
    if now.tzinfo is None:
        raise ValueError("clock must return timezone-aware datetimes")
    return now.astimezone(UTC)


def quote_fingerprint(quote: Quote) -> str:
    """sha256 over the full canonical content of an immutable quote version (binds links to it)."""
    return hashlib.sha256(canonical_json(quote.model_dump(mode="json")).encode("ascii")).hexdigest()


# ---------------------------------------------------------------- caps (R9)


class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class CapPolicy:
    """Per-order and daily-aggregate spend caps, per tenant, in one currency, in Decimal.

    The daily aggregate spans *all* orders of the tenant in a UTC day, so splitting one large
    order into several small POs cannot slip under the per-order cap."""

    def __init__(
        self,
        per_order: Decimal,
        daily_aggregate: Decimal,
        clock: Clock | None = None,
        *,
        currency: str = "USD",
    ) -> None:
        per_order = _money(per_order, "per_order")
        daily_aggregate = _money(daily_aggregate, "daily_aggregate")
        if per_order <= 0:
            raise ValueError("per_order cap must be > 0")
        if daily_aggregate < per_order:
            raise ValueError("daily aggregate cap must be >= the per_order cap")
        self.per_order = per_order
        self.daily_aggregate = daily_aggregate
        self.currency = currency.upper()
        self._clock: Clock = clock or _SystemClock()
        self._spent: dict[tuple[str, date], Decimal] = {}
        self._lock = threading.Lock()

    def _day(self) -> date:
        return _utc(self._clock.now()).date()

    def _validate(self, amount: object, currency: str | None) -> Decimal:
        value = _money(amount, "amount")
        if currency is not None and currency.upper() != self.currency:
            raise CapCurrencyMismatch(f"caps are in {self.currency}, got {currency}")
        return value

    def _check_locked(self, tenant_id: str, amount: Decimal) -> None:
        if amount > self.per_order:
            raise PerOrderCapExceeded(f"order exceeds the per-order cap of {self.per_order}")
        spent = self._spent.get((tenant_id, self._day()), Decimal(0))
        if spent + amount > self.daily_aggregate:
            raise DailyCapExceeded(
                f"order would exceed the daily aggregate cap of {self.daily_aggregate}"
            )

    def check(self, tenant_id: str, amount: Decimal, *, currency: str | None = None) -> None:
        """Raise a CapError if ``amount`` is not allowed now. Records nothing."""
        value = self._validate(amount, currency)
        with self._lock:
            self._check_locked(tenant_id, value)

    def reserve(self, tenant_id: str, amount: Decimal, *, currency: str | None = None) -> None:
        """Atomically check and record the spend (use right before the order is committed)."""
        value = self._validate(amount, currency)
        with self._lock:
            self._check_locked(tenant_id, value)
            key = (tenant_id, self._day())
            self._spent[key] = self._spent.get(key, Decimal(0)) + value

    def today(self) -> date:
        """The UTC day a reservation made now is booked against."""
        return self._day()

    def release(
        self, tenant_id: str, amount: Decimal, *, currency: str | None = None, day: date | None = None
    ) -> None:
        """Give back a reservation (cancelled/declined order). Never goes below zero."""
        value = self._validate(amount, currency)
        with self._lock:
            key = (tenant_id, day or self._day())
            self._spent[key] = max(Decimal(0), self._spent.get(key, Decimal(0)) - value)

    def spent_today(self, tenant_id: str) -> Decimal:
        with self._lock:
            return self._spent.get((tenant_id, self._day()), Decimal(0))

    def remaining_today(self, tenant_id: str) -> Decimal:
        return self.daily_aggregate - self.spent_today(tenant_id)


# ---------------------------------------------------------------- standing rules


class StandingRuleEngine:
    """Human-created standing pre-authorisations (vendor, family, $ band, count, expiry)."""

    def __init__(
        self,
        clock: Clock,
        store: Store,
        *,
        event_log: EventLog | None = None,
        caps: CapPolicy | None = None,
        max_lifetime: timedelta = timedelta(days=90),
        approval_ttl: timedelta = timedelta(minutes=15),
    ) -> None:
        self._clock = clock
        self._store = store
        self._log = event_log
        self._caps = caps
        self._max_lifetime = max_lifetime
        self._approval_ttl = approval_ttl

    def create_rule(
        self,
        *,
        tenant_id: str,
        vendor_id: str,
        family: str,
        max_amount: Decimal,
        max_count: int,
        expires_at: datetime,
        created_by: str,
    ) -> StandingRule:
        _require_human(created_by, "created_by")
        if not isinstance(vendor_id, str) or not vendor_id.strip():
            raise ValueError("vendor_id is required")
        if not isinstance(family, str) or not family.strip():
            raise ValueError("family is required")
        amount = _money(max_amount, "max_amount")
        if amount <= 0:
            raise ValueError("max_amount must be > 0")
        if isinstance(max_count, bool) or not isinstance(max_count, int) or not (
            1 <= max_count <= MAX_RULE_COUNT
        ):
            raise ValueError(f"max_count must be an integer in 1..{MAX_RULE_COUNT}")
        now = _utc(self._clock.now())
        if _utc(expires_at) <= now:
            raise ValueError("expires_at must be in the future")
        if _utc(expires_at) > now + self._max_lifetime:
            raise ValueError(f"expires_at must be within {self._max_lifetime} of now")
        ts = self._store.for_tenant(tenant_id)
        ts.vendors.get(vendor_id)  # must be a vendor of THIS tenant (NotFound / TenantIsolation)
        rule = StandingRule(
            id=f"rule-{secrets.token_hex(6)}",
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            family=family.strip(),
            max_amount=amount,
            max_count=max_count,
            expires_at=expires_at,
            created_by=created_by,
        )
        ts.standing_rules.add(rule)
        self._audit(
            tenant_id, created_by, EVT_RULE_CREATED,
            {
                "rule_id": rule.id, "vendor_id": vendor_id, "family": rule.family,
                "max_amount": amount, "max_count": max_count, "expires_at": expires_at,
            },
        )
        return rule

    def revoke_rule(self, tenant_id: str, rule_id: str, *, by: str) -> None:
        _require_human(by, "revoker")
        self._store.for_tenant(tenant_id).standing_rules.delete(rule_id)
        self._audit(tenant_id, by, EVT_RULE_REVOKED, {"rule_id": rule_id})

    def authorise_with_rule(
        self,
        rule_id: str,
        vendor_id: str,
        family: str,
        amount: Decimal,
        mime_hash: str,
        *,
        tenant_id: str,
    ) -> Approval:
        """Mint a ``standing`` Approval for one message/PO if the rule allows it.

        ``tenant_id`` is required (and keyword-only) so a rule can only ever be used inside the
        tenant that owns it."""
        _check_hash(mime_hash)
        value = _money(amount, "amount")
        ts = self._store.for_tenant(tenant_id)
        try:
            rule = ts.standing_rules.get(rule_id)
        except NotFoundError as exc:
            raise RuleNotUsable("standing rule does not exist or was revoked") from exc
        now = _utc(self._clock.now())
        if now >= _utc(rule.expires_at):
            raise RuleExpired("standing rule has expired")
        if vendor_id != rule.vendor_id or _norm_actor(family) != _norm_actor(rule.family):
            raise RuleScopeMismatch("vendor or part family is outside the standing rule")
        if value > rule.max_amount:
            raise AmountOverRule("amount exceeds the standing rule's band")
        if self._caps is not None:
            self._caps.check(tenant_id, value)
        if not ts.reserve_rule_use(rule.id, max_count=rule.max_count):
            raise RuleLimitReached("standing rule has no uses left")
        approval = Approval(
            id=f"appr-{secrets.token_hex(8)}",
            tenant_id=tenant_id,
            kind=ApprovalKind.STANDING,
            mime_hash=mime_hash,
            approver=rule.created_by,  # the human who set the rule stays accountable
            nonce=secrets.token_hex(16),
            expires_at=min(now + self._approval_ttl, _utc(rule.expires_at)),
            rule_id=rule.id,
        )
        ts.approvals.add(approval)
        self._audit(
            tenant_id, rule.created_by, EVT_APPROVAL_ISSUED,
            {
                "approval_id": approval.id, "kind": approval.kind.value, "rule_id": rule.id,
                "mime_hash": mime_hash, "amount": value, "approver": rule.created_by,
                "expires_at": approval.expires_at,
            },
        )
        return approval

    def _audit(self, tenant_id: str, actor: str, type_: str, payload: Mapping[str, Any]) -> None:
        if self._log is not None:
            self._log.append(tenant_id, None, actor, type_, payload)


# ---------------------------------------------------------------- approval links (R11)


class ApprovalAction(StrEnum):
    APPROVE = "approve"
    DECLINE = "decline"


@dataclass(frozen=True)
class TokenClaims:
    jti: str
    tenant_id: str
    approver: str
    action: ApprovalAction
    quote_version: int
    quote_hash: str
    requester: str
    amount: Decimal
    expires_at: datetime


@dataclass
class _TokenRecord:
    claims: TokenClaims
    consumed: bool = False
    po_issued: bool = False


_TOKEN_SALT = "purchasing-agent/approval-link/v1"  # noqa: S105 - salt, not a credential


class ApprovalService:
    """Issues approvals and approval links. Holds no mail credentials and cannot send."""

    def __init__(
        self,
        clock: Clock,
        secret: str | bytes,
        *,
        store: Store | None = None,
        event_log: EventLog | None = None,
        caps: CapPolicy | None = None,
        requester_threshold: Decimal = Decimal("500"),
        token_ttl: timedelta = timedelta(minutes=30),
        max_approval_ttl: timedelta = timedelta(hours=24),
    ) -> None:
        raw = secret.encode() if isinstance(secret, str) else secret
        if len(raw) < 16:
            raise ValueError("secret must be at least 16 bytes")
        self._clock = clock
        self._store = store if store is not None else Store()
        self._log = event_log
        self.caps = caps
        self._threshold = _money(requester_threshold, "requester_threshold")
        self._token_ttl = _check_ttl(token_ttl, max_approval_ttl)
        self._max_ttl = max_approval_ttl
        self._serializer = URLSafeSerializer(
            raw, salt=_TOKEN_SALT, signer_kwargs={"digest_method": hashlib.sha256}
        )
        self._tokens: dict[str, _TokenRecord] = {}
        self._lock = threading.RLock()
        self.rules = StandingRuleEngine(
            clock, self._store, event_log=event_log, caps=caps,
        )

    # ---- per-message approvals

    def issue_per_message_approval(
        self,
        tenant_id: str,
        approver: str,
        mime_hash: str,
        ttl: timedelta,
        *,
        request_id: str | None = None,
    ) -> Approval:
        """A human approves exactly one message (identified by its full-MIME sha256)."""
        _require_human(approver, "approver")
        return self._mint(
            tenant_id, ApprovalKind.PER_MESSAGE, approver, _check_hash(mime_hash), ttl,
            request_id=request_id,
        )

    def issue_substitution_approval(
        self, tenant_id: str, approver: str, candidate_mpn: str, quote_version: int, ttl: timedelta,
        *, request_id: str | None = None, quote_id: str | None = None,
    ) -> Approval:
        """R2: a human accepts a non-Tier-A candidate for one quote version. When ``request_id`` and
        ``quote_id`` are given they are bound into the approval subject (see ``substitution_subject``)
        so it cannot be replayed for another request or quote."""
        _require_human(approver, "approver")
        if not candidate_mpn.strip() or quote_version < 1:
            raise ValueError("candidate_mpn and quote_version are required")
        subject = substitution_subject(candidate_mpn, quote_version, request_id, quote_id)
        return self._mint(
            tenant_id, ApprovalKind.SUBSTITUTION, approver, subject, ttl, request_id=request_id,
            quote_version=quote_version, candidate_mpn=candidate_mpn,
        )

    def issue_po_approval(
        self, claims: TokenClaims, mime_hash: str, ttl: timedelta
    ) -> Approval:
        """Mint the PO send-approval for a link that a human has actually *consumed* (clicked)."""
        _check_hash(mime_hash)
        with self._lock:
            record = self._tokens.get(claims.jti)
            if record is None or record.claims != claims:
                raise TokenInvalid("claims do not match an issued approval link")
            if claims.action is not ApprovalAction.APPROVE:
                raise TokenWrongAction("only an approve click can authorise a PO")
            if not record.consumed:
                raise TokenError("approval link has not been consumed by its approver")
            if record.po_issued:
                raise TokenError("a PO approval was already issued for this approval")
            approval = self._mint(
                claims.tenant_id, ApprovalKind.PO, claims.approver, mime_hash, ttl,
                quote_version=claims.quote_version,
            )
            record.po_issued = True
            return approval

    def create_standing_rule(self, **kwargs: Any) -> StandingRule:
        return self.rules.create_rule(**kwargs)

    def authorise_with_rule(
        self,
        rule_id: str,
        vendor_id: str,
        family: str,
        amount: Decimal,
        mime_hash: str,
        *,
        tenant_id: str,
    ) -> Approval:
        return self.rules.authorise_with_rule(
            rule_id, vendor_id, family, amount, mime_hash, tenant_id=tenant_id
        )

    # ---- approval links

    def issue_approval_token(
        self,
        *,
        tenant_id: str,
        approver: str,
        action: ApprovalAction | str,
        quote_version: int,
        quote_hash: str,
        requester: str,
        amount: Decimal,
        ttl: timedelta | None = None,
        request_id: str | None = None,
    ) -> str:
        """Signed, single-use link token bound to approver, action and one immutable quote."""
        _require_human(approver, "approver")
        act = _coerce_action(action)
        _check_hash(quote_hash, "quote_hash")
        if isinstance(quote_version, bool) or not isinstance(quote_version, int):
            raise ValueError("quote_version must be a positive integer")
        if quote_version < 1:
            raise ValueError("quote_version must be a positive integer")
        if not isinstance(requester, str) or not requester.strip():
            raise ValueError("requester is required")
        value = _money(amount, "amount")
        lifetime = _check_ttl(ttl if ttl is not None else self._token_ttl, self._max_ttl)
        self._check_separation(act, approver, requester, value)
        # whole seconds: the signed payload carries an integer timestamp, claims must round-trip
        expires = datetime.fromtimestamp(
            math.ceil((_utc(self._clock.now()) + lifetime).timestamp()), tz=UTC
        )
        claims = TokenClaims(
            jti=secrets.token_urlsafe(16), tenant_id=tenant_id, approver=approver, action=act,
            quote_version=quote_version, quote_hash=quote_hash, requester=requester,
            amount=value, expires_at=expires,
        )
        token = self._serializer.dumps(
            {
                "v": 1, "jti": claims.jti, "tid": tenant_id, "apv": approver, "act": act.value,
                "qv": quote_version, "qh": quote_hash, "req": requester, "amt": str(value),
                "exp": int(expires.timestamp()),
            }
        )
        with self._lock:
            self._tokens[claims.jti] = _TokenRecord(claims)
        self._audit(
            tenant_id, approver, EVT_APPROVAL_TOKEN_ISSUED, request_id,
            {
                "jti": claims.jti, "approver": approver, "action": act.value,
                "quote_version": quote_version, "quote_hash": quote_hash, "requester": requester,
                "amount": value, "expires_at": expires,
            },
        )
        return str(token)

    def verify_token(
        self,
        token: str,
        *,
        tenant_id: str,
        approver: str,
        action: ApprovalAction | str,
        quote_version: int,
        quote_hash: str,
    ) -> TokenClaims:
        """Validate a link WITHOUT consuming it (safe for GET / link-preview traffic).

        Raises a ``TokenError`` subclass for: bad signature, never issued, expired, already used,
        another tenant, another approver, another action, or a different quote version/hash."""
        with self._lock:
            claims, _ = self._check(
                token, tenant_id, approver, _coerce_action(action), quote_version, quote_hash
            )
            return claims

    def consume_token(
        self,
        token: str,
        *,
        tenant_id: str,
        approver: str,
        action: ApprovalAction | str,
        quote_version: int,
        quote_hash: str,
        request_id: str | None = None,
    ) -> TokenClaims:
        """Verify and burn the link (call only from an authenticated POST). One use only."""
        with self._lock:
            claims, record = self._check(
                token, tenant_id, approver, _coerce_action(action), quote_version, quote_hash
            )
            self._check_separation(claims.action, claims.approver, claims.requester, claims.amount)
            record.consumed = True
            self._audit(
                tenant_id, approver, EVT_APPROVAL_TOKEN_CONSUMED, request_id,
                {
                    "approval_id": claims.jti, "jti": claims.jti, "approver": claims.approver,
                    "action": claims.action.value, "quote_version": claims.quote_version,
                    "quote_hash": claims.quote_hash,
                },
            )
            return claims

    # ---- internals

    def _check(
        self,
        token: object,
        tenant_id: str,
        approver: str,
        action: ApprovalAction,
        quote_version: int,
        quote_hash: str,
    ) -> tuple[TokenClaims, _TokenRecord]:
        claims = self._decode(token)
        if _utc(self._clock.now()) >= claims.expires_at:
            raise TokenExpired("approval link has expired")
        record = self._tokens.get(claims.jti)
        if record is None or record.claims != claims:
            raise TokenInvalid("approval link was not issued by this service")
        if record.consumed:
            raise TokenReplayed("approval link was already used")
        if claims.tenant_id != tenant_id:
            raise TokenTenantMismatch("approval link belongs to another tenant")
        if not _same(claims.approver, approver):
            raise TokenApproverMismatch("approval link was issued for another approver")
        if claims.action is not action:
            raise TokenWrongAction("approval link is for a different action")
        if claims.quote_version != quote_version or not _same(claims.quote_hash, quote_hash):
            raise TokenQuoteMismatch("quote changed since the link was issued")
        return claims, record

    def _decode(self, token: object) -> TokenClaims:
        if not isinstance(token, str) or not token:
            raise TokenInvalid("malformed approval link")
        try:
            data = self._serializer.loads(token)
            if not isinstance(data, dict) or data.get("v") != 1:
                raise TokenInvalid("unsupported approval link")
            return TokenClaims(
                jti=str(data["jti"]),
                tenant_id=str(data["tid"]),
                approver=str(data["apv"]),
                action=ApprovalAction(data["act"]),
                quote_version=int(data["qv"]),
                quote_hash=str(data["qh"]),
                requester=str(data["req"]),
                amount=Decimal(str(data["amt"])),
                expires_at=datetime.fromtimestamp(int(data["exp"]), tz=UTC),
            )
        except BadData as exc:
            raise TokenInvalid("approval link signature is invalid") from exc
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            raise TokenInvalid("malformed approval link") from exc

    def _check_separation(
        self, action: ApprovalAction, approver: str, requester: str, amount: Decimal
    ) -> None:
        if (
            action is ApprovalAction.APPROVE
            and amount > self._threshold
            and _norm_actor(approver) == _norm_actor(requester)
        ):
            raise SeparationOfDuties("the approver must differ from the requester above threshold")

    def _mint(
        self,
        tenant_id: str,
        kind: ApprovalKind,
        approver: str,
        mime_hash: str,
        ttl: timedelta,
        *,
        request_id: str | None = None,
        quote_version: int | None = None,
        candidate_mpn: str | None = None,
    ) -> Approval:
        lifetime = _check_ttl(ttl, self._max_ttl)
        approval = Approval(
            id=f"appr-{secrets.token_hex(8)}",
            tenant_id=tenant_id,
            kind=kind,
            mime_hash=mime_hash,
            approver=approver,
            nonce=secrets.token_hex(16),
            expires_at=_utc(self._clock.now()) + lifetime,
            quote_version=quote_version,
            candidate_mpn=candidate_mpn,
        )
        self._store.for_tenant(tenant_id).approvals.add(approval)
        self._audit(
            tenant_id, approver, EVT_APPROVAL_ISSUED, request_id,
            {
                "approval_id": approval.id, "kind": kind.value, "mime_hash": mime_hash,
                "approver": approver, "expires_at": approval.expires_at,
                "quote_version": quote_version, "candidate_mpn": candidate_mpn,
            },
        )
        return approval

    def _audit(
        self, tenant_id: str, actor: str, type_: str, request_id: str | None,
        payload: Mapping[str, Any],
    ) -> None:
        if self._log is not None:
            self._log.append(tenant_id, request_id, actor, type_, payload)


def substitution_subject(
    candidate_mpn: str, quote_version: int, request_id: str | None = None, quote_id: str | None = None
) -> str:
    """Hash a substitution approval is bound to: candidate + quote version (+ request and quote id)."""
    data: dict[str, Any] = {"substitution": candidate_mpn, "quote_version": quote_version}
    if request_id is not None or quote_id is not None:
        data.update({"request_id": request_id, "quote_id": quote_id})
    return hashlib.sha256(canonical_json(data).encode()).hexdigest()


def _coerce_action(action: ApprovalAction | str) -> ApprovalAction:
    try:
        return ApprovalAction(action)
    except ValueError as exc:
        raise ValueError(f"unknown action {action!r}; expected approve or decline") from exc


def _same(a: str, b: str) -> bool:
    return isinstance(a, str) and isinstance(b, str) and hmac.compare_digest(
        a.encode(), b.encode()
    )
