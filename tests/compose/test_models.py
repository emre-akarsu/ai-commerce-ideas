"""Template, module and pack models reject malformed or weakening input."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aiplat.compose.models import ApprovalRule, ModuleManifest, Step, WorkflowTemplate

STEPS = [
    {"id": "a", "uses": "RequestIntake@1"},
    {"id": "approve", "uses": "Approval@1", "human": "required", "covers": "outbound"},
    {"id": "send", "uses": "SendService@1"},
]


def test_minimal_template() -> None:
    t = WorkflowTemplate(workflow="flow-x@1", title="t", steps=STEPS)
    assert [s.id for s in t.steps] == ["a", "approve", "send"]


@pytest.mark.parametrize("bad", [
    {"id": "a", "uses": "Approval@1"},                                    # approval without human
    {"id": "a", "uses": "Approval@1", "human": "required"},               # approval covers nothing
    {"id": "a", "uses": "RequestIntake@1", "human": "required"},          # human on a module step
    {"id": "a", "uses": "intake"},                                        # not a capability ref
    {"id": "a", "uses": "RequestIntake@1", "branch": {"x > 3": "stop"}},  # expression, not predicate
    {"id": "A b", "uses": "RequestIntake@1"},
])
def test_bad_steps(bad) -> None:
    with pytest.raises(ValidationError):
        Step(**bad)


def test_branches_only_jump_forward_to_known_steps() -> None:
    back = [dict(STEPS[0]), {"id": "b", "uses": "ScopePlanner@1", "branch": {"loop": "a"}}]
    with pytest.raises(ValidationError, match="jump forward"):
        WorkflowTemplate(workflow="flow-x@1", title="t", steps=back)
    unknown = [{"id": "b", "uses": "ScopePlanner@1", "branch": {"p": "nowhere"}}]
    with pytest.raises(ValidationError, match="unknown"):
        WorkflowTemplate(workflow="flow-x@1", title="t", steps=unknown)
    with pytest.raises(ValidationError, match="duplicate"):
        WorkflowTemplate(workflow="flow-x@1", title="t", steps=[STEPS[0], STEPS[0]])


def test_module_entry_must_be_first_party() -> None:
    base = {"id": "m-x", "version": "1.0.0", "provides": ["ScopePlanner@1"], "effects": "pure"}
    ModuleManifest(**base, entry="employees.refurb.steps:scope")
    for entry in ("os:system", "thirdparty.plugin:run", "employees.refurb.steps"):
        with pytest.raises(ValidationError):
            ModuleManifest(**base, entry=entry)


def test_approval_rule_cannot_express_zero_approvers() -> None:
    with pytest.raises(ValidationError):
        ApprovalRule(mode="quorum", quorum=0)
    with pytest.raises(ValidationError):
        ApprovalRule(mode="quorum", quorum=1)
    with pytest.raises(ValidationError):
        ApprovalRule(mode="single", quorum=3)
    with pytest.raises(ValidationError):
        ApprovalRule(distinct_from_requester_over="100")
    assert ApprovalRule(mode="quorum", quorum=3).quorum == 3
