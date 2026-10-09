"""The composition linter refuses unsafe or incomplete compositions (C1, C2, C3, C6, C7)."""

from __future__ import annotations

import pytest

from aiplat.compose import CompositionError, Deployment, resolve
from tests.compose.conftest import edit

REFURB = Deployment(id="t-refurb", workflow="quote_to_award@1", pack="refurb-trades@1",
                    profile="uk", tenant="t1")


def _refused(roots, dep=REFURB) -> str:
    with pytest.raises(CompositionError) as exc:
        resolve(dep, roots)
    return str(exc.value)


def test_sandbox_copy_resolves(sandbox) -> None:
    assert resolve(REFURB, sandbox).bound["parse"].id == "refurb-quote-parser"


def test_c1_send_without_approval_is_refused(sandbox) -> None:
    def drop_approval(t):
        t["steps"] = [s for s in t["steps"] if s["id"] != "approve_send"]
    edit(sandbox.workflows / "quote_to_award.v1.yaml", drop_approval)
    edit(sandbox.packs / "refurb-trades" / "pack.yaml", lambda p: p["approvals"].pop("approve_send"))
    assert "C1 send: SendService must directly follow a human Approval" in _refused(sandbox)


def test_c1_branch_jumping_to_send_is_refused(sandbox) -> None:
    def jump(t):
        t["steps"][2]["branch"] = {"nothing_to_send": "send"}
    edit(sandbox.workflows / "quote_to_award.v1.yaml", jump)
    assert "a branch jumps to 'send' past its approval" in _refused(sandbox)


def test_c1_approval_must_cover_outbound(sandbox) -> None:
    def cover_other(t):
        t["steps"][3]["covers"] = "rfq"
    edit(sandbox.workflows / "quote_to_award.v1.yaml", cover_other)
    assert "must cover 'outbound'" in _refused(sandbox)


def test_module_cannot_declare_send_effect(sandbox) -> None:
    edit(sandbox.modules[0] / "refurb-packets.yaml", lambda m: m.update(effects="send"))
    assert "effects" in _refused(sandbox)


def test_module_cannot_provide_a_kernel_capability(sandbox) -> None:
    edit(sandbox.modules[0] / "refurb-packets.yaml",
         lambda m: m.update(provides=["SendService@1"]))
    assert "kernel capability" in _refused(sandbox)


def test_c2_tool_using_module_cannot_read_vendor_data(sandbox) -> None:
    edit(sandbox.modules[0] / "refurb-quote-parser.yaml",
         lambda m: m.update(llm={"role": "extractor", "tools": ["web_search"]}))
    assert "C2 parse" in _refused(sandbox)


def test_c3_vendor_data_needs_grounding(sandbox) -> None:
    edit(sandbox.modules[0] / "refurb-quote-parser.yaml", lambda m: m.update(grounded=False))
    assert "C3 parse" in _refused(sandbox)


def test_c6_unbound_capability(sandbox) -> None:
    edit(sandbox.packs / "refurb-trades" / "pack.yaml",
         lambda p: p["bindings"].pop("QuoteComparator@1"))
    assert "C6 compare: no module bound for QuoteComparator@1" in _refused(sandbox)


def test_c6_wrong_capability_and_missing_predicate(sandbox) -> None:
    edit(sandbox.packs / "refurb-trades" / "pack.yaml",
         lambda p: p["bindings"].update({"QuoteComparator@1": "refurb-quote-parser@1"}))
    out = _refused(sandbox)
    assert "does not provide QuoteComparator@1" in out
    assert "exports no predicate 'no_rankable_quote'" in out


def test_c6_unknown_module_major(sandbox) -> None:
    edit(sandbox.packs / "refurb-trades" / "pack.yaml",
         lambda p: p["bindings"].update({"QuoteComparator@1": "refurb-compare@2"}))
    assert "unknown module refurb-compare@2" in _refused(sandbox)


@pytest.mark.parametrize("key", ["skip_approval", "auto_send", "allow_scraping", "commit_allowed"])
def test_c7_reserved_keys_in_pack_settings(sandbox, key) -> None:
    edit(sandbox.packs / "refurb-trades" / "pack.yaml", lambda p: p["settings"].update({key: True}))
    assert f"reserved key {key!r}" in _refused(sandbox)


def test_c7_nested_reserved_key(sandbox) -> None:
    edit(sandbox.packs / "refurb-trades" / "pack.yaml",
         lambda p: p["settings"].update({"comms": {"Auto_Approve": True}}))
    assert "reserved key 'Auto_Approve'" in _refused(sandbox)


def test_c7_tenant_cannot_add_settings(sandbox) -> None:
    dep = REFURB.model_copy(update={"settings": {"max_chasers": 9}})
    assert "'max_chasers' is not a pack setting" in _refused(sandbox, dep)


def test_kernel_steps_cannot_be_rebound() -> None:
    with pytest.raises(ValueError, match="kernel capability"):
        Deployment(id="x-y", workflow="quote_to_award@1", pack="refurb-trades@1", profile="uk",
                   tenant="t", bindings={"Approval@1": "refurb-intake@1"})
