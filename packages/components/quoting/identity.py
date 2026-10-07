"""Named identity (CLAUDE.md rule 2, spec R2): a line that names a brand, MPN or GTIN is priced
against that product only.

The matching gate already refuses to accept a group whose members do not carry the named identity.
This module is the quoting step's own check on the same facts (defence in depth): the SKUs about to
be priced are re-verified against the parsed line, and a failure means NOTHING is priced for the
line. It also builds the generic version of a named line so that alternatives can be offered as
"suggested alternative, needs approval" (never priced, never in a total).
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from components.matching.models import CatalogItem, LineKind, ParsedLine
from components.matching.parser import normalise_mpn
from components.matching.text import TextNormaliser as Normaliser

_MARKERS = {"gtin", "ean", "barcode", "upc", "mpn", "part", "code", "sku", "ref"}


def is_named(parsed: ParsedLine) -> bool:
    return parsed.kind is LineKind.SPECIFIC


def carries_identity(parsed: ParsedLine, item: CatalogItem, norm: Normaliser) -> bool:
    """True when `item` is the brand, MPN and GTIN the line names (all that it names)."""
    if parsed.brand is not None and norm.tokens(parsed.brand) != norm.tokens(item.brand):
        return False
    if parsed.mpn is not None and (item.mpn is None or normalise_mpn(item.mpn) != parsed.mpn):
        return False
    return parsed.gtin is None or item.gtin == parsed.gtin


def all_carry_identity(
    parsed: ParsedLine, items: Iterable[CatalogItem], norm: Normaliser
) -> bool:
    return all(carries_identity(parsed, i, norm) for i in items)


def _brand_pattern(parsed: ParsedLine, norm: Normaliser) -> re.Pattern[str] | None:
    if parsed.brand is None:
        return None
    tokens = norm.tokens(parsed.brand)
    if not tokens:
        return None
    body = r"[\W_]+".join(re.escape(t) for t in tokens)
    return re.compile(rf"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9])", re.IGNORECASE)


def _is_identifier(word: str, parsed: ParsedLine) -> bool:
    bare = word.strip(",;:()")
    if parsed.mpn is not None and normalise_mpn(bare) == parsed.mpn:
        return True
    return parsed.gtin is not None and bare == parsed.gtin


def strip_identity(text: str, parsed: ParsedLine, norm: Normaliser) -> str:
    """`text` without the brand, MPN and GTIN it names (the generic line it implies)."""
    pattern = _brand_pattern(parsed, norm)
    out = pattern.sub(" ", text) if pattern is not None else text
    kept: list[str] = []
    for word in out.split():
        if _is_identifier(word, parsed):
            if kept and kept[-1].lower().strip(",;:") in _MARKERS:
                kept.pop()  # "GTIN 2000..." goes together
            continue
        kept.append(word)
    return " ".join(kept).strip(" ,;:")
