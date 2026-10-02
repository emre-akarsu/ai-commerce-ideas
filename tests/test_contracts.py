from datetime import UTC, datetime
from decimal import Decimal

from purchasing_agent.domain import Approval, ApprovalKind, Quote, Tier


def test_tiers_and_money_types():
    assert [t.value for t in Tier] == ["A", "B", "C", "D"]
    q = Quote(id="q", tenant_id="t", rfq_id="r", vendor_id="v", unit_price_each=Decimal("1.25"))
    assert isinstance(q.unit_price_each, Decimal)


def test_models_are_frozen():
    a = Approval(
        id="a", tenant_id="t", kind=ApprovalKind.PER_MESSAGE, mime_hash="h",
        approver="u", nonce="n", expires_at=datetime.now(UTC),
    )
    try:
        a.approver = "x"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("Approval must be immutable")
