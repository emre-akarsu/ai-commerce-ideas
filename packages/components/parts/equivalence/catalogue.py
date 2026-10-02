"""Catalogue of parts and documented cross-references the equivalence engine reasons over.

The bundled seed files are SYNTHETIC illustrative data (CLAUDE.md): invented manufacturers and
part numbers, invented cross-references, not licensed and not real. A production catalogue must
come from a source whose licence status passes ``assert_production_safe``.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from components.core.domain import Basis

DATA_DIR = Path(__file__).resolve().parent / "data"
_SEED_FILES = {
    "deep_groove_ball_bearing": "bearings_seed.json",
    "v_belt": "vbelt_seed.json",
}


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


def normalise_mpn(mpn: str) -> str:
    """Upper-case alphanumerics only, so "AL6205-2RS" and "al 6205 2rs" compare equal."""
    return re.sub(r"[^A-Z0-9]", "", mpn.upper())


def normalise_name(name: str) -> str:
    return " ".join(name.casefold().split())


class CatalogPart(_Frozen):
    mpn: str
    manufacturer: str
    iso_designation: str | None = None  # base designation such as "6205", if it has one
    attributes: dict[str, str]

    @property
    def key(self) -> tuple[str, str]:
        return (normalise_name(self.manufacturer), normalise_mpn(self.mpn))


class CrossRef(_Frozen):
    from_mpn: str
    from_manufacturer: str
    to_mpn: str
    to_manufacturer: str
    basis: Basis
    basis_source: str
    basis_date: date | None = None
    synthetic: bool = False
    note: str = ""

    @property
    def from_key(self) -> tuple[str, str]:
        return (normalise_name(self.from_manufacturer), normalise_mpn(self.from_mpn))

    @property
    def to_key(self) -> tuple[str, str]:
        return (normalise_name(self.to_manufacturer), normalise_mpn(self.to_mpn))


class Catalogue(_Frozen):
    label: str
    family: str
    source_name: str
    synthetic: bool
    as_of: date
    parts: tuple[CatalogPart, ...]
    crossrefs: tuple[CrossRef, ...] = Field(default_factory=tuple)

    def find_parts(self, mpn: str, manufacturer: str | None = None) -> list[CatalogPart]:
        want = normalise_mpn(mpn)
        hits = [p for p in self.parts if normalise_mpn(p.mpn) == want]
        if manufacturer:
            hits = [p for p in hits if normalise_name(p.manufacturer) == normalise_name(manufacturer)]
        return hits

    def crossrefs_from(self, part: CatalogPart) -> list[CrossRef]:
        return [x for x in self.crossrefs if x.from_key == part.key]


def load_catalogue(path: Path) -> Catalogue:
    return Catalogue.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load_seed(family: str) -> Catalogue:
    """The bundled SYNTHETIC seed for ``family`` (an empty catalogue for families without one)."""
    filename = _SEED_FILES.get(family)
    if filename is None:
        return Catalogue(
            label="NO SEED: empty catalogue",
            family=family,
            source_name="SYNTHETIC-TEST-SOURCE",
            synthetic=True,
            as_of=date(2026, 10, 2),
            parts=(),
        )
    return load_catalogue(DATA_DIR / filename)
