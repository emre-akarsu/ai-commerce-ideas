# ruff: noqa: E501
"""``@tool``: the only way an AI employee's capability becomes callable by an agent.

Guarantees enforced here (not in prompts):
- The first parameter is the verified context (``ToolContext``); tenant, user and role can never be
  declared as tool parameters, and a call that passes them as keyword arguments is refused. The
  model supplies business arguments only.
- Every call appends an audit ``Event`` (hash-chained, via the evidence ``EventLog``): tool name,
  argument names plus a digest of the arguments (never the values), outcome.
- Every successful call is metered (``ctx.meter.record(name)``).
- ``requires_approval=True`` refuses to run unless the context's ``approval_check`` says a human
  approved this tool call. This is a gate, not the authority: sends additionally need an
  ``Approval`` bound to the message hash, verified by the send-service (R1).
"""

from __future__ import annotations

import functools
import hashlib
import inspect
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, ParamSpec, Protocol, TypeVar

from aiplat.ctx import Ctx, Role
from components.evidence.log import EventLog, canonical_json

P = ParamSpec("P")
R = TypeVar("R")

FORBIDDEN_PARAMS = frozenset(
    {"tenant", "tenant_id", "user", "user_id", "actor", "role", "ctx_tenant", "organisation_id"}
)
EVT_TOOL_CALL = "tool.call"
EVT_TOOL_REFUSED = "tool.refused"


class ToolError(Exception):
    """Base class for tool-gate refusals."""


class ApprovalRequired(ToolError):  # noqa: N818 - reads as the refusal
    """The tool needs a human approval that the context cannot show."""


class ForbiddenArgument(ToolError):  # noqa: N818
    """The caller tried to pass tenant/user identity as a tool argument."""


class Meter(Protocol):
    def record(self, name: str, qty: int = 1) -> None: ...


@dataclass
class CounterMeter:
    """Stub meter: counts calls per name. Billing derives from Events, not from this."""

    counts: Counter[str] = field(default_factory=Counter)

    def record(self, name: str, qty: int = 1) -> None:
        self.counts[name] += qty


@dataclass(frozen=True)
class ToolContext:
    """Ctx-like object handed to tools. Identity comes from the verified ``Ctx`` only."""

    ctx: Ctx
    event_log: EventLog
    meter: Meter
    request_id: str | None = None
    approval_check: Callable[[str], bool] | None = None  # (tool name) -> a human approved it
    services: Mapping[str, Any] = field(default_factory=dict)  # pack services, by name

    @property
    def tenant_id(self) -> str:
        return self.ctx.tenant_id

    @property
    def user_id(self) -> str:
        return self.ctx.user_id

    @property
    def role(self) -> Role:
        return self.ctx.role

    @property
    def actor(self) -> str:
        return self.ctx.actor


@dataclass(frozen=True)
class ToolSpec:
    name: str
    requires_approval: bool
    meter_name: str
    description: str


def _digest(args: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(args).encode()).hexdigest()


def _check_signature(fn: Callable[..., Any]) -> None:
    params = list(inspect.signature(fn).parameters.values())
    if not params or params[0].name != "ctx":
        raise TypeError(f"tool {fn.__name__}: first parameter must be 'ctx' (ToolContext)")
    bad = [p.name for p in params if p.name in FORBIDDEN_PARAMS]
    if bad:
        raise TypeError(f"tool {fn.__name__}: identity parameters are not allowed: {bad}")
    for p in params[1:]:
        if p.kind is inspect.Parameter.VAR_KEYWORD:
            raise TypeError(f"tool {fn.__name__}: **kwargs would let the model smuggle identity")


def tool(
    *, name: str | None = None, requires_approval: bool = False, meter: str | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def wrap(fn: Callable[P, R]) -> Callable[P, R]:
        _check_signature(fn)
        tool_name = name or fn.__name__
        spec = ToolSpec(tool_name, requires_approval, meter or tool_name, (fn.__doc__ or "").strip())

        @functools.wraps(fn)
        def run(*args: P.args, **kwargs: P.kwargs) -> R:
            ctx = args[0] if args else kwargs.get("ctx")
            if not isinstance(ctx, ToolContext):
                raise TypeError("a tool must be called with a ToolContext as first argument")
            business = dict(kwargs)
            business.pop("ctx", None)
            smuggled = sorted(set(business) & FORBIDDEN_PARAMS)
            if smuggled:
                _log(ctx, EVT_TOOL_REFUSED, tool_name, business, f"identity_argument:{smuggled}")
                raise ForbiddenArgument(f"identity cannot be supplied as an argument: {smuggled}")
            if requires_approval and not (
                ctx.approval_check is not None and ctx.approval_check(tool_name)
            ):
                _log(ctx, EVT_TOOL_REFUSED, tool_name, business, "approval_required")
                raise ApprovalRequired(f"tool {tool_name} needs a recorded human approval")
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                _log(ctx, EVT_TOOL_CALL, tool_name, business, f"error:{type(exc).__name__}")
                raise
            _log(ctx, EVT_TOOL_CALL, tool_name, business, "ok")
            ctx.meter.record(spec.meter_name)
            return result

        run.tool_spec = spec  # type: ignore[attr-defined]
        return run

    return wrap


def _log(ctx: ToolContext, etype: str, tool_name: str, args: dict[str, Any], outcome: str) -> None:
    ctx.event_log.append(
        ctx.tenant_id,
        ctx.request_id,
        "agent",
        etype,
        {
            "tool": tool_name,
            "on_behalf_of": ctx.actor,
            "arg_names": sorted(args),
            "args_sha256": _digest({k: repr(v) for k, v in args.items()}),
            "outcome": outcome,
        },
    )
