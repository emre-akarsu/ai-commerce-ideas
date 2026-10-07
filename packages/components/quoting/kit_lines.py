"""Kit lines -> matching order lines (stage 1 of "quote for products").

Each resolved kit line becomes one `LineRequest` whose text is the chosen option's spec (the
resolver already puts the option's spec on the line; the generic spec is kept in `KitRef`). Lines
the tenant marked "not needed" or "already have" are returned in `skipped`, never dropped, so the
quote can say why a kit line is absent. A kit line id is the order line id, so every quote line
traces back to its kit line, its option, its forced-by rule and its sources.

The kit quantity keeps its `Decimal` value; its unit is mapped by the fixed table in `units.py`.
Nothing here reads a catalogue or a price: it is a pure mapping.

The spec is passed through verbatim on purpose. The matching gate needs size, grade, class, finish
or pack stated, and a rewrite here (dropping an alternative, picking a value) would silently decide
something for the buyer. Where a kit line cannot resolve, fix the kit text in
`profiles/data/job_kits` (see its README, "Writing a spec the matching step can use"); the gold set
`evals/matching/gold/kit_bathroom_gold_v1.jsonl` records the outcome each line should have.
"""

from __future__ import annotations

from collections.abc import Mapping

from components.job_kits import ResolvedKit, ResolvedLine
from components.pricing.text import clean_text

from .errors import QuotingError
from .models import (
    DESCRIPTION_MAX,
    SERVICE_KIND,
    ZERO_QUANTITY,
    KitOrderLines,
    KitRef,
    LineChoice,
    LineRequest,
    SkippedLine,
    inert_text,
)
from .units import kit_quantity


def _choice(value: LineChoice | str, line_id: str) -> LineChoice:
    try:
        return LineChoice(value)
    except ValueError:
        raise QuotingError(f"{line_id}: {value!r} is not a valid choice "
                           f"({', '.join(c.value for c in LineChoice)})") from None


def _text(line: ResolvedLine) -> str:
    spec = line.option.spec if line.option is not None else line.spec
    return inert_text(spec)


def _ref(kit: ResolvedKit, line: ResolvedLine) -> KitRef:
    option = line.option
    return KitRef(
        kit_line_id=line.id, scope_id=kit.scope_id, module=line.module,
        description=clean_text(line.description, "description", DESCRIPTION_MAX),
        generic_spec=line.spec, option_id=option.id if option else None,
        option_label=option.label if option else None, kit_unit=line.unit,
        kit_quantity=line.quantity, quantity_formula=line.quantity_formula,
        forced_by=dict(line.forced_by) if line.forced_by else None,
        provenance=tuple({k: str(v) for k, v in p.items()} for p in line.provenance),
        assumption_source=line.assumption_source, kind=line.kind)


def order_lines_from_kit(
    kit: ResolvedKit, choices: Mapping[str, LineChoice | str] | None = None
) -> KitOrderLines:
    """One `LineRequest` per kit line the tenant needs; the rest in `skipped` with the reason."""
    picked = {k: _choice(v, k) for k, v in (choices or {}).items()}
    known = {x.id for x in kit.lines}
    unknown = sorted(set(picked) - known)
    if unknown:
        raise QuotingError(f"{unknown}: not a line of this kit")
    requests: list[LineRequest] = []
    skipped: list[SkippedLine] = []
    for line in kit.lines:
        ref = _ref(kit, line)
        choice = picked.get(line.id, LineChoice.NEEDED)
        if choice is not LineChoice.NEEDED:
            skipped.append(SkippedLine(line.id, choice.value, ref))
        elif line.quantity == 0:
            skipped.append(SkippedLine(line.id, ZERO_QUANTITY, ref))
        else:
            quantity, unit = kit_quantity(line.quantity, line.unit)
            requests.append(LineRequest(
                line_id=line.id, text=_text(line), quantity=quantity, unit=unit,
                description=ref.description, kit=ref, is_service=line.kind == SERVICE_KIND))
    return KitOrderLines(tuple(requests), tuple(skipped))
