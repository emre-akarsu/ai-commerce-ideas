"""Per-message approvals (R1) and standing pre-authorisations (R1, F7)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from components.purchase_orders.approvals.service import (
    AmountOverRule,
    ApprovalService,
    NotHumanApprover,
    PerOrderCapExceeded,
    RuleExpired,
    RuleLimitReached,
    RuleNotUsable,
    RuleScopeMismatch,
    is_human_actor,
)
from components.evidence.log import EVT_APPROVAL_ISSUED, EVT_RULE_CREATED, EventLog
from components.core.domain import ApprovalKind
from components.core.fakes import FakeClock
from components.core.store import NotFoundError, Store, TenantIsolationError
from tests.security.factories import T1, T2, make_vendor, sha

H = sha("message-bytes")
FAMILY = "deep_groove_ball"


# ------------------------------------------------------------------ per-message


def test_per_message_approval_has_nonce_hash_and_expiry(
    svc: ApprovalService, clock: FakeClock, store: Store, log: EventLog
) -> None:
    a = svc.issue_per_message_approval(T1, "user:buyer-1", H, timedelta(minutes=10))
    assert a.kind is ApprovalKind.PER_MESSAGE
    assert a.tenant_id == T1 and a.mime_hash == H and a.approver == "user:buyer-1"
    assert a.expires_at == clock.now() + timedelta(minutes=10)
    assert a.rule_id is None
    assert len(a.nonce) >= 16
    assert store.for_tenant(T1).approvals.get(a.id) == a  # registered: the send-service checks it
    assert [e.type for e in log.events(T1)] == [EVT_APPROVAL_ISSUED]
    assert log.events(T1)[0].payload["mime_hash"] == H


def test_nonces_and_ids_are_random_and_unique(svc: ApprovalService) -> None:
    seen = {svc.issue_per_message_approval(T1, "user:b", H, timedelta(minutes=1)) for _ in range(50)}
    assert len({a.nonce for a in seen}) == 50
    assert len({a.id for a in seen}) == 50


@pytest.mark.parametrize("approver", ["", "  ", "agent", "agent:planner", "system", "operator:ops-1"])
def test_only_humans_can_approve(svc: ApprovalService, approver: str) -> None:
    with pytest.raises(NotHumanApprover):
        svc.issue_per_message_approval(T1, approver, H, timedelta(minutes=1))


def test_is_human_actor() -> None:
    assert is_human_actor("user:abc") and is_human_actor("buyer@acme.example")
    assert not is_human_actor("operator:x") and not is_human_actor("agent")
    assert not is_human_actor("System") and not is_human_actor("")


@pytest.mark.parametrize("bad_hash", ["", "abc", "Z" * 64, "A" * 64, H[:-1]])
def test_mime_hash_must_be_sha256_hex(svc: ApprovalService, bad_hash: str) -> None:
    with pytest.raises(ValueError, match="mime_hash"):
        svc.issue_per_message_approval(T1, "user:b", bad_hash, timedelta(minutes=1))


@pytest.mark.parametrize("ttl", [timedelta(0), timedelta(seconds=-5), timedelta(days=2)])
def test_ttl_must_be_positive_and_bounded(svc: ApprovalService, ttl: timedelta) -> None:
    with pytest.raises(ValueError, match="ttl"):
        svc.issue_per_message_approval(T1, "user:b", H, ttl)


def test_weak_secret_rejected(clock: FakeClock) -> None:
    with pytest.raises(ValueError, match="secret"):
        ApprovalService(clock, b"short")


def test_substitution_approval_binds_candidate_and_quote_version(svc: ApprovalService) -> None:
    a = svc.issue_substitution_approval(T1, "user:buyer-1", "6205-2RSH", 3, timedelta(hours=1))
    assert a.kind is ApprovalKind.SUBSTITUTION
    assert a.candidate_mpn == "6205-2RSH" and a.quote_version == 3
    with pytest.raises(NotHumanApprover):
        svc.issue_substitution_approval(T1, "agent", "6205-2RSH", 3, timedelta(hours=1))


# ------------------------------------------------------------------ standing rules


def _rule(svc: ApprovalService, clock: FakeClock, **kw: object):
    args: dict[str, object] = {
        "tenant_id": T1, "vendor_id": "v-1", "family": FAMILY, "max_amount": Decimal("500"),
        "max_count": 2, "expires_at": clock.now() + timedelta(days=7), "created_by": "user:admin-1",
    }
    args.update(kw)
    return svc.create_standing_rule(**args)  # type: ignore[arg-type]


def test_create_rule_is_stored_and_audited(
    svc: ApprovalService, clock: FakeClock, store: Store, log: EventLog
) -> None:
    rule = _rule(svc, clock)
    assert store.for_tenant(T1).standing_rules.get(rule.id) == rule
    assert rule.max_amount == Decimal("500") and rule.max_count == 2
    assert [e.type for e in log.events(T1)] == [EVT_RULE_CREATED]


@pytest.mark.parametrize(
    "kw,match",
    [
        ({"max_amount": Decimal("0")}, "max_amount"),
        ({"max_amount": Decimal("-1")}, "max_amount"),
        ({"max_amount": Decimal("NaN")}, "max_amount"),
        ({"max_amount": 500.0}, "max_amount"),
        ({"max_count": 0}, "max_count"),
        ({"max_count": 10_001}, "max_count"),
        ({"family": ""}, "family"),
        ({"expires_at": FakeClock().now() - timedelta(seconds=1)}, "expires_at"),
        ({"expires_at": FakeClock().now() + timedelta(days=400)}, "expires_at"),
        ({"vendor_id": ""}, "vendor"),
    ],
)
def test_create_rule_validation(
    svc: ApprovalService, clock: FakeClock, kw: dict[str, object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        _rule(svc, clock, **kw)


@pytest.mark.parametrize("creator", ["agent", "operator:ops", "system", ""])
def test_rules_are_created_by_humans_only(svc: ApprovalService, clock: FakeClock, creator: str) -> None:
    with pytest.raises(NotHumanApprover):
        _rule(svc, clock, created_by=creator)


def test_rule_requires_a_vendor_of_the_same_tenant(svc: ApprovalService, clock: FakeClock) -> None:
    with pytest.raises(NotFoundError):
        _rule(svc, clock, vendor_id="ghost")
    with pytest.raises(TenantIsolationError):
        _rule(svc, clock, vendor_id="v-9")  # other tenant's vendor


def test_authorise_with_rule_issues_standing_approval(
    svc: ApprovalService, clock: FakeClock, store: Store, log: EventLog
) -> None:
    rule = _rule(svc, clock)
    a = svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("120.50"), H, tenant_id=T1)
    assert a.kind is ApprovalKind.STANDING and a.rule_id == rule.id
    assert a.approver == "user:admin-1"  # the human who set the rule stays accountable
    assert a.mime_hash == H and a.tenant_id == T1
    assert a.expires_at <= rule.expires_at
    assert store.for_tenant(T1).approvals.get(a.id) == a
    assert log.events(T1)[-1].type == EVT_APPROVAL_ISSUED
    assert log.events(T1)[-1].payload["rule_id"] == rule.id


def test_rule_approval_never_outlives_the_rule(svc: ApprovalService, clock: FakeClock) -> None:
    rule = _rule(svc, clock, expires_at=clock.now() + timedelta(minutes=5))
    a = svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("1"), H, tenant_id=T1)
    assert a.expires_at == rule.expires_at


def test_rule_count_is_enforced(svc: ApprovalService, clock: FakeClock) -> None:
    rule = _rule(svc, clock, max_count=2)
    svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("1"), sha("1"), tenant_id=T1)
    svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("1"), sha("2"), tenant_id=T1)
    with pytest.raises(RuleLimitReached):
        svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("1"), sha("3"), tenant_id=T1)


def test_rule_amount_limit_is_enforced_and_failed_attempt_does_not_use_a_slot(
    svc: ApprovalService, clock: FakeClock
) -> None:
    rule = _rule(svc, clock, max_count=1, max_amount=Decimal("100"))
    with pytest.raises(AmountOverRule):
        svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("100.01"), H, tenant_id=T1)
    svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("100.00"), H, tenant_id=T1)  # boundary ok


def test_rule_expiry_is_enforced(svc: ApprovalService, clock: FakeClock) -> None:
    rule = _rule(svc, clock, expires_at=clock.now() + timedelta(hours=1))
    clock.advance(hours=1)
    with pytest.raises(RuleExpired):
        svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("1"), H, tenant_id=T1)


@pytest.mark.parametrize(
    "vendor,family", [("v-2", FAMILY), ("v-1", "v_belt"), ("v-1", "")]
)
def test_rule_scope_vendor_and_family(
    svc: ApprovalService, clock: FakeClock, store: Store, vendor: str, family: str
) -> None:
    store.for_tenant(T1).vendors.add(make_vendor("v-2", email="a@other.example", domain="other.example"))
    rule = _rule(svc, clock)
    with pytest.raises(RuleScopeMismatch):
        svc.authorise_with_rule(rule.id, vendor, family, Decimal("1"), H, tenant_id=T1)


def test_rule_of_another_tenant_cannot_be_used(svc: ApprovalService, clock: FakeClock) -> None:
    rule = _rule(svc, clock)
    with pytest.raises(TenantIsolationError):
        svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("1"), H, tenant_id=T2)


def test_unknown_or_revoked_rule(svc: ApprovalService, clock: FakeClock) -> None:
    with pytest.raises(RuleNotUsable):
        svc.authorise_with_rule("nope", "v-1", FAMILY, Decimal("1"), H, tenant_id=T1)
    rule = _rule(svc, clock)
    svc.rules.revoke_rule(T1, rule.id, by="user:admin-1")
    with pytest.raises(RuleNotUsable):
        svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("1"), H, tenant_id=T1)
    with pytest.raises(NotHumanApprover):
        svc.rules.revoke_rule(T1, "x", by="agent")


@pytest.mark.parametrize("amount", [Decimal("-1"), Decimal("NaN"), Decimal("Infinity"), 5, 5.0, "5"])
def test_rule_amount_must_be_a_finite_non_negative_decimal(
    svc: ApprovalService, clock: FakeClock, amount: object
) -> None:
    rule = _rule(svc, clock)
    with pytest.raises((ValueError, TypeError)):
        svc.authorise_with_rule(rule.id, "v-1", FAMILY, amount, H, tenant_id=T1)  # type: ignore[arg-type]


def test_rule_authorisation_respects_caps(svc: ApprovalService, clock: FakeClock) -> None:
    rule = _rule(svc, clock, max_amount=Decimal("5000"))  # rule band above the per-order cap
    with pytest.raises(PerOrderCapExceeded):
        svc.authorise_with_rule(rule.id, "v-1", FAMILY, Decimal("1000.01"), H, tenant_id=T1)
