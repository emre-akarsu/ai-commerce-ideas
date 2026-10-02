"""Worker task implementations (stack-map S2, U1, U6; spec R1, R6, R7, R10).

Every per-tenant task takes ``tenant_id`` as an argument set by the platform when the job is
deferred (never derived from job content) and runs inside ``aidb.session.tenant_session``: the
restricted ``app_user`` role plus ``SET LOCAL app.tenant_id``. There is no service-role path. The
worker never sends mail itself: ``run_follow_ups`` only asks the send-service to run the
pre-approved follow-up schedule, which refuses anything without a registered approval.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Protocol

from sqlalchemy import Connection, Engine, text

from aidb.session import tenant_session
from components.core.ports import Clock
from components.doc_parse import DocumentParser, LocalTextParser, ParsedDocument
from components.evidence.log import EventLog

log = logging.getLogger("worker")

EVT_INBOUND_PARSED = "inbound.parsed"
EVT_CHAIN_VERIFIED = "audit.chain_verified"
EVT_CHAIN_INVALID = "audit.chain_invalid"
EVT_USAGE_ROLLUP = "usage.rollup"

_REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/@=-]{0,199}")

# name -> cron (UTC). Used for Procrastinate periodic tasks and mirrored by the Render cron docs.
SCHEDULES: dict[str, str] = {
    "worker.fan_out_follow_ups": "*/15 * * * *",
    "worker.fan_out_verify_audit_chain": "30 2 * * *",
    "worker.fan_out_meter_usage_rollup": "5 * * * *",
}


class TenantContextError(RuntimeError):
    """A task was invoked without a usable tenant context. The task did nothing."""


@dataclass(frozen=True)
class RawInbound:
    filename: str
    content: bytes
    content_type: str | None = None


class InboundSource(Protocol):
    def fetch(self, conn: Connection, tenant_id: str, message_ref: str) -> RawInbound:
        """Load stored raw bytes for a message through the tenant-bound connection."""


class FollowUpRunner(Protocol):
    def run_due_follow_ups(self) -> list[str]: ...


class TenantDirectory(Protocol):
    def tenant_ids(self) -> list[str]:
        """Active tenant ids; the platform's tenant list, not data of any tenant."""


@dataclass
class WorkerContext:
    engine: Engine  # connects as app_user (NOBYPASSRLS); checked on every tenant_session
    clock: Clock
    event_log: EventLog  # PgEventStore in production
    inbound_source: InboundSource | None = None
    send_service_factory: Callable[[str], FollowUpRunner] | None = None
    parser: DocumentParser = field(default_factory=LocalTextParser)
    on_parsed: Callable[[str, str, ParsedDocument], None] | None = None
    on_chain_invalid: Callable[[str, dict[str, Any]], None] | None = None
    tenant_directory: TenantDirectory | None = None


def require_tenant(tenant_id: object) -> str:
    if not isinstance(tenant_id, str) or not tenant_id.strip() or "\x00" in tenant_id:
        raise TenantContextError("tenant_id is required and is set by the platform")
    return tenant_id


