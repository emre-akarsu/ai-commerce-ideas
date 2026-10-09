"""Helpers to build throwaway compositions on disk for hostile and edge-case tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from aiplat.compose import Roots
from aiplat.compose.resolve import ROOT


class Recorder:
    """Stands in for the send-service port and the event log. Holds no credentials."""

    def __init__(self) -> None:
        self.sent: list[tuple[list[dict[str, Any]], dict[str, Any]]] = []
        self.events: list[tuple[str, str, dict[str, Any]]] = []

    def send(self, messages: Any, approval: Any) -> list[str]:
        self.sent.append(([dict(m) for m in messages], dict(approval)))
        return [f"msg-{len(self.sent)}-{i}" for i in range(len(messages))]

    def append(self, kind: str, step: str, detail: Any) -> None:
        self.events.append((kind, step, dict(detail)))


@pytest.fixture()
def recorder() -> Recorder:
    return Recorder()


@pytest.fixture()
def sandbox(tmp_path: Path):
    """Copy of the real workflows, packs and module manifests that a test may edit."""
    roots = Roots(
        workflows=tmp_path / "workflows", packs=tmp_path / "packs",
        modules=(tmp_path / "modules",),
    )
    roots.workflows.mkdir()
    roots.modules[0].mkdir()
    for p in (ROOT / "workflows").glob("*.yaml"):
        (roots.workflows / p.name).write_text(p.read_text())
    for p in (ROOT / "employees").glob("*/modules/*.yaml"):
        (roots.modules[0] / p.name).write_text(p.read_text())
    for p in (ROOT / "packs").glob("*/pack.yaml"):
        d = roots.packs / p.parent.name
        d.mkdir(parents=True)
        (d / "pack.yaml").write_text(p.read_text())
    return roots


def edit(path: Path, fn) -> None:
    data = yaml.safe_load(path.read_text())
    fn(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
