"""Synthetic demo for the repairs pack: property, contractors and replies are INVENTED."""

from __future__ import annotations

CONTRACTORS = [
    {"id": "north-plumb", "name": "North Plumbing & Heating", "contact": "jobs@northplumb.example",
     "trades": ["plumbing", "heating"]},
    {"id": "fixit-heat", "name": "FixIt Heating Ltd", "contact": "office@fixitheat.example",
     "trades": ["heating"]},
    {"id": "dry-homes", "name": "Dry Homes Damp Care", "contact": "hello@dryhomes.example",
     "trades": ["damp"]},
    {"id": "cov-damp", "name": "Coventry Damp Solutions", "contact": "quotes@covdamp.example",
     "trades": ["damp"]},
]


def request(text: str, trade: str, reported_on: str = "2026-12-23") -> dict:
    return {
        "requester": "agent-kim",
        "property": {"id": "F-3B", "address": "Flat 3B, 9 Sample Street, Coventry CV1 1AA"},
        "report": {"text": text, "reported_on": reported_on, "trade": trade},
        "contractors": CONTRACTORS,
    }


REPLIES = [
    ("dry-homes", "email", "2026-12-24", """Hi Kim,
Mould treatment and extractor fan fix in the bathroom:
- Mould wash and stain block: £180.00
- Replace extractor fan: £240.00
Total £420.00 + VAT. Can start in 2 days. Valid for 30 days. Payment terms: 14 days."""),
    ("cov-damp", "email", "2026-12-24", """Quote: mould treatment and new fan, £520.00 + VAT all in.
We can start in 3 days. Valid for 14 days. Payment terms: on completion."""),
]
