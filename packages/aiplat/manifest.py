# ruff: noqa: E501
"""Employee manifest: the config-level description of an AI employee pack.

Loaded from ``employee.yaml``; validated strictly (unknown keys are rejected) so a typo in a pack
cannot silently drop a limit or an approval requirement. Money limits are ``Decimal``.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SLUG = re.compile(r"^[a-z][a-z0-9_-]{1,40}$")
_DOTTED = re.compile(r"^[A-Za-z_][\w]*(\.[A-Za-z_][\w]*)+$")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorkflowSpec(_Strict):
    approval: str | None = None
    schedule: str | None = None  # cron expression; empty means on demand


class EmployeeManifest(_Strict):
    id: str
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    model: str = Field(min_length=1)
    integrations: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    workflows: dict[str, WorkflowSpec] = Field(default_factory=dict)
    modules: list[str] = Field(default_factory=list)
    uses: dict[str, dict[str, Any]] = Field(default_factory=dict)
    limits: dict[str, Decimal] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _id_is_slug(cls, v: str) -> str:
        if not _SLUG.match(v):
            raise ValueError("id must be a lowercase slug")
        return v

    @field_validator("tools")
    @classmethod
    def _tools_dotted(cls, v: list[str]) -> list[str]:
        for t in v:
            if not _DOTTED.match(t):
                raise ValueError(f"tool {t!r} must be a dotted import path")
        if len(set(v)) != len(v):
            raise ValueError("duplicate tool")
        return v

    @field_validator("limits", mode="before")
    @classmethod
    def _limits_decimal(cls, v: Any) -> Any:
        if not isinstance(v, dict):
            return v
        out: dict[str, Decimal] = {}
        for k, x in v.items():
            if isinstance(x, float) or isinstance(x, bool):
                raise ValueError(f"limit {k!r} must be an integer or decimal string, not a float")
            out[k] = Decimal(str(x))
        return out

    @model_validator(mode="after")
    def _limits_sane(self) -> EmployeeManifest:
        for k, x in self.limits.items():
            if x <= 0:
                raise ValueError(f"limit {k!r} must be positive")
        per, daily = self.limits.get("per_order_max_usd"), self.limits.get("daily_aggregate_max_usd")
        if per is not None and daily is not None and daily < per:
            raise ValueError("daily_aggregate_max_usd must be >= per_order_max_usd")
        return self


class ManifestError(ValueError):
    """The manifest file is missing, not YAML, or fails validation."""


def parse_manifest(text: str) -> EmployeeManifest:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ManifestError(f"not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("manifest must be a mapping")
    try:
        return EmployeeManifest.model_validate(data)
    except ValueError as exc:  # pydantic.ValidationError subclasses ValueError
        raise ManifestError(str(exc)) from exc


def load_manifest(path: str | Path) -> EmployeeManifest:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(f"cannot read {p}: {exc}") from exc
    return parse_manifest(text)


def manifest_json_schema() -> dict[str, Any]:
    """JSON Schema (draft 2020-12) of ``employee.yaml``."""
    return EmployeeManifest.model_json_schema()
