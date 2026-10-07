"""Deterministic order-line parser (spec pipeline step 1).

Extracts quantity, sizes (`2.4x1.2`, `2400 x 1200`), single measures (`12.5mm`, `310 ml`, `20 kg`),
pack sizes (`box of 200`, `x50`), thread/gauge sizes (`4.0x40`, `M6x30`), grade and class codes
(`C16`, `OSB3`, `S1`), brand, MPN and GTIN, and a product-type hint, then binds the stated values
onto the ontology's attribute templates. Units are normalised to canonical mm, m2, kg, l with
Decimal. No LLM, no network, no randomness: the same text always gives the same `ParsedLine`.

The text is untrusted (R4). It is made inert first (HTML, links and invisible characters removed)
and is only ever read for the tokens listed above; prose such as "ignore previous instructions"
sets nothing.

Quantity-versus-size ambiguity ("20 x 12.5mm", "10 12.5mm boards") is detected, never resolved
here: the line carries an `Ambiguity` and the gate always sends it to a person.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from . import binding as bd
from .models import (
    Ambiguity,
    AmbiguityKind,
    LineKind,
    Measure,
    MeasureKind,
    OrderLine,
    ParsedLine,
    SizeToken,
    TypeHint,
)
from .ontology import AttrKind, Ontology, ProductType
from .text import clean_text
from .units import format_decimal, normalise_unit, to_canonical

_PH = re.compile(r"⟦(\d+)⟧")
_NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
_END = r"(?![a-z0-9/])"
_LEN_U = rf"(?:mm|cm|mtrs?|metres?|meters?|m){_END}"
_CONTEXT_WORDS = frozenset({"for", "suit", "suitable", "with"})
# Count words that mean "this many" wherever they appear ("SynthGyp 20 sheets ..."). Others, such
# as "set" (rapid set) or "no", only count at the start or end of the line.
_ANYWHERE_COUNT = frozenset({"sheet", "sheets", "length", "lengths", "bag", "bags", "boxes",
                             "rolls", "tubes", "tins", "cartridges", "pairs", "pcs", "pieces",
                             "off", "nos"})
_GTIN_MARKERS = ("gtin", "ean", "barcode", "upc")
_MAX_TEXT_ATTR_WORDS = 3
_GRADE = re.compile(
    r"^(?:c(?:14|16|18|22|24|27|30|35)|osb[1-4]|p[2-7]|s[12]|c[12](?:f?t?e?)?|ip[0-9x]{2})$"
)
_IMPLICIT_MPN = re.compile(r"^(?=[a-z0-9-]*[a-z])(?=[a-z0-9-]*\d)[a-z0-9]{2,}(?:-[a-z0-9]{2,})+$")


def _p(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern)


_PRE = (
    (_p(r"(?<=\d)(mm|cm|m)x(?=\d)"), r"\1 x "),
    (_p(r"\bosb\s*[/-]\s*([1-4])\b"), r"osb\1"),
    (_p(r"\bip\s+(\d[\dx])\b"), r"ip\1"),
)
_GTIN = _p(r"(?<![\d.,/-])(\d{8}|\d{12,14})(?![\d]|[.,]\d)")
_MPN_EXPLICIT = _p(
    r"\b(?:mpn|part\s*(?:no|number|num|#)|p/n|cat(?:alogue)?\s*(?:no|number)|sku|ref(?:erence)?)"
    r"\s*[:#]?\s*([a-z0-9][a-z0-9\-_./]{2,})"
)
_MPN_TOKEN = _p(r"(?<!\S)[a-z0-9][a-z0-9\-_./]*[a-z0-9](?!\S)")
_AREA = _p(rf"(?<![a-z0-9.])({_NUM})\s*(m2|sqm|sq\.?\s*m)(?![a-z0-9/])")
_FLOW = _p(rf"(?<![a-z0-9.])({_NUM})\s*(l/s|l/sec|lps|m3/h|m3/hr|cmh|l/min|lpm)(?![a-z0-9])")
_PDENS = _p(rf"(?<![a-z0-9.])({_NUM})\s*(w/m2|w/sqm)(?![a-z0-9])")
_POWER = _p(rf"(?<![a-z0-9.])({_NUM})\s*(kw|kilowatts?|watts?|w)(?![a-z0-9/])")
_WEIGHT = _p(rf"(?<![a-z0-9.])({_NUM})\s*(kgs?|kilos?|grams?|g)(?![a-z0-9/])")
_VOLUME = _p(rf"(?<![a-z0-9.])({_NUM})\s*(ml|ltrs?|litres?|liters?|lt|l)(?![a-z0-9/])")
_LENGTH = _p(rf"(?<![a-z0-9.])({_NUM})\s*({_LEN_U})")
_THREAD = _p(rf"(?<![a-z0-9.])m(\d{{1,2}})(?:\s*x\s*({_NUM})\s*(?:mm{_END})?)?(?![a-z0-9.])")
_TERM = rf"{_NUM}\s*(?:{_LEN_U})?"
_CHAIN = _p(rf"(?<![a-z0-9.,/-])({_TERM})((?:\s*(?:x|by)\s*{_TERM}){{1,2}})(?![a-z0-9.]|/\d)")
_SEP = _p(r"(\s*(?:x|by)\s*)")
_TERM_PARTS = _p(rf"^({_NUM})\s*({_LEN_U})?$")
_TRAIL = _p(r"(?<![a-z0-9.])x\s*(\d+)\s*$")
_LEAD_INT = _p(r"^\s*(\d+)\s*(?:x\s*)?(?=\S)")
_QTY_KW = _p(r"\b(?:qty|quantity)\s*[:=]?\s*(\d+)\b")
_TEXT_ATTR_VALUE = rf"([a-z0-9\-]+(?: [a-z0-9\-]+){{0,{_MAX_TEXT_ATTR_WORDS - 1}}})"


def gtin_check_digit(body: str) -> int:
    """GS1 mod-10 check digit for the digits before it (weights 3, 1, 3, 1 from the right)."""
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10


def is_valid_gtin(code: str) -> bool:
    return (code.isdigit() and len(code) in (8, 12, 13, 14)
            and gtin_check_digit(code[:-1]) == int(code[-1]))


def normalise_mpn(raw: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", raw.upper())


def _dec(text: str) -> Decimal:
    return Decimal(text.replace(",", ""))


@dataclass
class _Slot:
    kind: str  # gtin mpn pack qty trail measure size text thread ambig
    raw: str
    payload: Any = None
    qty_like: bool = False  # a size that could also be "quantity x measure"


@dataclass(frozen=True)
class _Term:
    value: Decimal
    unit: str | None
    has_point: bool
    raw: str

    @property
    def bare_int(self) -> bool:
        return self.unit is None and not self.has_point


class _Work:
    """The line text with extracted spans replaced by numbered placeholders."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.slots: list[_Slot] = []

    def sub(self, pattern: re.Pattern[str],
            make: Callable[[re.Match[str]], list[_Slot] | None]) -> None:
        def repl(m: re.Match[str]) -> str:
            made = make(m)
            if not made:
                return m.group(0)
            marks = []
            for slot in made:
                self.slots.append(slot)
                marks.append(f"⟦{len(self.slots) - 1}⟧")
            return " " + " ".join(marks) + " "

        self.text = pattern.sub(repl, self.text)


