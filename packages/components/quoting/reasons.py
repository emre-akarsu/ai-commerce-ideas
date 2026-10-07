"""Quoting-level reasons: fixed templates over codes, no free text (CLAUDE.md rule 3).

Matching and pricing keep their own templated reasons; these cover the few decisions the quoting
step makes itself. A UI localises by `code`; the English text here is the default.
"""

from __future__ import annotations

from .models import ReasonLine

TEMPLATES: dict[str, str] = {
    "service_not_a_product":
        "This line is a service or labour item, not a catalogue product; it is not priced here.",
    "identity_guard":
        "A product to be priced does not carry the brand, MPN or GTIN named on the line, so "
        "nothing is priced for this line.",
    "needs_a_person":
        "A person must choose a product for this line before it can be priced.",
    "no_catalogue_match":
        "No catalogue product fits this line closely enough; nothing is priced.",
    "previously_approved":
        "Previously approved: a person already chose the product for this normalised line.",
}


def reason(code: str) -> ReasonLine:
    return ReasonLine(code, TEMPLATES[code])
