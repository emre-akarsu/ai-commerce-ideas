"""Purchasing planner modules for the ``rfq_planning@1`` template (manifests in ``modules/``).

The same logic as the hand-built graph in ``graph.py`` (a parity test runs both), split into
modules so the planner can be composed like any other pack. Drafting only: no import path to the
send-service, approvals, transport or store.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

from aiplat.compose import StepConfig
from components.core.domain import Attribute, Tier
from components.parts.equivalence.engine import find_candidates, is_offerable
from components.parts.spec.intake import parse_request_text
from components.parts.spec.normaliser import normalise

from .graph import _intro

Data = Mapping[str, Any]


def intake(data: Data, cfg: StepConfig) -> dict[str, Any]:
    parsed = parse_request_text(data.get("text", ""), cfg.today)
    return {
        "quantity": data.get("quantity") or parsed.quantity,
        "need_by": parsed.need_by.isoformat() if isinstance(parsed.need_by, date) else None,
        "down_now": parsed.down_now,
        "criticality": bool(data.get("criticality")) or parsed.criticality_hint,
        "instruction_flags": list(parsed.raw_instruction_flags),  # data only, never acted on
    }


def spec(data: Data, cfg: StepConfig) -> dict[str, Any]:
    s = normalise(data.get("text", ""))
    status = "escalated" if s.escalate else "needs_info" if s.open_questions else "spec_ok"
    return {
        "family": s.family,
        "attributes": {k: a.model_dump(mode="json") for k, a in s.attributes.items()},
        "open_questions": list(s.open_questions),
        "escalate": s.escalate,
        "spec_status": status,
    }


def not_spec_ok(data: Data, cfg: StepConfig) -> bool:
    return data.get("spec_status") != "spec_ok"


def candidates(data: Data, cfg: StepConfig) -> dict[str, Any]:
    attrs = {k: Attribute.model_validate(v) for k, v in data["attributes"].items()}
    found = find_candidates(
        attrs, family=data["family"] or "", criticality=bool(data.get("criticality"))
    )
    offerable = [c for c in found if c.tier in (Tier.A, Tier.B) and is_offerable(c)]
    return {"candidates": [c.model_dump(mode="json") for c in found], "offerable": bool(offerable)}


def none_offerable(data: Data, cfg: StepConfig) -> bool:
    return not data.get("offerable")


def draft_rfq(data: Data, cfg: StepConfig) -> dict[str, Any]:
    offerable = [c for c in data["candidates"] if c["tier"] in ("A", "B") and not c["mismatches"]]
    mpns = [c["mpn"] for c in sorted(offerable, key=lambda c: (c["tier"], c["mpn"]))]
    return {"draft": {
        "candidate_mpns": mpns,
        "quantity": data.get("quantity"),
        "need_by": data.get("need_by"),
        "intro": _intro(cfg.llm, mpns, data.get("quantity")),
    }}
