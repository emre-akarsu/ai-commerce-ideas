"""Composition linter (composability.md section 7). A finding blocks the deployment.

Implemented: C1 (send only behind a human Approval, only through the kernel SendService), C2 (no
tool-using step consumes vendor data), C3 (vendor data is read only by grounded modules), C6
(every capability bound, majors compatible, module requirements present) and C7 (pack and
deployment settings carry no reserved key; tenants override only keys the pack declares).
Not yet: C4 (Decimal money in ports), C5 (tenant-scoped repositories), C8 (licence records),
C9 (eval suites before production). The runner repeats C1 at run time, so a linter bug cannot
send mail.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .models import (
    KERNEL_CAPABILITIES,
    RESERVED_SETTING_KEYS,
    ModuleManifest,
    WorkflowTemplate,
    parse_cap,
)


@dataclass(frozen=True)
class Finding:
    rule: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.rule} {self.where}: {self.message}"


def lint(
    template: WorkflowTemplate,
    bound: Mapping[str, ModuleManifest],
    pack_settings: Mapping[str, Any],
    tenant_settings: Mapping[str, Any],
) -> list[Finding]:
    """``bound`` maps each non-kernel step id to the module bound to it."""
    return [
        *_c1_send_behind_approval(template, bound),
        *_c2_c3_untrusted_data(template, bound),
        *_c6_bindings(template, bound),
        *_c7_settings(pack_settings, tenant_settings),
    ]


def _c1_send_behind_approval(
    template: WorkflowTemplate, bound: Mapping[str, ModuleManifest]
) -> list[Finding]:
    out: list[Finding] = []
    steps = list(template.steps)
    for i, s in enumerate(steps):
        if s.capability != "SendService":
            continue
        prev = steps[i - 1] if i > 0 else None
        if prev is None or prev.capability != "Approval":
            out.append(Finding("C1", s.id, "SendService must directly follow a human Approval"))
        for other in steps:
            if s.id in other.branch.values():
                out.append(Finding("C1", other.id, f"a branch jumps to {s.id!r} past its approval"))
        if prev is not None and prev.capability == "Approval" and prev.covers != "outbound":
            out.append(Finding("C1", prev.id, "the approval before a send must cover 'outbound'"))
    for step_id, mod in bound.items():
        if mod.effects not in ("pure", "read", "write", "external_read"):
            out.append(Finding("C1", step_id, f"module {mod.id} declares a send effect"))
    return out


def _c2_c3_untrusted_data(
    template: WorkflowTemplate, bound: Mapping[str, ModuleManifest]
) -> list[Finding]:
    out: list[Finding] = []
    for s in template.steps:
        mod = bound.get(s.id)
        if mod is None or "vendor" not in mod.consumes:
            continue
        if mod.llm is not None and mod.llm.tools:
            out.append(Finding("C2", s.id, f"{mod.id} has tools and consumes vendor data"))
        if not mod.grounded:
            out.append(Finding("C3", s.id, f"{mod.id} reads vendor data without grounding"))
    return out


def _c6_bindings(template: WorkflowTemplate, bound: Mapping[str, ModuleManifest]) -> list[Finding]:
    out: list[Finding] = []
    provided = {s.capability for s in template.steps}
    for s in template.steps:
        if s.capability in KERNEL_CAPABILITIES:
            continue
        mod = bound.get(s.id)
        if mod is None:
            out.append(Finding("C6", s.id, f"no module bound for {s.uses}"))
            continue
        if s.uses not in mod.provides:
            out.append(Finding("C6", s.id, f"{mod.ref} does not provide {s.uses}"))
        for pred in s.branch:
            if pred not in mod.predicates:
                out.append(Finding("C6", s.id, f"{mod.id} exports no predicate {pred!r}"))
        for req in mod.requires:
            if parse_cap(req)[0] not in provided:
                out.append(Finding("C6", s.id, f"{mod.id} requires {req}, not in the workflow"))
    return out


def _reserved(settings: Mapping[str, Any], where: str) -> list[Finding]:
    out: list[Finding] = []
    for key, value in settings.items():
        if key.lower() in RESERVED_SETTING_KEYS:
            out.append(Finding("C7", where, f"reserved key {key!r} cannot be configured"))
        if isinstance(value, Mapping):
            out.extend(_reserved(value, f"{where}.{key}"))
    return out


def _c7_settings(
    pack_settings: Mapping[str, Any], tenant_settings: Mapping[str, Any]
) -> list[Finding]:
    out = _reserved(pack_settings, "pack.settings") + _reserved(tenant_settings, "tenant.settings")
    for key in tenant_settings:
        if key not in pack_settings:
            out.append(Finding("C7", "tenant.settings", f"{key!r} is not a pack setting"))
    return out
