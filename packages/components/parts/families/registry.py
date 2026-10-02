"""Deterministic required-attribute tables per part family (spec §6.2, ADR-006).

These tables are data, not prompts: the LLM may extract values and explain, but it never edits
which attributes are required or critical. A family is added only together with its own
required-attribute table, source list with licences, and eval set (spec §6.2).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

DEEP_GROOVE_BALL_BEARING = "deep_groove_ball_bearing"
V_BELT = "v_belt"

# A critical attribute whose confidence is below this is treated as unknown (spec §3, Tier D:
# "confidence below threshold"). Illustrative assumption, to be tuned on the dev set.
MIN_CRITICAL_CONFIDENCE = 0.7

# Asked only when the part family itself cannot be determined from the request.
FAMILY_QUESTION = (
    "Which kind of part is this (for example a deep groove ball bearing or a V-belt)?"
)

_DIMENSIONS_QUESTION = (
    "What is the full bearing designation (for example 6205-2RS), or the bore, outer diameter "
    "and width in mm (for example 25 x 52 x 15)?"
)


class UnknownFamilyError(KeyError):
    """Raised for a family with no registered required-attribute table."""


@dataclass(frozen=True)
class FamilySpec:
    name: str
    required_attributes: tuple[str, ...]  # in the order questions are prioritised
    critical_attributes: tuple[str, ...]  # must match by rule before any Tier A/B/C (spec §3)
    questions: dict[str, str]  # attribute -> clarifying question (one per required attribute)
    optional_attributes: tuple[str, ...] = ()
    # attributes that identify the "same kind of part": near-miss candidates share these values
    identity_attributes: tuple[str, ...] = ()
    allowed_values: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # attribute -> (other attribute, value that makes it required/critical), e.g. bands if banded
    required_if: dict[str, tuple[str, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        missing_q = set(self.required_attributes) - set(self.questions)
        if missing_q:
            raise ValueError(f"{self.name}: no question for {sorted(missing_q)}")
        if not set(self.critical_attributes) <= set(self.required_attributes):
            raise ValueError(f"{self.name}: critical attributes must be required attributes")
        if not set(self.identity_attributes) <= set(self.critical_attributes):
            raise ValueError(f"{self.name}: identity attributes must be critical attributes")

    def _applies(self, attr: str, values: Mapping[str, str]) -> bool:
        cond = self.required_if.get(attr)
        if cond is None:
            return True
        other, wanted = cond
        return values.get(other, "").strip().casefold() == wanted

    def required_for(self, values: Mapping[str, str]) -> tuple[str, ...]:
        """Required attributes given the (attribute -> value) known so far."""
        return tuple(a for a in self.required_attributes if self._applies(a, values))

    def critical_for(self, values: Mapping[str, str]) -> tuple[str, ...]:
        return tuple(a for a in self.critical_attributes if self._applies(a, values))

    def question_for(self, attr: str) -> str:
        return self.questions[attr]


_BEARING = FamilySpec(
    name=DEEP_GROOVE_BALL_BEARING,
    required_attributes=(
        "bore_mm",
        "outer_diameter_mm",
        "width_mm",
        "seal_type",
        "internal_clearance",
        "precision_class",
    ),
    critical_attributes=(
        "bore_mm",
        "outer_diameter_mm",
        "width_mm",
        "seal_type",
        "internal_clearance",
        "precision_class",
    ),
    questions={
        "bore_mm": _DIMENSIONS_QUESTION,
        "outer_diameter_mm": _DIMENSIONS_QUESTION,
        "width_mm": _DIMENSIONS_QUESTION,
        "seal_type": (
            "Is the bearing open, metal-shielded (Z, 2Z, ZZ) or rubber contact-sealed "
            "(2RS, 2RSH, DDU, LLU), and is it fitted on both sides?"
        ),
        "internal_clearance": (
            "Which radial internal clearance does it need: Normal (CN, no suffix), C3, "
            "or another class (C2, C4, C5)?"
        ),
        "precision_class": (
            "Which precision (tolerance) class does it need: Normal (P0) or a higher class "
            "(P6, P5, P4, P2)?"
        ),
    },
    optional_attributes=(
        "designation",
        "series",
        "seal_designation",
        "manufacturer",
        "mpn",
        "cage_material",
        "unrecognised_suffix",
    ),
    identity_attributes=("bore_mm", "outer_diameter_mm", "width_mm"),
    allowed_values={
        "seal_type": ("open", "shield", "contact_seal"),
        "internal_clearance": ("C2", "CN", "C3", "C4", "C5"),
        "precision_class": ("P0", "P6", "P5", "P4", "P2"),
    },
)

_V_BELT = FamilySpec(
    name=V_BELT,
    required_attributes=("profile", "length_mm", "banded", "number_of_bands"),
    critical_attributes=("profile", "length_mm", "banded", "number_of_bands"),
    questions={
        "profile": (
            "What is the belt profile (for example A, B, C, SPZ, SPA, SPB, SPC, 3V, 5V, 8V)?"
        ),
        "length_mm": "What is the effective (pitch) length in mm, as marked on the belt?",
        "banded": "Is it a single belt or a banded (joined) belt?",
        "number_of_bands": "How many bands (ribs) does the banded belt have?",
    },
    optional_attributes=("manufacturer", "mpn", "application"),
    identity_attributes=("profile", "length_mm"),
    allowed_values={
        "profile": (
            "Z", "A", "B", "C", "D", "E", "SPZ", "SPA", "SPB", "SPC",
            "XPZ", "XPA", "XPB", "XPC", "3V", "5V", "8V", "AX", "BX", "CX",
        ),  # fmt: skip
        "banded": ("yes", "no"),
    },
    required_if={"number_of_bands": ("banded", "yes")},
)

_FAMILIES: dict[str, FamilySpec] = {f.name: f for f in (_BEARING, _V_BELT)}


def get_family(name: str) -> FamilySpec:
    try:
        return _FAMILIES[name]
    except KeyError:
        raise UnknownFamilyError(f"no required-attribute table for family {name!r}") from None


def list_families(enabled: Iterable[str] | None = None) -> tuple[str, ...]:
    """Registered families; with ``enabled`` (a deployment profile's ``parts.enabled_families``)
    only those. ``None`` keeps the unfiltered behaviour."""
    if enabled is None:
        return tuple(_FAMILIES)
    allowed = set(enabled)
    return tuple(name for name in _FAMILIES if name in allowed)


def is_family_enabled(name: str | None, enabled: Iterable[str] | None) -> bool:
    return name is not None and (enabled is None or name in set(enabled))
