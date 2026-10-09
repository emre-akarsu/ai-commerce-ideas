"""Rented-home repairs modules for ``quote_to_award@1`` (manifests in ``modules/``).

A tenant's report is triaged by rules into a hazard class. The class sets how many contractor
quotes to get (one for an emergency) and the working-day target to fix it, counted on the
profile's bank-holiday calendar. RFQ packets, quote parsing and comparison reuse the refurb modules.
The run's hash-chained events are the landlord's record of when each step happened.

The classes and targets are the landlord's own policy in pack settings. For private rentals in
England, Renters' Rights Act duties (and any Awaab's Law extension) are not dated yet; confirm the
targets against them when they are. Not legal advice.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any

from aiplat.compose import StepConfig
from components.rfq.quotes.normalise import working_days_to_calendar

Data = Mapping[str, Any]
CLASSES = ("emergency", "urgent", "routine")


def intake(data: Data, cfg: StepConfig) -> dict[str, Any]:
    req = data.get("request") or {}
    report = req["report"]
    reported = date.fromisoformat(str(report["reported_on"]))
    return {
        "property": {"id": str(req["property"]["id"]), "address": str(req["property"]["address"])},
        "report": {"text": str(report["text"])[:2000], "reported_on": reported.isoformat(),
                   "trade": str(report["trade"]).lower()},
        "contractors": [{"id": str(c["id"]), "name": str(c["name"]), "contact": str(c["contact"]),
                         "trades": sorted({str(t).lower() for t in c.get("trades", [])})}
                        for c in req.get("contractors", [])],
        "requester": str(req.get("requester", "")),
    }


def classify(text: str, rules: Mapping[str, list[str]]) -> tuple[str, str | None]:
    """First class whose keyword appears in the report wins; the matched words are the evidence."""
    for cls in CLASSES[:-1]:
        for word in rules.get(cls, []):
            if re.search(rf"\b{re.escape(word)}\b", text, re.I):
                return cls, word
    return "routine", None


def triage(data: Data, cfg: StepConfig) -> dict[str, Any]:
    s = cfg.settings
    report = data["report"]
    cls, evidence = classify(report["text"], s["hazard_keywords"])
    target_days = int(s["fix_within_working_days"][cls])
    quotes = int(s["quotes_needed"][cls])
    loc = cfg.profile.profile.locale
    reported = date.fromisoformat(report["reported_on"])
    fix_by = reported + timedelta(
        days=working_days_to_calendar(target_days, reported, loc.working_week, loc.holidays))
    able = [c for c in data.get("contractors", []) if report["trade"] in c["trades"]]
    questions = [] if able else [f"Which contractor can do {report['trade']} work?"]
    chosen = able[:quotes]
    rfq = {
        "id": f"RFQ-{data['property']['id']}-{reported.strftime('%Y%m%d')}",
        "property_id": data["property"]["id"], "trade": report["trade"].capitalize(),
        "items": [{"description": f"Repair: {report['text'][:200]}", "quantity": "1",
                   "unit": "job"}],
        "budget_cap": str(s["job_limit"]), "needed_by": fix_by.isoformat(),
        "reply_by": min(fix_by, reported + timedelta(days=2)).isoformat(),
    }
    return {
        "triage": {"class": cls, "evidence": evidence, "fix_by": fix_by.isoformat(),
                   "target_working_days": target_days, "quotes_needed": quotes,
                   "basis": "landlord policy in pack settings, keyword rules"},
        "rfq": rfq,
        "suppliers": [{"id": c["id"], "name": c["name"], "contact": c["contact"]} for c in chosen],
        "open_questions": questions,
    }


def needs_info(data: Data, cfg: StepConfig) -> bool:
    return bool(data.get("open_questions"))
