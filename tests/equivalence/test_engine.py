"""Tiered equivalence rules (spec §3). All data is the SYNTHETIC seed; nothing here is real."""

import pytest

from components.core.domain import Attribute, AttrSource, Basis, Candidate, Tier
from components.parts.equivalence.engine import (
    classify_offered,
    find_candidates,
    is_offerable,
)
from components.parts.equivalence.sources import UnsafeSourceError

BEARING = "deep_groove_ball_bearing"
ALL_TIERS = frozenset({Tier.A, Tier.B, Tier.C})

BASE = {
    "bore_mm": "25",
    "outer_diameter_mm": "52",
    "width_mm": "15",
    "seal_type": "contact_seal",
    "internal_clearance": "CN",
    "precision_class": "P0",
}


def mk(base: dict[str, str] | None = None, **over: str) -> dict[str, Attribute]:
    values = dict(BASE if base is None else base)
    values.update(over)
    out: dict[str, Attribute] = {}
    for name, value in values.items():
        out[name] = Attribute(
            name=name,
            value=value,
            unit="mm" if name.endswith("_mm") else None,
            source=AttrSource.USER_INPUT,
            source_ref="test",
        )
    return out


def by_mpn(cands: list[Candidate]) -> dict[str, Candidate]:
    return {c.mpn: c for c in cands}


def tier_of(offered: str, attrs: dict[str, Attribute], **kw) -> tuple[Tier, tuple[str, ...]]:
    return classify_offered(offered, attrs, family=BEARING, **kw)


# ---------------------------------------------------------------- Tier A


def test_tier_a_same_manufacturer_and_mpn():
    attrs = mk(manufacturer="SynthCo Alpha", mpn="AL6205-2RS")
    got = by_mpn(find_candidates(attrs, family=BEARING))
    c = got["AL6205-2RS"]
    assert c.tier is Tier.A
    assert c.basis is Basis.SAME_MPN
    assert c.synthetic is True


def test_tier_a_same_manufacturer_documented_supersession():
    attrs = mk(manufacturer="SynthCo Alpha", mpn="AL6205-2RS-V1")
    c = by_mpn(find_candidates(attrs, family=BEARING))["AL6205-2RS"]
    assert c.tier is Tier.A
    assert c.basis is Basis.SUPERSESSION
    assert c.basis_source == "SYNTHETIC-TEST-SOURCE"
    assert c.basis_date is not None


def test_cross_manufacturer_supersession_is_never_tier_a():
    attrs = mk(
        bore_mm="20", outer_diameter_mm="47", width_mm="14",
        manufacturer="SynthCo Gamma", mpn="GM6204-2RS1",
    )  # fmt: skip
    c = by_mpn(find_candidates(attrs, family=BEARING))["AL6204-2RS"]
    assert c.tier is not Tier.A
    assert tier_of("AL6204-2RS", attrs)[0] is Tier.B  # ISO series equivalence, not "supersession"


def test_different_manufacturer_is_never_tier_a_even_with_the_same_designation():
    attrs = mk(manufacturer="SynthCo Beta", mpn="BT6205-2RSH")
    assert tier_of("AL6205-2RS", attrs)[0] is Tier.B
    assert tier_of("BT6205-2RSH", attrs)[0] is Tier.A


def test_same_mpn_without_a_manufacturer_is_not_tier_a():
    attrs = mk(mpn="AL6205-2RS")
    assert tier_of("AL6205-2RS", attrs)[0] is Tier.B


def test_classify_identity_even_for_parts_outside_the_catalogue():
    attrs = mk(manufacturer="Unlisted Maker", mpn="X-100")
    assert tier_of("x100", attrs, offered_manufacturer="unlisted maker") == (Tier.A, ())
    assert tier_of("X-100", attrs, offered_manufacturer="Another Maker")[0] is Tier.D
    assert tier_of("X-100", attrs)[0] is Tier.D  # manufacturer not stated by the vendor


# ---------------------------------------------------------------- Tier B


