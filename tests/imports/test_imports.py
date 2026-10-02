"""CSV importers with messy, partly hostile fixtures (synthetic data only)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from employees.purchasing.views import ImportSummary

from components.core.domain import UoM, Vendor
from components.imports import (
    clean_text,
    import_assets,
    import_parts,
    import_po_history,
    neutralise,
)

T = "t-acme"


def vendor(vid: str, name: str) -> Vendor:
    return Vendor(id=vid, tenant_id=T, name=name, domain=f"{vid}.example",
                  contact_email=f"q@{vid}.example")


VENDORS = [vendor("v1", "Bearings Direct, Inc."), vendor("v2", "Acme Supply LLC"),
           vendor("v3", "Twin Co"), vendor("v4", "Twin Corp")]

PO_CSV = (
    "PO #,Supplier,Part No,Qty,Unit Price,Currency,UoM,Date\n"
    "1001,bearings direct,6204-2RS,\"1,200\",$4.25,usd,each,2025-03-04\n"
    "1002,ACME SUPPLY,V-BELT A42,10,\"$1,234.50\",USD,per 100,03/05/2025\n"
    "1003,Unknown Vendor,X1,1,1.00,USD,each,2025-03-04\n"
    "1004,Twin,X2,1,1.00,USD,each,2025-03-04\n"
    "1005,Acme Supply,X3,abc,1.00,USD,each,2025-03-04\n"
    "1006,Acme Supply,X4,1,-5,USD,each,2025-03-04\n"
    "1007,Acme Supply,X5,1,1.00,ZZZ,each,2025-03-04\n"
    "1008,Acme Supply,X6,1,1.00,USD,bushel,2025-03-04\n"
    "1009,Acme Supply,X7,1,1.00,USD,each,04/05/25\n"
    ",,,,,,,\n"
    "1010,\"=HYPERLINK(\"\"http://evil.example\"\")\",X8,1,1.00,USD,each,2025-03-04\n"
)


def test_po_history_typed_rows_and_rejects() -> None:
    res = import_po_history(PO_CSV.encode(), VENDORS)
    assert [r.po_number for r in res.accepted] == ["1001", "1002"]
    r1, r2 = res.accepted
    assert r1.unit_price == Decimal("4.25") and isinstance(r1.unit_price, Decimal)
    assert r1.quantity == 1200 and r1.currency == "USD" and r1.uom is UoM.EACH
    assert r1.vendor_id == "v1" and r1.po_date == date(2025, 3, 4)
    assert r2.unit_price == Decimal("1234.50") and r2.uom is UoM.PER_100
    assert r2.po_date == date(2025, 3, 5)
    reasons = {e.row: e.reason for e in res.errors}
    assert reasons == {4: "unknown_vendor", 5: "ambiguous_vendor", 6: "invalid_integer",
                       7: "invalid_amount", 8: "unknown_currency", 9: "unknown_uom",
                       10: "invalid_date", 12: "unknown_vendor"}
    assert res.rows == 10 and res.rejected_rows == 8  # blank line skipped


def test_summary_is_import_summary_compatible() -> None:
    res = import_po_history(PO_CSV.encode(), VENDORS)
    s = ImportSummary.model_validate(res.summary())
    assert (s.rows, s.accepted, s.rejected) == (10, 2, 8) and len(s.errors) == 8


def test_formula_injection_never_echoed_raw() -> None:
    res = import_po_history(PO_CSV.encode(), VENDORS)
    echoed = [e.value for e in res.errors if e.row == 12][0]
    assert "evil.example" not in echoed and not echoed.startswith("=")
    res2 = import_po_history(b"po,vendor,part,qty,price,currency,uom,date\n1,=cmd|x,A,1,1,USD,each,"
                             b"2025-01-01\n", VENDORS)
    assert res2.errors[0].value == "'=cmd|x"
    for e in res.errors:
        assert not e.value.lstrip().startswith(("=", "+", "-", "@"))


def test_neutralise_and_clean_text() -> None:
    for bad in ("=1+1", "+cmd", "-2+3", "@SUM(A1)", "  =x", "\t=x", " @x"):
        assert neutralise(bad).startswith("'")
    assert neutralise("6204-2RS") == "6204-2RS"
    assert clean_text("=cmd|' /C calc'!A0").startswith("'=")
    assert clean_text("a​b <!-- x --> http://e.example\nnext") == "ab [link removed] next"


def test_currency_default_and_missing() -> None:
    csv_ = "po,vendor,part,qty,price,date\n1,Acme Supply,A,1,2.5,2025-01-01\n"
    assert import_po_history(csv_.encode(), VENDORS).accepted == []
    res = import_po_history(csv_.encode(), VENDORS, default_currency="usd", default_uom=UoM.EACH)
    assert res.accepted[0].currency == "USD" and res.accepted[0].uom is UoM.EACH
    assert import_po_history(csv_.encode(), VENDORS, default_currency="USD").errors[0].reason == (
        "uom_required"
    )


def test_money_is_not_float_and_precision_bounded() -> None:
    csv_ = ("po,vendor,part,qty,price,currency,uom,date\n"
            "1,Acme Supply,A,1,0.1234567,USD,each,2025-01-01\n"
            "2,Acme Supply,A,1,1e5,USD,each,2025-01-01\n"
            "3,Acme Supply,A,1,0.10,USD,each,2025-01-01\n")
    res = import_po_history(csv_.encode(), VENDORS)
    assert [r.unit_price for r in res.accepted] == [Decimal("0.10")]
    assert [e.reason for e in res.errors] == ["amount_out_of_range", "invalid_amount"]


def test_tenant_vendors_only() -> None:
    other = [vendor("vx", "Globex")]
    res = import_po_history(PO_CSV.encode(), other)
    assert res.accepted == []


def test_missing_columns_and_empty_and_binary_and_large() -> None:
    assert import_po_history(b"a,b\n1,2\n", VENDORS).errors[0].reason.startswith("missing_columns")
    assert import_parts(b"").errors[0].reason == "empty_file"
    assert import_parts(b"part,desc\n\x00\x01").errors[0].reason == "binary_content"
    big = b"part,desc\n" + b"x,y\n" * 2_000_000
    s = import_parts(big).summary()
    assert s["rows"] == 0 and s["errors"][0]["reason"] == "file_too_large"


def test_parts_messy() -> None:
    csv_ = (
        "﻿Part Number;Description;MFR;Unit;MOQ\n"
        "6204-2RS;Ball bearing 20mm <b>sealed</b>;SKF;each;10\n"
        "6204-2rs;dup;SKF;each;1\n"
        ";no number;;;\n"
        "BELT-A42;=SUM(A1:A9);Gates;per 100;x\n"
        "SEAL-1;\"multi\nline desc http://evil.example\";;;\n"
    )
    res = import_parts(csv_.encode("utf-8"))
    assert [p.part_number for p in res.accepted] == ["6204-2RS", "SEAL-1"]
    assert res.accepted[0].description == "Ball bearing 20mm sealed"
    assert res.accepted[1].description == "multi line desc [link removed]"
    assert [e.reason for e in res.errors] == ["duplicate_in_file", "required", "invalid_integer"]


def test_parts_formula_description_is_stored_neutralised() -> None:
    res = import_parts(b"part,description\nA1,=1+1\n")
    assert res.accepted[0].description == "'=1+1"


def test_cp1252_fallback_flagged() -> None:
    res = import_parts("part,description\nA1,Caf\xe9 valve\n".encode("cp1252"))
    assert res.accepted[0].description == "Caf\xe9 valve" and "decoded_as_cp1252" in res.flags


def test_cell_too_long() -> None:
    res = import_parts(b"part,description\nA1," + b"x" * 5000 + b"\n")
    assert res.errors[0].reason == "cell_too_long" and res.rejected_rows == 1


def test_assets() -> None:
    csv_ = ("Asset Tag,Name,Site,Area,Criticality\n"
            "P-101,Feed pump,Plant 1,Line 2,High\n"
            "P-101,Dupe,Plant 1,,\n"
            "@P-102,Cooling fan,,,maybe\n"
            "P-103,Mixer,Plant 2,,no\n")
    res = import_assets(csv_.encode())
    assert [(a.asset_tag, a.critical) for a in res.accepted] == [("P-101", True), ("P-103", False)]
    assert [e.reason for e in res.errors] == ["duplicate_in_file", "invalid_flag"]
    assert ImportSummary.model_validate(res.summary()).accepted == 2
