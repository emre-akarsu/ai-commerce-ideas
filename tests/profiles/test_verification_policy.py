"""Profile checks for the `verification:` thresholds and the review-event retention window."""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest
import yaml
from pydantic import ValidationError

from aiplat.profile import (
    PROFILES_DIR,
    ProfileError,
    RetentionPolicy,
    VerificationPolicy,
    _chain,
    load_profile,
    resolve,
)
from components.verify.config import VerifyConfig

ALL = ("uk", "uk-scotland", "uk-ni", "us")


@pytest.mark.parametrize("pid", ALL)
def test_every_profile_carries_the_verification_defaults(pid: str) -> None:
    assert load_profile(pid).profile.verification == VerificationPolicy()


def test_the_profile_block_has_exactly_the_verify_config_fields() -> None:
    assert set(VerificationPolicy.model_fields) == {f.name for f in dataclasses.fields(VerifyConfig)}


def test_the_profile_block_builds_the_verify_config_with_its_defaults() -> None:
    block = load_profile("uk").profile.verification.model_dump(mode="json")
    assert VerifyConfig.from_mapping(block) == VerifyConfig()


@pytest.mark.parametrize(
    ("field", "raw"),
    [
        ("arith_abs_tolerance", "-0.01"),
        ("arith_rel_tolerance", "0.2"),
        ("vat_rel_tolerance", "0.11"),
        ("price_jump_ratio", "1"),
        ("unit_basis_tolerance", "0.6"),
        ("quantity_ratio", "1"),
        ("min_history_points", 0),
        ("min_history_points", 51),
    ],
)
def test_an_out_of_range_verification_value_is_refused(field: str, raw: object) -> None:
    with pytest.raises(ValidationError):
        VerificationPolicy(**{field: raw})


def test_the_verification_bounds_are_inclusive_at_the_edges() -> None:
    edge = VerificationPolicy(
        arith_abs_tolerance="0",
        arith_rel_tolerance="0.1",
        vat_rel_tolerance="0.1",
        price_jump_ratio="1.01",
        unit_basis_tolerance="0.5",
        quantity_ratio="1.01",
        min_history_points=50,
    )
    assert edge.arith_rel_tolerance == Decimal("0.1") and edge.min_history_points == 50


def test_the_verification_block_is_frozen_and_refuses_unknown_keys() -> None:
    with pytest.raises(ValidationError):
        VerificationPolicy(price_jumpy_ratio="2")  # a typo must not be silently ignored
    policy = VerificationPolicy()
    with pytest.raises(ValidationError):
        policy.price_jump_ratio = Decimal("2")


@pytest.mark.parametrize(
    "override",
    [{"verification": {"price_jump_ratio": "1"}}, {"retention": {"review_event_days": 731}}],
)
def test_the_loader_refuses_an_out_of_range_profile_value(override: dict) -> None:
    chain = _chain("uk", PROFILES_DIR)
    name, data = chain[-1]
    with pytest.raises(ProfileError):
        resolve([*chain[:-1], (name, {**data, **override})])


def test_review_event_retention_defaults_to_180_days() -> None:
    assert RetentionPolicy().review_event_days == 180
    assert load_profile("uk").profile.retention.review_event_days == 180


@pytest.mark.parametrize("days", [0, 6, 731])
def test_review_event_retention_refuses_values_outside_7_to_730_days(days: int) -> None:
    with pytest.raises(ValidationError):
        RetentionPolicy(review_event_days=days)


@pytest.mark.parametrize("days", [7, 730])
def test_review_event_retention_accepts_the_bounds(days: int) -> None:
    assert RetentionPolicy(review_event_days=days).review_event_days == days


@pytest.mark.parametrize(
    "override",
    [{"verification": {"price_jump_ratio": "2"}}, {"verification": {"min_history_points": 1}}],
)
def test_a_tenant_cannot_override_the_verification_thresholds(override: dict) -> None:
    chain = _chain("uk", PROFILES_DIR)
    with pytest.raises(ProfileError, match="may not override"):
        resolve(chain, tenant_overrides=override, tenant_id="t1")


@pytest.mark.parametrize("name", ["base", "_template"])
def test_the_base_and_template_carry_the_code_defaults(name: str) -> None:
    raw = yaml.safe_load((PROFILES_DIR / f"{name}.yaml").read_text(encoding="utf-8"))
    assert VerificationPolicy(**raw["verification"]) == VerificationPolicy()
    assert RetentionPolicy(**raw["retention"]).review_event_days == 180
