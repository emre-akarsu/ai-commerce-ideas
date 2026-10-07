"""MatchingEngine: parse, approvals, retrieve, validate, judge, re-validate, gate (spec pipeline).

`match(tenant_id, line)` returns a `MatchResult` with every step traced. The LLM is optional and
used only on ambiguous lines (rank-related reviews and marginal accepts). Approvals are looked up
and written through a tenant-scoped store. Nothing here sends mail, fetches a link or writes an
Event; recording a decision in the hash-chained log is the caller's follow-up.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from components.core.domain import Basis
from components.core.ports import LLMProvider

from .approvals import ApprovalRecord, ApprovedMatchStore, signature
from .checks import check_candidate
from .gate import Decision, JudgeInput, decide, viable
from .index import CatalogIndex
from .judge import JudgeVerdict, MatchJudge
from .models import (
    AssistantNote,
    Candidate,
    CheckOutcome,
    MatchResult,
    OrderLine,
    Outcome,
    ParsedLine,
    ReasonCode,
    TraceStep,
)
from .policy import GatePolicy
from .reasons import render_candidate, render_reason


def _check_all(
    line: ParsedLine, cands: Iterable[Candidate], index: CatalogIndex
) -> list[Candidate]:
    out = []
    for c in cands:
        checks = check_candidate(line, c.item, index.ontology)
        updated = c.model_copy(update={"checks": checks})
        ok = viable(line, updated)
        basis = (Basis.SAME_MPN if (line.mpn or line.gtin) else Basis.RULE_MATCH) if ok else None
        out.append(updated.model_copy(update={"basis": basis}))
    return out


class MatchingEngine:
    def __init__(self, index: CatalogIndex, store: ApprovedMatchStore, *,
                 llm: LLMProvider | None = None, policy: GatePolicy | None = None) -> None:
        self.index = index
        self.store = store
        self.policy = policy or GatePolicy()
        self._judge = MatchJudge(llm) if llm is not None else None
        self.judge_calls = 0

    # ------------------------------------------------------------------ public

    def match(self, tenant_id: str, line: OrderLine) -> MatchResult:
        trace: list[TraceStep] = []
        parsed = self.index.parser.parse(line)
        trace.append(TraceStep(step="parse", summary="line parsed", data={
            "type": parsed.type_hint.type_id, "certain": parsed.type_hint.certain,
            "kind": parsed.kind.value,
            "attributes": [f"{a.name}={a.value}" for a in parsed.attributes],
            "ambiguities": [a.kind.value for a in parsed.ambiguities],
            "unbound": list(parsed.unbound), "canonical_text": parsed.canonical_text}))
        sig = signature(parsed)
        approved = self._approved(tenant_id, parsed, sig, trace)
        if approved is not None:
            return approved
        found = self.index.search(parsed, self.policy.retrieve_top_k)
        ranked = sorted(_check_all(parsed, found, self.index),
                        key=lambda c: (-c.scores.hybrid, c.item.sku_id))
        trace.append(TraceStep(step="retrieve", summary="hybrid retrieval", data={
            "retrieved": len(found), "top": [c.item.sku_id for c in ranked[:5]]}))
        trace.append(TraceStep(step="validate", summary="deterministic attribute checks", data={
            "passing": [c.item.sku_id for c in ranked if viable(parsed, c)][:10],
            "failed": {c.item.sku_id: [x.value for x in c.failed_codes] for c in ranked[:10]
                       if not viable(parsed, c)}}))
        decision, verdict = self._decide(tenant_id, parsed, ranked, trace)
        return self._result(tenant_id, parsed, sig, ranked, decision, verdict, trace)

    def match_many(self, tenant_id: str, lines: Sequence[OrderLine]) -> list[MatchResult]:
        return [self.match(tenant_id, line) for line in lines]

    def learn(self, tenant_id: str, line: OrderLine, sku_ids: Sequence[str],
              approver: str) -> ApprovalRecord:
        """Store a person's approval; it becomes an instant resolution and a judge example."""
        parsed = self.index.parser.parse(line)
        sig = signature(parsed)
        if sig is None:
            raise ValueError("a quantity-versus-size ambiguous line cannot be approved by "
                             "signature; clarify the line first")
        unknown = [s for s in sku_ids if self.index.get(s) is None]
        if unknown:
            raise ValueError(f"unknown SKU ids: {unknown}")
        return self.store.approve(tenant_id, sig, line.text, parsed.retrieval_text, sku_ids,
                                  approver)

    # ------------------------------------------------------------------ approvals

    def _approved(self, tenant_id: str, parsed: ParsedLine, sig: str | None,
                  trace: list[TraceStep]) -> MatchResult | None:
        if sig is None:
            return None
        record = self.store.lookup(tenant_id, sig)
        trace.append(TraceStep(step="approvals", summary="signature lookup", data={
            "signature": sig, "found": record is not None}))
        if record is None:
            return None
        members = []
        for sku in record.sku_ids:
            item = self.index.get(sku)
            if item is None or not item.active:
                continue
            cand = self.index.score_item(parsed, item)
            members.append(_check_all(parsed, [cand], self.index)[0])
        stale = not members or any(
            r.outcome in (CheckOutcome.FAIL, CheckOutcome.UNVERIFIABLE)
            for m in members for r in m.checks)
        if stale:
            trace.append(TraceStep(step="approvals", summary="approval is stale; matching afresh",
                                   data={"skus": list(record.sku_ids)}))
            return None
        members.sort(key=lambda c: (-c.scores.hybrid, c.item.sku_id))
        reasons = (render_reason(ReasonCode.PREVIOUSLY_APPROVED, who=record.approver),)
        return MatchResult(
            tenant_id=tenant_id, line_id=parsed.line_id, outcome=Outcome.PREVIOUSLY_APPROVED,
            chosen=members[0], group=tuple(members),
            top=tuple(members[:self.policy.review_show_top]),
            reason_codes=(ReasonCode.PREVIOUSLY_APPROVED,), reasons=reasons, signature=sig,
            trace=(*trace, TraceStep(step="gate", summary="resolved from approvals store",
                                     data={"approver": record.approver})),
            policy=self.policy.snapshot())

    # ------------------------------------------------------------------ judge and gate

    def _title_words(self, sku_id: str) -> frozenset[str]:
        return frozenset(self.index.item_text(sku_id).split())

    def _gate(self, parsed: ParsedLine, ranked: list[Candidate],
              judge: JudgeInput | None = None) -> Decision:
        return decide(parsed, ranked, self.policy, self.index.ontology, self._title_words, judge)

    def _decide(self, tenant_id: str, parsed: ParsedLine, ranked: list[Candidate],
                trace: list[TraceStep]) -> tuple[Decision, JudgeVerdict | None]:
        decision = self._gate(parsed, ranked)
        if not (decision.needs_judge and self._judge is not None):
            return decision, None
        # Only candidates that pass every check can be accepted, so only they are put to the judge.
        shown = [c for c in ranked if viable(parsed, c)][:self.policy.judge_top_k]
        if not shown:
            return decision, None
        examples = self._examples(tenant_id, parsed)
        verdict = self._judge.judge(parsed, shown, examples)
        self.judge_calls += verdict.calls
        top_ok = False
        if verdict.top is not None:
            item = self.index.get(verdict.top)
            assert item is not None  # the verdict only holds ids from `shown`
            again = _check_all(parsed, [self.index.score_item(parsed, item)], self.index)[0]
            top_ok = viable(parsed, again)  # re-validation: the same checks, run again
        trace.append(TraceStep(step="judge", summary="two candidate orderings", data={
            "status": verdict.status, "top": verdict.top, "ranking": list(verdict.ranking),
            "discarded_ids": verdict.discarded, "calls": verdict.calls}))
        trace.append(TraceStep(step="revalidate", summary="judge's choice re-checked",
                               data={"top": verdict.top, "passes": top_ok}))
        return self._gate(parsed, ranked, JudgeInput(verdict, top_ok)), verdict

    def _examples(self, tenant_id: str, parsed: ParsedLine) -> list[tuple[ApprovalRecord, str]]:
        out = []
        for record in self.store.nearest(tenant_id, parsed.retrieval_text,
                                         self.policy.judge_examples):
            item = self.index.get(record.sku_ids[0])
            if item is not None:
                out.append((record, item.title))
        return out

    # ------------------------------------------------------------------ result

    def _display(self, parsed: ParsedLine, ranked: list[Candidate],
                 verdict: JudgeVerdict | None) -> list[Candidate]:
        rank = {s: i for i, s in enumerate(verdict.ranking)} if verdict else {}
        good = [c for c in ranked if viable(parsed, c)]
        bad = [c for c in ranked if not viable(parsed, c)]
        good.sort(key=lambda c: (rank.get(c.item.sku_id, len(rank)), -c.scores.hybrid,
                                 c.item.sku_id))
        bad.sort(key=lambda c: (len(c.blocking), -c.scores.hybrid, c.item.sku_id))
        return [*good, *bad]

    def _result(self, tenant_id: str, parsed: ParsedLine, sig: str | None, ranked: list[Candidate],
                decision: Decision, verdict: JudgeVerdict | None,
                trace: list[TraceStep]) -> MatchResult:
        shown = (list(decision.group) if decision.outcome is Outcome.AUTO_ACCEPT
                 else self._display(parsed, ranked, verdict))[:self.policy.review_show_top]
        values = dict(decision.details)
        reasons = tuple(render_reason(code, **values) for code in decision.reasons)
        note = (AssistantNote(text=verdict.note) if verdict and verdict.note else None)
        trace.append(TraceStep(step="gate", summary=decision.outcome.value, data={
            "reasons": [c.value for c in decision.reasons],
            "group": [c.item.sku_id for c in decision.group]}))
        return MatchResult(
            tenant_id=tenant_id, line_id=parsed.line_id, outcome=decision.outcome,
            chosen=decision.chosen, group=decision.group, top=tuple(shown),
            reason_codes=decision.reasons, reasons=reasons,
            candidate_reasons={c.item.sku_id: render_candidate(c) for c in shown},
            question=decision.question, assistant_note=note, signature=sig, trace=tuple(trace),
            policy=self.policy.snapshot(), judge_calls=verdict.calls if verdict else 0)
