"""The decision gate (spec "Decision gate"), deterministic and pure.

Order of evaluation, first match wins:

1. quantity-versus-size ambiguity -> review (always, before anything else)
1b. a named MPN or GTIN that matches a SKU is definitive (same part): the text-score thresholds
   and required attributes do not apply, but everything the line does state must still verify
2. no candidate, or best score below `reject_below_score` -> reject
3. product type not certain -> review (question)
4. required attribute unresolved -> review (templated question)
5. no candidate passes every check -> review (a failed OR unverifiable check blocks)
6. best passing candidate below `auto_accept_min_score` -> review
7. specific line (brand named, no MPN/GTIN): lead over the runner-up below `auto_accept_min_lead`
   -> review. Generic line: the MATCH GROUP is every passing candidate within `group_band` of the
   best; the lead is meaningless there and is not used.
8. terms the ontology cannot place, or a number no attribute could take -> review
9. identity guard: a named brand/MPN/GTIN must hold for every group member -> review
10. marginal accept (score or lead near the threshold): the judge must confirm. Judge missing,
    failed, order-dependent, invalid or in disagreement -> review
11. auto-accept

EXTENSION (deviation from the spec table, documented in docs/architecture/matching-engine.md):
lines are `specific` (a brand/MPN/GTIN is named) or `generic` (specification only; many SKUs
qualify), and generic lines are accepted as a group so a pricing step can choose within it.
`unexplained_terms` and the marginal-accept confirmation are also extensions. The judge can only
reorder or push a line to review; it never turns a review into an accept.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from .checks import unresolved_required
from .judge import JudgeVerdict
from .models import (
    Candidate,
    CheckCode,
    CheckOutcome,
    LineKind,
    Outcome,
    ParsedLine,
    ReasonCode,
)
from .ontology import Ontology
from .policy import GatePolicy
from .reasons import question_for, safe

_IDENTITY_CODES = {CheckCode.BRAND_MISMATCH, CheckCode.IDENTIFIER_MISMATCH}


@dataclass(frozen=True)
class JudgeInput:
    verdict: JudgeVerdict
    top_validated: bool  # the engine re-ran the deterministic checks on the judge's top pick


@dataclass(frozen=True)
class Decision:
    outcome: Outcome
    reasons: tuple[ReasonCode, ...]
    chosen: Candidate | None = None
    group: tuple[Candidate, ...] = ()
    question: str | None = None
    needs_judge: bool = False  # a judge call is wanted (ordering, or confirming a marginal accept)
    details: tuple[tuple[str, str], ...] = ()  # values for the reason templates


def has_identifier(line: ParsedLine) -> bool:
    return bool(line.mpn or line.gtin)


def viable(line: ParsedLine, cand: Candidate) -> bool:
    """Passes every check. A named MPN/GTIN identifies the SKU, so attributes the line leaves
    unstated are not required then; anything the line does state must still verify."""
    for c in cand.checks:
        if c.outcome is CheckOutcome.PASSED:
            continue
        if c.outcome is CheckOutcome.UNRESOLVED and has_identifier(line):
            continue
        return False
    return True


def _review(reasons: list[ReasonCode], **kw: object) -> Decision:
    needs_judge = bool(kw.pop("needs_judge", False))
    question = kw.pop("question", None)
    details = tuple((k, safe(v)) for k, v in kw.items())
    return Decision(Outcome.REVIEW, tuple(reasons), question=question if isinstance(
        question, str) else None, needs_judge=needs_judge, details=details)


def _eligible(ranked: list[Candidate]) -> list[Candidate]:
    """Candidates that would pass once the line states what is missing."""
    return [c for c in ranked if all(
        r.outcome in (CheckOutcome.PASSED, CheckOutcome.UNRESOLVED) for r in c.checks)]


def _runner_up(line: ParsedLine, top: Candidate, rest: list[Candidate]) -> Decimal:
    """Best score among passing candidates that are not another listing of the same product."""
    same = {x for x in (top.item.mpn, top.item.gtin) if x}
    others = [c for c in rest if not ({c.item.mpn, c.item.gtin} & same)]
    return others[0].score if others else Decimal(0)


def _unexplained(line: ParsedLine, group: list[Candidate], ontology: Ontology,
                 title_words: Callable[[str], frozenset[str]]) -> list[str]:
    type_id = line.type_hint.type_id
    vocab = ontology.vocabulary(type_id) if type_id else frozenset()
    in_every_title = frozenset.intersection(*(title_words(c.item.sku_id) for c in group))
    terms = [t for t in line.tokens if t not in vocab and t not in in_every_title]
    return [*dict.fromkeys(terms), *line.unbound]


def _identity_ok(line: ParsedLine, group: list[Candidate], ontology: Ontology) -> bool:
    norm = ontology.normaliser
    for c in group:
        if line.brand is not None and norm.tokens(line.brand) != norm.tokens(c.item.brand):
            return False
        if any(r.code in _IDENTITY_CODES for r in c.checks if r.outcome is not CheckOutcome.PASSED):
            return False
    return True


def _confirm(group: list[Candidate], judge: JudgeInput | None) -> Decision | None:
    """A review Decision unless the judge confirmed the scorer's pick; None = confirmed."""
    if judge is None or judge.verdict.status == "unavailable":
        return _review([ReasonCode.JUDGE_UNAVAILABLE])
    if judge.verdict.status == "position_disagreement":
        return _review([ReasonCode.JUDGE_POSITION_DISAGREEMENT])
    if not judge.top_validated:
        return _review([ReasonCode.JUDGE_CHOICE_FAILED_VALIDATION])
    if judge.verdict.top not in {c.item.sku_id for c in group}:
        return _review([ReasonCode.JUDGE_DISAGREES])
    return None


