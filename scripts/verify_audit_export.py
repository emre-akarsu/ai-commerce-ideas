#!/usr/bin/env python3
"""Offline verifier for `GET /v1/audit/export` files. Standard library only: no database, no network.

    AUDIT_CHAIN_KEY=<key> python scripts/verify_audit_export.py export.json
    python scripts/verify_audit_export.py export.json --linkage-only

The audit chain is keyed (HMAC-SHA256 under the deployment's AUDIT_CHAIN_KEY, see
packages/components/evidence/log.py), so recomputing a hash needs that key; the export never
contains it. With the key the verifier recomputes every event hash and the links between events.
With --linkage-only it checks structure only (ids, prev_hash links, head) and says so: that mode
cannot detect an edited payload.

Exit codes: 0 verified, 1 mismatch (tampered or inconsistent), 2 unreadable input or bad usage,
3 no key given and --linkage-only not requested (nothing was fully verified).

A request-scoped export (`request_id` set) holds a subset of the chain: each event hash is
recomputed, links are checked only between adjacent events, and the head is not compared.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime
from typing import Any

GENESIS = "0" * 64
PII_KEY, DIGESTS_KEY = "_pii", "_pii_digests"


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def chain_hash(prev_hash: str, envelope: dict[str, Any], key: bytes) -> str:
    msg = (prev_hash + "|" + canonical_json(envelope)).encode("ascii")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def envelope(ev: dict[str, Any]) -> dict[str, Any]:
    payload = dict(ev["payload"])
    payload.pop(PII_KEY, None)
    digests = payload.pop(DIGESTS_KEY, {})
    ts = datetime.fromisoformat(ev["ts"]).isoformat()  # same text the log hashed ("Z" -> "+00:00")
    return {"id": ev["id"], "tenant_id": ev["tenant_id"], "request_id": ev["request_id"], "ts": ts,
            "actor": ev["actor"], "type": ev["type"], "payload": payload, "pii_digests": digests}


def _seq(ev: dict[str, Any]) -> int:
    return int(ev["id"].rsplit("-", 1)[1])


def verify(doc: dict[str, Any], key: bytes | None) -> list[str]:
    """Problems found (empty = verified, to the extent the mode allows)."""
    problems: list[str] = []
    events = doc.get("events")
    if not isinstance(events, list):
        return ["no events list"]
    scoped = doc.get("request_id") is not None
    prev: dict[str, Any] | None = None
    for i, ev in enumerate(events):
        try:
            seq = _seq(ev)
            adjacent = prev is not None and seq == _seq(prev) + 1
            if prev is None:
                expected_prev = None if scoped else GENESIS
                if not scoped and seq != 1:
                    problems.append(f"{ev['id']}: chain does not start at event 1")
            elif adjacent:
                expected_prev = prev["hash"]
            else:
                expected_prev = None
                if not scoped:
                    problems.append(f"{ev['id']}: gap or reordering after {prev['id']}")
            if expected_prev is not None and ev["prev_hash"] != expected_prev:
                problems.append(f"{ev['id']}: prev_hash does not link to the previous event")
            if key is not None and not hmac.compare_digest(
                    chain_hash(ev["prev_hash"], envelope(ev), key), str(ev["hash"])):
                problems.append(f"{ev['id']}: hash mismatch (event changed or wrong key)")
        except (KeyError, ValueError, TypeError, IndexError):
            problems.append(f"event #{i}: malformed")
        prev = ev if isinstance(ev, dict) else None
    if not scoped and events and prev is not None:
        if doc.get("head_hash") != prev.get("hash"):
            problems.append("head_hash does not match the last event")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify an audit export offline.")
    ap.add_argument("file")
    ap.add_argument("--key-env", default="AUDIT_CHAIN_KEY", help="env var holding the chain key")
    ap.add_argument("--linkage-only", action="store_true", help="structure only; no key needed")
    args = ap.parse_args(argv)
    try:
        with open(args.file, encoding="utf-8") as fh:
            doc = json.load(fh)
        if not isinstance(doc, dict):
            raise ValueError("not an export object")
    except (OSError, ValueError) as exc:
        print(f"cannot read export: {exc}", file=sys.stderr)
        return 2
    raw = os.environ.get(args.key_env, "")
    key = raw.encode("utf-8") if raw else None
    if key is None and not args.linkage_only:
        print(f"no key: set {args.key_env}, or pass --linkage-only (cannot detect edited payloads)",
              file=sys.stderr)
        return 3
    problems = verify(doc, None if args.linkage_only else key)
    if problems:
        print("FAILED")
        for p in problems:
            print(" -", p)
        return 1
    mode = "linkage only (payloads NOT verified)" if args.linkage_only else "hashes and links"
    print(f"OK: {len(doc['events'])} event(s), {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
