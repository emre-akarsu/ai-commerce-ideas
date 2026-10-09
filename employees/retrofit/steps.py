"""Landlord EPC retrofit modules for ``quote_to_award@1`` (manifests in ``modules/``).

The pack takes a rented home's EPC (current SAP score and the report's recommended measures), plans
the cheapest set of measures that reaches the target band within the landlord's remaining cost
cap, and sends one like-for-like RFQ to each installer certified for every planned measure. Quote
parsing and comparison reuse the refurb modules (bound in ``packs/landlord-epc-retrofit``).

Costs and score gains in an EPC are indicative estimates, so the plan says "indicative" and the
installers' quotes decide. If the target cannot be reached within the cap, the plan says so and
marks the exemption route; it never claims an exemption is granted. Not legal advice.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import Any

from aiplat.compose import StepConfig

Data = Mapping[str, Any]

# SAP score lower bound per EPC band (England and Wales, domestic).
BAND_FLOOR = {"A": 92, "B": 81, "C": 69, "D": 55, "E": 39, "F": 21, "G": 1}
# Who may install each measure, by scheme. The pack can tighten this list, never empty it.
DEFAULT_CERTS = {
    "loft_insulation": "trustmark", "cavity_wall_insulation": "trustmark",
    "solid_wall_insulation": "trustmark", "floor_insulation": "trustmark",
    "heating_controls": "trustmark", "low_energy_lighting": "trustmark",
    "double_glazing": "trustmark", "solar_pv": "mcs", "air_source_heat_pump": "mcs",
    "hot_water_cylinder_insulation": "trustmark",
}


def band(score: int) -> str:
    for name, floor in BAND_FLOOR.items():
        if score >= floor:
            return name
    return "G"


def _measures(epc: Mapping[str, Any]) -> list[dict[str, Any]]:
    out = []
    for r in epc.get("recommendations", []):
        low, high = Decimal(str(r["cost_low"])), Decimal(str(r["cost_high"]))
        if low < 0 or high < low or int(r["points"]) <= 0:
            raise ValueError(f"recommendation {r.get('measure')!r} has an invalid cost or gain")
        out.append({"measure": str(r["measure"]), "label": str(r["label"]),
                    "points": int(r["points"]), "cost_low": low, "cost_high": high,
                    "cost_mid": ((low + high) / 2).quantize(Decimal("1"))})
    return out


# ------------------------------------------------------------------------------------- intake


def intake(data: Data, cfg: StepConfig) -> dict[str, Any]:
    req = data.get("request") or {}
    prop, epc = req["property"], req["epc"]
    score = int(epc["current_score"])
    if not 1 <= score <= 100:
        raise ValueError("EPC score must be 1-100")
    _measures(epc)  # validate now; nothing downstream guesses
    installers = [{"id": str(i["id"]), "name": str(i["name"]), "contact": str(i["contact"]),
                   "certs": sorted({str(c).lower() for c in i.get("certs", [])})}
                  for i in req.get("installers", [])]
    return {
        "property": {"id": str(prop["id"]), "address": str(prop["address"])},
        "epc": {"current_score": score, "current_band": band(score),
                "certificate": str(epc.get("certificate", "")),
                "recommendations": epc["recommendations"]},
        "installers": installers,
        "prior_spend": str(Decimal(str(req.get("prior_qualifying_spend", "0")))),
        "requester": str(req.get("requester", "")),
        "needed_by": str(req["needed_by"]), "reply_by": str(req["reply_by"]),
    }


# --------------------------------------------------------------------------------------- plan


def plan(data: Data, cfg: StepConfig) -> dict[str, Any]:
    s = cfg.settings
    target = str(s.get("target_band", "C"))
    target_score = BAND_FLOOR[target]
    cap = Decimal(str(s["cost_cap"]))
    remaining = max(cap - Decimal(data["prior_spend"]), Decimal(0))
    certs = {**DEFAULT_CERTS, **{k: str(v) for k, v in s.get("required_certs", {}).items()}}
    score = int(data["epc"]["current_score"])
    questions: list[str] = []

    chosen: list[dict[str, Any]] = []
    spend, expected = Decimal(0), score
    # Best gain per pound first; ties broken by the cheaper measure so the plan is deterministic.
    ranked = sorted(_measures(data["epc"]),
                    key=lambda m: (-Decimal(m["points"]) / max(m["cost_mid"], Decimal(1)),
                                   m["cost_mid"], m["measure"]))
    for m in ranked:
        if expected >= target_score:
            break
        if spend + m["cost_mid"] > remaining:
            continue
        chosen.append(m)
        spend += m["cost_mid"]
        expected += m["points"]
    reaches = expected >= target_score

    needed = sorted({certs.get(m["measure"], "trustmark") for m in chosen})
    eligible = [i for i in data.get("installers", []) if set(needed) <= set(i["certs"])]
    limit = int(s.get("max_installers_per_rfq", 4))
    if score >= target_score:
        questions.append(f"The EPC is already band {band(score)}; no works are needed for {target}.")
    elif not chosen:
        questions.append("No recommended measure fits within the remaining cost cap.")
    elif not eligible:
        questions.append(f"None of your installers holds every scheme needed ({', '.join(needed)}).")
    elif len(eligible) > limit:
        questions.append(f"Pick at most {limit} installers for one RFQ.")

    deadline = date.fromisoformat(str(s["deadline"]))
    rfq = {
        "id": f"RFQ-{data['property']['id']}-EPC", "property_id": data["property"]["id"],
        "trade": "Energy efficiency retrofit",
        "items": [{"description": m["label"], "quantity": "1", "unit": "job"} for m in chosen],
        "budget_cap": str(remaining), "needed_by": data["needed_by"], "reply_by": data["reply_by"],
    }
    return {
        "plan": {
            "target_band": target, "current_score": score, "expected_score": expected,
            "expected_band": band(expected), "reaches_target": reaches,
            "measures": [{"measure": m["measure"], "label": m["label"], "points": m["points"],
                          "indicative_cost": str(m["cost_mid"]), "scheme": certs.get(m["measure"])}
                         for m in chosen],
            "indicative_total": str(spend), "cost_cap": str(cap),
            "remaining_cap": str(remaining), "deadline": deadline.isoformat(),
            # The landlord may be able to register an exemption if the cap is spent and the
            # target is still out of reach. A human decides; the plan only flags it.
            "exemption_route": not reaches and bool(chosen),
            "basis": "EPC recommendations; costs and gains are indicative until quoted",
        },
        "rfq": rfq,
        "suppliers": [{"id": i["id"], "name": i["name"], "contact": i["contact"]} for i in eligible],
        "open_questions": questions,
    }


def needs_info(data: Data, cfg: StepConfig) -> bool:
    return bool(data.get("open_questions"))


# ------------------------------------------------------------------------------------ packets


def packets(data: Data, cfg: StepConfig) -> dict[str, Any]:
    p, rfq = data["plan"], data["rfq"]
    tax = cfg.profile.profile.tax.name
    schemes = sorted({str(m["scheme"]).upper() for m in p["measures"]})
    body = "\n".join([
        f"Please quote for these energy efficiency measures at {data['property']['address']} "
        f"(ref {rfq['id']}). The goal is EPC band {p['target_band']} "
        f"(current SAP score {p['current_score']}).",
        *(f"- {m['label']}" for m in p["measures"]),
        f"Please quote each measure on its own line and give a total, stating whether {tax} "
        "applies and at what rate.",
        f"Please include your {' and '.join(schemes)} registration number(s), your start date, "
        "how long the quote is valid and your payment terms.",
        f"Works must be complete by {rfq['needed_by']}. Please reply by {rfq['reply_by']}.",
    ])
    return {"outbound": [{"supplier_id": s["id"], "to": s["contact"],
                          "subject": f"RFQ {rfq['id']}: energy efficiency works", "body": body}
                         for s in data.get("suppliers", [])]}


def nothing_to_send(data: Data, cfg: StepConfig) -> bool:
    return not data.get("outbound")