def _identifier_decision(line: ParsedLine, ranked: list[Candidate], ontology: Ontology,
                         title_words: Callable[[str], frozenset[str]]) -> Decision | None:
    """Decision for a line whose MPN/GTIN matches SKUs; None when nothing matched it."""
    matched = [c for c in ranked if viable(line, c)]
    if not matched:
        return None
    if len({c.item.brand for c in matched}) > 1:
        return _review([ReasonCode.IDENTIFIER_AMBIGUOUS])
    stray = _unexplained(line, matched, ontology, title_words)
    if stray:
        return _review([ReasonCode.UNEXPLAINED_TERMS], terms=", ".join(stray))
    if not _identity_ok(line, matched, ontology):
        return _review([ReasonCode.NAMED_IDENTITY_UNAVAILABLE])
    top = matched[0]
    return Decision(Outcome.AUTO_ACCEPT, (ReasonCode.AUTO_ACCEPT_SPECIFIC,), chosen=top,
                    group=tuple(matched), details=(("score", str(top.score)), ("lead", "n/a"),
                                                   ("count", str(len(matched)))))


def decide(line: ParsedLine, ranked: list[Candidate], policy: GatePolicy, ontology: Ontology,
           title_words: Callable[[str], frozenset[str]],
           judge: JudgeInput | None = None) -> Decision:
    """`ranked` is sorted by hybrid score, best first, with checks filled in."""
    if line.ambiguities:
        return _review([ReasonCode.QUANTITY_SIZE_AMBIGUITY], raw=line.ambiguities[0].raw)
    if has_identifier(line):
        named = _identifier_decision(line, ranked, ontology, title_words)
        if named is not None:
            return named
    if not ranked:
        return Decision(Outcome.REJECT, (ReasonCode.NO_CANDIDATES,))
    best = ranked[0]
    if best.score < policy.reject_below_score:
        return Decision(Outcome.REJECT, (ReasonCode.BELOW_REJECT_THRESHOLD,),
                        details=(("score", str(best.score)),
                                 ("threshold", str(policy.reject_below_score))))
    if not line.type_hint.certain:
        types = line.type_hint.alternatives or tuple(dict.fromkeys(
            c.item.product_type for c in ranked[:policy.review_show_top * 2]))
        labels = ", ".join(ontology.types[t].label for t in types if t in ontology.types)
        return _review([ReasonCode.PRODUCT_TYPE_UNCERTAIN],
                       question=f"Which product is this? Options: {safe(labels)}.")
    ptype = ontology.types[line.type_hint.type_id or ""]
    missing = [] if has_identifier(line) else list(unresolved_required(line, ptype))
    if missing:
        return _review([ReasonCode.REQUIRED_ATTRIBUTE_UNRESOLVED],
                       names=", ".join(t.name for t in missing),
                       question=question_for(missing[0], _eligible(ranked)[:policy.judge_top_k],
                                             ontology))
    passing = [c for c in ranked if viable(line, c)]
    if not passing:
        identity_blocked = line.kind is LineKind.SPECIFIC and all(
            _IDENTITY_CODES & set(c.failed_codes) for c in ranked[:policy.review_show_top])
        return _review([ReasonCode.NAMED_IDENTITY_UNAVAILABLE if identity_blocked
                        else ReasonCode.ALL_CANDIDATES_FAILED_CHECKS])
    top = passing[0]
    if top.score < policy.auto_accept_min_score:
        return _review([ReasonCode.SCORE_BELOW_ACCEPT_THRESHOLD], needs_judge=True,
                       score=top.score, threshold=policy.auto_accept_min_score)
    lead = Decimal(1)
    if line.kind is LineKind.SPECIFIC and not has_identifier(line):
        lead = top.score - _runner_up(line, top, passing[1:])
        if lead < policy.auto_accept_min_lead:
            return _review([ReasonCode.NARROW_LEAD], needs_judge=True, lead=lead,
                           threshold=policy.auto_accept_min_lead)
        same = {x for x in (top.item.mpn, top.item.gtin) if x}
        group = [top, *[c for c in passing[1:] if {c.item.mpn, c.item.gtin} & same]]
    elif line.kind is LineKind.SPECIFIC:
        group = list(passing)
    else:
        group = [c for c in passing if c.score >= top.score - policy.group_band]
    stray = _unexplained(line, group, ontology, title_words)
    if stray:
        return _review([ReasonCode.UNEXPLAINED_TERMS], terms=", ".join(stray))
    if not _identity_ok(line, group, ontology):
        return _review([ReasonCode.NAMED_IDENTITY_UNAVAILABLE])
    marginal = top.score < policy.auto_accept_min_score + policy.judge_margin or (
        line.kind is LineKind.SPECIFIC and not has_identifier(line)
        and lead < policy.auto_accept_min_lead + policy.judge_margin)
    if marginal:
        refused = _confirm(group, judge)
        if refused is not None:
            return Decision(refused.outcome, refused.reasons, needs_judge=judge is None)
    code = (ReasonCode.AUTO_ACCEPT_SPECIFIC if line.kind is LineKind.SPECIFIC
            else ReasonCode.AUTO_ACCEPT_GROUP)
    return Decision(Outcome.AUTO_ACCEPT, (code,), chosen=group[0], group=tuple(group),
                    details=(("score", str(top.score)), ("lead", str(lead)),
                             ("count", str(len(group)))))
