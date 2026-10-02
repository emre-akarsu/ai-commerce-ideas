"""Profile layer: merge, provenance, invariants (config may localise/tighten, never loosen)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from aiplat.profile import (
    PROFILES_DIR,
    TENANT_OVERRIDABLE,
    ProfileError,
    diff,
    load_profile,
    main,
)

LEAVES = sorted(
    p.stem for p in PROFILES_DIR.glob("*.yaml") if p.stem not in {"base", "_template"}
)


def write(root: Path, name: str, data: dict) -> None:
    (root / f"{name}.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")


BASE = {
    "profile_version": 1,
    "approvals": {"threshold": "500"},
}
LEAF = {
    "extends": "base",
    "locale": {"region": "XX"},
    "money": {"base_currency": "USD", "accepted_currencies": ["USD"]},
    "legal": {
        "jurisdiction": "Testland",
        "contact_data_regime": "none",
        "disclosure_footer": "Prepared with an AI assistant. It cannot accept terms; only {buyer} binds.",
    },
    "billing": {"currency": "USD"},
}


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    write(tmp_path, "base", BASE)
    write(tmp_path, "leaf", LEAF)
    return tmp_path


def mutate(root: Path, **sections: dict) -> None:
    data = yaml.safe_load((root / "leaf.yaml").read_text())
    for k, v in sections.items():
        if isinstance(v, dict) and isinstance(data.get(k), dict):
            data[k].update(v)
        else:
            data[k] = v
    write(root, "leaf", data)


def test_layers_provenance_and_digest(root: Path) -> None:
    r = load_profile("leaf", root=root)
    assert r.layers == ("base", "leaf")
    assert r.provenance["approvals.threshold"] == "base"
    assert r.provenance["money.base_currency"] == "leaf"
    assert r.profile.approvals.threshold == Decimal("500")
    assert load_profile("leaf", root=root).digest == r.digest  # deterministic
    mutate(root, approvals={"threshold": "250"})
    assert load_profile("leaf", root=root).digest != r.digest


def test_extends_cycle_and_missing_are_rejected(root: Path) -> None:
    write(root, "a", {"extends": "b"})
    write(root, "b", {"extends": "a"})
    with pytest.raises(ProfileError, match="cycle"):
        load_profile("a", root=root)
    with pytest.raises(ProfileError, match="not found"):
        load_profile("nope", root=root)


@pytest.mark.parametrize(
    "section,value,match",
    [
        ("legal", {"disclosure_footer": "Hello"}, "disclosure_footer"),
        ("legal", {"disclosure_footer": "AI assistant cannot accept terms"}, "buyer"),
        ("legal", {"marketing_email_allowed": True}, "marketing_email_allowed"),
        ("comms", {"followups_default_enabled": True}, "followups_default_enabled"),
        ("comms", {"alias_domain_required": False}, "alias_domain_required"),
        ("comms", {"max_vendors": 50}, "max_vendors"),
        ("tiers", {"enabled": ["B"]}, "tier A"),
        ("tiers", {"enabled": ["A", "D"]}, "enabled"),
        ("tiers", {"unlock_c_after_confirmed": 5}, "unlock_c_after_confirmed"),
        ("tiers", {"safety_critical_forces_d": False}, "safety_critical_forces_d"),
        ("parts", {"require_licensed_sources_in_production": False}, "require_licensed"),
        ("approvals", {"send_approval_ttl_minutes": 100000}, "send_approval_ttl_minutes"),
        ("approvals", {"threshold": "0"}, "threshold"),
        ("money", {"accepted_currencies": ["EUR"]}, "base_currency"),
        ("billing", {"currency": "JPY"}, "billing.currency"),
        ("unknown_section", {"x": 1}, "unknown_section"),
    ],
)
def test_invariants_cannot_be_loosened(root: Path, section: str, value: dict, match: str) -> None:
    mutate(root, **{section: value})
    with pytest.raises(ProfileError, match=match):
        load_profile("leaf", root=root)


def test_tenant_overrides_are_whitelisted_and_bounded(root: Path) -> None:
    r = load_profile(
        "leaf", root=root, tenant_id="acme", tenant_overrides={"approvals": {"threshold": "250"}}
    )
    assert r.profile.approvals.threshold == Decimal("250")
    assert r.layers[-1] == "tenant:acme"
    assert r.provenance["approvals.threshold"] == "tenant:acme"
    for bad in (
        {"legal": {"disclosure_footer": "x"}},
        {"comms": {"followups_default_enabled": True}},
        {"money": {"base_currency": "EUR"}},
        {"tiers": {"enabled": ["A"]}},
    ):
        with pytest.raises(ProfileError, match="may not override"):
            load_profile("leaf", root=root, tenant_overrides=bad)
    with pytest.raises(ProfileError):  # whitelisted key but out of bounds
        load_profile("leaf", root=root, tenant_overrides={"comms": {"max_vendors": 99}})


def test_overridable_keys_exclude_every_safety_setting() -> None:
    forbidden = ("legal", "tiers", "money", "tax", "parts", "locale", "alias", "followups")
    assert not [k for k in TENANT_OVERRIDABLE if k.startswith(forbidden)]


@pytest.mark.parametrize("pid", LEAVES)
def test_every_shipped_profile_validates(pid: str) -> None:
    r = load_profile(pid)
    assert r.profile.id == pid
    assert "{buyer}" in r.profile.legal.disclosure_footer
    assert r.profile.billing.currency in r.profile.money.accepted_currencies


def test_cli_validate_show_diff(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "us"]) == 0
    assert "OK us@" in capsys.readouterr().out
    assert main(["validate", "base"]) == 1  # abstract
    assert main(["show", "us"]) == 0
    assert main(["bogus"]) == 2
    assert diff(load_profile("us"), load_profile("us")) == {}
