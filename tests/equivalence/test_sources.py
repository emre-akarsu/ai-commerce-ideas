import pytest

from components.parts.equivalence.sources import (
    SYNTHETIC_SOURCE,
    LicenceStatus,
    Source,
    UnsafeSourceError,
    assert_production_safe,
    get_source,
)


def test_synthetic_source_is_registered_as_synthetic():
    src = get_source(SYNTHETIC_SOURCE)
    assert src.name == "SYNTHETIC-TEST-SOURCE"
    assert src.licence_status == "synthetic"


def test_iso15_is_standard_public_dimensions():
    assert get_source("ISO 15 boundary dimensions").licence_status == "standard_public_dimensions"


def test_production_guard_rejects_synthetic():
    with pytest.raises(UnsafeSourceError, match="synthetic"):
        assert_production_safe(get_source(SYNTHETIC_SOURCE))
    with pytest.raises(UnsafeSourceError):
        assert_production_safe(SYNTHETIC_SOURCE)  # by name too


def test_production_guard_rejects_unlicensed():
    with pytest.raises(UnsafeSourceError, match="unlicensed"):
        assert_production_safe(Source(name="x", licence_status=LicenceStatus.UNLICENSED))
    with pytest.raises(UnsafeSourceError):
        assert_production_safe("COMPETITOR-MARKETING-CROSSREF")


def test_unknown_source_is_denied_by_default():
    assert get_source("never-heard-of-it").licence_status == "unlicensed"
    with pytest.raises(UnsafeSourceError):
        assert_production_safe("never-heard-of-it")


def test_production_guard_allows_public_standard_dimensions():
    assert_production_safe("ISO 15 boundary dimensions")
    assert_production_safe(
        Source(name="licensed feed", licence_status=LicenceStatus.LICENSED)
    )
