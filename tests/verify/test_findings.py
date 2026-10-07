"""Findings: catalogue integrity, safe values, templated explanations."""

from __future__ import annotations

import re
from decimal import Decimal
from string import Formatter

import pytest

from components.verify.config import VerifyConfig
from components.verify.findings import CATALOGUE, NOT_SHOWN, Finding, Severity, explain, safe_value


def test_every_template_uses_only_plain_placeholders_and_no_links() -> None:
    for code, (sev, template) in CATALOGUE.items():
        assert isinstance(sev, Severity)
        assert not re.search(r"https?:|www\.|<[^>]*>", template), code
        for _, name, spec, conv in Formatter().parse(template):
            assert name is None or (re.fullmatch(r"[a-z][a-z0-9_]*", name) and not spec and not conv)


def test_explain_fills_values_and_shows_missing_ones_as_not_shown() -> None:
    f = Finding.of("line_total_mismatch", "total", total="100.00", quantity="10",
                   unit_price="9.00", expected="90.00")
    assert explain(f) == "The line total 100.00 is not 10 x 9.00 (90.00)."
    g = Finding.of("line_total_mismatch", "total", total="100.00")
    assert NOT_SHOWN in explain(g)


@pytest.mark.parametrize("bad", ["see https://x.example", "a@b.co", "<b>x</b>", "x" * 61, "a\x00b",
                                 "{name}", "", "   "])
def test_unplain_values_are_replaced_never_shown(bad: str) -> None:
    assert safe_value(bad) == NOT_SHOWN
    f = Finding.of("negative_value", "price", name="price", value=bad)
    assert f.value("value") == NOT_SHOWN


def test_direct_construction_refuses_unplain_values_and_unknown_codes() -> None:
    with pytest.raises(ValueError):
        Finding("negative_value", Severity.REVIEW, "price", (("value", "http://x.example"),))
    with pytest.raises(ValueError):
        Finding.of("made_up_code", "price")
    with pytest.raises(ValueError):
        Finding("negative_value", "review", "price")  # type: ignore[arg-type]


def test_default_severities_are_review_for_number_and_shadow_checks_and_flag_for_history() -> None:
    assert CATALOGUE["line_total_mismatch"][0] is Severity.REVIEW
    assert CATALOGUE["readings_disagree"][0] is Severity.REVIEW
    assert CATALOGUE["price_jump_vs_last_paid"][0] is Severity.FLAG
    assert Finding.of("price_jump_vs_last_paid", "price").severity is Severity.FLAG


def test_config_defaults_validate_and_from_mapping_refuses_unknown_keys() -> None:
    assert VerifyConfig().price_jump_ratio == Decimal("1.5")
    cfg = VerifyConfig.from_mapping({"price_jump_ratio": "2", "min_history_points": 3})
    assert cfg.price_jump_ratio == Decimal("2") and cfg.min_history_points == 3
    with pytest.raises(ValueError):
        VerifyConfig.from_mapping({"nope": "1"})
    with pytest.raises(ValueError):
        VerifyConfig.from_mapping({"price_jump_ratio": "1"})