def _measure(kind: MeasureKind, num: str, unit_raw: str, raw: str) -> Measure | None:
    unit = normalise_unit(re.sub(r"\s+", "", unit_raw))
    if unit is None:
        return None
    value, canonical = to_canonical(_dec(num), unit)
    return Measure(kind=kind, value=value, unit=canonical, raw=raw.strip())


def _term(text: str) -> _Term:
    m = _TERM_PARTS.match(text.strip())
    assert m is not None  # the chain pattern only matches well-formed terms
    unit = normalise_unit(m.group(2)) if m.group(2) else None
    return _Term(_dec(m.group(1)), unit, "." in m.group(1), text.strip())


def _size_slot(terms: list[_Term], raw: str, *, allow_qty_like: bool) -> _Slot:
    units = [t.unit for t in terms if t.unit]
    inferred = False
    chain_unit = units[-1] if units else None
    if chain_unit is None:
        inferred = all(t.value <= 10 for t in terms) and any(t.has_point for t in terms)
        chain_unit = "m" if inferred else "mm"
    values: list[Decimal] = []
    for t in terms:
        unit = t.unit or chain_unit
        if t.unit is None and unit in ("m", "cm") and t.value >= 100:
            unit = "mm"  # "2.4m x 1200": a bare 1200 is millimetres
        values.append(to_canonical(t.value, unit)[0])
    qty_like = False
    if allow_qty_like and len(terms) == 2:
        first, second = terms
        qty_like = (first.bare_int and (second.unit is not None or second.has_point)) or (
            second.bare_int and first.unit is not None)
    size = SizeToken(values=tuple(values), raw=raw.strip(), unit_inferred=inferred)
    return _Slot("size", raw.strip(), size, qty_like=qty_like)


