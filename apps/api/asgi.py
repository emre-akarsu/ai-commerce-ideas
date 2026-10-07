"""Deployment entrypoint: `uvicorn apps.api.asgi:app` (built lazily).

Without `DATABASE_URL` everything is the in-memory build (per-process state). With it, the quote
stores, the event log and the purchasing service's shared security state are Postgres-backed
(`apps.api.quote_pg`, `aidb.state.PgSharedState`); the URL must be the restricted `app_user` role
(row level security never applies to an owner). The purchasing service's own request store is still
in-memory, so ENV=production stays refused (docs/architecture/known-gaps.md, H2).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from components.core.ports import Clock

from .auth import build_authenticator
from .main import create_app

PROD_ENVS = frozenset({"production", "prod"})
MIN_KEY = 16


class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def _stable_key(env: Mapping[str, str], name: str) -> bytes:
    """Keys that must be identical across processes and restarts once state is persisted: an
    ephemeral random key would leave stored events and approvals unverifiable."""
    value = env.get(name, "")
    if len(value) < MIN_KEY:
        raise RuntimeError(f"{name} (at least {MIN_KEY} characters) is required with DATABASE_URL")
    return value.encode("utf-8")


def _quote_service_kwargs(env: Mapping[str, str]) -> dict[str, Any]:
    catalogue = env.get("QUOTE_CATALOGUE_FILE", "").strip()
    return {
        "demo": env.get("QUOTE_DEMO_DATA", "").strip() == "1",
        "catalogue_file": Path(catalogue) if catalogue else None,
    }


def build_app(env: Mapping[str, str] | None = None, *, clock: Clock | None = None) -> Any:
    e = os.environ if env is None else env
    if e.get("ENV", "").strip().lower() in PROD_ENVS:
        raise RuntimeError(
            "refusing to start: the shipped entrypoint uses the in-memory purchasing service, "
            "whose security state (approvals, kill switch, event chain) is process-local. "
            "See docs/architecture/known-gaps.md (H2) before deploying to production."
        )
    try:
        from employees.purchasing.service import build_in_memory_service
    except ImportError as exc:
        raise RuntimeError(
            "employees.purchasing.service.build_in_memory_service is not available yet"
        ) from exc
    from aiplat.profile import load_profile

    profile = load_profile(e.get("DEPLOYMENT_PROFILE", "us"))
    origins = [o for o in e.get("CORS_ORIGINS", "").split(",") if o]
    secret = e.get("INBOUND_WEBHOOK_SECRET") or None
    clk = clock or _SystemClock()
    url = e.get("DATABASE_URL", "").strip()
    if not url:
        from .quote_service import QuoteUnavailableError, build_quote_service

        app = create_app(
            build_in_memory_service(profile=profile, clock=clock), build_authenticator(e),
            cors_origins=origins, profile=profile, inbound_secret=secret)
        try:  # in-memory stores; the demo seed only with QUOTE_DEMO_DATA=1
            app.state.quote_service = build_quote_service(
                profile, clock=clk, **_quote_service_kwargs(e))
        except QuoteUnavailableError:
            pass  # the quote routes answer 503
        return app
    return _build_pg_app(url, e, profile, clk, origins, secret)


def _build_pg_app(url: str, e: Mapping[str, str], profile: Any, clk: Clock,
                  origins: list[str], secret: str | None) -> Any:
    import hashlib
    import hmac

    from employees.purchasing.service import build_in_memory_service

    from aidb.repositories import PgEventStore
    from aidb.session import make_engine
    from aidb.state import PgSharedState

    from .quote_pg import build_pg_stores
    from .quote_provision import demo_shared_summaries
    from .quote_service import EventLogSink, build_quote_service

    chain = _stable_key(e, "AUDIT_CHAIN_KEY")
    approval = _stable_key(e, "APPROVAL_SECRET")
    pii = e.get("AUDIT_PII_KEY", "").encode("utf-8") or hmac.new(
        chain, b"pii-key", hashlib.sha256).digest()
    engine = make_engine(url)  # app_user: every session verifies the role does not bypass RLS
    events = PgEventStore(engine, clk, pii_key=pii, chain_key=chain)
    shared = PgSharedState(engine, clock=clk)
    service = build_in_memory_service(
        profile=profile, clock=clk, event_log=events, approval_secret=approval,
        audit_key=chain, shared=shared.as_kwargs())
    opts = _quote_service_kwargs(e)
    from components.pricing import PricingConfig

    pricing = PricingConfig.from_mapping(profile.profile.model_dump(mode="json"))
    shared_imports = demo_shared_summaries(pricing) if opts["demo"] else ()
    quote = build_quote_service(
        profile, clock=clk, events=EventLogSink(events), seed_offers=False,
        stores=build_pg_stores(engine, pricing, clk, shared_imports), **opts)
    app = create_app(
        service, build_authenticator(e), cors_origins=origins, profile=profile,
        inbound_secret=secret, idempotency_store=shared.idempotency)
    app.state.quote_service = quote
    return app


def __getattr__(name: str) -> Any:
    if name == "app":
        return build_app()
    raise AttributeError(name)
