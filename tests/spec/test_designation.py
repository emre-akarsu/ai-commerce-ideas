import pytest

from components.core.domain import AttrSource
from components.parts.spec.designation import (
    ISO15_SOURCE_REF,
    find_designations,
    iso_designation_for,
    lookup_dimensions,
    parse_designation,
)


def attrs(text: str) -> dict[str, str]:
    return {a.name: a.value for a in parse_designation(text).attributes}


# ---------------------------------------------------------------- ISO 15 table

KNOWN_DIMS = {
    "6205": (25, 52, 15),
    "6204": (20, 47, 14),
    "6305": (25, 62, 17),
    "6005": (25, 47, 12),
    "6000": (10, 26, 8),
    "6210": (50, 90, 20),
    "6310": (50, 110, 27),
    "6010": (50, 80, 16),
}


@pytest.mark.parametrize(("base", "dims"), KNOWN_DIMS.items())
def test_iso15_known_values(base, dims):
    d = lookup_dimensions(base)
    assert d is not None
    assert (d.bore_mm, d.outer_diameter_mm, d.width_mm) == dims


def test_iso15_table_is_internally_consistent():
    bore_by_code = {"00": 10, "01": 12, "02": 15, "03": 17}
    bore_by_code.update({f"{c:02d}": c * 5 for c in range(4, 11)})
    for series in ("60", "62", "63"):
        for code, bore in bore_by_code.items():
            d = lookup_dimensions(series + code)
            assert d is not None, series + code
            assert d.bore_mm == bore
    # outer diameter and width grow with the dimension series at the same bore
    for code in bore_by_code:
        d60, d62, d63 = (lookup_dimensions(s + code) for s in ("60", "62", "63"))
        assert d60 and d62 and d63
        assert d60.outer_diameter_mm < d62.outer_diameter_mm < d63.outer_diameter_mm
        assert d60.width_mm < d62.width_mm < d63.width_mm


def test_values_outside_the_table_are_omitted_not_guessed():
    assert lookup_dimensions("6212") is None
    assert lookup_dimensions("6011") is None
    assert lookup_dimensions("7205") is None


def test_reverse_lookup_by_dimensions():
    assert iso_designation_for(25, 52, 15) == "6205"
    assert iso_designation_for(25, 62, 17) == "6305"
    assert iso_designation_for(25, 52, 99) is None


# ---------------------------------------------------------------- seal / clearance table

SEAL_TABLE = [
    ("6205-2RS", "contact_seal", None),
    ("6205 2RS", "contact_seal", None),
    ("6205-2RSH", "contact_seal", None),
    ("6205-2RS1/C3", "contact_seal", "C3"),
    ("6205-2RSR", "contact_seal", None),
    ("6205DDU", "contact_seal", None),
    ("6205LLU", "contact_seal", None),
    ("6205DDUC3", "contact_seal", "C3"),
    ("62052RS", "contact_seal", None),
    ("6205-2RS/C4", "contact_seal", "C4"),
    ("6205ZZ", "shield", None),
    ("6205-2Z", "shield", None),
    ("6205 ZZ C3", "shield", "C3"),
    ("6205-2ZR", "shield", None),
    ("6205-2z/c3", "shield", "C3"),  # case-insensitive
    ("6205-2Z/CN", "shield", "CN"),
]


@pytest.mark.parametrize(("text", "seal", "clearance"), SEAL_TABLE)
def test_suffix_table(text, seal, clearance):
    got = attrs(text)
    assert got["bore_mm"] == "25"
    assert got["outer_diameter_mm"] == "52"
    assert got["width_mm"] == "15"
    assert got["seal_type"] == seal
    assert got.get("internal_clearance") == clearance
    assert "unrecognised_suffix" not in got