def test_tier_b_iso_series_equivalent_has_named_source_and_date():
    got = by_mpn(find_candidates(mk(), family=BEARING))
    c = got["BT6205-2RSH"]
    assert c.tier is Tier.B
    assert c.basis is Basis.STANDARD
    assert c.basis_source == "ISO 15 boundary dimensions"
    assert c.basis_date is not None
    assert c.mismatches == ()


def test_tier_b_documented_manufacturer_crossref_has_source_and_date():
    attrs = mk(manufacturer="SynthCo Alpha", mpn="AL6205-2RS")
    c = by_mpn(find_candidates(attrs, family=BEARING))["BT-HD2552-2RSH"]
    assert c.tier is Tier.B
    assert c.basis is Basis.MANUFACTURER_CROSSREF
    assert c.basis_source == "SYNTHETIC-TEST-SOURCE"
    assert c.basis_date is not None


def test_tier_b_carries_the_load_rating_caveat_without_numbers():
    c = by_mpn(find_candidates(mk(), family=BEARING))["GM6205-2RS1"]
    joined = " ".join(c.caveats)
    assert "load ratings" in joined.lower()
    assert "differ between manufacturers" in joined.lower()
    assert not any(ch.isdigit() for ch in joined if "load ratings" in joined.lower() and False)
    load_caveat = next(x for x in c.caveats if "oad ratings" in x)
    assert not any(ch.isdigit() for ch in load_caveat)  # no invented numbers
    assert any("SYNTHETIC" in x for x in c.caveats)  # seed candidates say so


def test_tier_b_differing_seal_variant_adds_a_templated_caveat():
    attrs = mk(seal_designation="2RS")
    c = by_mpn(find_candidates(attrs, family=BEARING))["BT6205-2RSH"]
    assert c.tier is Tier.B
    assert any("seal_designation differs" in x for x in c.caveats)


def test_candidate_evidence_is_templated_from_data():
    c = by_mpn(find_candidates(mk(), family=BEARING))["BT6205-2RSH"]
    text = "\n".join(c.evidence)
    for name in BASE:
        assert name in text
    assert "ISO 15 boundary dimensions" in text
    # every number in the evidence appears in the request/part data or the source date
    allowed = {"25", "52", "15", "2017", "01", "0", "1"}
    import re

    for num in re.findall(r"\d+", text):
        assert num in allowed or num in "".join(allowed), num


def test_candidates_are_sorted_by_tier_then_mpn():
    cands = find_candidates(
        mk(manufacturer="SynthCo Alpha", mpn="AL6205-2RS"), family=BEARING,
        unlocked_tiers=ALL_TIERS,
    )  # fmt: skip
    order = [c.tier.value for c in cands]
    assert order == sorted(order)
    assert order[0] == "A"


# ---------------------------------------------------------------- near-miss pairs (must NOT match)


@pytest.mark.parametrize(
    ("req", "offered", "mismatch"),
    [
        ({"seal_type": "contact_seal"}, "AL6205-2Z", "seal_type"),  # 2RS vs 2Z
        ({"seal_type": "contact_seal"}, "BT6205-2ZZ", "seal_type"),  # 2RS vs ZZ
        ({"seal_type": "shield"}, "AL6205-2RS", "seal_type"),  # 2Z vs 2RS
        ({"seal_type": "contact_seal"}, "AL6205", "seal_type"),  # sealed vs open
        ({"internal_clearance": "CN"}, "AL6205-2RS-C3", "internal_clearance"),  # CN vs C3
        ({"internal_clearance": "C3"}, "AL6205-2RS", "internal_clearance"),  # C3 vs CN
        ({"precision_class": "P0"}, "AL6205-2RS-P6", "precision_class"),
    ],
)
def test_near_miss_pairs_are_tier_d_with_the_differing_attribute_listed(req, offered, mismatch):
    tier, mismatches = tier_of(offered, mk(**req))
    assert tier is Tier.D
    assert mismatch in mismatches