def _is_length_slot(slot: _Slot) -> bool:
    if slot.kind == "size":
        return True
    return slot.kind == "measure" and slot.payload.kind is MeasureKind.LENGTH


def _size_token(size: SizeToken) -> str:
    values = list(size.values)
    if not size.thread_prefix:
        values.sort(reverse=True)  # "12.5 x 1200 x 2400" and "2400x1200x12.5" are one size
    token = "x".join(format_decimal(v) for v in values)
    return f"m{token}" if size.thread_prefix else token


def _typed_tokens(attributes: Iterable[Any]) -> tuple[str, ...]:
    """`name:value[unit]` tokens that make stated numbers and grades visible to retrieval."""
    out = []
    for a in attributes:
        unit = "" if a.unit in (None, "nr") else a.unit
        out.append(f"{a.name}:{a.value.replace(' ', '_')}{unit}")
    return tuple(sorted(out))


class LineParser:
    """Parses order lines against one ontology and the catalogue's brands and MPNs."""

    def __init__(self, ontology: Ontology, *, brands: Iterable[str] = (),
                 mpns: Iterable[str] = ()) -> None:
        self.ontology = ontology
        self.norm = ontology.normaliser
        lex = ontology.lexicon
        words = sorted(lex.count_words, key=len, reverse=True)
        alt = "|".join(re.escape(w) for w in words)
        self._count_word = _p(rf"^\s*(\d+)\s*(?:x\s*)?({alt})(?![a-z0-9])")
        self._count_trail = _p(rf"(?<![a-z0-9.])(\d+)\s*({alt})\s*$")
        safe_alt = "|".join(re.escape(w) for w in words if w in _ANYWHERE_COUNT)
        self._count_any = _p(rf"(?<![a-z0-9.])(\d+)\s*({safe_alt})(?![a-z0-9])")
        self._count_label = dict(lex.count_words)
        pack_alt = "|".join(re.escape(w) + r"(?:e?s)?" for w in lex.pack_words)
        self._pack_of = _p(rf"(?:^\s*(\d+)\s*)?\b({pack_alt})\s+of\s+(\d+)\b")
        self._pack_n = _p(r"(?<![a-z0-9.])(\d+)\s*-?\s*(?:pk|pack)(?![a-z0-9])")
        self._brands = self._brand_table(brands)
        self._mpns = {normalise_mpn(m) for m in mpns if normalise_mpn(m)}
        aliases = sorted({a for t in ontology.types.values() for attr in t.attributes
                          if attr.kind is AttrKind.TEXT for a in attr.aliases},
                         key=len, reverse=True)
        self._text_attr = (
            _p(rf"\b({'|'.join(re.escape(a) for a in aliases)})\s*[:=]\s*"
               rf"{_TEXT_ATTR_VALUE}(?=\s*[,;]|\s*$)") if aliases else None)

    # ------------------------------------------------------------------ brands

    def _brand_table(self, brands: Iterable[str]) -> list[tuple[tuple[str, ...], str]]:
        table: dict[tuple[str, ...], str] = {}
        for brand in brands:
            tokens = self.norm.tokens(brand)
            if tokens:
                table[tokens] = brand
        return sorted(table.items(), key=lambda kv: (-len(kv[0]), kv[0]))

    def _take_brand(self, elements: list[bd.Element]) -> str | None:
        words = [el.text if isinstance(el, bd.Word) else None for el in elements]
        for phrase, brand in self._brands:
            for start in range(len(words) - len(phrase) + 1):
                if tuple(words[start:start + len(phrase)]) == phrase:
                    for i in range(start, start + len(phrase)):
                        elements[i] = bd.Break()
                    return brand
        return None

    # ------------------------------------------------------------------ extraction passes

    def _identifiers(self, work: _Work) -> None:
        def gtin(m: re.Match[str]) -> list[_Slot] | None:
            code = m.group(1)
            if not is_valid_gtin(code):
                return None
            before = m.string[max(0, m.start() - 10):m.start()]
            if len(code) == 8 and not any(mk in before for mk in _GTIN_MARKERS):
                return None
            return [_Slot("gtin", code, code)]

        def mpn_explicit(m: re.Match[str]) -> list[_Slot] | None:
            token = m.group(1).rstrip("./-_")
            if len(token) < 3 or not any(c.isdigit() for c in token):
                return None
            return [_Slot("mpn", token, normalise_mpn(token))]

        def mpn_token(m: re.Match[str]) -> list[_Slot] | None:
            token = m.group(0)
            normal = normalise_mpn(token)
            known = normal in self._mpns and any(c.isdigit() for c in normal)
            if known or _IMPLICIT_MPN.match(token):
                return [_Slot("mpn", token, normal)]
            return None

        work.sub(_GTIN, gtin)
        work.sub(_MPN_EXPLICIT, mpn_explicit)
        work.sub(_MPN_TOKEN, mpn_token)

    def _text_attrs(self, work: _Work) -> None:
        if self._text_attr is None:
            return

        def make(m: re.Match[str]) -> list[_Slot] | None:
            return [_Slot("text", m.group(0), (m.group(1), m.group(2)))]

        work.sub(self._text_attr, make)

    def _packs_and_quantities(self, work: _Work, *, is_line: bool) -> None:
        def pack_of(m: re.Match[str]) -> list[_Slot] | None:
            slots = [_Slot("pack", m.group(0).strip(), int(m.group(3)))]
            if is_line and m.group(1):
                unit = re.sub(r"(e?s)$", "", m.group(2))
                slots.insert(0, _Slot("qty", m.group(0).strip(), (Decimal(m.group(1)), unit)))
            return slots

        def pack_n(m: re.Match[str]) -> list[_Slot] | None:
            return [_Slot("pack", m.group(0).strip(), int(m.group(1)))]

        work.sub(self._pack_of, pack_of)
        work.sub(self._pack_n, pack_n)
        if not is_line:
            return

        def qty_kw(m: re.Match[str]) -> list[_Slot] | None:
            return [_Slot("qty", m.group(0).strip(), (Decimal(m.group(1)), None))]

        def qty_lead(m: re.Match[str]) -> list[_Slot] | None:
            label = self._count_label[m.group(2)]
            return [_Slot("qty", m.group(0).strip(), (Decimal(m.group(1)), label))]

        work.sub(_QTY_KW, qty_kw)
        work.sub(self._count_word, qty_lead)
        work.sub(self._count_trail, qty_lead)
        work.sub(self._count_any, qty_lead)

    def _measures(self, work: _Work) -> None:
        def maker(kind: MeasureKind) -> Callable[[re.Match[str]], list[_Slot] | None]:
            def make(m: re.Match[str]) -> list[_Slot] | None:
                found = _measure(kind, m.group(1), m.group(2), m.group(0))
                return [_Slot("measure", m.group(0).strip(), found)] if found else None
            return make

        for pattern, kind in ((_AREA, MeasureKind.AREA), (_FLOW, MeasureKind.FLOW),
                              (_PDENS, MeasureKind.POWER_DENSITY), (_POWER, MeasureKind.POWER),
                              (_WEIGHT, MeasureKind.WEIGHT), (_VOLUME, MeasureKind.VOLUME)):
            work.sub(pattern, maker(kind))

    def _threads_and_sizes(self, work: _Work, *, is_line: bool) -> None:
        def thread(m: re.Match[str]) -> list[_Slot] | None:
            if m.group(2) is None:
                return [_Slot("thread", m.group(0).strip(), None)]
            size = SizeToken(values=(_dec(m.group(1)), _dec(m.group(2))),
                             raw=m.group(0).strip(), thread_prefix=True)
            return [_Slot("size", size.raw, size)]

        def chain(m: re.Match[str]) -> list[_Slot] | None:
            return self._chain_slots(m.group(0), is_line=is_line)

        def single(m: re.Match[str]) -> list[_Slot] | None:
            found = _measure(MeasureKind.LENGTH, m.group(1), m.group(2), m.group(0))
            return [_Slot("measure", m.group(0).strip(), found)] if found else None

        work.sub(_THREAD, thread)
        work.sub(_CHAIN, chain)
        work.sub(_LENGTH, single)

    def _chain_slots(self, raw: str, *, is_line: bool) -> list[_Slot]:
        parts = _SEP.split(raw.strip())
        terms = [_term(t) for t in parts[0::2]]
        tight = [s == "x" for s in parts[1::2]]
        if is_line and len(terms) == 3 and tight == [False, True] and terms[0].bare_int:
            qty = _Slot("qty", terms[0].raw, (terms[0].value, None))
            size = _size_slot(terms[1:], "x".join(t.raw for t in terms[1:]), allow_qty_like=False)
            return [qty, size]
        if is_line and len(terms) == 3 and tight == [True, False] and terms[2].bare_int:
            size = _size_slot(terms[:2], "x".join(t.raw for t in terms[:2]), allow_qty_like=False)
            return [size, _Slot("trail", terms[2].raw, terms[2].value)]
        return [_size_slot(terms, raw, allow_qty_like=is_line)]

    def _trailing(self, work: _Work) -> None:
        def make(m: re.Match[str]) -> list[_Slot] | None:
            return [_Slot("trail", m.group(0).strip(), Decimal(m.group(1)))]

        work.sub(_TRAIL, make)

    def _lead_measure_ambiguity(self, work: _Work) -> Ambiguity | None:
        """A bare integer straight before a length ("10 12.5mm boards") could be a size."""
        lead = _LEAD_INT.match(work.text)
        if lead is None:
            return None
        nxt = _PH.match(work.text[lead.end():].lstrip())
        if nxt is None:
            return None
        slot = work.slots[int(nxt.group(1))]
        if not _is_length_slot(slot):
            return None
        slot.kind = "ambig"
        raw = f"{lead.group(1)} {slot.raw}"
        return Ambiguity(
            kind=AmbiguityKind.QUANTITY_SIZE, raw=raw,
            readings=(f"quantity {lead.group(1)} of an item sized {slot.raw}",
                      f"{raw} read together as one size"))

    # ------------------------------------------------------------------ elements

    def _elements(self, work: _Work) -> list[bd.Element]:
        out: list[bd.Element] = []
        pos = 0
        for m in _PH.finditer(work.text):
            out.extend(bd.Word(t) for t in self.norm.tokens(work.text[pos:m.start()]))
            out.append(self._slot_element(work.slots[int(m.group(1))]))
            pos = m.end()
        out.extend(bd.Word(t) for t in self.norm.tokens(work.text[pos:]))
        return out

    def _slot_element(self, slot: _Slot) -> bd.Element:
        if slot.kind == "measure":
            return bd.MeasureEl(slot.payload)
        if slot.kind == "size":
            return bd.SizeEl(slot.payload)
        if slot.kind == "pack":
            return bd.PackEl(slot.payload, slot.raw)
        if slot.kind == "text":
            alias, value = slot.payload
            return bd.TextEl(alias, value, slot.raw)
        return bd.Break()

    # ------------------------------------------------------------------ type hint

    def _score_types(self, words: list[str | None]) -> dict[str, tuple[int, int, str]]:
        scores: dict[str, tuple[int, int, str]] = {}
        for type_id, phrases in self.ontology.type_phrases.items():
            for phrase in phrases:
                for start in range(len(words) - len(phrase) + 1):
                    if tuple(words[start:start + len(phrase)]) == phrase:
                        key = (len(phrase), start + len(phrase), " ".join(phrase))
                        if type_id not in scores or key[:2] > scores[type_id][:2]:
                            scores[type_id] = key
        return scores

    def _type_hint(self, elements: list[bd.Element]) -> TypeHint:
        """Longest synonym phrase wins; ties go to the phrase nearer the end (English compound
        nouns put the head noun last); a remaining tie is uncertain and lists the tied types."""
        words: list[str | None] = [el.text if isinstance(el, bd.Word) else None
                                   for el in elements]
        cut = next((i for i, w in enumerate(words) if w in _CONTEXT_WORDS), len(words))
        scores = self._score_types(words[:cut]) or self._score_types(words)
        if not scores:
            return TypeHint()
        best = max(s[:2] for s in scores.values())
        top = sorted(t for t, s in scores.items() if s[:2] == best)
        matched = tuple(sorted({scores[t][2] for t in top}))
        if len(top) == 1:
            return TypeHint(type_id=top[0], certain=True, matched=matched)
        return TypeHint(alternatives=tuple(top), matched=matched)

    # ------------------------------------------------------------------ tokens

    def _canonical_tokens(self, elements: list[bd.Element],
                          dropped: frozenset[int]) -> tuple[list[str], list[str]]:
        words: list[str] = []
        canon: list[str] = []
        for i, el in enumerate(elements):
            if i in dropped:
                continue
            if isinstance(el, bd.Word) and el.text not in self.norm.noise_words:
                words.append(el.text)
                canon.append(el.text)
            elif isinstance(el, bd.MeasureEl):
                canon.append(f"{format_decimal(el.measure.value)}{el.measure.unit}")
            elif isinstance(el, bd.SizeEl):
                canon.append(_size_token(el.size))
            elif isinstance(el, bd.PackEl):
                canon.append(f"pack{el.n}")
            elif isinstance(el, bd.TextEl):
                canon.extend(self.norm.content_tokens(el.value))
        return words, canon

    def title_tokens(self, title: str) -> tuple[str, ...]:
        """Canonical tokens of a catalogue title: same normalisation as a line, no quantity."""
        work = _Work(self._prepare(title))
        self._identifiers(work)
        self._packs_and_quantities(work, is_line=False)
        self._measures(work)
        self._threads_and_sizes(work, is_line=False)
        _words, canon = self._canonical_tokens(self._elements(work), frozenset())
        return tuple(sorted(set(canon)))

    # ------------------------------------------------------------------ parse

    def _prepare(self, raw: str) -> str:
        text = clean_text(raw)
        for pattern, repl in _PRE:
            text = pattern.sub(repl, text)
        return text

    def parse(self, line: OrderLine) -> ParsedLine:
        cleaned = self._prepare(line.text)
        work = _Work(cleaned)
        self._text_attrs(work)
        self._identifiers(work)
        self._packs_and_quantities(work, is_line=True)
        self._measures(work)
        self._threads_and_sizes(work, is_line=True)
        self._trailing(work)
        lead_ambiguity = self._lead_measure_ambiguity(work)
        elements = self._elements(work)
        brand = self._take_brand(elements)
        hint = self._type_hint(elements)
        ptype = self.ontology.types[hint.type_id] if hint.type_id else None
        ambiguities = self._size_ambiguities(work, elements, ptype)
        if lead_ambiguity is not None:
            ambiguities.append(lead_ambiguity)
        return self._assemble(line, cleaned, work, elements, brand, hint, ptype, ambiguities)

    def _size_ambiguities(self, work: _Work, elements: list[bd.Element],
                          ptype: ProductType | None) -> list[Ambiguity]:
        """A `20 x 12.5mm` chain is a size only if the certain type has a plausible size."""
        found: list[Ambiguity] = []
        qty_like = {id(s.payload) for s in work.slots if s.kind == "size" and s.qty_like}
        for i, el in enumerate(elements):
            if not (isinstance(el, bd.SizeEl) and id(el.size) in qty_like):
                continue
            if ptype is not None and bd.size_is_plausible(ptype, el.size):
                continue
            first, second = (format_decimal(v) for v in el.size.values)
            found.append(Ambiguity(
                kind=AmbiguityKind.QUANTITY_SIZE, raw=el.size.raw,
                readings=(f"a quantity and an item size, in some order ({el.size.raw})",
                          f"one size of {first} x {second} mm")))
            elements[i] = bd.Break()
        return found

    def _quantity(self, line: OrderLine, work: _Work, ptype: ProductType | None,
                  ) -> tuple[Decimal | None, str | None, int | None, list[str]]:
        quantity: Decimal | None = None
        unit: str | None = None
        pack = next((int(s.payload) for s in work.slots if s.kind == "pack"), None)
        stray: list[str] = []
        for s in work.slots:
            if s.kind == "qty" and quantity is None:
                quantity, unit = s.payload
        for s in work.slots:
            if s.kind != "trail":
                continue
            if ptype is not None and ptype.trailing_multiplier == "pack" and pack is None:
                pack = int(s.payload)
            elif quantity is None:
                quantity = s.payload
            else:
                stray.append(s.raw)
        if line.quantity is not None:
            quantity, unit = line.quantity, line.uom
        return quantity, unit, pack, stray

    def _assemble(self, line: OrderLine, cleaned: str, work: _Work, elements: list[bd.Element],
                  brand: str | None, hint: TypeHint, ptype: ProductType | None,
                  ambiguities: list[Ambiguity]) -> ParsedLine:
        quantity, qty_unit, pack_size, stray = self._quantity(line, work, ptype)
        if pack_size is not None and not any(isinstance(e, bd.PackEl) for e in elements):
            elements.append(bd.PackEl(pack_size, f"x{pack_size}"))
        bound = (bd.bind_attributes(self.ontology, ptype, elements) if ptype is not None
                 else bd.BindResult(unbound=_unplaced(elements)))
        dropped: set[int] = set()
        lead = elements[0] if elements else None
        if (isinstance(lead, bd.Word) and lead.text.isdigit() and 0 not in bound.consumed_words
                and line.quantity is None and quantity is None):
            quantity, dropped = Decimal(lead.text), {0}  # a leading bare number is a quantity
        words, canon = self._canonical_tokens(elements, frozenset(dropped))
        typed = _typed_tokens(bound.attributes)
        slots = work.slots
        return ParsedLine(
            line_id=line.line_id, raw_text=line.text, cleaned_text=cleaned,
            quantity=quantity, quantity_unit=qty_unit,
            measures=tuple(e.measure for e in elements if isinstance(e, bd.MeasureEl)),
            sizes=tuple(e.size for e in elements if isinstance(e, bd.SizeEl)),
            pack_size=pack_size, grades=_grades(elements, dropped),
            brand=brand,
            mpn=next((str(s.payload) for s in slots if s.kind == "mpn"), None),
            gtin=next((str(s.payload) for s in slots if s.kind == "gtin"), None),
            type_hint=hint, attributes=bound.attributes, conflicts=bound.conflicts,
            implausible=bound.implausible,
            unbound=(*bound.unbound, *stray, *(s.raw for s in slots if s.kind == "thread")),
            ambiguities=tuple(ambiguities), tokens=tuple(words),
            canonical_text=" ".join(sorted(set(canon))), typed_tokens=typed,
            retrieval_text=" ".join(sorted(set(canon) | set(typed))),
            kind=LineKind.SPECIFIC if (brand or any(
                s.kind in ("mpn", "gtin") for s in slots)) else LineKind.GENERIC,
        )


def _unplaced(elements: list[bd.Element]) -> tuple[str, ...]:
    """Raw text of every number the line states, for when no type can place them."""
    raws: list[str] = []
    for el in elements:
        if isinstance(el, bd.MeasureEl):
            raws.append(el.measure.raw)
        elif isinstance(el, bd.SizeEl):
            raws.append(el.size.raw)
        elif isinstance(el, bd.PackEl | bd.TextEl):
            raws.append(el.raw)
    return tuple(raws)


def _grades(elements: list[bd.Element], dropped: set[int]) -> tuple[str, ...]:
    found = [el.text for i, el in enumerate(elements)
             if i not in dropped and isinstance(el, bd.Word) and _GRADE.match(el.text)]
    return tuple(dict.fromkeys(found))