def test_no_suffix_is_ambiguous_seal_and_must_ask():
    p = parse_designation("6205")
    got = {a.name: a.value for a in p.attributes}
    assert got["bore_mm"] == "25"
    assert "seal_type" not in got  # "no suffix" is NOT assumed to mean open
    assert "internal_clearance" not in got
    assert p.unresolved == ("seal_type", "internal_clearance")


def test_clearance_absent_is_unresolved_not_assumed_normal():
    p = parse_designation("6205-2RS")
    assert p.unresolved == ("internal_clearance",)
    assert "internal_clearance" not in {a.name for a in p.attributes}


@pytest.mark.parametrize("text", ["6205-RS", "6205 Z", "6205-RSH", "6205-LU", "6205DU"])
def test_single_sided_suffix_is_not_resolved_to_a_seal_class(text):
    p = parse_designation(text)
    assert "seal_type" not in {a.name for a in p.attributes}
    assert "seal_type" in p.unresolved
    assert any(n.startswith("single_sided_seal") for n in p.notes)


def test_conflicting_seal_tokens_are_unresolved():
    p = parse_designation("6205-2RS-2Z")
    assert "seal_type" not in {a.name for a in p.attributes}
    assert "seal_type" in p.unresolved


def test_unrecognised_suffix_is_recorded_and_seal_not_guessed():
    p = parse_designation("6205-2RSNR")
    got = {a.name: a.value for a in p.attributes}
    assert got["unrecognised_suffix"] == "2RSNR"
    assert "seal_type" not in got
    p2 = parse_designation("6205-2RS/GJN")
    got2 = {a.name: a.value for a in p2.attributes}
    assert got2["seal_type"] == "contact_seal"
    assert got2["unrecognised_suffix"] == "GJN"


def test_explicit_precision_class_token():
    got = attrs("6205-2RS/P6")
    assert got["precision_class"] == "P6"
    assert "precision_class" not in attrs("6205-2RS")  # default is applied by the normaliser


@pytest.mark.parametrize("base", ["6212", "6011", "7205", "1234", "ABC"])
def test_unknown_designations_produce_no_attributes(base):
    p = parse_designation(f"{base}-2RS")
    assert p.attributes == ()
    assert p.known is False


def test_series_other_than_60_62_63_is_not_parsed():
    assert parse_designation("6805-2RS").attributes == ()
    assert parse_designation("16005").attributes == ()


# ---------------------------------------------------------------- provenance (R3)


def test_every_attribute_has_provenance():
    p = parse_designation("6205-2RS1/C3")
    by_name = {a.name: a for a in p.attributes}
    for name in ("bore_mm", "outer_diameter_mm", "width_mm", "series"):
        assert by_name[name].source is AttrSource.STANDARD
        assert by_name[name].source_ref == ISO15_SOURCE_REF
    assert by_name["bore_mm"].unit == "mm"
    for name in ("seal_type", "internal_clearance", "seal_designation", "designation"):
        assert by_name[name].source is AttrSource.USER_INPUT
        assert by_name[name].source_ref
    assert by_name["seal_designation"].value == "2RS1"
    assert by_name["designation"].value == "6205-2RS1/C3"
    assert all(a.source is not AttrSource.MODEL_INFERENCE for a in p.attributes)


# ---------------------------------------------------------------- scanning free text


def test_find_designations_in_free_text():
    found = find_designations("Need 10 pcs of 6205-2RS C3 bearings for pump 7, ASAP")
    assert len(found) == 1
    assert found[0].base == "6205"
    got = {a.name: a.value for a in found[0].attributes}
    assert got["seal_type"] == "contact_seal"
    assert got["internal_clearance"] == "C3"


def test_find_designations_does_not_swallow_following_words_or_quantities():
    found = find_designations("6205-2RS 10 pcs")
    assert [a.value for a in found[0].attributes if a.name == "designation"] == ["6205-2RS"]


def test_part_numbers_embedding_digits_are_not_designations():
    assert find_designations("MPN AL6205-2RS") == []
    assert find_designations("order 162050 units") == []
