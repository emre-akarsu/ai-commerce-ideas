"""QuotingConfig is a plain dataclass the caller fills; it holds presentation limits only."""

from __future__ import annotations

import pytest

from components.quoting import QuotingConfig, QuotingConfigError


def test_defaults_and_mapping() -> None:
    assert QuotingConfig() == QuotingConfig.from_mapping({})
    cfg = QuotingConfig.from_mapping({"review_top": 5, "alternatives_max": 0,
                                      "quote_id_prefix": "q-demo"})
    assert (cfg.review_top, cfg.alternatives_max, cfg.quote_id_prefix) == (5, 0, "q-demo")


@pytest.mark.parametrize("bad", [
    {"review_top": 0}, {"review_top": 11}, {"review_top": True}, {"review_top": 2.5},
    {"alternatives_max": -1}, {"quote_id_prefix": ""}, {"quote_id_prefix": "a b"},
    {"quote_id_prefix": "x" * 25}, {"unknown_key": 1}, {"require_zero_failed_checks": False},
])
def test_bad_values_and_unknown_keys_are_refused(bad: dict[str, object]) -> None:
    with pytest.raises(QuotingConfigError):
        QuotingConfig.from_mapping(bad)


def test_the_review_payload_is_capped_by_the_config(bare_ctx) -> None:  # type: ignore[no-untyped-def]
    import dataclasses
    from decimal import Decimal

    from components.quoting import search_best_price
    ctx = dataclasses.replace(bare_ctx, config=QuotingConfig(review_top=2))
    r = search_best_price(ctx, "demo-tenant-a", "grout flexible cement 5kg", Decimal("1"))
    assert r.review is not None and len(r.review.candidates) == 2
