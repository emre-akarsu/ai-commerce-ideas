"""Source registry with a recorded licence status per source (spec §7, §11 Q1, ADR-006).

Cross-reference data licensing is decided per source before any data reaches production. This
module is the code-level guard: ``assert_production_safe`` raises for synthetic or unlicensed
sources, and an unregistered source is treated as unlicensed (default deny).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class LicenceStatus(StrEnum):
    SYNTHETIC = "synthetic"  # illustrative test data we wrote; never real
    STANDARD_PUBLIC_DIMENSIONS = "standard_public_dimensions"  # published standard dimension tables
    UNLICENSED = "unlicensed"  # no licence decision recorded (or competitor marketing material)
    LICENSED = "licensed"  # reserved: a source with a recorded licence (none registered yet)


class UnsafeSourceError(RuntimeError):
    """A synthetic or unlicensed source was about to be used where production data is required."""


@dataclass(frozen=True)
class Source:
    name: str
    licence_status: LicenceStatus
    description: str = ""
    edition_date: date | None = None


SYNTHETIC_SOURCE = "SYNTHETIC-TEST-SOURCE"
ISO15_SOURCE = "ISO 15 boundary dimensions"
COMPETITOR_MARKETING_SOURCE = "COMPETITOR-MARKETING-CROSSREF"

_REGISTRY: dict[str, Source] = {
    s.name: s
    for s in (
        Source(
            SYNTHETIC_SOURCE,
            LicenceStatus.SYNTHETIC,
            "Illustrative seed data written for tests; not real manufacturer data.",
        ),
        Source(
            ISO15_SOURCE,
            LicenceStatus.STANDARD_PUBLIC_DIMENSIONS,
            "ISO 15 radial bearing boundary dimensions (edition year 2017).",
            date(2017, 1, 1),
        ),
        Source(
            COMPETITOR_MARKETING_SOURCE,
            LicenceStatus.UNLICENSED,
            "A competitor's marketing cross-reference; never above Tier C, never production data.",
        ),
    )
}


def register_source(source: Source) -> None:
    """Record a source's licence status (e.g. once counsel clears a licensed feed)."""
    _REGISTRY[source.name] = source


def get_source(name: str) -> Source:
    return _REGISTRY.get(name) or Source(name, LicenceStatus.UNLICENSED, "unregistered source")


def assert_production_safe(source: Source | str) -> None:
    src = get_source(source) if isinstance(source, str) else source
    if src.licence_status in (LicenceStatus.SYNTHETIC, LicenceStatus.UNLICENSED):
        raise UnsafeSourceError(
            f"source {src.name!r} has licence_status={src.licence_status.value!r} "
            "and must never reach production"
        )
