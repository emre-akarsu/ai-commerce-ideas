"""Shadow diff: two independent readings of one quote are compared on the critical fields.

Findings only: these tests never expect a merged value or a chosen reading.
"""

import pytest

from components.core.domain import ExtractedQuote
from components.verify.findings import NOT_SHOWN, Finding, Severity, explain
from components.verify.shadow import CRITICAL_FIELDS, diff_readings

BASE: dict[str, str] = {
    "unit_price": "12.50",
    "currency": "GBP",
    "uom": "each",
    "quantity_available": "500",
    "moq": "10",
    "lead_time": "3 days",
    "freight": "15.00",
    "validity": "30 days",
    "offered_mpn": "AB-123",
    "condition": "new",
    "authenticity_claim": "genuine OEM",
    "tax_text": "+ VAT",
}

HOSTILE: list[str] = [
    "see https://vendor.example/terms",
    "www.vendor.example",
    "mailto:sales@vendor.example",
    "<b>new</b>",
    "new [offer]",
    "new `offer`",
    "new\x07",
    "n" * 61,
]


def _reading(**changes: str | None) -> ExtractedQuote:
    values: dict[str, str | None] = {**BASE, **changes}
    return ExtractedQuote(**values)


def _only(findings: tuple[Finding, ...]) -> Finding:
    assert len(findings) == 1, findings
    return findings[0]


def test_identical_readings_give_nothing() -> None:
    assert diff_readings(_reading(), _reading()) == ()


@pytest.mark.parametrize(
    ("field", "first", "other"),
    [
        ("unit_price", "12.50", "12.75"),
        ("freight", "15.00", "20.00"),
        ("currency", "GBP", "USD"),
        ("uom", "each", "per 100"),
        ("quantity_available", "500", "250"),
        ("moq", "10", "25"),
        ("lead_time", "3 days", "2 weeks"),
        ("validity", "30 days", "60 days"),
        ("offered_mpn", "AB-123", "AB-124"),
        ("condition", "new", "remanufactured"),
        ("authenticity_claim", "genuine OEM", "aftermarket"),
        ("tax_text", "+ VAT", "exclusive of tax"),
    ],
)
def test_each_kind_of_field_can_disagree(field: str, first: str, other: str) -> None:
    found = _only(diff_readings(_reading(**{field: first}), _reading(**{field: other})))
    assert found == Finding.of("readings_disagree", field, name=field, first=first, other=other)


@pytest.mark.parametrize("field", CRITICAL_FIELDS)
@pytest.mark.parametrize("blank", [None, "", "   "])
def test_blank_against_value_is_reading_missing(field: str, blank: str | None) -> None:
    expected = Finding.of("reading_missing", field, name=field, first=BASE[field])
    assert diff_readings(_reading(**{field: blank}), _reading()) == (expected,)
    assert diff_readings(_reading(), _reading(**{field: blank})) == (expected,)


@pytest.mark.parametrize("field", CRITICAL_FIELDS)
def test_both_blank_gives_nothing(field: str) -> None:
    assert diff_readings(_reading(**{field: None}), _reading(**{field: "  "})) == ()


@pytest.mark.parametrize(
    ("field", "first", "other"),
    [
        ("unit_price", "12.50", "GBP 12.50"),
        ("unit_price", "12.5", "12.50"),
        ("unit_price", "1,234.50", "1234.50"),
        ("freight", "10", "10.00"),
        ("currency", "gbp", " GBP "),
        ("uom", "per each", "EA"),
        ("uom", "/100", "per 100"),
        ("lead_time", "3 days", "three days"),
        ("lead_time", "2 weeks", "14 days"),
        ("validity", "30 days", "30 Days"),
        ("offered_mpn", "ab 123-x", "AB123-X"),
        ("condition", "New  Stock", "new stock"),
        ("tax_text", "Inc. VAT", "inc. vat"),
    ],
)
def test_formatting_differences_that_normalise_equal_give_nothing(
    field: str, first: str, other: str
) -> None:
    assert diff_readings(_reading(**{field: first}), _reading(**{field: other})) == ()


def test_currency_tokens_that_differ_disagree() -> None:
    found = _only(diff_readings(_reading(unit_price="GBP 12.50"), _reading(unit_price="USD 12.50")))
    assert found == Finding.of(
        "readings_disagree", "unit_price", name="unit_price", first="GBP 12.50", other="USD 12.50"
    )


def test_currency_token_case_is_ignored_and_a_missing_token_is_compatible() -> None:
    assert diff_readings(_reading(unit_price="gbp 12.50"), _reading(unit_price="GBP 12.50")) == ()
    assert diff_readings(_reading(unit_price="12.50"), _reading(unit_price="USD 12.50")) == ()


