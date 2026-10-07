"""OntologyWriter: the single place the ontology changes (spec "Reference data layer").

Operations: add, merge, replace, discard (types) and add_noise_words. Every change is validated
against the same schema as seed data (classification codes must be in the verified registry),
needs a named actor and a reason, produces a new immutable `Ontology`, and appends an entry to an
append-only change log. The log is hash-chained so tampering is detectable. Wiring the log into
the platform's hash-chained Event store (rule 6) is a follow-up; this chain is local to the writer.

Nothing calls the writer automatically. `OntologyBuilder` only proposes; a person applies.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from components.core.ports import Clock

from .classification import VerifiedCodes
from .ontology import (
    EntryStatus,
    Lexicon,
    Ontology,
    OntologyError,
    ProductType,
    validate_type_entry,
)

GENESIS = "0" * 64


class WriterAction(StrEnum):
    ADD = "add"
    MERGE = "merge"
    REPLACE = "replace"
    DISCARD = "discard"
    ADD_NOISE_WORDS = "add_noise_words"


@dataclass(frozen=True)
class ChangeLogEntry:
    seq: int
    ts: datetime
    actor: str
    action: WriterAction
    target: str
    reason: str
    before_digest: str | None
    after_digest: str | None
    prev_hash: str
    hash: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _chain(prev: str, fields: Mapping[str, Any]) -> str:
    return hashlib.sha256((prev + json.dumps(fields, sort_keys=True)).encode()).hexdigest()


def _dump(entry: ProductType) -> dict[str, Any]:
    data: dict[str, Any] = entry.model_dump(mode="json")
    data.pop("id", None)
    return data


class OntologyWriter:
    def __init__(self, ontology: Ontology, registry: VerifiedCodes, clock: Clock) -> None:
        self._ontology = ontology
        self._registry = registry
        self._clock = clock
        self._log: list[ChangeLogEntry] = []

    @property
    def ontology(self) -> Ontology:
        return self._ontology

    @property
    def log(self) -> tuple[ChangeLogEntry, ...]:
        return tuple(self._log)

    # ------------------------------------------------------------------ helpers

    def _record(self, actor: str, reason: str, action: WriterAction, target: str,
                before: object, after: object) -> ChangeLogEntry:
        prev = self._log[-1].hash if self._log else GENESIS
        before_d = _digest(before) if before is not None else None
        after_d = _digest(after) if after is not None else None
        fields = {"seq": len(self._log) + 1, "actor": actor, "action": action.value,
                  "target": target, "reason": reason, "before": before_d, "after": after_d}
        entry = ChangeLogEntry(
            seq=len(self._log) + 1, ts=self._clock.now(), actor=actor, action=action,
            target=target, reason=reason, before_digest=before_d, after_digest=after_d,
            prev_hash=prev, hash=_chain(prev, fields))
        self._log.append(entry)
        return entry

    @staticmethod
    def _need(actor: str, reason: str) -> None:
        if not actor.strip() or not reason.strip():
            raise OntologyError("a change needs an actor and a reason")

    def _validated(self, type_id: str, raw: Mapping[str, Any], status: EntryStatus) -> ProductType:
        if status is EntryStatus.PROPOSED:
            raise OntologyError("the writer never stores a 'proposed' entry; "
                                "choose needs_tradesperson_review or approved")
        return validate_type_entry(type_id, {**raw, "status": status.value}, self._registry)

    def _commit(self, types: dict[str, ProductType], lexicon: Lexicon | None = None) -> None:
        self._ontology = self._ontology.with_types(types, lexicon)

    # ------------------------------------------------------------------ type operations

    def add(self, type_id: str, entry: Mapping[str, Any], *, actor: str, reason: str,
            status: EntryStatus = EntryStatus.NEEDS_REVIEW) -> ChangeLogEntry:
        self._need(actor, reason)
        if type_id in self._ontology.types:
            raise OntologyError(f"{type_id} already exists: use merge or replace")
        new = self._validated(type_id, entry, status)
        self._commit({**self._ontology.types, type_id: new})
        return self._record(actor, reason, WriterAction.ADD, type_id, None, _dump(new))

    def replace(self, type_id: str, entry: Mapping[str, Any], *, actor: str, reason: str,
                status: EntryStatus = EntryStatus.NEEDS_REVIEW) -> ChangeLogEntry:
        self._need(actor, reason)
        old = self._existing(type_id)
        new = self._validated(type_id, entry, status)
        self._commit({**self._ontology.types, type_id: new})
        return self._record(actor, reason, WriterAction.REPLACE, type_id, _dump(old), _dump(new))

    def merge(self, type_id: str, entry: Mapping[str, Any], *, actor: str, reason: str,
              status: EntryStatus = EntryStatus.NEEDS_REVIEW) -> ChangeLogEntry:
        """Fold a duplicate or extension into an existing type: synonyms and vocabulary are
        unioned, new attributes and enum values are added, provenance is appended. A clash on an
        existing attribute's kind or unit is refused (replace it instead)."""
        self._need(actor, reason)
        old = self._existing(type_id)
        merged = _merge(_dump(old), dict(entry))
        new = self._validated(type_id, merged, status)
        self._commit({**self._ontology.types, type_id: new})
        return self._record(actor, reason, WriterAction.MERGE, type_id, _dump(old), _dump(new))

    def discard(self, type_id: str, *, actor: str, reason: str) -> ChangeLogEntry:
        self._need(actor, reason)
        old = self._existing(type_id)
        if len(self._ontology.types) == 1:
            raise OntologyError("cannot discard the last product type")
        rest = {k: v for k, v in self._ontology.types.items() if k != type_id}
        self._commit(rest)
        return self._record(actor, reason, WriterAction.DISCARD, type_id, _dump(old), None)

    def add_noise_words(self, words: Sequence[str], *, actor: str, reason: str) -> ChangeLogEntry:
        self._need(actor, reason)
        clean = sorted({w.strip().lower() for w in words if w.strip()})
        if not clean or any(not w.isalpha() or len(w) > 20 for w in clean):
            raise OntologyError("noise words must be short plain words")
        spec_words = {tok for tid in self._ontology.types
                      for tok in self._ontology.vocabulary(tid)}
        clash = sorted(set(clean) & spec_words)
        if clash:
            raise OntologyError(f"words that carry a specification cannot be noise: {clash}")
        lex = self._ontology.lexicon
        merged = tuple(dict.fromkeys((*lex.noise_words, *clean)))
        self._commit(dict(self._ontology.types), lex.model_copy(update={"noise_words": merged}))
        return self._record(actor, reason, WriterAction.ADD_NOISE_WORDS, "lexicon",
                            list(lex.noise_words), list(merged))

    def _existing(self, type_id: str) -> ProductType:
        try:
            return self._ontology.types[type_id]
        except KeyError:
            raise OntologyError(f"unknown product type {type_id!r}") from None

    # ------------------------------------------------------------------ audit

    def verify_log(self) -> bool:
        prev = GENESIS
        for i, e in enumerate(self._log, start=1):
            fields = {"seq": i, "actor": e.actor, "action": e.action.value, "target": e.target,
                      "reason": e.reason, "before": e.before_digest, "after": e.after_digest}
            if e.seq != i or e.prev_hash != prev or e.hash != _chain(prev, fields):
                return False
            prev = e.hash
        return True


