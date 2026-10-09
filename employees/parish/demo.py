"""Synthetic demo for the parish pack: council, suppliers and replies are INVENTED."""

from __future__ import annotations

REQUEST = {
    "council": "Example Parva Parish Council",
    "requester": "clerk-ann",
    "need": {
        "ref": "PC-2026-014", "title": "Playground safety surfacing",
        "items": [{"description": "Wet-pour safety surfacing under swings", "quantity": "40",
                   "unit": "m2"}],
        "estimate_inc_vat": "6000", "budget_remaining": "5500",
        "needed_by": "2027-03-31", "reply_by": "2026-11-20",
    },
    "suppliers": [
        {"id": "play-safe", "name": "PlaySafe Surfaces Ltd",
         "contact": "quotes@playsafe.example"},
        {"id": "green-play", "name": "GreenPlay Contractors",
         "contact": "office@greenplay.example"},
        {"id": "county-surf", "name": "County Surfacing", "contact": "sales@countysurf.example"},
    ],
}

REPLIES = [
    ("play-safe", "email", "2026-11-12", "Wet-pour surfacing 40 m2, total £4,600.00 + VAT. "
     "Start in 3 weeks. Valid for 60 days. Payment terms: 30 days."),
    ("green-play", "pdf", "2026-11-14", "Quotation: wet-pour 40 m2. Total £5,280.00 + VAT. "
     "Lead time 4 weeks. Valid for 30 days. Payment terms: 30 days."),
    ("county-surf", "email", "2026-11-15", "Price for surfacing 40 m2: £4,950.00 + VAT. "
     "Can start in 5 weeks. Valid for 45 days. Payment terms: 50% deposit, balance on completion."),
]
