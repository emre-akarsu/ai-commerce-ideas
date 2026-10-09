"""Declarative models for composable workflows (ADR-012): capability refs, module manifests,
workflow templates and industry packs.

Everything is validated strictly (unknown keys rejected). The DSL has no expressions: a branch
names a predicate that a module exports, and a jump can only go forward, so a template is always a
DAG and cannot grow into a second programming language.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SLUG = re.compile(r"^[a-z][a-z0-9-]{1,48}$")
_STEP_ID = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_PRED = re.compile(r"^[a-z][a-z0-9_]{0,47}$")
_CAP = re.compile(r"^([A-Z][A-Za-z0-9]{1,48})@([1-9]\d{0,2})$")
_MOD_REF = re.compile(r"^([a-z][a-z0-9-]{1,48})@([1-9]\d{0,2})$")
_SEMVER = re.compile(r"^([1-9]\d{0,2})\.(\d{1,3})\.(\d{1,3})$")
_ENTRY = re.compile(r"^[A-Za-z_]\w*(\.[A-Za-z_]\w*)+:[A-Za-z_]\w*$")

# Steps the platform implements itself. Packs and deployments can never bind or replace them.
KERNEL_CAPABILITIES = frozenset({"Approval", "SendService", "AwaitReplies"})
# Module code may only be imported from these packages (no third-party plug-ins until a signing
# and review process exists: composability.md section 11).
ALLOWED_ENTRY_PREFIXES = ("employees.", "components.")
# Data origins a module can consume. "vendor" is untrusted inbound content (R6).
DataTag = Literal["request", "pack", "vendor"]
Effects = Literal["pure", "read", "write", "external_read"]  # "send" is kernel-only (R1)

# Keys that would weaken a hard rule if they existed. No module reads them; their presence in pack
# or deployment settings is an error (linter C7), so a typo or a "temporary" switch cannot land.
RESERVED_SETTING_KEYS = frozenset({
    "approval_required", "require_approval", "skip_approval", "auto_approve", "auto_send",
    "send_without_approval", "autonomous", "allow_scraping", "fetch_links", "follow_links",
    "auto_substitute", "allow_substitution", "commit_allowed", "auto_order", "disable_audit",
    "audit", "tenant_id", "tenant", "kill_switch", "footer", "ai_disclosure", "trust_vendor",
})


M = TypeVar("M", bound=BaseModel)


class CompositionError(ValueError):
    """A template, module, pack or deployment is malformed or fails the composition linter."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def parse_cap(ref: str) -> tuple[str, int]:
    m = _CAP.match(ref)
    if not m:
        raise ValueError(f"capability {ref!r} must look like Name@1")
    return m.group(1), int(m.group(2))


def parse_module_ref(ref: str) -> tuple[str, int]:
    m = _MOD_REF.match(ref)
    if not m:
        raise ValueError(f"module ref {ref!r} must look like module-id@1")
    return m.group(1), int(m.group(2))


# ------------------------------------------------------------------------------------- modules


class LlmSpec(_Strict):
    role: str = Field(min_length=1)
    tools: tuple[str, ...] = ()


