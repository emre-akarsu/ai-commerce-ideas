"""Deterministic parser for deep groove ball bearing designations (spec §6.2, F2).

Rules-first (ADR-006): no LLM, no guessing.

* Dimensions come only from the ISO 15 boundary-dimension table below (series 60xx, 62xx, 63xx,
  bore codes 00-10). Values we are not certain of are omitted, never invented; an unknown
  designation produces NO attributes.
* Suffix tokens map to the seal classes ``open | shield | contact_seal`` and the clearance /
  tolerance classes. A designation with no seal suffix is *ambiguous* (people drop suffixes), so
  ``seal_type`` is left unresolved and the normaliser must ask. A one-sided suffix (RS, Z, ...)
  is likewise unresolved because it does not say whether both sides are fitted.
* Anything we cannot interpret is recorded as ``unrecognised_suffix`` so downstream tier logic can
  refuse to treat the request as fully specified.

Every attribute carries provenance (R3): STANDARD for table dimensions, USER_INPUT for tokens
typed by the requester.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import NamedTuple

from components.core.domain import Attribute, AttrSource

ISO15_SOURCE_REF = "ISO 15 boundary dimensions"
# Edition year only (ISO 15:2017); the month/day are not significant.
ISO15_EDITION_DATE = date(2017, 1, 1)


class BoundaryDimensions(NamedTuple):
    bore_mm: int
    outer_diameter_mm: int
    width_mm: int


# (bore d, outer diameter D, width B) in mm. Bore codes 00-03 = 10/12/15/17 mm; from 04 up the
# bore is code x 5. Only values we are certain of are listed.
_ISO15: dict[str, BoundaryDimensions] = {
    # 60xx (dimension series 10)
    "6000": BoundaryDimensions(10, 26, 8),
    "6001": BoundaryDimensions(12, 28, 8),
    "6002": BoundaryDimensions(15, 32, 9),
    "6003": BoundaryDimensions(17, 35, 10),
    "6004": BoundaryDimensions(20, 42, 12),
    "6005": BoundaryDimensions(25, 47, 12),
    "6006": BoundaryDimensions(30, 55, 13),
    "6007": BoundaryDimensions(35, 62, 14),
    "6008": BoundaryDimensions(40, 68, 15),
    "6009": BoundaryDimensions(45, 75, 16),
    "6010": BoundaryDimensions(50, 80, 16),
    # 62xx (dimension series 02)
    "6200": BoundaryDimensions(10, 30, 9),
    "6201": BoundaryDimensions(12, 32, 10),
    "6202": BoundaryDimensions(15, 35, 11),
    "6203": BoundaryDimensions(17, 40, 12),
    "6204": BoundaryDimensions(20, 47, 14),
    "6205": BoundaryDimensions(25, 52, 15),
    "6206": BoundaryDimensions(30, 62, 16),
    "6207": BoundaryDimensions(35, 72, 17),
    "6208": BoundaryDimensions(40, 80, 18),
    "6209": BoundaryDimensions(45, 85, 19),
    "6210": BoundaryDimensions(50, 90, 20),
    # 63xx (dimension series 03)
    "6300": BoundaryDimensions(10, 35, 11),
    "6301": BoundaryDimensions(12, 37, 12),
    "6302": BoundaryDimensions(15, 42, 13),
    "6303": BoundaryDimensions(17, 47, 14),
    "6304": BoundaryDimensions(20, 52, 15),
    "6305": BoundaryDimensions(25, 62, 17),
    "6306": BoundaryDimensions(30, 72, 19),
    "6307": BoundaryDimensions(35, 80, 21),
    "6308": BoundaryDimensions(40, 90, 23),
    "6309": BoundaryDimensions(45, 100, 25),
    "6310": BoundaryDimensions(50, 110, 27),
}


def lookup_dimensions(base: str) -> BoundaryDimensions | None:
    return _ISO15.get(base)


def iso_designation_for(bore_mm: object, outer_diameter_mm: object, width_mm: object) -> str | None:
    """Reverse lookup: the unique ISO 15 designation with these boundary dimensions, if any."""
    try:
        want = (Decimal(str(bore_mm)), Decimal(str(outer_diameter_mm)), Decimal(str(width_mm)))
    except InvalidOperation:
        return None
    hits = [b for b, d in _ISO15.items() if tuple(Decimal(x) for x in d) == want]
    return hits[0] if len(hits) == 1 else None


# ---------------------------------------------------------------- suffix tables


class _SealInfo(NamedTuple):
    seal_type: str
    sides: int


_SEAL: dict[str, _SealInfo] = {
    # rubber contact seal, both sides
    "2RS": _SealInfo("contact_seal", 2),
    "2RS1": _SealInfo("contact_seal", 2),
    "2RSH": _SealInfo("contact_seal", 2),
    "2RSR": _SealInfo("contact_seal", 2),
    "DDU": _SealInfo("contact_seal", 2),
    "LLU": _SealInfo("contact_seal", 2),
    # metal shield, both sides
    "2Z": _SealInfo("shield", 2),
    "ZZ": _SealInfo("shield", 2),
    "2ZR": _SealInfo("shield", 2),
    # one-sided variants: not resolvable to a both-sides class
    "RS": _SealInfo("contact_seal", 1),
    "RS1": _SealInfo("contact_seal", 1),
    "RSH": _SealInfo("contact_seal", 1),
    "RSR": _SealInfo("contact_seal", 1),
    "DU": _SealInfo("contact_seal", 1),
    "LU": _SealInfo("contact_seal", 1),
    "Z": _SealInfo("shield", 1),
    "ZR": _SealInfo("shield", 1),
}
_CLEARANCE = frozenset({"C2", "C3", "C4", "C5", "CN"})
_PRECISION = frozenset({"P0", "P6", "P5", "P4", "P2"})

# longest first so "2RS1" is not read as "2RS" + "1"
_KNOWN_TOKENS: tuple[str, ...] = tuple(
    sorted({*_SEAL, *_CLEARANCE, *_PRECISION}, key=lambda t: (-len(t), t))
)

BOTH_SIDE_SEAL_TOKENS = tuple(t for t, i in _SEAL.items() if i.sides == 2)
CLEARANCE_TOKENS = tuple(sorted(_CLEARANCE))
PRECISION_TOKENS = tuple(sorted(_PRECISION))


def seal_class_for_token(token: str) -> str | None:
    """Seal class for a both-sides token (``2RS`` -> ``contact_seal``), else None."""
    info = _SEAL.get(token.upper())
    return info.seal_type if info and info.sides == 2 else None


def _split_known(token: str) -> list[str] | None:
    """Split an upper-case token into known suffix tokens; None unless fully consumed."""
    out: list[str] = []
    i = 0
    while i < len(token):
        for known in _KNOWN_TOKENS:
            if token.startswith(known, i):
                out.append(known)
                i += len(known)
                break
        else:
            return None
    return out


# ---------------------------------------------------------------- parsing

_BASE_RE = re.compile(r"(?<![0-9A-Za-z])(6[023]\d{2})")
_ATTACHED_RE = re.compile(r"[A-Za-z0-9]+")
_SEP_TOKEN_RE = re.compile(r"([\s\-/]+)([A-Za-z0-9]+)")
_MAX_UNRECOGNISED_LEN = 6


@dataclass(frozen=True)
class ParsedDesignation:
    raw: str
    base: str | None
    known: bool
    attributes: tuple[Attribute, ...] = ()
    unresolved: tuple[str, ...] = ()  # critical attributes the designation does not settle
    unrecognised_suffix: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()  # machine-readable flags, e.g. "single_sided_seal:RS"
    span: tuple[int, int] = (0, 0)

    def attribute_map(self) -> dict[str, Attribute]:
        return {a.name: a for a in self.attributes}


def implied_normal_precision() -> Attribute:
    """Tolerance-class default when no suffix is given (recorded as an assumption, not a guess)."""
    return Attribute(
        name="precision_class",
        value="P0",
        source=AttrSource.RULE,
        source_ref="designation convention: no tolerance-class suffix denotes Normal (P0)",
        confidence=0.8,
    )


def _looks_like_suffix(token: str) -> bool:
    return (
        len(token) <= _MAX_UNRECOGNISED_LEN
        and any(c.isalpha() for c in token)
        and token.isalnum()
    )


def _ordered_unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _build(
    raw: str,
    base: str,
    recognised: list[str],
    unrecognised: list[str],
    span: tuple[int, int],
) -> ParsedDesignation:
    dims = lookup_dimensions(base)
    if dims is None:
        # Never guess: unknown designation -> no attributes at all.
        return ParsedDesignation(raw=raw, base=base, known=False, span=span)

    src_ref = f"designation suffix in {raw!r}"
    attrs: list[Attribute] = []
    notes: list[str] = []
    unresolved: list[str] = []

    seal_tokens = _ordered_unique([t for t in recognised if t in _SEAL])
    clearances = _ordered_unique([t for t in recognised if t in _CLEARANCE])
    precisions = _ordered_unique([t for t in recognised if t in _PRECISION])

    seal_type: str | None = None
    if seal_tokens:
        infos = {_SEAL[t] for t in seal_tokens}
        if len(infos) == 1:
            info = next(iter(infos))
            if info.sides == 2:
                seal_type = info.seal_type
            else:
                notes.append(f"single_sided_seal:{'/'.join(seal_tokens)}")
        else:
            notes.append(f"conflicting_seal_tokens:{'/'.join(seal_tokens)}")
    if seal_type is None:
        unresolved.append("seal_type")
    if len(clearances) != 1:
        unresolved.append("internal_clearance")
        if len(clearances) > 1:
            notes.append(f"conflicting_clearance_tokens:{'/'.join(clearances)}")
    if len(precisions) > 1:
        notes.append(f"conflicting_precision_tokens:{'/'.join(precisions)}")
        unresolved.append("precision_class")

    canonical = base
    if seal_tokens:
        canonical += "-" + "-".join(seal_tokens)
    canonical += "".join("/" + t for t in [*clearances, *precisions, *unrecognised])

    def user(name: str, value: str) -> Attribute:
        return Attribute(name=name, value=value, source=AttrSource.USER_INPUT, source_ref=src_ref)

    def std(name: str, value: str, unit: str | None = None) -> Attribute:
        return Attribute(
            name=name, value=value, unit=unit, source=AttrSource.STANDARD,
            source_ref=ISO15_SOURCE_REF,
        )  # fmt: skip

    attrs.append(
        Attribute(
            name="designation", value=canonical, source=AttrSource.USER_INPUT,
            source_ref=f"user text {raw!r}",
        )  # fmt: skip
    )
    attrs.append(std("series", base[:2]))
    attrs.append(std("bore_mm", str(dims.bore_mm), "mm"))
    attrs.append(std("outer_diameter_mm", str(dims.outer_diameter_mm), "mm"))
    attrs.append(std("width_mm", str(dims.width_mm), "mm"))
    if seal_type is not None:
        attrs.append(user("seal_type", seal_type))
    if seal_tokens:
        attrs.append(user("seal_designation", "/".join(seal_tokens)))
    if len(clearances) == 1:
        attrs.append(user("internal_clearance", clearances[0]))
    if len(precisions) == 1:
        attrs.append(user("precision_class", precisions[0]))
    if unrecognised:
        attrs.append(user("unrecognised_suffix", "/".join(unrecognised)))
        notes.append(f"unrecognised_suffix:{'/'.join(unrecognised)}")

    return ParsedDesignation(
        raw=raw,
        base=base,
        known=True,
        attributes=tuple(attrs),
        unresolved=tuple(unresolved),
        unrecognised_suffix=tuple(unrecognised),
        notes=tuple(notes),
        span=span,
    )


def _parse_at(text: str, match: re.Match[str]) -> ParsedDesignation | None:
    base = match.group(1)
    rest = text[match.end() :]
    recognised: list[str] = []
    unrecognised: list[str] = []
    pos = 0

    if rest[:1].isdigit():
        # "62052RS": the digit belongs to a suffix only if it starts a known both-sides token.
        if not rest.upper().startswith(("2RS", "2Z")):
            return None
    attached = _ATTACHED_RE.match(rest)
    if attached:
        known = _split_known(attached.group().upper())
        if known is None:
            unrecognised.append(attached.group().upper())
        else:
            recognised.extend(known)
        pos = attached.end()

    while True:
        sm = _SEP_TOKEN_RE.match(rest, pos)
        if not sm:
            break
        sep, tok = sm.groups()
        known = _split_known(tok.upper())
        if known is not None:
            recognised.extend(known)
        elif sep.strip() and _looks_like_suffix(tok):
            # a hyphen/slash group continues the designation even if we cannot interpret it
            unrecognised.append(tok.upper())
        else:
            break
        pos = sm.end()

    span = (match.start(), match.end() + pos)
    raw = text[span[0] : span[1]].strip()
    return _build(raw, base, recognised, unrecognised, span)


def find_designations(text: str) -> list[ParsedDesignation]:
    """All designations (60xx/62xx/63xx pattern) found in free text, known or not."""
    found: list[ParsedDesignation] = []
    consumed_to = 0
    for m in _BASE_RE.finditer(text):
        if m.start() < consumed_to:
            continue
        parsed = _parse_at(text, m)
        if parsed is None:
            continue
        found.append(parsed)
        consumed_to = parsed.span[1]
    return found


def parse_designation(text: str) -> ParsedDesignation:
    """Parse the first designation in ``text``; unknown/absent -> ``known=False``, no attributes."""
    found = find_designations(text)
    if found:
        return found[0]
    return ParsedDesignation(raw=text.strip(), base=None, known=False)