class Tasks:
    def __init__(self, ctx: WorkerContext) -> None:
        self.ctx = ctx

    @contextmanager
    def tenant(self, tenant_id: object) -> Iterator[tuple[str, Connection]]:
        tid = require_tenant(tenant_id)
        with tenant_session(self.ctx.engine, tid) as conn:
            known = conn.execute(text("SELECT 1 FROM tenants WHERE id = :t"), {"t": tid}).first()
            if known is None:
                raise TenantContextError("unknown tenant")
            yield tid, conn

    # ------------------------------------------------------------------ tasks

    def parse_inbound_message(
        self, tenant_id: str | None = None, message_ref: str | None = None
    ) -> dict[str, Any]:
        with self.tenant(tenant_id) as (tid, conn):
            if not isinstance(message_ref, str) or not _REF_RE.fullmatch(message_ref):
                raise ValueError("message_ref must be an opaque storage reference")
            if self.ctx.inbound_source is None:
                raise RuntimeError("no inbound source configured")
            raw = self.ctx.inbound_source.fetch(conn, tid, message_ref)
        doc = self.ctx.parser.parse(raw.content, filename=raw.filename,
                                    content_type=raw.content_type)
        summary = {
            "message_ref": message_ref,
            "sha256": doc.sha256,
            "usable": doc.usable,
            "flags": list(doc.flags),
            "chars": len(doc.text),
            "pages": len(doc.pages),
            "attachments": len(doc.attachments),
        }
        self.ctx.event_log.append(tid, None, "system", EVT_INBOUND_PARSED, summary)
        if self.ctx.on_parsed is not None:
            self.ctx.on_parsed(tid, message_ref, doc)
        return summary

    def run_follow_ups(self, tenant_id: str | None = None) -> dict[str, Any]:
        with self.tenant(tenant_id) as (tid, _conn):
            if self.ctx.send_service_factory is None:
                raise RuntimeError("no send-service factory configured")
            runner = self.ctx.send_service_factory(tid)
            sent = runner.run_due_follow_ups()  # the service enforces approvals/kill switch
        return {"tenant_id": tid, "sent": len(sent)}

    def verify_audit_chain(self, tenant_id: str | None = None) -> dict[str, Any]:
        with self.tenant(tenant_id) as (tid, _conn):
            first_bad = self.ctx.event_log.first_invalid(tid)
            count, head = self.ctx.event_log.head(tid)
        result: dict[str, Any] = {
            "tenant_id": tid, "valid": first_bad is None, "first_invalid": first_bad,
            "events": count, "head": head,
        }
        payload = {k: v for k, v in result.items() if k != "tenant_id"}
        self.ctx.event_log.append(
            tid, None, "system", EVT_CHAIN_VERIFIED if first_bad is None else EVT_CHAIN_INVALID,
            payload,
        )
        if first_bad is not None:
            log.error("audit chain INVALID for tenant %s at index %s", tid, first_bad)
            if self.ctx.on_chain_invalid is not None:
                self.ctx.on_chain_invalid(tid, result)
        return result

    def meter_usage_rollup(self, tenant_id: str | None = None) -> dict[str, Any]:
        """Stub: usage metering is not designed yet (no pricing claims). Does nothing but run
        in tenant context so the schedule and wiring can be exercised."""
        with self.tenant(tenant_id) as (tid, _conn):
            return {"tenant_id": tid, "status": "stub"}


def register_tasks(app: Any, ctx: WorkerContext) -> Tasks:
    """Register the tasks and periodic fan-outs on a Procrastinate app."""
    import procrastinate

    impl = Tasks(ctx)
    task = app.task

    @task(name="worker.parse_inbound_message", queue="inbound")
    def parse_inbound_message(tenant_id: str | None = None,
                              message_ref: str | None = None) -> dict[str, Any]:
        return impl.parse_inbound_message(tenant_id, message_ref)

    @task(name="worker.run_follow_ups", queue="followups")
    def run_follow_ups(tenant_id: str | None = None) -> dict[str, Any]:
        return impl.run_follow_ups(tenant_id)

    @task(name="worker.verify_audit_chain", queue="audit")
    def verify_audit_chain(tenant_id: str | None = None) -> dict[str, Any]:
        return impl.verify_audit_chain(tenant_id)

    @task(name="worker.meter_usage_rollup", queue="metering")
    def meter_usage_rollup(tenant_id: str | None = None) -> dict[str, Any]:
        return impl.meter_usage_rollup(tenant_id)

    async def fan_out(target: str, timestamp: int) -> int:
        import asyncio

        if ctx.tenant_directory is None:
            raise RuntimeError("no tenant directory configured")
        ids = await asyncio.to_thread(ctx.tenant_directory.tenant_ids)
        deferred = 0
        for tid in ids:
            try:
                await app.configure_task(target, queueing_lock=f"{target}:{tid}").defer_async(
                    tenant_id=tid
                )
                deferred += 1
            except procrastinate.exceptions.AlreadyEnqueued:
                continue
        return deferred

    @app.periodic(cron=SCHEDULES["worker.fan_out_follow_ups"])
    @task(name="worker.fan_out_follow_ups", queue="fanout")
    async def fan_out_follow_ups(timestamp: int) -> int:
        return await fan_out("worker.run_follow_ups", timestamp)

    @app.periodic(cron=SCHEDULES["worker.fan_out_verify_audit_chain"])
    @task(name="worker.fan_out_verify_audit_chain", queue="fanout")
    async def fan_out_verify_audit_chain(timestamp: int) -> int:
        return await fan_out("worker.verify_audit_chain", timestamp)

    @app.periodic(cron=SCHEDULES["worker.fan_out_meter_usage_rollup"])
    @task(name="worker.fan_out_meter_usage_rollup", queue="fanout")
    async def fan_out_meter_usage_rollup(timestamp: int) -> int:
        return await fan_out("worker.meter_usage_rollup", timestamp)

    return impl
