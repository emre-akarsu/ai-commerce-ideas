"""Text cleaning and normalisation shared by order lines, catalogue titles and ontology phrases.

Order lines and catalogue titles are untrusted text (R4): `clean_text` first runs the repo's
inert-text filter (invisible characters, HTML and links removed) and only then lowercases and
folds symbols. Nothing here fetches anything or follows any instruction in the text.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection, Mapping

from components.rfq.quotes.inert import inert_text

_WORD = re.compile(r"[a-z0-9]+(?:[/&'.\-][a-z0-9]+)*")
_SPLIT = re.compile(r"[/&'\-]")
_DROP = frozenset({"x"})  # a stray multiplication sign

# Common plumbing fractions become words so that "1/2in" never reads as a size chain.
_FRACTIONS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern), replacement)
    for pattern, replacement in (
        (r'\b1\s+1/4\s*(?:"|in(?:ch(?:es)?)?\b)?', " one and quarter inch "),
        (r'\b1\s+1/2\s*(?:"|in(?:ch(?:es)?)?\b)?', " one and half inch "),
        (r'\b1/2\s*(?:"|in(?:ch(?:es)?)?\b)?', " half inch "),
        (r'\b3/4\s*(?:"|in(?:ch(?:es)?)?\b)?', " three quarter inch "),
        (r'\b1/4\s*(?:"|in(?:ch(?:es)?)?\b)?', " quarter inch "),
        (r'\b3/8\s*(?:"|in(?:ch(?:es)?)?\b)?', " three eighth inch "),
    )
)
_SYMBOLS = str.maketrans({"×": "x", "✕": "x", "✖": "x", "–": "-", "—": "-", "’": "'", "⁄": "/"})


def clean_text(raw: str) -> str:
    """Inert, lowercase, symbol-folded, single-spaced text; fractions rewritten as words."""
    text = unicodedata.normalize("NFKC", inert_text(raw)).translate(_SYMBOLS).lower()
    for pattern, replacement in _FRACTIONS:
        text = pattern.sub(replacement, text)
    return " ".join(text.split())


def singularise(token: str) -> str:
    """Cheap plural folding applied identically to both sides ("valves" -> "valve")."""
    if len(token) <= 3 or not token.endswith("s") or not token.isalpha():
        return token
    if token.endswith(("ss", "us", "is")):
        return token
    if token.endswith(("ches", "shes", "xes", "sses")):
        return token[:-2]
    return token[:-1]


class TextNormaliser:
    """Tokenise, expand UK trade abbreviations, fold plurals; optionally drop noise words."""

    def __init__(self, abbreviations: Mapping[str, str], noise_words: Collection[str]) -> None:
        self._abbreviations = {k.lower(): v.lower().split() for k, v in abbreviations.items()}
        self._noise = frozenset(w.lower() for w in noise_words)

    @property
    def noise_words(self) -> frozenset[str]:
        return self._noise

    def _lookup(self, raw: str) -> list[str] | None:
        if raw in self._abbreviations:
            return self._abbreviations[raw]
        if raw.endswith("s") and raw[:-1] in self._abbreviations:  # "p/boards"
            return self._abbreviations[raw[:-1]]
        return None

    def _expand(self, raw: str) -> list[str]:
        raw = raw.removesuffix("'s")  # possessive: "basin's" -> "basin"
        hit = self._lookup(raw)
        if hit is not None:
            return list(hit)
        if not _SPLIT.search(raw):
            return [singularise(raw)]
        out: list[str] = []
        for part in _SPLIT.split(raw):
            if not part:
                continue
            out.extend(self._lookup(part) or [singularise(part)])
        return out

    def tokens(self, text: str) -> tuple[str, ...]:
        out: list[str] = []
        for raw in _WORD.findall(clean_text(text)):
            out.extend(t for t in self._expand(raw) if t not in _DROP)
        return tuple(out)

    def content_tokens(self, text: str) -> tuple[str, ...]:
        return tuple(t for t in self.tokens(text) if t not in self._noise)
