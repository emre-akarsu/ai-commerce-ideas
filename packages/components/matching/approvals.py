"""Approved matches: the store that makes "previously approved" resolve instantly (step 7, Learn).

Every method takes `tenant_id` first and only ever touches that tenant's records (CLAUDE.md rule
7). The in-memory store takes an injected `Clock` for approval timestamps. Wiring approvals into
the hash-chained Event log (rule 6) is a follow-up: until then an approval is a record here, not
an audit Event (docs/architecture/matching-engine.md, "Known gaps").
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from components.core.ports import Clock

from .embedding import HashingEmbedder, cosine
from .models import ParsedLine
from .similarity import cosine_counts, trigrams


def signature(line: ParsedLine) -> str | None:
    """Normalised signature of what a line asks for (quantity excluded). None when the line is
    quantity-versus-size ambiguous: such a line is never approved or resolved by signature."""
    if line.ambiguities:
        return None
    parts = [f"type={line.type_hint.type_id or '|'.join(line.type_hint.alternatives) or '?'}"]
    parts += sorted(f"{a.name}={a.value}{a.unit or ''}" for a in line.attributes)
    parts += [f"brand={line.brand or ''}", f"mpn={line.mpn or ''}", f"gtin={line.gtin or ''}"]
    if line.conflicts:
        parts.append("conflicts=" + ",".join(sorted(line.conflicts)))
    if line.unbound:
        parts.append("unbound=" + ",".join(sorted(line.unbound)))
    if not line.type_hint.certain:
        parts.append("tokens=" + " ".join(sorted(line.tokens)))
    return "sig1:" + hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class ApprovalRecord:
    tenant_id: str
    signature: str
    sku_ids: tuple[str, ...]  # one SKU, or the interchangeable group a person approved
    approver: str
    approved_at: datetime  # from the injected Clock
    line_text: str  # untrusted: the approved line as typed
    retrieval_text: str  # canonical text, for nearest-example lookup


class ApprovedMatchStore(Protocol):
    def approve(self, tenant_id: str, signature: str, line_text: str, retrieval_text: str,
                sku_ids: Sequence[str], approver: str) -> ApprovalRecord: ...

    def lookup(self, tenant_id: str, signature: str) -> ApprovalRecord | None: ...

    def nearest(self, tenant_id: str, retrieval_text: str, k: int) -> list[ApprovalRecord]: ...

    def count(self, tenant_id: str) -> int: ...


class InMemoryApprovedMatchStore:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._by_tenant: dict[str, dict[str, ApprovalRecord]] = {}
        self._embedder = HashingEmbedder()

    def approve(self, tenant_id: str, signature: str, line_text: str, retrieval_text: str,
                sku_ids: Sequence[str], approver: str) -> ApprovalRecord:
        if not tenant_id or not approver or not sku_ids:
            raise ValueError("tenant, approver and at least one SKU are required")
        record = ApprovalRecord(tenant_id, signature, tuple(sku_ids), approver,
                                self._clock.now(), line_text, retrieval_text)
        self._by_tenant.setdefault(tenant_id, {})[signature] = record
        return record

    def lookup(self, tenant_id: str, signature: str) -> ApprovalRecord | None:
        return self._by_tenant.get(tenant_id, {}).get(signature)

    def nearest(self, tenant_id: str, retrieval_text: str, k: int) -> list[ApprovalRecord]:
        records = self._by_tenant.get(tenant_id, {}).values()
        tri, vec = trigrams(retrieval_text), self._embedder.embed(retrieval_text)

        def score(r: ApprovalRecord) -> float:
            return (cosine_counts(tri, trigrams(r.retrieval_text))
                    + cosine(vec, self._embedder.embed(r.retrieval_text)))

        return sorted(records, key=lambda r: (-score(r), r.signature))[:max(0, k)]

    def count(self, tenant_id: str) -> int:
        return len(self._by_tenant.get(tenant_id, {}))
