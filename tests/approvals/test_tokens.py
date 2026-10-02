"""Signed approval-link tokens (R11): bound, single-use, short-lived, verify != consume."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest

from components.core.domain import ApprovalKind
from components.core.fakes import FakeClock
from components.core.store import Store
from components.evidence.log import (
    EVT_APPROVAL_ISSUED,
    EVT_APPROVAL_TOKEN_CONSUMED,
    EVT_APPROVAL_TOKEN_ISSUED,
    EventLog,
)
from components.purchase_orders.approvals.service import (
    ApprovalAction,
    ApprovalService,
    NotHumanApprover,
    SeparationOfDuties,
    TokenApproverMismatch,
    TokenError,
    TokenExpired,
    TokenInvalid,
    TokenQuoteMismatch,
    TokenReplayed,
    TokenTenantMismatch,
    TokenWrongAction,
    quote_fingerprint,
)
from tests.security.factories import APPROVAL_KEY, T1, T2, make_quote, sha

APPROVER = "user:approver-1"
REQUESTER = "user:tech-1"
QUOTE = make_quote()
QH = quote_fingerprint(QUOTE)


def issue(svc: ApprovalService, **kw: Any) -> str:
    args: dict[str, Any] = {
        "tenant_id": T1, "approver": APPROVER, "action": ApprovalAction.APPROVE,
        "quote_version": 1, "quote_hash": QH, "requester": REQUESTER, "amount": Decimal("200"),
    }
    args.update(kw)
    return svc.issue_approval_token(**args)


def check(**kw: Any) -> dict[str, Any]:
    args: dict[str, Any] = {
        "tenant_id": T1, "approver": APPROVER, "action": ApprovalAction.APPROVE,
        "quote_version": 1, "quote_hash": QH,
    }
    args.update(kw)
    return args


def test_issue_verify_consume_happy_path(svc: ApprovalService, clock: FakeClock) -> None:
    token = issue(svc)
    assert isinstance(token, str) and len(token) > 40
    claims = svc.verify_token(token, **check())
    assert claims.approver == APPROVER and claims.action is ApprovalAction.APPROVE
    assert claims.quote_version == 1 and claims.quote_hash == QH and claims.tenant_id == T1
    assert claims.expires_at == clock.now() + timedelta(minutes=30)
    consumed = svc.consume_token(token, **check())
    assert consumed == claims


def test_verify_never_consumes_so_link_prefetchers_are_harmless(
    svc: ApprovalService, log: EventLog
) -> None:
    token = issue(svc)
    events_before = len(log.events(T1))
    for _ in range(25):  # mail scanners / preview bots / the human opening the page repeatedly
        svc.verify_token(token, **check())
    assert len(log.events(T1)) == events_before  # GET-equivalent: no state change at all
    svc.consume_token(token, **check())  # the real POST still works, exactly once
    with pytest.raises(TokenReplayed):
        svc.consume_token(token, **check())


def test_verify_after_consume_reports_replay(svc: ApprovalService) -> None:
    token = issue(svc)
    svc.consume_token(token, **check())
    with pytest.raises(TokenReplayed):
        svc.verify_token(token, **check())


def test_failed_consume_does_not_burn_the_token(svc: ApprovalService) -> None:
    token = issue(svc)
    with pytest.raises(TokenWrongAction):
        svc.consume_token(token, **check(action=ApprovalAction.DECLINE))
    with pytest.raises(TokenApproverMismatch):
        svc.consume_token(token, **check(approver="user:someone-else"))
    svc.consume_token(token, **check())  # still usable by the right person with the right action


def test_events_for_issue_and_consume_never_contain_the_token(
    svc: ApprovalService, log: EventLog
) -> None:
    token = issue(svc)
    svc.consume_token(token, **check())
    types = [e.type for e in log.events(T1)]
    assert types == [EVT_APPROVAL_TOKEN_ISSUED, EVT_APPROVAL_TOKEN_CONSUMED]
    assert token not in str(log.export(T1))
    consumed = log.events(T1)[-1].payload
    assert consumed["approver"] == APPROVER and consumed["action"] == "approve"
    assert consumed["quote_hash"] == QH


def test_expired_token_rejected(svc: ApprovalService, clock: FakeClock) -> None:
    token = issue(svc, ttl=timedelta(minutes=5))
    clock.advance(minutes=4, seconds=59)
    svc.verify_token(token, **check())
    clock.advance(seconds=1)
    with pytest.raises(TokenExpired):
        svc.verify_token(token, **check())
    with pytest.raises(TokenExpired):
        svc.consume_token(token, **check())


@pytest.mark.parametrize(
    "kw,exc",
    [
        ({"action": ApprovalAction.DECLINE}, TokenWrongAction),
        ({"quote_version": 2}, TokenQuoteMismatch),
        ({"quote_hash": sha("a different quote")}, TokenQuoteMismatch),
        ({"approver": "user:other"}, TokenApproverMismatch),
        ({"tenant_id": T2}, TokenTenantMismatch),
    ],
)
def test_binding_mismatches_are_rejected(svc: ApprovalService, kw: dict[str, Any], exc: type) -> None:
    token = issue(svc)
    with pytest.raises(exc):
        svc.verify_token(token, **check(**kw))
    with pytest.raises(exc):
        svc.consume_token(token, **check(**kw))


def test_decline_token_cannot_approve(svc: ApprovalService) -> None:
    token = issue(svc, action=ApprovalAction.DECLINE)
    with pytest.raises(TokenWrongAction):
        svc.verify_token(token, **check(action=ApprovalAction.APPROVE))
    svc.consume_token(token, **check(action=ApprovalAction.DECLINE))


def test_changed_quote_content_changes_the_fingerprint() -> None:
    assert quote_fingerprint(make_quote()) == QH  # stable
    assert quote_fingerprint(make_quote(version=2)) != QH
    assert quote_fingerprint(make_quote(flags=("x",))) != QH
    changed = make_quote().model_copy(update={"unit_price_each": Decimal("0.01")})
    assert quote_fingerprint(changed) != QH


def _flip_middle(token: str) -> str:
    mid = len(token) // 2
    return token[:mid] + ("A" if token[mid] != "A" else "B") + token[mid + 1 :]


@pytest.mark.parametrize(
    "mutate",
    [_flip_middle, lambda t: "x" + t[1:], lambda t: t + "a", lambda t: "", lambda t: "not.a.token",
     lambda t: t.upper()],
)
def test_tampered_or_garbage_tokens_are_invalid(svc: ApprovalService, mutate: Any) -> None:
    token = issue(svc)
    with pytest.raises(TokenInvalid):
        svc.verify_token(mutate(token), **check())


def test_token_signed_with_another_secret_is_invalid(
    svc: ApprovalService, clock: FakeClock, store: Store
) -> None:
    other = ApprovalService(clock, b"x" * 32, store=store)
    forged = issue(other)
    with pytest.raises(TokenInvalid):
        svc.verify_token(forged, **check())


def test_validly_signed_but_never_issued_token_is_invalid(
    svc: ApprovalService, clock: FakeClock
) -> None:
    """A second service sharing the secret but not the issue registry cannot mint working links."""
    twin = ApprovalService(clock, APPROVAL_KEY)
    with pytest.raises(TokenInvalid):
        svc.verify_token(issue(twin), **check())


def test_approver_must_differ_from_requester_above_threshold(svc: ApprovalService) -> None:
    with pytest.raises(SeparationOfDuties):
        issue(svc, approver=REQUESTER, requester=REQUESTER, amount=Decimal("500.01"))
    with pytest.raises(SeparationOfDuties):  # case/whitespace games do not help
        issue(svc, approver=" USER:Tech-1 ", requester=REQUESTER, amount=Decimal("9999"))
    issue(svc, approver=REQUESTER, requester=REQUESTER, amount=Decimal("500"))  # at threshold: ok
    issue(svc, approver=REQUESTER, requester=REQUESTER, amount=Decimal("9999"),
          action=ApprovalAction.DECLINE)  # declining authorises nothing


def test_separation_of_duties_is_rechecked_on_consume(svc: ApprovalService) -> None:
    """Even if the claims were somehow edited the check also runs when the link is used."""
    token = issue(svc, approver=APPROVER, requester=APPROVER, amount=Decimal("100"))
    svc._threshold = Decimal("50")  # noqa: SLF001 - policy tightened after the link was issued
    with pytest.raises(SeparationOfDuties):
        svc.consume_token(token, **check())


@pytest.mark.parametrize("approver", ["agent", "operator:ops-1", "system", ""])
def test_only_humans_get_links(svc: ApprovalService, approver: str) -> None:
    with pytest.raises(NotHumanApprover):
        issue(svc, approver=approver, requester=REQUESTER)


@pytest.mark.parametrize(
    "ttl", [timedelta(0), timedelta(seconds=-1), timedelta(days=3)]
)
def test_token_ttl_must_be_short(svc: ApprovalService, ttl: timedelta) -> None:
    with pytest.raises(ValueError, match="ttl"):
        issue(svc, ttl=ttl)


@pytest.mark.parametrize("bad", [0.5, 5, "5", None, Decimal("NaN"), Decimal("-1")])
def test_token_amount_must_be_a_valid_decimal(svc: ApprovalService, bad: Any) -> None:
    with pytest.raises(ValueError, match="amount"):
        issue(svc, amount=bad)


def test_unknown_action_rejected(svc: ApprovalService) -> None:
    with pytest.raises(ValueError, match="action"):
        issue(svc, action="delete")


# ------------------------------------------------------------------ PO approval from a consumed link


def test_po_approval_only_exists_after_a_human_consumed_an_approve_link(
    svc: ApprovalService, store: Store, log: EventLog, clock: FakeClock
) -> None:
    token = issue(svc)
    claims = svc.verify_token(token, **check())
    with pytest.raises(TokenError, match="consumed"):  # merely viewing the link authorises nothing
        svc.issue_po_approval(claims, sha("po-mime"), timedelta(minutes=30))
    claims = svc.consume_token(token, **check())
    a = svc.issue_po_approval(claims, sha("po-mime"), timedelta(minutes=30))
    assert a.kind is ApprovalKind.PO and a.quote_version == 1 and a.approver == APPROVER
    assert a.mime_hash == sha("po-mime") and a.tenant_id == T1
    assert a.expires_at == clock.now() + timedelta(minutes=30)
    assert store.for_tenant(T1).approvals.get(a.id) == a
    assert log.events(T1)[-1].type == EVT_APPROVAL_ISSUED
    with pytest.raises(TokenError, match="already"):  # one PO approval per approval click
        svc.issue_po_approval(claims, sha("po-mime-2"), timedelta(minutes=30))


def test_decline_click_never_yields_a_po_approval(svc: ApprovalService) -> None:
    token = issue(svc, action=ApprovalAction.DECLINE)
    claims = svc.consume_token(token, **check(action=ApprovalAction.DECLINE))
    with pytest.raises(TokenWrongAction):
        svc.issue_po_approval(claims, sha("po"), timedelta(minutes=5))


def test_forged_claims_cannot_mint_a_po_approval(svc: ApprovalService) -> None:
    token = issue(svc)
    claims = svc.consume_token(token, **check())
    from dataclasses import replace

    with pytest.raises(TokenError):
        svc.issue_po_approval(replace(claims, jti="made-up"), sha("po"), timedelta(minutes=5))
    with pytest.raises(TokenError):
        svc.issue_po_approval(replace(claims, approver="user:attacker"), sha("po"),
                              timedelta(minutes=5))
