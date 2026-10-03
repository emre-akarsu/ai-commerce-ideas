"""Profile-level checks for the UK corrections made after the second research round."""

from __future__ import annotations

from pathlib import Path

import pytest

from aiplat.profile import load_profile

UK, SCOTLAND, NI, US = (load_profile(i).profile for i in ("uk", "uk-scotland", "uk-ni", "us"))


def test_uk_never_assumes_a_vat_basis_and_asks_the_supplier() -> None:
    assert UK.tax.unknown_basis == "flag_require_approval"
    assert UK.tax.quote_basis_default == "ex_tax"  # market norm for display, not applied to silent quotes
    assert UK.tax.ask_basis_in_rfq is True


def test_other_profiles_do_not_ask_and_us_keeps_its_policy() -> None:
    assert US.tax.ask_basis_in_rfq is False
    assert US.tax.unknown_basis == "assume_default_flag"  # unchanged US behaviour


@pytest.mark.parametrize("regional", [SCOTLAND, NI], ids=["scotland", "ni"])
def test_regional_profiles_inherit_the_uk_vat_policy(regional) -> None:  # type: ignore[no-untyped-def]
    assert regional.tax == UK.tax


@pytest.mark.parametrize("regional", [SCOTLAND, NI], ids=["scotland", "ni"])
def test_regional_notices_start_with_the_uk_notices(regional) -> None:  # type: ignore[no-untyped-def]
    """Lists are replaced, not merged, so a regional profile repeats the UK notices; this keeps them in step."""
    n = len(UK.legal.notices)
    assert tuple(regional.legal.notices[:n]) == tuple(UK.legal.notices)
    assert len(regional.legal.notices) == n + 1  # plus its own note on the regional legal text


def test_uk_regulator_is_named_correctly_and_notices_cover_the_research() -> None:
    assert "Information Commission" in UK.legal.contact_data_regime
    assert "Data (Use and Access) Act 2025" in UK.legal.contact_data_regime
    text = " ".join(UK.legal.notices)
    for needle in ("PECR", "treated as unknown", "supplier-declared", "SI 2015/17", "transfer mechanism"):
        assert needle in text, needle
    assert "ex-VAT unless stated" not in text  # the old wording assumed ex-VAT


def _vat_notice(profile) -> str:  # type: ignore[no-untyped-def]
    (notice,) = [n for n in profile.legal.notices if "whether VAT is included" in n]
    return str(notice)


@pytest.mark.parametrize("profile", [UK, SCOTLAND, NI], ids=["uk", "scotland", "ni"])
def test_the_vat_notice_leaves_the_legal_position_open(profile) -> None:  # type: ignore[no-untyped-def]
    """A red-team review found the old claim ("in contract law a price silent on VAT is normally
    VAT-inclusive") overstated: the one authority found is a land-sale case about conflicting
    conditions, and nothing found covers B2B parts quotations. The notice now says only what the product
    does (unknown, sent to a human) and that the law is unsettled."""
    notice = _vat_notice(profile)
    assert "treated as unknown and sent to a human" in notice
    assert "unsettled" in notice and "confirm the basis with the supplier" in notice
    for claim in ("VAT-inclusive", "VAT-exclusive", "normally", "contract law", "presum", "default"):
        assert claim not in notice, claim
    assert "construction reverse charge is not determined by the product" in notice


def test_no_profile_comment_or_architecture_doc_states_the_contract_default_as_settled() -> None:
    root = Path(__file__).resolve().parents[2]
    claims = ("normally VAT-inclusive", "VAT-inclusive in contract law", "CLP Holding",
              "contract-law default", "legal default for a price")
    paths = [*(root / "profiles").glob("*.yaml"), *(root / "docs/architecture").glob("*.md"),
             *(root / "packages").rglob("*.py"), *(root / "employees").rglob("*.py"),
             *(root / "apps").rglob("*.py"), *(root / "tests").rglob("test_*.py")]
    for path in paths:
        if path == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8")
        assert not [c for c in claims if c in text], (path.name, [c for c in claims if c in text])


def test_the_unknown_basis_behaviour_is_unchanged() -> None:
    """Wording only: the flags and keys that make an unstated basis go to a human did not move."""
    assert UK.tax.unknown_basis == "flag_require_approval" and UK.tax.ask_basis_in_rfq is True
    assert UK.tax.quote_basis_default == "ex_tax"
    assert SCOTLAND.tax == UK.tax == NI.tax


def test_marketing_email_remains_off_everywhere() -> None:
    assert UK.legal.marketing_email_allowed is False and US.legal.marketing_email_allowed is False