def test_6205_vs_6305_is_tier_d_on_dimensions():
    tier, mismatches = tier_of("AL6305-2RS", mk())
    assert tier is Tier.D
    assert set(mismatches) == {"outer_diameter_mm", "width_mm"}
    tier, mismatches = tier_of("AL6205-2RS", mk(outer_diameter_mm="62", width_mm="17"))
    assert tier is Tier.D


def test_2rs_vs_2z_is_never_offered_as_a_match_by_find_candidates():
    cands = by_mpn(find_candidates(mk(), family=BEARING, unlocked_tiers=ALL_TIERS))
    for mpn in ("AL6205-2Z", "BT6205-2ZZ", "GM6205-ZZ", "AL6205", "GM6205"):
        assert cands[mpn].tier is Tier.D
        assert "seal_type" in cands[mpn].mismatches
        assert not is_offerable(cands[mpn])
    for mpn in ("AL6205-2RS-C3", "BT6205-2RSH-C3", "GM6205-2RS1-C3"):
        assert cands[mpn].tier is Tier.D
        assert "internal_clearance" in cands[mpn].mismatches


def test_documentation_never_overrides_a_critical_mismatch():
    attrs = mk(manufacturer="SynthCo Alpha", mpn="AL6205-2RS")
    got = by_mpn(find_candidates(attrs, family=BEARING))
    for wrong in ("BT6205-2ZZ", "BT6205-2RSH-C3", "BT6305-2RSH"):
        assert got[wrong].tier is Tier.D, wrong  # a documented cross-reference exists in the seed
        assert got[wrong].mismatches
        assert any("does not override" in x for x in got[wrong].caveats)


# ---------------------------------------------------------------- criticality and unknowns -> D


def test_criticality_forces_tier_d_for_everything_including_the_same_part():
    attrs = mk(manufacturer="SynthCo Alpha", mpn="AL6205-2RS")
    cands = find_candidates(attrs, family=BEARING, criticality=True, unlocked_tiers=ALL_TIERS)
    assert cands, "the engine still reports what it considered"
    assert all(c.tier is Tier.D for c in cands)
    assert all("criticality" in c.mismatches for c in cands)
    assert not any(is_offerable(c) for c in cands)
    assert tier_of("AL6205-2RS", attrs, criticality=True)[0] is Tier.D
    assert "criticality" in tier_of("BT6205-2RSH", mk(), criticality=True)[1]


def test_unknown_critical_attribute_forces_tier_d():
    attrs = mk()
    del attrs["internal_clearance"]
    tier, mismatches = tier_of("BT6205-2RSH", attrs)
    assert (tier, mismatches) == (Tier.D, ("internal_clearance",))
    cands = find_candidates(attrs, family=BEARING, unlocked_tiers=ALL_TIERS)
    assert cands and all(c.tier is Tier.D for c in cands)


def test_empty_value_is_unknown():
    assert tier_of("BT6205-2RSH", mk(seal_type="  "))[0] is Tier.D


def test_model_inference_never_satisfies_a_critical_attribute():
    attrs = mk()
    attrs["seal_type"] = Attribute(
        name="seal_type", value="contact_seal", source=AttrSource.MODEL_INFERENCE, confidence=1.0
    )
    tier, mismatches = tier_of("BT6205-2RSH", attrs)
    assert tier is Tier.D and "seal_type" in mismatches


def test_low_confidence_attribute_is_unknown():
    attrs = mk()
    attrs["internal_clearance"] = Attribute(
        name="internal_clearance", value="CN", source=AttrSource.NAMEPLATE_OCR, confidence=0.4
    )
    assert tier_of("BT6205-2RSH", attrs) == (Tier.D, ("internal_clearance",))


def test_dimension_in_another_unit_is_unknown_not_converted():
    attrs = mk()
    attrs["bore_mm"] = Attribute(
        name="bore_mm", value="1", unit="in", source=AttrSource.USER_INPUT, source_ref="t"
    )
    assert tier_of("BT6205-2RSH", attrs) == (Tier.D, ("bore_mm",))


