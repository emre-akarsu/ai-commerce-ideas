"""Bind what an order line states onto the attribute templates of its product type.

Binding is rule-based and conservative: a stated value is bound only when exactly one reading is
plausible. Two different stated values for one attribute, a number that fits no attribute, or a
number outside every plausible range is never guessed; it is reported (`conflicts`, `unbound`,
`implausible`) and the line goes to a person (R3: no claim without provenance; ask, don't guess).
Every bound attribute carries source `user_input` and the text it came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from components.core.domain import Attribute, AttrSource

from .models import Measure, MeasureKind, SizeToken
from .ontology import AttrKind, AttrTemplate, Ontology, ProductType, SizePattern
from .units import format_decimal

INFERRED_UNIT_CONFIDENCE = 0.9
_KIND_UNIT = {
    MeasureKind.LENGTH: "mm",
    MeasureKind.AREA: "m2",
    MeasureKind.WEIGHT: "kg",
    MeasureKind.VOLUME: "l",
    MeasureKind.POWER: "w",
    MeasureKind.POWER_DENSITY: "w/m2",
    MeasureKind.FLOW: "l/s",
}


@dataclass(frozen=True)
class Word:
    text: str


@dataclass(frozen=True)
class Break:
    """Something already consumed (quantity, identifier ...): words do not run across it."""


@dataclass(frozen=True)
class MeasureEl:
    measure: Measure


@dataclass(frozen=True)
class SizeEl:
    size: SizeToken


@dataclass(frozen=True)
class PackEl:
    n: int
    raw: str


@dataclass(frozen=True)
class TextEl:
    alias: str
    value: str
    raw: str


Element = Word | Break | MeasureEl | SizeEl | PackEl | TextEl


@dataclass(frozen=True)
class BindResult:
    attributes: tuple[Attribute, ...] = ()
    conflicts: tuple[str, ...] = ()
    implausible: tuple[str, ...] = ()
    unbound: tuple[str, ...] = ()
    consumed_words: frozenset[int] = frozenset()  # element indices of words that bound a value


def in_range(template: AttrTemplate, value: Decimal) -> bool:
    return template.min is not None and template.max is not None and (
        template.min <= value <= template.max
    )


def _numeric_attr(template: AttrTemplate, value: Decimal, raw: str,
                  confidence: float = 1.0) -> Attribute:
    return Attribute(name=template.name, value=format_decimal(value), unit=template.unit,
                     source=AttrSource.USER_INPUT, source_ref=raw, confidence=confidence)


def _enum_attr(template: AttrTemplate, value_id: str, raw: str) -> Attribute:
    return Attribute(name=template.name, value=value_id, unit=None,
                     source=AttrSource.USER_INPUT, source_ref=raw)


def size_axes(pattern: SizePattern, values: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
    """The size terms in axis order (`desc`/`asc` sort them; `given` keeps the written order)."""
    if pattern.order == "desc":
        return tuple(sorted(values, reverse=True))
    if pattern.order == "asc":
        return tuple(sorted(values))
    return values


def pattern_for(ptype: ProductType, terms: int) -> SizePattern | None:
    return next((p for p in ptype.size_patterns if p.terms == terms), None)


def size_is_plausible(ptype: ProductType, size: SizeToken) -> bool:
    """True when the type has a pattern for this many terms and every term fits its axis."""
    pattern = pattern_for(ptype, len(size.values))
    if pattern is None or (size.thread_prefix and pattern.order != "given"):
        return False
    for axis, value in zip(pattern.axes, size_axes(pattern, size.values), strict=True):
        template = ptype.attribute(axis)
        if template is None or not in_range(template, value):
            return False
    return True


class _Binder:
    def __init__(self, ontology: Ontology, ptype: ProductType, elements: list[Element]) -> None:
        self.ontology = ontology
        self.ptype = ptype
        self.elements = elements
        self.bound: dict[str, Attribute] = {}
        self.poisoned: set[str] = set()  # attributes given two different values
        self._alias_cache: dict[str, frozenset[str]] = {}
        self.conflicts: list[str] = []
        self.implausible: list[str] = []
        self.unbound: list[str] = []
        self.consumed: set[int] = set()

    def run(self) -> BindResult:
        self._sizes()
        self._measures()
        self._packs()
        self._enums()
        self._texts()
        order = {a.name: i for i, a in enumerate(self.ptype.attributes)}
        attrs = sorted(self.bound.values(), key=lambda a: order[a.name])
        return BindResult(tuple(attrs), tuple(dict.fromkeys(self.conflicts)),
                          tuple(self.implausible), tuple(self.unbound), frozenset(self.consumed))

    # ------------------------------------------------------------------ sizes and measures

    def _put(self, attr: Attribute) -> None:
        if attr.name in self.bound and self.bound[attr.name].value != attr.value:
            self.conflicts.append(attr.name)
            del self.bound[attr.name]
            self.poisoned.add(attr.name)
        elif attr.name not in self.poisoned:
            self.bound[attr.name] = attr

    def _sizes(self) -> None:
        for el in self.elements:
            if not isinstance(el, SizeEl):
                continue
            size = el.size
            pattern = pattern_for(self.ptype, len(size.values))
            if pattern is None or (size.thread_prefix and pattern.order != "given"):
                self.unbound.append(size.raw)
                continue
            if not size_is_plausible(self.ptype, size):
                self.implausible.append(size.raw)
                self.unbound.append(size.raw)
                continue
            confidence = INFERRED_UNIT_CONFIDENCE if size.unit_inferred else 1.0
            for axis, value in zip(pattern.axes, size_axes(pattern, size.values), strict=True):
                template = self.ptype.attribute(axis)
                assert template is not None  # validated by the ontology loader
                self._put(_numeric_attr(template, value, size.raw, confidence))

    def _alias_tokens(self, template: AttrTemplate) -> frozenset[str]:
        if template.name not in self._alias_cache:
            norm = self.ontology.normaliser
            self._alias_cache[template.name] = frozenset(
                tok for alias in template.aliases for tok in norm.tokens(alias)
            )
        return self._alias_cache[template.name]

    def _neighbour_words(self, index: int) -> list[str]:
        out: list[str] = []
        for j in (index + 1, index - 1):  # the word after a number labels it more often
            if 0 <= j < len(self.elements):
                el = self.elements[j]
                if isinstance(el, Word):
                    out.append(el.text)
        return out

    def _measure_target(self, index: int, measure: Measure) -> AttrTemplate | None:
        unit = _KIND_UNIT[measure.kind]
        free = [a for a in self.ptype.attributes
                if a.kind is AttrKind.NUMERIC and a.unit == unit and a.name not in self.bound
                and a.name not in self.poisoned]
        for word in self._neighbour_words(index):
            labelled = [a for a in free if word in self._alias_tokens(a)]
            if len(labelled) == 1:
                return labelled[0]
        fitting = [a for a in free if in_range(a, measure.value)]
        return fitting[0] if len(fitting) == 1 else None

    def _measures(self) -> None:
        for index, el in enumerate(self.elements):
            if not isinstance(el, MeasureEl):
                continue
            target = self._measure_target(index, el.measure)
            if target is None:
                self.unbound.append(el.measure.raw)
            elif not in_range(target, el.measure.value):
                self.implausible.append(el.measure.raw)
                self.unbound.append(el.measure.raw)
            else:
                confidence = INFERRED_UNIT_CONFIDENCE if el.measure.unit_inferred else 1.0
                self._put(_numeric_attr(target, el.measure.value, el.measure.raw, confidence))

    def _packs(self) -> None:
        template = next((a for a in self.ptype.attributes
                         if a.kind is AttrKind.NUMERIC and a.unit == "nr"
                         and a.check.value == "pack"), None)
        for el in self.elements:
            if not isinstance(el, PackEl):
                continue
            if template is None or not in_range(template, Decimal(el.n)):
                self.unbound.append(el.raw)
            else:
                self._put(_numeric_attr(template, Decimal(el.n), el.raw))

    # ------------------------------------------------------------------ enums and text

    def _enums(self) -> None:
        words: list[str | None] = [el.text if isinstance(el, Word) else None
                                   for el in self.elements]
        spans: list[tuple[int, int, int, str, str]] = []  # (-length, start, end, attr, value)
        for template in self.ptype.attributes:
            if template.kind is not AttrKind.ENUM:
                continue
            for value_id, phrases in self.ontology.enum_phrases(
                    self.ptype.id, template.name).items():
                for phrase in phrases:
                    for start in range(len(words) - len(phrase) + 1):
                        if tuple(words[start:start + len(phrase)]) == phrase:
                            spans.append((-len(phrase), start, start + len(phrase),
                                          template.name, value_id))
        used: set[int] = set()
        found: dict[str, set[str]] = {}
        for _neg, start, end, attr, value_id in sorted(spans):
            if used & set(range(start, end)):
                continue
            used |= set(range(start, end))
            self.consumed |= set(range(start, end))
            found.setdefault(attr, set()).add(value_id)
        for template in self.ptype.attributes:
            values = found.get(template.name, set())
            if len(values) == 1:
                self._put(_enum_attr(template, next(iter(values)), "stated in the line"))
            elif len(values) > 1:
                self.conflicts.append(template.name)

    def _texts(self) -> None:
        for el in self.elements:
            if not isinstance(el, TextEl):
                continue
            template = next((a for a in self.ptype.attributes if a.kind is AttrKind.TEXT
                             and el.alias in a.aliases), None)
            if template is None:
                self.unbound.append(el.raw)
            else:
                self._put(Attribute(name=template.name, value=el.value, unit=None,
                                    source=AttrSource.USER_INPUT, source_ref=el.raw))


def bind_attributes(ontology: Ontology, ptype: ProductType,
                    elements: list[Element]) -> BindResult:
    return _Binder(ontology, ptype, elements).run()
