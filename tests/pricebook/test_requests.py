"""Request-your-price-file drafts: templated text only; unknown placeholders and unsafe values
are refused; no URL, no HTML, no legal footer, nothing sent."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pytest
import yaml

from components.pricebook import (
    ACCOUNT_REFERENCE_MISSING,
    PLACEHOLDERS,
    MerchantBook,
    MerchantStatus,
    RequestContext,
    RequestTemplate,
    RequestTemplateError,
    VatSummary,
    draft_request,
    draft_requests,
)
from components.pricebook.models import Coverage

from .conftest import DATA, T0

CTX = RequestContext("Alex Example", "Example Bathrooms Ltd (fictional)",
                     {"m-a": "ACC-A-1001"})
URL = re.compile(r"https?:|www\.|://|\.(com|net|org|co\.uk)\b", re.IGNORECASE)
HTML = re.compile(r"<[^>]*>|&[#a-z0-9]+;", re.IGNORECASE)


def template_data() -> dict[str, Any]:
    return yaml.safe_load((DATA / "request_templates.yaml").read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def merchant(mid: str = "m-a", name: str = "Alpha Supplies (fictional)",
             status: MerchantStatus = MerchantStatus.MISSING) -> MerchantBook:
    return MerchantBook(
        merchant_id=mid, name=name, status=status, status_reason_code="x", status_reason="x",
        ladder_level=0, source_kinds=(), visibility="tenant_private", attested=False,
        offers_count=0, firm_offers_count=0, indicative_offers_count=0, quarantined_count=0,
        as_of=None, valid_until_earliest=None, valid_until_latest=None,
        vat_basis=VatSummary.UNKNOWN, vat_counts=(), offers_current=0, offers_stale=0,
        offers_expired=0, dominant_source_kind=None, max_age_hours=None, next_refresh_due=None,
        coverage=Coverage(0, 0))


@pytest.fixture(scope="module")
def template() -> RequestTemplate:
    return RequestTemplate.from_mapping(template_data())


def test_the_shipped_template_loads_and_fills_the_four_placeholders(
        template: RequestTemplate) -> None:
    d = draft_request(template, merchant(), CTX)
    assert d.merchant_id == "m-a" and d.status == "draft_not_sent"
    assert d.subject == "Price file request for Example Bathrooms Ltd (fictional), account ACC-A-1001"
    assert d.body.startswith("Dear Alpha Supplies (fictional) account team,")
    assert d.body.rstrip().endswith("Account reference: ACC-A-1001")
    assert "Alex Example\nExample Bathrooms Ltd (fictional)" in d.body
    assert "{" not in d.body and "}" not in d.body  # every placeholder was filled


def test_the_draft_asks_for_everything_the_step_requires(template: RequestTemplate) -> None:
    body = draft_request(template, merchant(), CTX).body.lower()
    for needle in ("csv or excel", "valid from and valid until", "include vat or exclude",
                   "product code", "manufacturer part number", "gtin", "pack size",
                   "delivery terms", "delivery is free", "load the file into a purchasing tool"):
        assert needle in body, needle


@pytest.mark.parametrize("status", [MerchantStatus.MISSING, MerchantStatus.STALE,
                                    MerchantStatus.INDICATIVE_ONLY])
def test_each_status_has_its_own_subject_and_intro(template: RequestTemplate,
                                                   status: MerchantStatus) -> None:
    d = draft_request(template, merchant(status=status), CTX)
    intro = {"missing": "do not yet hold", "stale": "out of date",
             "indicative_only": "only hold public list prices"}[status.value]
    assert intro in d.body


def test_no_draft_is_made_for_a_merchant_whose_prices_are_current(
        template: RequestTemplate) -> None:
    with pytest.raises(RequestTemplateError):
        draft_request(template, merchant(status=MerchantStatus.CURRENT), CTX)
    drafts = draft_requests(template, (merchant("m-a", status=MerchantStatus.CURRENT),
                                       merchant("m-b", status=MerchantStatus.STALE)), CTX)
    assert [d.merchant_id for d in drafts] == ["m-b"]


def test_a_missing_account_reference_is_a_visible_marker_not_a_guess(
        template: RequestTemplate) -> None:
    d = draft_request(template, merchant("m-b"), CTX)
    assert ACCOUNT_REFERENCE_MISSING in d.body and ACCOUNT_REFERENCE_MISSING in d.subject


def test_a_draft_has_no_url_no_html_and_no_legal_footer(template: RequestTemplate) -> None:
    for status in (MerchantStatus.MISSING, MerchantStatus.STALE, MerchantStatus.INDICATIVE_ONLY):
        d = draft_request(template, merchant(status=status), CTX)
        for text in (d.subject, d.body):
            assert not URL.search(text), text
            assert not HTML.search(text), text
            assert "http" not in text.lower() and "<" not in text and ">" not in text
        low = d.body.lower()
        assert not any(w in low for w in ("unsubscribe", "confidential", "registered office",
                                          "disclaimer", "this email"))


def test_an_unknown_placeholder_is_refused_in_every_text_field() -> None:
    for path in (("greeting",), ("closing",), ("sign_off",), ("ask_heading",),
                 ("asks", 0), ("variants", "missing", "subject"),
                 ("variants", "stale", "intro")):
        raw = template_data()
        target: Any = raw
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = "Hello {supplier_email}, {merchant_name}"
        with pytest.raises(RequestTemplateError, match="unknown placeholder"):
            RequestTemplate.from_mapping(raw)


@pytest.mark.parametrize("bad", ["{merchant_name!r}", "{merchant_name:>10}", "{merchant_name.x}",
                                 "{0}", "{}", "{{literal}}", "oops {", "}"])
def test_format_tricks_and_stray_braces_are_refused(bad: str) -> None:
    raw = template_data()
    raw["greeting"] = bad
    with pytest.raises(RequestTemplateError):
        RequestTemplate.from_mapping(raw)


@pytest.mark.parametrize("bad", [
    "See http://example.com for details", "visit www.example.org", "<b>hello</b>",
    "mail a@b.co.uk", "[click here](x)", "line &amp; more", "bad\x07control", "pipe | here"])
def test_links_markup_and_addresses_in_a_template_are_refused(bad: str) -> None:
    raw = template_data()
    raw["closing"] = bad
    with pytest.raises(RequestTemplateError):
        RequestTemplate.from_mapping(raw)


def test_a_template_with_extra_or_missing_keys_is_refused() -> None:
    raw = template_data()
    raw["footer"] = "Legal footer text"
    with pytest.raises(RequestTemplateError, match="unknown template keys"):
        RequestTemplate.from_mapping(raw)
    raw = template_data()
    del raw["variants"]["stale"]
    with pytest.raises(RequestTemplateError):
        RequestTemplate.from_mapping(raw)


@pytest.mark.parametrize("bad", [
    "Evil Ltd http://evil.example", "www.evil.com", "<script>x</script>", "A & B &lt;",
    "name@example.com", "two\nlines", "tab\there", "{merchant_name}", "x" * 121, "", "   ",
    "see evil.co.uk", "[link]"])
def test_unsafe_placeholder_values_are_refused_not_repaired(
        template: RequestTemplate, bad: str) -> None:
    for ctx in (RequestContext(bad, "Fine Ltd", {}), RequestContext("Fine", bad, {}),
                RequestContext("Fine", "Fine Ltd", {"m-a": bad})):
        with pytest.raises(RequestTemplateError):
            draft_request(template, merchant(), ctx)
    with pytest.raises(RequestTemplateError):
        draft_request(template, merchant(name=bad), CTX)


def test_the_only_placeholders_are_the_four_documented_ones() -> None:
    assert PLACEHOLDERS == {"merchant_name", "buyer_name", "buyer_company", "account_reference"}
    used = set(re.findall(r"\{(\w+)\}", (DATA / "request_templates.yaml").read_text("utf-8")))
    assert used <= PLACEHOLDERS


def test_the_package_has_no_model_text_and_no_sender() -> None:
    import components.pricebook.requests as mod
    source = open(mod.__file__, encoding="utf-8").read()  # noqa: SIM115
    assert not re.search(r"complete_json|LLMProvider|\.deliver\b|send_service|MailTransport",
                         source)
    assert isinstance(T0, datetime)
