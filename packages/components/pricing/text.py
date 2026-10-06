"""Text handling for untrusted data (CLAUDE.md rule 4; spec R6 inert rendering, R7 no link fetching).

* Identifiers (`check_id`) and machine tokens (`check_token`) are validated, never repaired: an
  id with an invisible character or a space is rejected, so it cannot impersonate another id.
* Free text (`clean_text`) is made inert: invisible, control and bidi characters are removed,
  whitespace is collapsed, and every link is replaced by a marker. Nothing in this package ever
  fetches anything, and no link found in data is kept (a link in a feed is display text at best).
"""

from __future__ import annotations

import re
import unicodedata

from .errors import OfferValidationError

LINK_REMOVED = "[link removed]"

_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,95}")
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.:-]{0,63}")

_SPACE_LIKE = frozenset("\t\n\r\x0b\x0c\x85  ")
# Letters and marks that draw nothing although they are not in a control or format category
# (the Hangul fillers, braille blank, combining grapheme joiner, Khmer inherent vowels).
_EXTRA_INVISIBLE = frozenset(chr(c) for c in (0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x2800,
                                              0x3164, 0xFFA0))

_URL_TOKEN_RE = re.compile(r"(?<!\S)\S*?://\S*")
_PSEUDO_URL_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:javascript|vbscript)\s*:\S*"
    r"|(?<![A-Za-z0-9])mailto:\S*"
    r"|(?<![A-Za-z0-9])data:[A-Za-z]+/[A-Za-z0-9.+-]+[;,]\S*"
    r"|(?<![A-Za-z0-9@.])www\.\S+"
    r"|(?<![A-Za-z0-9@./-])(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}/\S*",
    re.IGNORECASE,
)


def check_id(value: object, name: str) -> str:
    """An identifier: 1-96 characters, ASCII letters, digits and ``._:-``, not starting with
    punctuation. Anything else is rejected rather than cleaned."""
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise OfferValidationError(f"{name} must be a plain identifier (letters, digits, ._:-)")
    return value


def check_token(value: object, name: str) -> str:
    """A lowercase machine token (flags, methods, licence tags): 1-64 characters."""
    if not isinstance(value, str) or _TOKEN_RE.fullmatch(value) is None:
        raise OfferValidationError(f"{name} must be a lowercase token (a-z, 0-9, _.:-)")
    return value


def _is_invisible(ch: str) -> bool:
    if unicodedata.category(ch) in ("Cc", "Cf", "Cs", "Co", "Cn"):
        return True
    code = ord(ch)
    return (
        ch in _EXTRA_INVISIBLE
        or 0xFE00 <= code <= 0xFE0F  # variation selectors
        or 0x180B <= code <= 0x180D
        or 0xE0100 <= code <= 0xE01EF  # variation selectors supplement
    )


def _defang(text: str) -> str:
    text = _URL_TOKEN_RE.sub(LINK_REMOVED, text)
    return _PSEUDO_URL_RE.sub(LINK_REMOVED, text)


def clean_text(value: object, name: str, max_len: int, *, defang_urls: bool = True) -> str:
    """Make untrusted text inert: NFKC, no control/format/bidi/zero-width characters, single
    spaces, links replaced by ``[link removed]``, at most `max_len` characters. Idempotent."""
    if not isinstance(value, str):
        raise OfferValidationError(f"{name} must be text, got {type(value).__name__}")
    text = unicodedata.normalize("NFKC", value[: max_len * 8])
    out: list[str] = []
    for ch in text:
        if ch in _SPACE_LIKE or unicodedata.category(ch) == "Zs":
            out.append(" ")
        elif not _is_invisible(ch):
            out.append(ch)
    text = " ".join("".join(out).split())
    if defang_urls:
        text = _defang(text)
    return text[:max_len].rstrip()
