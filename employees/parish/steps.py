"""Parish and town council purchasing modules for ``quote_to_award@1`` (manifests in ``modules/``).

The council's own financial regulations decide how many quotes a purchase needs; the pack holds
them as settings (the defaults follow the shape of the NALC model regulations, with a GBP 30,000
inc-VAT point above which a formal tender and a Contracts Finder notice apply). Above that point
this pack stops: tenders are out of scope. The award is a committee resolution: a quorum of
councillors in pack settings. Not legal advice; each council's own regulations win.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import Any

from aiplat.compose import StepConfig

Data = Mapping[str, Any]


def intake(data: Data, cfg: StepConfig) -> dict[str, Any]:
    req = data.get("request") or {}
    need = req["need"]
    estimate = Decimal(str(need["estimate_inc_vat"]))
    if estimate <= 0:
        raise ValueError("estimate must be positive")
    return {
        "council": str(req["council"]),
        "need": {"ref": str(need["ref"]), "title": str(need["title"]),
                 "items": [{"description": str(i["description"]),
                            "quantity": str(Decimal(str(i["quantity"]))), "unit": str(i["unit"])}
                           for i in need["items"]],
                 "estimate_inc_vat": str(estimate),
                 "budget_remaining": str(Decimal(str(need["budget_remaining"]))),  # ex VAT
                 "needed_by": date.fromisoformat(str(need["needed_by"])).isoformat(),
                 "reply_by": date.fromisoformat(str(need["reply_by"])).isoformat()},
        "suppliers": [{"id": str(s["id"]), "name": str(s["name"]), "contact": str(s["contact"])}
                      for s in req.get("suppliers", [])],
        "requester": str(req.get("requester", "")),
    }


def quotes_required(estimate: Decimal, tiers: list[Mapping[str, Any]]) -> int | None:
    """Quotes the regulations require for this estimate; None = above every tier (tender)."""
    for t in sorted(tiers, key=lambda t: Decimal(str(t["up_to"]))):
        if estimate < Decimal(str(t["up_to"])):
            return int(t["quotes"])
    return None


def rules(data: Data, cfg: StepConfig) -> dict[str, Any]:
    s, need = cfg.settings, data["need"]
    estimate = Decimal(need["estimate_inc_vat"])
    needed = quotes_required(estimate, s["quote_tiers"])
    questions: list[str] = []
    if needed is None:
        questions.append("This is above the tender point: run a formal tender and publish a "
                         "Contracts Finder notice; this workflow does not cover tenders.")
    elif len(data.get("suppliers", [])) < needed:
        questions.append(f"Financial regulations need {needed} quotes; add more suppliers.")
    rate = cfg.profile.profile.tax.standard_rate  # councils recover VAT: budgets are ex VAT
    if estimate / (1 + rate) > Decimal(need["budget_remaining"]):
        questions.append("The estimate is above the remaining budget; the council must "
                         "approve a virement or extra budget first.")
    rfq = {"id": need["ref"], "property_id": data["council"], "trade": need["title"],
           "items": need["items"], "budget_cap": need["budget_remaining"],
           "needed_by": need["needed_by"], "reply_by": need["reply_by"]}
    return {
        "procurement": {"estimate_inc_vat": str(estimate), "quotes_required": needed,
                        "rule": "council financial regulations (pack settings)"},
        "rfq": rfq, "open_questions": questions,
    }


def needs_info(data: Data, cfg: StepConfig) -> bool:
    return bool(data.get("open_questions"))
