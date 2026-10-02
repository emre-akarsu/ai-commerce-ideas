import pytest

from components.parts.families.registry import (
    DEEP_GROOVE_BALL_BEARING,
    V_BELT,
    FamilySpec,
    UnknownFamilyError,
    get_family,
    list_families,
)


def test_both_r0_families_registered():
    assert set(list_families()) == {DEEP_GROOVE_BALL_BEARING, V_BELT}


def test_bearing_required_and_critical_attributes_match_spec_6_2():
    fam = get_family("deep_groove_ball_bearing")
    assert isinstance(fam, FamilySpec)
    assert fam.critical_attributes == (
        "bore_mm",
        "outer_diameter_mm",
        "width_mm",
        "seal_type",
        "internal_clearance",
        "precision_class",
    )
    assert set(fam.critical_attributes) <= set(fam.required_attributes)
    assert fam.allowed_values["seal_type"] == ("open", "shield", "contact_seal")
    assert {"CN", "C3", "C4", "C2"} <= set(fam.allowed_values["internal_clearance"])


@pytest.mark.parametrize("name", [DEEP_GROOVE_BALL_BEARING, V_BELT])
def test_every_required_attribute_has_exactly_one_question(name):
    fam = get_family(name)
    for attr in fam.required_attributes:
        assert fam.questions[attr].strip().endswith("?")
    assert set(fam.questions) == set(fam.required_attributes)


def test_vbelt_banded_conditional_requirement():
    fam = get_family("v_belt")
    assert "number_of_bands" not in fam.required_for({"banded": "no"})
    assert "number_of_bands" not in fam.required_for({})
    assert "number_of_bands" in fam.required_for({"banded": "yes"})
    assert "number_of_bands" in fam.critical_for({"banded": "yes"})
    assert {"profile", "length_mm", "banded"} <= set(fam.critical_for({}))


def test_unknown_family_is_an_error_not_a_guess():
    with pytest.raises(UnknownFamilyError):
        get_family("hydraulic_hose")