def test_unrecognised_request_suffix_blocks_any_match():
    attrs = mk(unrecognised_suffix="NR")
    tier, mismatches = tier_of("BT6205-2RSH", attrs)
    assert tier is Tier.D and "unrecognised_suffix" in mismatches


def test_request_without_enough_to_identify_a_part_returns_nothing():
    assert find_candidates({}, family=BEARING) == []


def test_bare_designation_lists_candidates_only_as_tier_d():
    attrs = mk()
    del attrs["seal_type"]
    del attrs["internal_clearance"]
    cands = find_candidates(attrs, family=BEARING, unlocked_tiers=ALL_TIERS)
    assert cands
    assert all(c.tier is Tier.D for c in cands)
    assert all({"seal_type", "internal_clearance"} <= set(c.mismatches) for c in cands)


# ---------------------------------------------------------------- Tier C and marketing cross-refs


def test_marketing_crossref_is_capped_at_tier_c_never_b():
    attrs = mk(manufacturer="SynthCo Alpha", mpn="AL6205-2RS")
    tier, mismatches = tier_of("GM-X2552-2RS", attrs)
    assert (tier, mismatches) == (Tier.C, ())
    hidden = by_mpn(find_candidates(attrs, family=BEARING))  # C not unlocked by default
    assert "GM-X2552-2RS" not in hidden
    shown = by_mpn(find_candidates(attrs, family=BEARING, unlocked_tiers=ALL_TIERS))
    c = shown["GM-X2552-2RS"]
    assert c.tier is Tier.C
    assert c.basis is Basis.MARKETING_CROSSREF
    assert any("marketing" in x.lower() for x in c.caveats)


def test_rule_match_without_a_published_source_is_tier_c_and_hidden_by_default():
    attrs = mk()
    assert tier_of("AL-P2552-2RS", attrs) == (Tier.C, ())
    assert "AL-P2552-2RS" not in by_mpn(find_candidates(attrs, family=BEARING))
    c = by_mpn(find_candidates(attrs, family=BEARING, unlocked_tiers=ALL_TIERS))["AL-P2552-2RS"]
    assert c.tier is Tier.C
    assert c.basis is Basis.RULE_MATCH
    assert any("explicit buyer acceptance" in x for x in c.caveats)


def test_tier_b_needs_both_a_source_and_a_date():
    from components.parts.equivalence.catalogue import Catalogue, CatalogPart, CrossRef

    def part(mpn: str, mfr: str) -> CatalogPart:
        return CatalogPart(
            mpn=mpn, manufacturer=mfr, iso_designation=None,
            attributes=dict(BASE),
        )  # fmt: skip

    def cat(source: str, date):  # type: ignore[no-untyped-def]
        return Catalogue(
            label="SYNTHETIC test", family=BEARING, source_name="SYNTHETIC-TEST-SOURCE",
            synthetic=True, as_of="2026-10-02",
            parts=(part("A-1", "M1"), part("B-1", "M2")),
            crossrefs=(
                CrossRef(
                    from_mpn="A-1", from_manufacturer="M1", to_mpn="B-1", to_manufacturer="M2",
                    basis=Basis.MANUFACTURER_CROSSREF, basis_source=source, basis_date=date,
                    synthetic=True,
                ),
            ),
        )  # fmt: skip

    from datetime import date as d

    attrs = mk(manufacturer="M1", mpn="A-1")
    assert tier_of("B-1", attrs, catalogue=cat("SYNTHETIC-TEST-SOURCE", d(2025, 1, 1)))[0] is Tier.B
    assert tier_of("B-1", attrs, catalogue=cat("SYNTHETIC-TEST-SOURCE", None))[0] is Tier.C
    assert tier_of("B-1", attrs, catalogue=cat("", d(2025, 1, 1)))[0] is Tier.C