class ModuleManifest(_Strict):
    id: str
    version: str
    provides: tuple[str, ...] = Field(min_length=1)
    requires: tuple[str, ...] = ()
    effects: Effects
    consumes: tuple[DataTag, ...] = ()
    grounded: bool = False  # vendor data passes the quarantined parse + verbatim grounding check
    llm: LlmSpec | None = None
    entry: str
    predicates: dict[str, str] = Field(default_factory=dict)
    settings: tuple[str, ...] = ()  # pack setting keys this module reads
    evals: tuple[str, ...] = ()

    @field_validator("id")
    @classmethod
    def _slug(cls, v: str) -> str:
        if not _SLUG.match(v):
            raise ValueError("module id must be a lowercase slug")
        return v

    @field_validator("version")
    @classmethod
    def _semver(cls, v: str) -> str:
        if not _SEMVER.match(v):
            raise ValueError("module version must be MAJOR.MINOR.PATCH")
        return v

    @field_validator("provides", "requires")
    @classmethod
    def _caps(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        for ref in v:
            name, _ = parse_cap(ref)
            if name in KERNEL_CAPABILITIES:
                raise ValueError(f"{name} is a kernel capability; a module cannot provide it")
        return v

    @field_validator("entry")
    @classmethod
    def _entry(cls, v: str) -> str:
        return _check_entry(v)

    @field_validator("predicates")
    @classmethod
    def _predicates(cls, v: dict[str, str]) -> dict[str, str]:
        for name, entry in v.items():
            if not _PRED.match(name):
                raise ValueError(f"predicate name {name!r} must be snake_case")
            _check_entry(entry)
        return v

    @property
    def major(self) -> int:
        return int(self.version.split(".")[0])

    @property
    def ref(self) -> str:
        return f"{self.id}@{self.major}"


def _check_entry(v: str) -> str:
    if not _ENTRY.match(v):
        raise ValueError(f"entry {v!r} must be 'package.module:function'")
    if not v.startswith(ALLOWED_ENTRY_PREFIXES):
        raise ValueError(f"entry {v!r} is outside the allowed packages {ALLOWED_ENTRY_PREFIXES}")
    return v


# ----------------------------------------------------------------------------------- templates


class Step(_Strict):
    id: str
    uses: str
    human: Literal["required"] | None = None
    covers: str | None = None  # Approval only: the data key the human approves (hash-bound)
    # predicate -> "stop" | later step id ("branch", not "on": YAML 1.1 reads a bare on as true)
    branch: dict[str, str] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not _STEP_ID.match(v):
            raise ValueError(f"step id {v!r} must be snake_case")
        return v

    @field_validator("uses")
    @classmethod
    def _uses(cls, v: str) -> str:
        parse_cap(v)
        return v

    @field_validator("branch")
    @classmethod
    def _branch(cls, v: dict[str, str]) -> dict[str, str]:
        for pred in v:
            if not _PRED.match(pred):
                raise ValueError(f"branch {pred!r} must name a predicate, not an expression")
        return v

    @property
    def capability(self) -> str:
        return parse_cap(self.uses)[0]

    @model_validator(mode="after")
    def _approval_shape(self) -> Step:
        is_approval = self.capability == "Approval"
        if is_approval and (self.human != "required" or not self.covers):
            raise ValueError(f"step {self.id!r}: Approval needs human: required and covers")
        if not is_approval and (self.human is not None or self.covers is not None):
            raise ValueError(f"step {self.id!r}: only an Approval step takes human/covers")
        return self


class WorkflowTemplate(_Strict):
    workflow: str
    title: str = Field(min_length=1)
    steps: tuple[Step, ...] = Field(min_length=1)

    @field_validator("workflow")
    @classmethod
    def _ref(cls, v: str) -> str:
        parse_module_ref(v.replace("_", "-"))
        return v

    @model_validator(mode="after")
    def _graph(self) -> WorkflowTemplate:
        ids = [s.id for s in self.steps]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate step id")
        position = {sid: i for i, sid in enumerate(ids)}
        for i, s in enumerate(self.steps):
            for pred, target in s.branch.items():
                if target == "stop":
                    continue
                if target not in position:
                    raise ValueError(f"step {s.id!r}: branch {pred!r} targets unknown {target!r}")
                if position[target] <= i:
                    raise ValueError(f"step {s.id!r}: branch {pred!r} must jump forward")
        return self

    def step(self, step_id: str) -> Step:
        for s in self.steps:
            if s.id == step_id:
                return s
        raise KeyError(step_id)


# --------------------------------------------------------------------------------------- packs


def _check_bindings(v: dict[str, str]) -> dict[str, str]:
    for cap, mod in v.items():
        name, _ = parse_cap(cap)
        if name in KERNEL_CAPABILITIES:
            raise ValueError(f"{name} is a kernel capability and cannot be rebound")
        parse_module_ref(mod)
    return v


class ApprovalRule(_Strict):
    """How a human Approval step is satisfied. There is no way to express zero approvers."""

    mode: Literal["single", "quorum"] = "single"
    quorum: int = Field(default=1, ge=1, le=15)
    roles: tuple[str, ...] = ("buyer",)
    # Above this amount (in the profile's base currency) the requester's own vote does not count.
    distinct_from_requester_over: Decimal | None = Field(default=None, ge=0)
    amount_key: str | None = None  # data key holding the amount the threshold compares against

    @model_validator(mode="after")
    def _shape(self) -> ApprovalRule:
        if self.mode == "single" and self.quorum != 1:
            raise ValueError("mode single takes quorum 1; use mode quorum for more approvers")
        if self.mode == "quorum" and self.quorum < 2:
            raise ValueError("mode quorum needs at least 2 approvers")
        if self.distinct_from_requester_over is not None and not self.amount_key:
            raise ValueError("distinct_from_requester_over needs amount_key")
        return self


class PackManifest(_Strict):
    id: str
    version: str
    title: str = Field(min_length=1)
    workflow: str
    jurisdictions: tuple[str, ...] = Field(min_length=1)  # profile ids this pack is written for
    bindings: dict[str, str] = Field(default_factory=dict)  # Capability@N -> module-id@N
    approvals: dict[str, ApprovalRule] = Field(default_factory=dict)  # step id -> rule
    settings: dict[str, Any] = Field(default_factory=dict)  # pack defaults, tenant may override
    synthetic: bool = True  # seed and demo data are illustrative, never real (CLAUDE.md)

    @field_validator("id")
    @classmethod
    def _slug(cls, v: str) -> str:
        if not _SLUG.match(v):
            raise ValueError("pack id must be a lowercase slug")
        return v

    @field_validator("version")
    @classmethod
    def _semver(cls, v: str) -> str:
        if not _SEMVER.match(v):
            raise ValueError("pack version must be MAJOR.MINOR.PATCH")
        return v

    @field_validator("bindings")
    @classmethod
    def _bindings(cls, v: dict[str, str]) -> dict[str, str]:
        return _check_bindings(v)


# --------------------------------------------------------------------------------- deployments


class Deployment(_Strict):
    id: str
    workflow: str
    pack: str  # pack-id@major
    profile: str
    tenant: str = Field(min_length=1)
    bindings: dict[str, str] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)  # overrides of existing pack settings
    approvals: dict[str, ApprovalRule] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _slug(cls, v: str) -> str:
        if not _SLUG.match(v):
            raise ValueError("deployment id must be a lowercase slug")
        return v

    @field_validator("pack")
    @classmethod
    def _pack(cls, v: str) -> str:
        parse_module_ref(v)
        return v

    @field_validator("bindings")
    @classmethod
    def _bindings(cls, v: dict[str, str]) -> dict[str, str]:
        return _check_bindings(v)


# ------------------------------------------------------------------------------------- loading


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CompositionError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CompositionError(f"{path}: top level must be a mapping")
    return data


def load_model(cls: type[M], path: Path) -> M:
    try:
        return cls.model_validate(read_yaml(path))
    except ValueError as exc:
        if isinstance(exc, CompositionError):
            raise
        raise CompositionError(f"{path}: {exc}") from exc
