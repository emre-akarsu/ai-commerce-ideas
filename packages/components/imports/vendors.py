"""Match imported vendor names to the tenant's own vendors. Exact on a normalised form only:
no fuzzy auto-match (a wrong vendor on a PO row is worse than a rejected row)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from components.core.domain import Vendor

_SUFFIX = {"inc", "llc", "ltd", "co", "corp", "corporation", "company", "gmbh", "plc", "the"}


def normalise_vendor(name: str) -> str:
    s = unicodedata.normalize("NFKC", name).casefold()
    words = [w for w in re.sub(r"[^\w]+", " ", s).split() if w not in _SUFFIX]
    return " ".join(words)


class VendorIndex:
    def __init__(self, vendors: Iterable[Vendor]) -> None:
        self._by_name: dict[str, list[str]] = {}
        for v in vendors:
            self._by_name.setdefault(normalise_vendor(v.name), []).append(v.id)

    def match(self, name: str) -> tuple[str | None, str | None]:
        """(vendor_id, None) or (None, reason)."""
        ids = self._by_name.get(normalise_vendor(name), [])
        if not normalise_vendor(name) or not ids:
            return None, "unknown_vendor"
        if len(ids) > 1:
            return None, "ambiguous_vendor"
        return ids[0], None
