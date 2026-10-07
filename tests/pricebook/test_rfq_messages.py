"""Quote-request drafts: one aggregated message per supplier by default, individual per-line
messages on request; templated text, no URL or markup, nothing sent."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

import pytest
import yaml

from components.pricebook import (
    ACCOUNT_REFERENCE_MISSING,
    RequestContext,
    RequestTemplateError,
    RfqGapGroup,
    RfqGapItem,
    RfqMode,
    RfqTemplate,
    draft_rfq_messages,
)

from .conftest import DATA

CTX = RequestContext("Alex Example", "Example Bathrooms Ltd (fictional)", {"m-a": "ACC-A-1001"})
NAMES = {"m-a": "Alpha Supplies (fictional)", "m-b": "Beta Trade (fictional)"}
URL = re.compile(r"https?:|www\.|://|<[^>]*>", re.IGNORECASE)


def tmpl_data() -> dict[str, Any]:
    return yaml.safe_load((DATA / "rfq_templates.yaml").read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def item(rank: int, text: str, q: str = "2") -> RfqGapItem:
    return RfqGapItem(rank, f"l{rank}", f"k{rank}", text, Decimal(q), "nr")


GROUPS = (
    RfqGapGroup("m-a", (item(1, "Basin tap, chrome"), item(2, "Flexible hose 15mm", "4.50"))),
    RfqGapGroup("m-b", (item(2, "Flexible hose 15mm", "4.50"), item(3, "Silicone, white"))),
)


@pytest.fixture(scope="module")
def tmpl() -> RfqTemplate:
    return RfqTemplate.from_mapping(tmpl_data())


def test_default_is_one_message_per_supplier_with_all_its_lines(tmpl: RfqTemplate) -> None:
    msgs = draft_rfq_messages(tmpl, GROUPS, NAMES, CTX)
    assert [m.merchant_id for m in msgs] == ["m-a", "m-b"]
    assert all(m.mode == "per_supplier" and m.status == "draft_not_sent" for m in msgs)
    assert msgs[0].line_ids == ("l1", "l2") and msgs[1].line_ids == ("l2", "l3")
    assert "1. Basin tap, chrome - quantity 2 nr" in msgs[0].body
    assert "2. Flexible hose 15mm - quantity 4.5 nr" in msgs[0].body
    assert msgs[0].subject == "Quote request for 2 items, Example Bathrooms Ltd (fictional), account ACC-A-1001"
    assert ACCOUNT_REFERENCE_MISSING in msgs[1].body


def test_individual_mode_is_one_message_per_line_and_covers_the_same_lines(
        tmpl: RfqTemplate) -> None:
    agg = draft_rfq_messages(tmpl, GROUPS, NAMES, CTX, RfqMode.PER_SUPPLIER)
    ind = draft_rfq_messages(tmpl, GROUPS, NAMES, CTX, RfqMode.PER_ITEM)
    assert len(ind) == 4 and all(len(m.line_ids) == 1 and m.mode == "per_item" for m in ind)
    assert sorted((m.merchant_id, i) for m in agg for i in m.line_ids) == \
        sorted((m.merchant_id, i) for m in ind for i in m.line_ids)
    assert "Quote request for 1 item" in ind[0].subject


def test_no_link_or_markup_and_no_footer(tmpl: RfqTemplate) -> None:
    for mode in RfqMode:
        for m in draft_rfq_messages(tmpl, GROUPS, NAMES, CTX, mode):
            assert not URL.search(m.subject + m.body)


@pytest.mark.parametrize("bad", ["see https://x.example/p", "mail a@b.co.uk", "<b>tap</b>",
                                 "tap {name}", "tap\x00", "", "x" * 400])
def test_unsafe_line_text_is_refused_not_repaired(tmpl: RfqTemplate, bad: str) -> None:
    g = (RfqGapGroup("m-a", (RfqGapItem(1, "l1", None, bad, Decimal("1"), "nr"),)),)
    if bad == "":  # an empty text falls back to the line id, which is plain
        assert "l1" in draft_rfq_messages(tmpl, g, NAMES, CTX)[0].body
    else:
        with pytest.raises(RequestTemplateError):
            draft_rfq_messages(tmpl, g, NAMES, CTX)


def test_template_with_unknown_placeholder_or_link_is_refused() -> None:
    d = tmpl_data()
    d["closing"] = "Thanks {nope}"
    with pytest.raises(RequestTemplateError):
        RfqTemplate.from_mapping(d)
    d = tmpl_data()
    d["closing"] = "See https://example.com"
    with pytest.raises(RequestTemplateError):
        RfqTemplate.from_mapping(d)


def test_a_supplier_with_no_lines_gets_no_message(tmpl: RfqTemplate) -> None:
    for mode in RfqMode:
        assert draft_rfq_messages(tmpl, (RfqGapGroup("m-a", ()),), NAMES, CTX, mode) == ()
