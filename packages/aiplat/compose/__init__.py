"""Composable workflows (ADR-012): template + pack + profile = deployment.

    comp = load_deployment("deployments/refurb-leeds.yaml")    # resolved, linted, hashed
    graph = compile_workflow(comp, outbound=..., events=...)    # LangGraph, human steps interrupt
    python -m aiplat.compose validate deployments/*.yaml
"""

from .models import CompositionError, Deployment, ModuleManifest, PackManifest, WorkflowTemplate
from .resolve import ResolvedComposition, Roots, load_deployment, resolve
from .runner import ApprovalMissing, StepConfig, compile_workflow

__all__ = [
    "ApprovalMissing", "CompositionError", "Deployment", "ModuleManifest", "PackManifest",
    "ResolvedComposition", "Roots", "StepConfig", "WorkflowTemplate", "compile_workflow",
    "load_deployment", "resolve",
]
