"""Profile-level checks for the UK corrections made after the second research round."""

from __future__ import annotations

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
    for needle in ("PECR", "VAT-inclusive", "supplier-declared", "SI 2015/17", "transfer mechanism"):
        assert needle in text, needle
    assert "ex-VAT unless stated" not in text  # the old wording assumed ex-VAT


def test_marketing_email_remains_off_everywhere() -> None:
    assert UK.legal.marketing_email_allowed is False and US.legal.marketing_email_allowed is False