def test_unlocked_tiers_filter_offered_candidates():
    attrs = mk(manufacturer="SynthCo Alpha", mpn="AL6205-2RS")
    only_a = find_candidates(attrs, family=BEARING, unlocked_tiers=frozenset({Tier.A}))
    assert {c.tier for c in only_a if is_offerable(c)} == {Tier.A}
    assert any(c.tier is Tier.D for c in only_a)  # D is always reported, never offered


# ---------------------------------------------------------------- classify_offered on generic designations


def test_generic_offered_designation_with_all_attributes_is_tier_b():
    assert tier_of("6205-2RS/CN", mk()) == (Tier.B, ())
    assert tier_of("6205-2RS1/C3", mk(internal_clearance="C3")) == (Tier.B, ())
    assert tier_of("6205-2ZR/CN", mk(seal_type="shield")) == (Tier.B, ())


def test_generic_offered_designation_without_clearance_is_unknown_not_assumed_cn():
    tier, mismatches = tier_of("6205-2RS", mk())
    assert tier is Tier.D
    assert mismatches == ("internal_clearance",)


def test_generic_offered_designation_near_misses():
    assert tier_of("6205-2Z/CN", mk())[0] is Tier.D
    assert tier_of("6305-2RS/CN", mk())[0] is Tier.D
    assert tier_of("6205-2RS/C3", mk())[0] is Tier.D
    assert tier_of("6205-2RSNR", mk())[0] is Tier.D  # unrecognised suffix cannot be verified


def test_unknown_offered_part_is_tier_d_not_a_guess():
    tier, mismatches = tier_of("ZZ-99999", mk())
    assert tier is Tier.D
    assert set(mismatches) == set(BASE)


def test_offered_mpn_is_matched_on_normalised_form():
    assert tier_of("al 6205-2rs", mk())[0] is Tier.B


# ---------------------------------------------------------------- production guard


def test_production_use_of_synthetic_seed_is_refused():
    with pytest.raises(UnsafeSourceError):
        find_candidates(mk(), family=BEARING, production=True)
    with pytest.raises(UnsafeSourceError):
        classify_offered("AL6205-2RS", mk(), family=BEARING, production=True)


# ---------------------------------------------------------------- V-belt family (abstraction check)

VBELT = "v_belt"
BELT = {"profile": "SPA", "length_mm": "1250", "banded": "no"}


def belt(**over: str) -> dict[str, Attribute]:
    return mk(BELT, **over)


def test_vbelt_documented_crossref_is_tier_b_and_near_misses_are_d():
    attrs = belt(manufacturer="SynthCo Alpha", mpn="SA-SPA1250")
    got = by_mpn(find_candidates(attrs, family=VBELT, unlocked_tiers=ALL_TIERS))
    assert got["SA-SPA1250"].tier is Tier.A
    assert got["SB-SPA1250"].tier is Tier.B
    assert got["SG-SPA1250"].tier is Tier.C  # marketing only
    assert got["SB-SPA1250-B2"].tier is Tier.D  # documented but wrong: single vs banded
    assert "banded" in got["SB-SPA1250-B2"].mismatches
    # no ISO-style standard basis exists for belts in our data: no published source -> not B
    assert all("Load ratings" not in x for c in got.values() for x in c.caveats)


def test_vbelt_generic_request_without_source_is_only_tier_c():
    assert classify_offered("SB-SPA1250", belt(), family=VBELT)[0] is Tier.C
    assert classify_offered("SA-SPA1262", belt(), family=VBELT)[0] is Tier.D  # 1262 vs 1250
    assert classify_offered("SA-SPB1250", belt(), family=VBELT)[0] is Tier.D  # SPB vs SPA


def test_vbelt_banded_requires_number_of_bands_to_match():
    attrs = mk({"profile": "SPA", "length_mm": "1250", "banded": "yes", "number_of_bands": "2"})
    assert classify_offered("SB-SPA1250-B2", attrs, family=VBELT)[0] is Tier.C
    tier, mismatches = classify_offered("SB-SPA1250-B3", attrs, family=VBELT)
    assert tier is Tier.D and mismatches == ("number_of_bands",)
