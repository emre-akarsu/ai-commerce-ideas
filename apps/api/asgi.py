"""Deployment entrypoint: `uvicorn apps.api.asgi:app` (built lazily)."""

from __future__ import annotations

import os
from typing import Any

from .auth import build_authenticator
from .main import create_app

PROD_ENVS = frozenset({"production", "prod"})


def build_app() -> Any:
    if os.environ.get("ENV", "").strip().lower() in PROD_ENVS:
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

    profile = load_profile(os.environ.get("DEPLOYMENT_PROFILE", "us"))
    origins = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]
    return create_app(
        build_in_memory_service(profile=profile), build_authenticator(), cors_origins=origins,
        profile=profile,
        inbound_secret=os.environ.get("INBOUND_WEBHOOK_SECRET") or None,
    )


def __getattr__(name: str) -> Any:
    if name == "app":
        return build_app()
    raise AttributeError(name)
