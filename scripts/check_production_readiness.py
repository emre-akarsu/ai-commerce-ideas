#!/usr/bin/env python3
# ruff: noqa: E501
"""Prints each H2 production-readiness item as PASS or FAIL (docs/architecture/known-gaps.md).

The checks are code introspection only (no network, no database, nothing is started or sent): they read
the source of the shipped wiring and of the stores, so an item flips to PASS only when the code changes.
Exit status 1 while anything FAILs: ENV=production stays refused (`apps/api/asgi.py`) until all PASS and a
person has reviewed the result. A PASS here means "the code has this property", not "production ready".
"""

from __future__ import annotations

import ast
import inspect
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("packages", "."):
    path = str(ROOT / sub)
    if path not in sys.path:
        sys.path.insert(0, path)

Check = Callable[[], tuple[bool, str]]


def _src(obj: object) -> str:
    return inspect.getsource(obj)  # type: ignore[arg-type]


def stores_in_postgres() -> tuple[bool, str]:
    from apps.api import asgi
    from employees.purchasing import service

    ok = "PgServiceStore" in _src(service.build_pg_service) and "build_pg_service" in _src(asgi._build_pg_app)
    return ok, "asgi (DATABASE_URL) builds the service with build_pg_service over PgServiceStore"


def tenant_kill_switch_shared() -> tuple[bool, str]:
    from aidb.state import PgSharedState

    return "kill_switch" in _src(PgSharedState.as_kwargs), "per-tenant kill switch is a shared Postgres row"


def global_kill_switch_shared() -> tuple[bool, str]:
    from aidb.state import PgKillSwitch

    shared = "super().engage(None)" not in _src(PgKillSwitch.engage)
    return shared, "global (all-tenant) kill switch flag is process-local (PgKillSwitch.engage(None))"


def threshold_aggregate_atomic() -> tuple[bool, str]:
    from employees.purchasing.service import SpendBook

    names = [n for n in dir(SpendBook) if n.startswith(("claim", "try_", "reserve_committed"))]
    return bool(names), "committed_today then set_committed is read-then-write; no atomic claim on SpendBook"


def idempotency_atomic() -> tuple[bool, str]:
    from aidb.state import PgIdempotencyStore

    names = [n for n in dir(PgIdempotencyStore) if n.startswith(("claim", "put_if", "reserve", "begin"))]
    return bool(names), "idempotency replay is get-then-put; no atomic first-writer claim"


def prepared_cache_shared() -> tuple[bool, str]:
    from employees.purchasing.service import PurchasingService

    shared = "self._prepared: dict" not in _src(PurchasingService.__init__) and (
        "self._prepared:" not in _src(PurchasingService.__init__))
    return shared, "prepared-message cache is a per-process dict (approve-send fails closed elsewhere)"


def notifier_durable() -> tuple[bool, str]:
    from apps.api import asgi

    return "notifier" in _src(asgi._build_pg_app), "approval-link notifier: shipped entrypoint passes none (in-memory)"


def multi_step_atomic() -> tuple[bool, str]:
    from employees.purchasing.service import PurchasingService

    shared = "threading.Lock" not in _src(PurchasingService.__init__)
    return shared, "service operations are separate transactions; prepare_rfqs lock is threading (in-process)"


def real_transport_exists() -> tuple[bool, str]:
    found: list[str] = []
    for base in ("packages", "apps", "employees"):
        for py in (ROOT / base).rglob("*.py"):
            if py.name == "fakes.py" or "node_modules" in py.parts:
                continue
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and any(
                    isinstance(f, ast.FunctionDef) and f.name == "deliver" for f in node.body
                ) and node.name not in {"MailTransport"} and "Recording" not in node.name:
                    found.append(f"{py.relative_to(ROOT)}:{node.name}")
    return bool(found), "no real MailTransport / inbound provider implementation (recording transport only)"


CHECKS: tuple[tuple[str, Check], ...] = (
    ("purchasing stores in Postgres when DATABASE_URL is set", stores_in_postgres),
    ("per-tenant kill switch shared", tenant_kill_switch_shared),
    ("global kill switch shared", global_kill_switch_shared),
    ("approval-threshold aggregate atomic across processes", threshold_aggregate_atomic),
    ("idempotency replay atomic", idempotency_atomic),
    ("prepared-message cache shared", prepared_cache_shared),
    ("approval-link notifier durable", notifier_durable),
    ("multi-step operations transactional / prepare lock shared", multi_step_atomic),
    ("real mail transport exists", real_transport_exists),
)


def main() -> int:
    failed = 0
    for name, check in CHECKS:
        ok, detail = check()
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  [{detail}]")
    print(f"{len(CHECKS) - failed} pass, {failed} fail; ENV=production stays refused until none fail.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
