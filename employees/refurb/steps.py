"""Refurb modules for the ``quote_to_award@1`` template (manifests in ``modules/``).

Each step takes the run's JSON data and a ``StepConfig`` and returns updates. Money travels as
decimal strings in the run state and is ``Decimal`` inside every calculation (R9). Nothing here
sends: the platform's SendService step does, after a human approved the exact ``outbound`` list.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import Any

from aiplat.compose import StepConfig

from .compare import compare as compare_quotes
from .compare import missing_fields
from .model import RFQ, LineItem, Quote
from .parser import parse_quote

Data = Mapping[str, Any]


def _rfq(d: Mapping[str, Any]) -> RFQ:
    return RFQ(
        id=str(d["id"]), property_id=str(d["property_id"]), trade=str(d["trade"]),
        items=tuple(LineItem(str(i["description"]), Decimal(str(i["quantity"])), str(i["unit"]))
                    for i in d["items"]),
        budget_cap=Decimal(str(d["budget_cap"])),
        needed_by=date.fromisoformat(str(d["needed_by"])),
        reply_by=date.fromisoformat(str(d["reply_by"])),
    )


def _quote_json(q: Quote) -> dict[str, Any]:
    return {
        "rfq_id": q.rfq_id, "supplier_id": q.supplier_id, "channel": q.channel,
        "received": q.received.isoformat(),
        "total_stated": None if q.total_stated is None else str(q.total_stated),
        "vat_basis": q.vat_basis,
        "total_ex_vat": None if q.total_ex_vat is None else str(q.total_ex_vat),
        "lead_time_days": q.lead_time_days,
        "valid_until": None if q.valid_until is None else q.valid_until.isoformat(),
        "payment_terms": q.payment_terms, "substitutions": q.substitutions,
        "spans": dict(q.spans), "confidence": dict(q.confidence), "flags": list(q.flags),
        "quarantined": q.quarantined, "missing": list(missing_fields(q)),
    }


def _quote(d: Mapping[str, Any]) -> Quote:
    def dec(k: str) -> Decimal | None:
        return None if d.get(k) is None else Decimal(str(d[k]))

    return Quote(
        rfq_id=d["rfq_id"], supplier_id=d["supplier_id"], channel=d["channel"],
        received=date.fromisoformat(d["received"]), total_stated=dec("total_stated"),
        vat_basis=d["vat_basis"], total_ex_vat=dec("total_ex_vat"),
        lead_time_days=d["lead_time_days"],
        valid_until=None if d["valid_until"] is None else date.fromisoformat(d["valid_until"]),
        payment_terms=d["payment_terms"], substitutions=d["substitutions"],
        spans=dict(d["spans"]), confidence=dict(d["confidence"]), flags=list(d["flags"]),
        quarantined=d["quarantined"],
    )


# ------------------------------------------------------------------------------------- intake


def intake(data: Data, cfg: StepConfig) -> dict[str, Any]:
    req = data.get("request") or {}
    rfq = _rfq(req["rfq"])  # raises on a malformed request: nothing downstream guesses
    suppliers = [{"id": str(s["id"]), "name": str(s["name"]), "contact": str(s["contact"])}
                 for s in req.get("suppliers", [])]
    return {
        "rfq": dict(req["rfq"], budget_cap=str(rfq.budget_cap)),
        "suppliers": suppliers,
        "requester": str(req.get("requester", "")),
        "currency": cfg.profile.profile.money.base_currency,
    }


# -------------------------------------------------------------------------------------- scope


def scope(data: Data, cfg: StepConfig) -> dict[str, Any]:
    rfq = _rfq(data["rfq"])
    limit = int(cfg.settings.get("max_suppliers_per_rfq", 4))
    questions: list[str] = []
    if not rfq.items:
        questions.append("What work should the trades quote for?")
    if rfq.budget_cap <= 0:
        questions.append("What is the budget cap for this job, ex VAT?")
    if not data.get("suppliers"):
        questions.append("Which of your trades should receive this RFQ?")
    elif len(data["suppliers"]) > limit:
        questions.append(f"Pick at most {limit} trades for one RFQ.")
    if rfq.reply_by > rfq.needed_by:
        questions.append("The reply-by date is after the needed-by date; which is right?")
    return {"open_questions": questions}


def needs_info(data: Data, cfg: StepConfig) -> bool:
    return bool(data.get("open_questions"))


# ------------------------------------------------------------------------------------ packets


def packets(data: Data, cfg: StepConfig) -> dict[str, Any]:
    rfq = _rfq(data["rfq"])
    lines = [f"- {i.description}: {i.quantity} {i.unit}" for i in rfq.items]
    ask_basis = cfg.profile.profile.tax.ask_basis_in_rfq
    tax = cfg.profile.profile.tax.name
    body = "\n".join([
        f"Please quote for the following {rfq.trade.lower()} work (ref {rfq.id}).",
        *lines,
        f"Needed by {rfq.needed_by.isoformat()}. Please reply by {rfq.reply_by.isoformat()}.",
        *( [f"Please state whether your price is ex or inc {tax}."] if ask_basis else [] ),
        "Please include your start date, how long the quote is valid and payment terms.",
    ])
    outbound = [{"supplier_id": s["id"], "to": s["contact"],
                 "subject": f"RFQ {rfq.id}: {rfq.trade}", "body": body}
                for s in data.get("suppliers", [])]
    return {"outbound": outbound}


def nothing_to_send(data: Data, cfg: StepConfig) -> bool:
    return not data.get("outbound")


# -------------------------------------------------------------------------------------- parse


def parse(data: Data, cfg: StepConfig) -> dict[str, Any]:
    """Rule-based parser: every field keeps its verbatim span; unread fields stay empty."""
    rfq_id = data["rfq"]["id"]
    rate = cfg.profile.profile.tax.standard_rate
    allowed = {s["id"] for s in data.get("suppliers", [])}
    quotes = []
    for r in data.get("replies", []):
        if r.get("supplier_id") not in allowed:
            continue  # a reply from someone we did not ask is not a quote
        q = parse_quote(str(r["text"]), rfq_id, str(r["supplier_id"]), str(r["channel"]),
                        date.fromisoformat(str(r["received"])))
        if q.vat_basis == "inc" and q.total_stated is not None:
            q.total_ex_vat = (q.total_stated / (1 + rate)).quantize(Decimal("0.01"))
        quotes.append(_quote_json(q))
    return {"quotes": quotes}


# ------------------------------------------------------------------------------------ compare


def compare(data: Data, cfg: StepConfig) -> dict[str, Any]:
    rfq = _rfq(data["rfq"])
    rows = compare_quotes(rfq, [_quote(q) for q in data.get("quotes", [])], cfg.today)
    table = [{
        "supplier_id": r.supplier_id,
        "total_ex_vat": None if r.total_ex_vat is None else str(r.total_ex_vat),
        "vs_median_pct": None if r.vs_median_pct is None else str(r.vs_median_pct),
        "lead_time_days": r.lead_time_days,
        "valid_until": None if r.valid_until is None else r.valid_until.isoformat(),
        "flags": list(r.flags), "rank": r.rank, "missing": list(r.missing),
    } for r in rows]
    ranked = sorted((r for r in table if isinstance(r["rank"], int)), key=lambda r: r["rank"])  # type: ignore[arg-type,return-value]
    best = ranked[0] if ranked else None
    recommendation = None if best is None else {
        "supplier_id": best["supplier_id"], "total_ex_vat": best["total_ex_vat"],
        "flags": best["flags"], "basis": "lowest ex-VAT total among rankable quotes",
    }
    return {"comparison": table, "recommendation": recommendation,
            "award_amount": None if best is None else best["total_ex_vat"]}


def no_rankable_quote(data: Data, cfg: StepConfig) -> bool:
    return data.get("recommendation") is None
