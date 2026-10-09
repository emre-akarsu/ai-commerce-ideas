"""Composition root: one deployment file -> one immutable, hashed ``ResolvedComposition``.

A deployment picks a workflow template, an industry pack and a jurisdiction profile (layers 3-5 of
composability.md). Resolution order for settings: pack defaults, then tenant overrides (only keys
the pack declares). Bindings: pack defaults, then deployment overrides. The linter runs here, so
nothing unresolved or unsafe can be handed to the runner. Every run event records
``composition.short()`` next to the profile digest.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from aiplat.profile import ProfileError, ResolvedProfile, load_profile

from .lint import Finding, lint
from .models import (
    KERNEL_CAPABILITIES,
    ApprovalRule,
    CompositionError,
    Deployment,
    ModuleManifest,
    PackManifest,
    WorkflowTemplate,
    load_model,
    parse_module_ref,
)

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Roots:
    workflows: Path = ROOT / "workflows"
    packs: Path = ROOT / "packs"
    modules: tuple[Path, ...] = field(
        default_factory=lambda: tuple(sorted((ROOT / "employees").glob("*/modules")))
    )
    profiles: Path | None = None  # None = aiplat.profile default


class ModuleRegistry:
    """Module manifests discovered from ``*.yaml`` files in the module directories."""

    def __init__(self, manifests: list[ModuleManifest]) -> None:
        self._by_ref: dict[str, ModuleManifest] = {}
        for m in manifests:
            if m.ref in self._by_ref:
                raise CompositionError(f"module {m.ref} declared twice")
            self._by_ref[m.ref] = m

    @classmethod
    def discover(cls, dirs: tuple[Path, ...]) -> ModuleRegistry:
        found = [load_model(ModuleManifest, p) for d in dirs for p in sorted(d.glob("*.yaml"))]
        return cls(found)

    def get(self, ref: str) -> ModuleManifest:
        parse_module_ref(ref)
        try:
            return self._by_ref[ref]
        except KeyError:
            raise CompositionError(f"unknown module {ref}") from None

    def refs(self) -> list[str]:
        return sorted(self._by_ref)


def load_entry(entry: str) -> Callable[..., Any]:
    module_name, _, attr = entry.partition(":")
    fn = getattr(importlib.import_module(module_name), attr, None)
    if not callable(fn):
        raise CompositionError(f"entry {entry} is not callable")
    return fn  # type: ignore[no-any-return]


@dataclass(frozen=True)
class ResolvedComposition:
    deployment: Deployment
    template: WorkflowTemplate
    pack: PackManifest
    profile: ResolvedProfile
    bound: Mapping[str, ModuleManifest]  # step id -> module (kernel steps absent)
    approvals: Mapping[str, ApprovalRule]  # Approval step id -> rule
    settings: Mapping[str, Any]
    provenance: Mapping[str, str]  # "settings.<key>" / "binding.<Cap@N>" -> layer
    digest: str

    def short(self) -> str:
        return f"{self.deployment.id}@{self.digest[:12]}"


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def resolve(deployment: Deployment, roots: Roots | None = None) -> ResolvedComposition:
    roots = roots or Roots()
    template = load_model(WorkflowTemplate, _template_path(roots.workflows, deployment.workflow))
    pack_id, pack_major = parse_module_ref(deployment.pack)
    pack = load_model(PackManifest, roots.packs / pack_id / "pack.yaml")
    if int(pack.version.split(".")[0]) != pack_major:
        raise CompositionError(
            f"pack {pack.id} is version {pack.version}, deployment wants @{pack_major}"
        )
    if pack.workflow != deployment.workflow:
        raise CompositionError(
            f"pack {pack.id} is written for {pack.workflow}, not {deployment.workflow}"
        )
    if deployment.profile not in pack.jurisdictions:
        raise CompositionError(f"pack {pack.id} does not support profile {deployment.profile!r}")
    try:
        profile = load_profile(deployment.profile, root=roots.profiles)
    except ProfileError as exc:
        raise CompositionError(str(exc)) from exc

    registry = ModuleRegistry.discover(roots.modules)
    provenance: dict[str, str] = {}
    bindings: dict[str, str] = {}
    for layer, source in (("pack", pack.bindings), ("deployment", deployment.bindings)):
        for cap, mod in source.items():
            bindings[cap] = mod
            provenance[f"binding.{cap}"] = layer
    bound: dict[str, ModuleManifest] = {}
    for s in template.steps:
        if s.capability in KERNEL_CAPABILITIES:
            continue
        ref = bindings.get(s.uses)
        if ref is not None:
            bound[s.id] = registry.get(ref)

    settings = dict(pack.settings)
    for key in pack.settings:
        provenance[f"settings.{key}"] = "pack"
    for key, value in deployment.settings.items():
        settings[key] = value
        provenance[f"settings.{key}"] = f"tenant:{deployment.tenant}"

    approvals: dict[str, ApprovalRule] = {}
    for s in template.steps:
        if s.capability != "Approval":
            continue
        if s.id in deployment.approvals:
            rule, layer = deployment.approvals[s.id], "deployment"
        elif s.id in pack.approvals:
            rule, layer = pack.approvals[s.id], "pack"
        else:
            rule, layer = ApprovalRule(), "platform"
        approvals[s.id] = rule
        provenance[f"approval.{s.id}"] = layer
    for sid in (*pack.approvals, *deployment.approvals):
        if sid not in approvals:
            raise CompositionError(f"approval rule for {sid!r}, which is not an Approval step")

    findings: list[Finding] = lint(template, bound, pack.settings, deployment.settings)
    if findings:
        raise CompositionError("composition refused:\n" + "\n".join(f"  {f}" for f in findings))

    body = {
        "deployment": deployment.model_dump(mode="json"),
        "template": template.model_dump(mode="json"),
        "pack": pack.model_dump(mode="json"),
        "profile": profile.digest,
        "bound": {k: v.model_dump(mode="json") for k, v in sorted(bound.items())},
        "approvals": {k: v.model_dump(mode="json") for k, v in sorted(approvals.items())},
        "settings": settings,
    }
    digest = hashlib.sha256(_canonical(body).encode()).hexdigest()
    return ResolvedComposition(
        deployment=deployment, template=template, pack=pack, profile=profile,
        bound=MappingProxyType(bound), approvals=MappingProxyType(approvals),
        settings=MappingProxyType(settings), provenance=MappingProxyType(provenance),
        digest=digest,
    )


def _template_path(root: Path, ref: str) -> Path:
    name, _, major = ref.partition("@")
    return root / f"{name}.v{major}.yaml"


def load_deployment(path: str | Path, roots: Roots | None = None) -> ResolvedComposition:
    return resolve(load_model(Deployment, Path(path)), roots)
