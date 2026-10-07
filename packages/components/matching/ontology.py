"""The product ontology as data: product types, attribute templates, synonyms, lexicon.

Ontology entries live in YAML under `profiles/data/matching/<market>/ontology/`. Every entry
carries a `status` and `provenance`; classification codes are accepted only from the verified
registry (`classification.py`). The ontology is immutable: `OntologyWriter` (the single writer)
produces a new `Ontology` for each logged change, and `OntologyBuilder` only ever proposes.

An attribute template says what is compared (`kind`, `unit`, `rule`), how a mismatch is reported
(`check`: size, pack, grade or class), and whether the buyer must state it before a line can be
accepted without a person (`required`). Required attributes are domain judgements recorded as
data and flagged `needs_tradesperson_review`; the engine never decides them.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from decimal import Decimal
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .classification import ClassificationError, VerifiedCodes
from .text import TextNormaliser
from .units import CANONICAL_UNITS

NUMERIC_UNITS = frozenset(CANONICAL_UNITS.values()) | {"nr"}
_ID = re.compile(r"^[a-z][a-z0-9_]*$")
_META_FILES = frozenset({"meta.yaml", "lexicon.yaml"})


class OntologyError(ValueError):
    """Ontology data or an ontology entry is invalid."""


class EntryStatus(StrEnum):
    PROPOSED = "proposed"  # LLM builder output, pending a person
    NEEDS_REVIEW = "needs_tradesperson_review"  # authored seed data, not yet reviewed
    APPROVED = "approved"  # reviewed by a named person


class AttrKind(StrEnum):
    NUMERIC = "numeric"
    ENUM = "enum"
    TEXT = "text"


class CompareRule(StrEnum):
    EXACT = "exact"
    GE = "ge"  # SKU value must be at least the line's value
    LE = "le"  # SKU value must be at most the line's value
    TOLERANCE = "tolerance"  # SKU value within tolerance_abs or tolerance_pct of the line's


class CheckGroup(StrEnum):
    """Which check code a failed comparison reports."""

    SIZE = "size"  # size_mismatch
    PACK = "pack"  # pack_mismatch (pack count, pack weight, pack volume, coverage)
    GRADE = "grade"  # grade_mismatch (strength grade such as C16, OSB3)
    CLASS = "class"  # class_mismatch (type, class, rating, finish, option)


class ProvenanceKind(StrEnum):
    RESEARCH_NOTE = "research_note"
    CLASSIFICATION = "classification_table"
    AUTHORED = "authored"
    BUILDER = "builder_proposal"
    HUMAN = "human"


class _M(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Provenance(_M):
    kind: ProvenanceKind
    ref: str = Field(min_length=1)
    note: str = ""


class ClassCode(_M):
    code: str = Field(min_length=3)
    title: str = Field(min_length=1)


class EnumValue(_M):
    label: str = Field(min_length=1)
    synonyms: tuple[str, ...] = ()
    uniclass_pr: ClassCode | None = None
    etim_class: ClassCode | None = None


class AttrTemplate(_M):
    name: str = Field(pattern=_ID.pattern)
    label: str = Field(min_length=1)
    kind: AttrKind
    unit: str | None = None
    required: bool = False
    rule: CompareRule = CompareRule.EXACT
    check: CheckGroup
    values: dict[str, EnumValue] = Field(default_factory=dict)
    min: Decimal | None = None
    max: Decimal | None = None
    tolerance_abs: Decimal | None = None
    tolerance_pct: Decimal | None = None
    aliases: tuple[str, ...] = ()
    question: str | None = None

    @model_validator(mode="after")
    def _shape(self) -> AttrTemplate:
        if self.kind is AttrKind.NUMERIC:
            self._check_numeric()
        elif self.kind is AttrKind.ENUM:
            if len(self.values) < 2:
                raise ValueError("enum attribute needs at least two values")
            if self.unit is not None or self.min is not None or self.max is not None:
                raise ValueError("enum attribute takes no unit or range")
            if self.rule is CompareRule.TOLERANCE:
                raise ValueError("enum attribute cannot use the tolerance rule")
            if not all(_ID.match(v) for v in self.values):
                raise ValueError("enum value ids must be snake_case")
        else:
            if self.values or self.unit is not None or self.min is not None:
                raise ValueError("text attribute takes no values, unit or range")
            if self.rule is not CompareRule.EXACT:
                raise ValueError("text attribute can only use the exact rule")
        return self

    def _check_numeric(self) -> None:
        if self.unit is None:
            raise ValueError("numeric attribute needs a unit")
        if self.unit not in NUMERIC_UNITS:
            raise ValueError(f"unknown unit {self.unit!r}; use one of {sorted(NUMERIC_UNITS)}")
        if self.values:
            raise ValueError("numeric attribute takes no enum values")
        if self.min is None or self.max is None:
            raise ValueError("numeric attribute needs min and max (plausible range)")
        if self.min > self.max:
            raise ValueError("min must not exceed max")
        if self.rule is CompareRule.TOLERANCE and not (self.tolerance_abs or self.tolerance_pct):
            raise ValueError("rule tolerance needs tolerance_abs or tolerance_pct")


class SizePattern(_M):
    """How an `A x B` (or `A x B x C`) size in a line maps onto numeric attributes."""

    terms: Literal[2, 3]
    axes: tuple[str, ...]
    order: Literal["given", "asc", "desc"] = "given"

    @model_validator(mode="after")
    def _axes(self) -> SizePattern:
        if len(self.axes) != self.terms or len(set(self.axes)) != self.terms:
            raise ValueError("axes must be distinct and match terms")
        return self


class ProductType(_M):
    id: str = Field(default="", pattern=r"^([a-z][a-z0-9_]*)?$")
    label: str = Field(min_length=1)
    status: EntryStatus
    provenance: tuple[Provenance, ...] = Field(min_length=1)
    synonyms: tuple[str, ...] = Field(min_length=1)
    vocab: tuple[str, ...] = ()
    uniclass_pr: ClassCode | None = None
    etim_class: ClassCode | None = None
    trailing_multiplier: Literal["quantity", "pack"] = "quantity"
    size_patterns: tuple[SizePattern, ...] = ()
    attributes: tuple[AttrTemplate, ...] = ()

    @model_validator(mode="after")
    def _consistent(self) -> ProductType:
        names = [a.name for a in self.attributes]
        if len(names) != len(set(names)):
            raise ValueError("duplicate attribute name")
        numeric_mm = {a.name for a in self.attributes
                      if a.kind is AttrKind.NUMERIC and a.unit == "mm"}
        seen_terms: set[int] = set()
        for pattern in self.size_patterns:
            if not set(pattern.axes) <= numeric_mm:
                raise ValueError(f"size pattern axes must be numeric mm attributes of this type: "
                                 f"{list(pattern.axes)}")
            if pattern.terms in seen_terms:
                raise ValueError(f"two size patterns for {pattern.terms} terms")
            seen_terms.add(pattern.terms)
        if any(not s.strip() for s in self.synonyms):
            raise ValueError("synonyms must not be blank")
        return self

    def attribute(self, name: str) -> AttrTemplate | None:
        return next((a for a in self.attributes if a.name == name), None)

    @property
    def required_attributes(self) -> tuple[AttrTemplate, ...]:
        return tuple(a for a in self.attributes if a.required)


class Lexicon(_M):
    noise_words: tuple[str, ...]
    abbreviations: dict[str, str]
    count_words: dict[str, str]
    pack_words: tuple[str, ...]
    status: EntryStatus = EntryStatus.NEEDS_REVIEW
    provenance: tuple[Provenance, ...] = ()


class OntologyMeta(_M):
    id: str
    version: str
    market: str
    label: str
    status: EntryStatus
    classification_attribution: dict[str, str]

    @model_validator(mode="after")
    def _labelled(self) -> OntologyMeta:
        if "synthetic" not in self.label.lower():
            raise ValueError("label must say the data is synthetic/illustrative")
        attribution = self.classification_attribution
        if "Uniclass 2015 © NBS, CC BY-ND 4.0" not in attribution.get("uniclass", ""):
            raise ValueError("classification_attribution.uniclass is required")
        if "ODC-By" not in attribution.get("etim", ""):
            raise ValueError("classification_attribution.etim is required")
        return self


Phrases = tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Ontology:
    meta: OntologyMeta
    lexicon: Lexicon
    types: Mapping[str, ProductType]
    _cache: dict[tuple[str, str, str], Any] = field(
        default_factory=dict, compare=False, repr=False
    )

    @cached_property
    def normaliser(self) -> TextNormaliser:
        return TextNormaliser(self.lexicon.abbreviations, self.lexicon.noise_words)

    def _phrases(self, texts: tuple[str, ...]) -> Phrases:
        phrases = {self.normaliser.tokens(t) for t in texts}
        return tuple(sorted((p for p in phrases if p), key=lambda p: (-len(p), p)))

    @cached_property
    def type_phrases(self) -> dict[str, Phrases]:
        return {tid: self._phrases(t.synonyms) for tid, t in self.types.items()}

    def enum_phrases(self, type_id: str, attr_name: str) -> dict[str, Phrases]:
        key = ("enum", type_id, attr_name)
        if key not in self._cache:
            attr = self.types[type_id].attribute(attr_name)
            if attr is None:
                raise OntologyError(f"{type_id} has no attribute {attr_name!r}")
            self._cache[key] = {vid: self._phrases(v.synonyms) for vid, v in attr.values.items()}
        result: dict[str, Phrases] = self._cache[key]
        return result

    def vocabulary(self, type_id: str) -> frozenset[str]:
        """Every token that means something for this type (it is "explained", not residual)."""
        key = ("vocab", type_id, "")
        if key not in self._cache:
            t = self.types[type_id]
            texts: list[str] = [*t.synonyms, *t.vocab, t.label]
            for a in t.attributes:
                texts.extend((a.label, *a.aliases))
                for v in a.values.values():
                    texts.extend((v.label, *v.synonyms))
            self._cache[key] = frozenset(
                tok for text in texts for tok in self.normaliser.tokens(text)
            )
        vocab: frozenset[str] = self._cache[key]
        return vocab

    def with_types(self, types: Mapping[str, ProductType],
                   lexicon: Lexicon | None = None) -> Ontology:
        """A new ontology with these types (and optionally a new lexicon); caches start empty."""
        return replace(self, types=dict(types), lexicon=lexicon or self.lexicon, _cache={})


# --------------------------------------------------------------------------- validation


def _summarise(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(p) for p in e['loc']) or 'entry'}: {e['msg']}" for e in exc.errors()
    )


def _class_codes(entry: ProductType) -> list[tuple[str, ClassCode]]:
    found: list[tuple[str, ClassCode]] = []
    if entry.uniclass_pr:
        found.append(("uniclass_pr", entry.uniclass_pr))
    if entry.etim_class:
        found.append(("etim", entry.etim_class))
    for attr in entry.attributes:
        for value in attr.values.values():
            if value.uniclass_pr:
                found.append(("uniclass_pr", value.uniclass_pr))
            if value.etim_class:
                found.append(("etim", value.etim_class))
    return found


def validate_type_entry(
    type_id: str, raw: Mapping[str, Any], registry: VerifiedCodes
) -> ProductType:
    """Schema-check one entry and verify its classification codes; raise OntologyError."""
    if not _ID.match(type_id):
        raise OntologyError(f"type id {type_id!r} must be snake_case")
    if raw.get("id", type_id) != type_id:
        raise OntologyError(f"{type_id}: id does not match the key")
    try:
        entry = ProductType.model_validate({**raw, "id": type_id})
    except ValidationError as exc:
        raise OntologyError(f"{type_id}: {_summarise(exc)}") from exc
    for system, code in _class_codes(entry):
        try:
            registry.check(system, code.code, code.title)
        except ClassificationError as exc:
            raise OntologyError(f"{type_id}: {exc}") from exc
    return entry


# --------------------------------------------------------------------------- loading


def default_data_dir(market: str = "uk") -> Path:
    """`profiles/data/matching/<market>` of this repository checkout."""
    return Path(__file__).resolve().parents[3] / "profiles" / "data" / "matching" / market


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise OntologyError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise OntologyError(f"{path}: expected a mapping")
    return data


def _model(cls: type[Any], data: Mapping[str, Any], where: str) -> Any:
    try:
        return cls.model_validate(dict(data))
    except ValidationError as exc:
        raise OntologyError(f"{where}: {_summarise(exc)}") from exc


def load_ontology(directory: Path, registry: VerifiedCodes) -> Ontology:
    """Load `meta.yaml`, `lexicon.yaml` and every other `*.yaml` (a `types:` mapping)."""
    meta = _model(OntologyMeta, _read_yaml(directory / "meta.yaml"), "meta.yaml")
    lexicon = _model(Lexicon, _read_yaml(directory / "lexicon.yaml"), "lexicon.yaml")
    types: dict[str, ProductType] = {}
    for path in sorted(directory.glob("*.yaml")):
        if path.name in _META_FILES:
            continue
        data = _read_yaml(path)
        unknown = set(data) - {"types", "file"}
        if unknown or not isinstance(data.get("types"), dict):
            raise OntologyError(f"{path.name}: expected only `file` and a `types` mapping")
        for type_id, raw in data["types"].items():
            if type_id in types:
                raise OntologyError(f"duplicate type id {type_id!r} (again in {path.name})")
            types[type_id] = validate_type_entry(str(type_id), raw, registry)
    if not types:
        raise OntologyError(f"{directory}: no product types found")
    return Ontology(meta=meta, lexicon=lexicon, types=types)
