"""Supplier records (profile, verification, suppression), the assumption ledger records and the
pure rules around them. In-memory repositories; the Postgres twins are in tests/aidb."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from components.core.store import (
    DuplicateError,
    NotFoundError,
    TenantIsolationError,
)
from components.suppliers import (
    Assumption,
    Money,
    SupplierProfile,
    SupplierStore,
    Verification,
    is_stop_request,
    parse_vendor_csv,
)

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)


def test_profile_defaults_are_unverified_not_suppressed() -> None:
    p = SupplierProfile(tenant_id="t1", vendor_id="v1")
    assert p.verification.state == "unverified"
    assert p.suppressed is False and p.contact_kind == "unknown"
    assert p.id == "v1"  # keyed by (tenant_id, vendor_id)


def test_profile_rejects_unknown_fields_and_bad_values() -> None:
    with pytest.raises(ValidationError):
        SupplierProfile(tenant_id="t1", vendor_id="v1", surprise=1)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        SupplierProfile(tenant_id="t1", vendor_id="v1", account_type="barter")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Money(amount=Decimal("-1"), currency="GBP")
    with pytest.raises(ValidationError):
        Money(amount=Decimal("NaN"), currency="GBP")
    with pytest.raises(ValidationError):
        Money(amount=Decimal("1"), currency="gbp")


def test_attested_state_needs_who_and_when() -> None:
    with pytest.raises(ValidationError):
        Verification(state="attested")
    v = Verification(state="attested", attested_by="user:a", attested_at=NOW)
    assert v.note is None


def test_store_is_tenant_scoped() -> None:
    s = SupplierStore()
    a, b = s.for_tenant("t1"), s.for_tenant("t2")
    a.profiles.add(SupplierProfile(tenant_id="t1", vendor_id="v1", account_number="A-1"))
    assert a.profiles.get("v1").account_number == "A-1"
    assert b.profiles.list() == []
    with pytest.raises(TenantIsolationError):
        b.profiles.add(SupplierProfile(tenant_id="t1", vendor_id="v1"))
    with pytest.raises(TenantIsolationError):
        b.profiles.get("v1")
    with pytest.raises(DuplicateError):
        a.profiles.add(SupplierProfile(tenant_id="t1", vendor_id="v1"))
    with pytest.raises(NotFoundError):
        a.profiles.get("nope")


def test_store_returns_copies() -> None:
    t = SupplierStore().for_tenant("t1")
    t.profiles.add(SupplierProfile(tenant_id="t1", vendor_id="v1"))
    got = t.profiles.get("v1")
    got.suppressed = True
    assert t.profiles.get("v1").suppressed is False


def test_assumption_repo_filters_by_request() -> None:
    t = SupplierStore().for_tenant("t1")
    for i, rid in enumerate(("r1", "r1", "r2")):
        t.assumptions.add(Assumption(
            id=f"a{i}", tenant_id="t1", request_id=rid, statement="s", source="default_template",
            confidence="medium", critical=False, created_at=NOW))
    assert [a.id for a in t.assumptions.list(lambda a: a.request_id == "r1")] == ["a0", "a1"]


@pytest.mark.parametrize("text", [
    "stop", "STOP", "Stop.", "  unsubscribe ", "Unsubscribe!", "remove me", "REMOVE   ME",
    "please stop", "Stop please",
])
def test_stop_requests_are_recognised(text: str) -> None:
    assert is_stop_request(text)


@pytest.mark.parametrize("text", [
    "", "stop by tuesday for the quote", "unit price 4.20 each", "do not stop the order",
    "Please quote 6205-2RS, and stop", "x" * 5000, "remove meters from the quote",
])
def test_other_text_is_not_a_stop_request(text: str) -> None:
    assert not is_stop_request(text)


CSV = (
    "name,domain,contact_email,phone,account_number,account_type,credit_days,"
    "quote_validity_days,contact_kind\n"
)


def test_parse_vendor_csv_accepts_good_rows_and_numbers_rows_from_two() -> None:
    data = (CSV + "Acme Ltd,acme.example,sales@acme.example,+44 20 7946 0001,A-1,credit,30,14,company\n"
            "Bolt,bolt.example,sales@bolt.example,,,,,,\n").encode()
    res = parse_vendor_csv(data, max_rows=10)
    assert [r.row for r in res.rows] == [2, 3]
    assert res.rejected == []
    first = res.rows[0]
    assert (first.name, first.domain, first.contact_email) == (
        "Acme Ltd", "acme.example", "sales@acme.example")
    assert first.credit_days == 30 and first.account_type == "credit"
    assert res.rows[1].account_type is None and res.rows[1].contact_kind is None


@pytest.mark.parametrize(("row", "reason_part"), [
    ("A​B,a.example,s@a.example,,,,,,", "name"),
    ("Ok,a.example,s@a.example,+44\x07,,,,,", "phone"),
    ("x" * 201 + ",a.example,s@a.example,,,,,,", "name"),
    ("Ok,https://a.example/x,s@a.example,,,,,,", "domain"),
    ("Ok,a b.example,s@a.example,,,,,,", "domain"),
    ("Ok,nodot,s@a.example,,,,,,", "domain"),
    ("Ok,a.example,not-an-email,,,,,,", "contact_email"),
    ("Ok,a.example,s@a.example,,,barter,,,", "account_type"),
    ("Ok,a.example,s@a.example,,,,abc,,", "credit_days"),
    ("Ok,a.example,s@a.example,,,,,-1,", "quote_validity_days"),
    ("Ok,a.example,s@a.example,,,,,,martian", "contact_kind"),
    (",a.example,s@a.example,,,,,,", "name"),
])
def test_bad_rows_are_rejected_with_row_and_reason_and_never_echo_values(
    row: str, reason_part: str,
) -> None:
    data = (CSV + "Good,g.example,s@g.example,,,,,,\n" + row + "\n").encode()
    res = parse_vendor_csv(data, max_rows=10)
    assert [r.row for r in res.rows] == [2]
    assert len(res.rejected) == 1
    rej = res.rejected[0]
    assert rej.row == 3 and reason_part in rej.reason
    assert "​" not in rej.reason and "https" not in rej.reason


def test_every_row_is_accounted_for() -> None:
    lines = [f"V{i},v{i}.example,s@v{i}.example,,,,,," for i in range(5)]
    lines[2] = "Bad,nodot,s@x.example,,,,,,"
    res = parse_vendor_csv((CSV + "\n".join(lines) + "\n").encode(), max_rows=10)
    assert len(res.rows) + len(res.rejected) == 5


def test_header_problems_refuse_the_file() -> None:
    with pytest.raises(ValueError, match="missing required column"):
        parse_vendor_csv(b"name,domain\nA,a.example\n", max_rows=10)
    with pytest.raises(ValueError, match="unknown column"):
        parse_vendor_csv((CSV.strip() + ",preferred\n").encode(), max_rows=10)
    with pytest.raises(ValueError, match="duplicate column"):
        parse_vendor_csv(b"name,domain,contact_email,name\n", max_rows=10)
    with pytest.raises(ValueError, match="UTF-8"):
        parse_vendor_csv(b"\xff\xfe\x00bad", max_rows=10)
    with pytest.raises(ValueError, match="empty"):
        parse_vendor_csv(b"", max_rows=10)


def test_too_many_rows_refuse_the_file() -> None:
    body = "".join(f"V{i},v{i}.example,s@v{i}.example,,,,,,\n" for i in range(4))
    with pytest.raises(ValueError, match="too many rows"):
        parse_vendor_csv((CSV + body).encode(), max_rows=3)


def test_row_with_wrong_cell_count_is_rejected_not_dropped() -> None:
    res = parse_vendor_csv((CSV + "A,a.example,s@a.example\n").encode(), max_rows=10)
    assert res.rows == [] and res.rejected[0].row == 2
    res = parse_vendor_csv((CSV + "A,a.example,s@a.example,,,,,,,extra,cells\n").encode(), max_rows=10)
    assert res.rows == [] and res.rejected[0].row == 2


def test_domain_is_lowercased_and_email_lowercased() -> None:
    res = parse_vendor_csv((CSV + "A,ACME.Example,Sales@ACME.example,,,,,,\n").encode(), max_rows=5)
    assert res.rows[0].domain == "acme.example"
    assert res.rows[0].contact_email == "sales@acme.example"
