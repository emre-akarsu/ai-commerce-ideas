"""Conformance: every deployment in the repo resolves and lints clean; digests are stable."""

from __future__ import annotations

from pathlib import Path

import pytest

from aiplat.compose import CompositionError, Deployment, load_deployment, resolve
from aiplat.compose.__main__ import main
from aiplat.compose.resolve import ROOT

DEPLOYMENTS = sorted((ROOT / "deployments").glob("*.yaml"))


def test_there_are_deployments() -> None:
    assert len(DEPLOYMENTS) >= 2


@pytest.mark.parametrize("path", DEPLOYMENTS, ids=lambda p: p.stem)
def test_deployment_resolves(path: Path) -> None:
    comp = load_deployment(path)
    assert comp.pack.synthetic  # no real customer data in the repo
    assert comp.short().startswith(comp.deployment.id + "@")
    assert load_deployment(path).digest == comp.digest


def test_digest_changes_with_settings_and_provenance_names_the_tenant() -> None:
    dep = Deployment(id="d-one", workflow="quote_to_award@1", pack="refurb-trades@1",
                     profile="uk", tenant="t1")
    a = resolve(dep)
    b = resolve(dep.model_copy(update={"settings": {"max_suppliers_per_rfq": 2}}))
    assert a.digest != b.digest
    assert a.provenance["settings.max_suppliers_per_rfq"] == "pack"
    assert b.provenance["settings.max_suppliers_per_rfq"] == "tenant:t1"


@pytest.mark.parametrize("update,message", [
    ({"profile": "us"}, "does not support profile 'us'"),
    ({"pack": "refurb-trades@2"}, "deployment wants @2"),
    ({"workflow": "rfq_planning@1"}, "written for quote_to_award@1"),
    ({"approvals": {"intake": {"mode": "single"}}}, "not an Approval step"),
])
def test_mismatched_deployment_is_refused(update, message) -> None:
    base = {"id": "d-two", "workflow": "quote_to_award@1", "pack": "refurb-trades@1",
            "profile": "uk", "tenant": "t1"}
    with pytest.raises(CompositionError, match=message):
        resolve(Deployment.model_validate({**base, **update}))


def test_cli(capsys) -> None:
    assert main(["validate", *map(str, DEPLOYMENTS)]) == 0
    assert main(["show", str(DEPLOYMENTS[0])]) == 0
    assert "kernel" in capsys.readouterr().out
    assert main(["nope"]) == 2