def _union(a: Sequence[Any], b: Sequence[Any]) -> list[Any]:
    seen: dict[str, Any] = {}
    for item in [*a, *b]:
        seen.setdefault(json.dumps(item, sort_keys=True, default=str), item)
    return list(seen.values())


def _merge_attribute(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    for key in ("kind", "unit"):
        if old.get(key) != new.get(key):
            raise OntologyError(f"merge refused: {old['name']}.{key} differs "
                                f"({old.get(key)!r} vs {new.get(key)!r})")
    merged = dict(old)
    merged["aliases"] = _union(old.get("aliases", []), new.get("aliases", []))
    values = {k: dict(v) for k, v in old.get("values", {}).items()}
    for vid, val in new.get("values", {}).items():
        if vid in values:
            values[vid]["synonyms"] = _union(values[vid].get("synonyms", []),
                                             val.get("synonyms", []))
        else:
            values[vid] = dict(val)
    merged["values"] = values
    return merged


def _merge(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = dict(old)
    merged["synonyms"] = _union(old["synonyms"], new.get("synonyms", []))
    merged["vocab"] = _union(old.get("vocab", []), new.get("vocab", []))
    merged["provenance"] = _union(old["provenance"], new.get("provenance", []))
    by_name = {a["name"]: a for a in old["attributes"]}
    for attr in new.get("attributes", []):
        by_name[attr["name"]] = (_merge_attribute(by_name[attr["name"]], attr)
                                 if attr["name"] in by_name else attr)
    merged["attributes"] = list(by_name.values())
    return merged
