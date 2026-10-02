"""Deployment entrypoint: `uvicorn apps.api.asgi:app` (built lazily)."""

from __future__ import annotations

import os
from typing import Any

from .auth import build_authenticator
from .main import create_app


def build_app() -> Any:
    try:
        from employees.purchasing.service import build_in_memory_service
    except ImportError as exc:
        raise RuntimeError(
            "employees.purchasing.service.build_in_memory_service is not available yet"
        ) from exc
    origins = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]
    return create_app(build_in_memory_service(), build_authenticator(), cors_origins=origins)


def __getattr__(name: str) -> Any:
    if name == "app":
        return build_app()
    raise AttributeError(name)
