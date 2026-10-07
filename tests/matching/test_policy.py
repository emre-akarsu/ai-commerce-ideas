"""GatePolicy: defaults equal the deployment profile's, no off switch for the hard rules."""

from __future__ import annotations

from decimal import Decimal

import pytest

from aiplat.profile import MatchingPolicy
from components.matching.policy import GatePolicy, PolicyError


def test_defaults_equal_the_profile_defaults() -> None:
    profile = MatchingPolicy()
    policy = GatePolicy()
    for key in ("auto_accept_min_score", "auto_accept_min_lead", "reject_below_score",
                "retrieve_top_k", "judge_top_k", "judge_examples", "review_show_top",
                "llm_cost_ceiling_per_1000_lines"):
        assert getattr(policy, key) == getattr(profile, key), key
    assert (policy.auto_accept_min_score, policy.auto_accept_min_lead,
            policy.reject_below_score) == (Decimal("0.75"), Decimal("0.05"), Decimal("0.35"))


def test_from_mapping_accepts_the_whole_resolved_profile_section() -> None:
    policy = GatePolicy.from_mapping(MatchingPolicy().model_dump())
    assert policy == GatePolicy()
    tuned = GatePolicy.from_mapping({"auto_accept_min_score": "0.8", "retrieve_top_k": 20,
                                     "group_band": "0.08"})
    assert tuned.auto_accept_min_score == Decimal("0.8") and tuned.retrieve_top_k == 20
    assert tuned.group_band == Decimal("0.08")


@pytest.mark.parametrize("key", ["require_zero_failed_checks",
                                 "quantity_size_ambiguity_forces_review"])
def test_the_hard_rules_cannot_be_switched_off(key: str) -> None:
    with pytest.raises(PolicyError, match="hard rule"):
        GatePolicy.from_mapping({key: False})
    assert GatePolicy.from_mapping({key: True}) == GatePolicy()


@pytest.mark.parametrize(
    "bad",
    [
        {"surprise": 1},
        {"auto_accept_min_score": 0.8},  # floats are refused
        {"auto_accept_min_score": "0.4"},
        {"reject_below_score": "0.8"},
        {"retrieve_top_k": 3},
        {"judge_top_k": 60},
        {"retrieve_top_k": True},
        {"review_show_top": 0},
        {"llm_cost_ceiling_per_1000_lines": "0"},
        {"group_band": "0.9"},
        {"auto_accept_min_lead": "nope"},
    ],
)
def test_bad_values_are_refused(bad: dict[str, object]) -> None:
    with pytest.raises(PolicyError):
        GatePolicy.from_mapping(bad)


def test_snapshot_is_text_for_the_audit_trail() -> None:
    snap = GatePolicy().snapshot()
    assert snap["auto_accept_min_score"] == "0.75" and snap["retrieve_top_k"] == "50"
    assert all(isinstance(v, str) for v in snap.values())