@pytest.mark.parametrize(
    ("field", "unreadable", "readable"),
    [
        ("unit_price", "approx 12.50", "12.50"),
        ("freight", "free", "15.00"),
        ("lead_time", "soon", "3 days"),
        ("validity", "call", "30 days"),
    ],
)
def test_one_unparseable_reading_counts_as_blank(
    field: str, unreadable: str, readable: str
) -> None:
    expected = Finding.of("reading_missing", field, name=field, first=readable)
    with_text = _reading(**{field: readable})
    assert diff_readings(_reading(**{field: unreadable}), with_text) == (expected,)
    assert diff_readings(with_text, _reading(**{field: unreadable})) == (expected,)


def test_unit_of_measure_the_parser_cannot_read_is_compared_as_text() -> None:
    found = _only(diff_readings(_reading(uom="box"), _reading(uom="each")))
    assert found == Finding.of("readings_disagree", "uom", name="uom", first="box", other="each")
    assert diff_readings(_reading(uom="box"), _reading(uom="BOX ")) == ()


def test_two_unreadable_readings_are_compared_as_text() -> None:
    assert diff_readings(_reading(lead_time="call us"), _reading(lead_time="CALL  US")) == ()
    found = _only(diff_readings(_reading(lead_time="call us"), _reading(lead_time="ask sales")))
    assert found == Finding.of(
        "readings_disagree", "lead_time", name="lead_time", first="call us", other="ask sales"
    )


@pytest.mark.parametrize("hostile", HOSTILE)
def test_vendor_text_that_is_not_plain_is_never_shown(hostile: str) -> None:
    found = _only(diff_readings(_reading(condition=hostile), _reading(condition="used")))
    assert found.value("first") == NOT_SHOWN
    assert found.value("other") == "used"
    assert hostile not in explain(found)


def test_unreadable_vendor_text_is_dropped_and_the_other_reading_is_shown() -> None:
    found = _only(
        diff_readings(
            _reading(unit_price="https://vendor.example/p"),
            _reading(unit_price="12.50"),
        )
    )
    assert found == Finding.of("reading_missing", "unit_price", name="unit_price", first="12.50")
    assert "vendor" not in explain(found)


def test_severity_comes_from_the_catalogue_and_text_is_templated() -> None:
    disagree = _only(diff_readings(_reading(moq="10"), _reading(moq="11")))
    missing = _only(diff_readings(_reading(moq=None), _reading(moq="11")))
    assert disagree.severity == Severity.REVIEW
    assert missing.severity == Severity.FLAG
    assert explain(disagree) == (
        "The two readings of this quote disagree on moq: 10 and 11. "
        "A person must check the quote text."
    )


def test_findings_are_sorted_by_field_and_code_and_repeatable() -> None:
    a = _reading(unit_price="12.50", currency="GBP", lead_time="soon")
    b = _reading(unit_price="13.00", currency="USD", lead_time="3 days", moq=None)
    first = diff_readings(a, b)
    assert [(f.field, f.code) for f in first] == [
        ("currency", "readings_disagree"),
        ("lead_time", "reading_missing"),
        ("moq", "reading_missing"),
        ("unit_price", "readings_disagree"),
    ]
    assert diff_readings(a, b) == first


def test_critical_fields_are_every_extracted_quote_field() -> None:
    assert set(CRITICAL_FIELDS) == set(ExtractedQuote.model_fields)
    assert set(BASE) == set(CRITICAL_FIELDS)


@pytest.mark.parametrize(
    ("a", "b"),
    [("£12.50", "GBP 12.50"), ("$12.50", "USD 12.50"), ("$12.50", "CAD 12.50"),
     ("€12.50", "eur 12.50"), ("US$12.50", "USD 12.50")],
)
def test_currency_symbols_and_codes_for_the_same_currency_agree(a: str, b: str) -> None:
    assert diff_readings(_reading(unit_price=a), _reading(unit_price=b)) == ()


@pytest.mark.parametrize(
    ("a", "b"), [("£12.50", "USD 12.50"), ("£12.50", "€12.50"), ("GBP 12.50", "EUR 12.50")]
)
def test_different_currencies_still_disagree(a: str, b: str) -> None:
    (f,) = diff_readings(_reading(unit_price=a), _reading(unit_price=b))
    assert f.code == "readings_disagree"


@pytest.mark.parametrize(("a", "b"), [("£", "GBP"), ("$", "USD"), ("US$", "usd"), ("$", "MXN")])
def test_the_currency_field_compares_what_the_tokens_mean(a: str, b: str) -> None:
    assert diff_readings(_reading(currency=a), _reading(currency=b)) == ()


def test_the_currency_field_disagrees_for_different_currencies() -> None:
    (f,) = diff_readings(_reading(currency="£"), _reading(currency="USD"))
    assert (f.code, f.field) == ("readings_disagree", "currency")

