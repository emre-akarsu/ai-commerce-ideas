"""Tenant-scoped company particulars in the send-service (review findings M3 and M2).

M3: the values of every tenant used to sit in one process-wide mapping, held by reference, and
``SendService.prepare`` rendered whatever pairs its caller handed over. With an identity provider
configured, ``prepare`` derives the lines from the RFQ's own tenant and refuses any other pairs.

M2: a send-service built by a deployment (for example the worker's ``send_service_factory``) must not
silently lose the profile's footer and required identity lines; ``SendService.from_profile`` derives
them from the profile.
"""

from __future__ import annotations

import hashlib
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from aiplat.profile import load_profile
from components.send_service.errors import (
    FooterMissing,
    IdentityMissing,
    KillSwitchEngaged,
    MalformedMessage,
    TenantMismatch,
)
from components.send_service.message import identity_pairs, parse_message
from components.send_service.service import (
    FollowUpSchedule,
    IdentityProvider,
    KillSwitch,
    SendService,
    TenantIdentities,
)
from tests.security.factories import BUYER, T1, T2
from tests.security.world import World, build_world

ROOT = Path(__file__).resolve().parents[2]
LABELS = ("Company name", "Company number", "Registered office", "Registered in")
IDENT_T1 = (
    ("Company name", "Acme Plant Ltd"),
    ("Company number", "01234567"),
    ("Registered office", "1 Example Street, London, EC1A 1AA"),
    ("Registered in", "England and Wales"),
)
IDENT_T2 = (
    ("Company name", "Beta Works Limited"),
    ("Company number", "SC765432"),
    ("Registered office", "2 Sample Road, Edinburgh, EH1 1AA"),
    ("Registered in", "Scotland"),
)
SECRET = "SECRET-VALUE-4711"
# sha256 of the plain RFQ bytes produced before the business-identity feature existed.
GOLDEN_PLAIN_RFQ = "5c47b21a66426871ce2ba2fe5cdd44f1893064253f5966c6f71285338c86b270"


def book() -> TenantIdentities:
    return TenantIdentities({T1: IDENT_T1, T2: IDENT_T2})


def world_with(provider: IdentityProvider | None, labels: tuple[str, ...] = LABELS) -> World:
    return build_world(required_identity_labels=labels, identity_provider=provider)


def prepare_t2(w: World, **kw: Any) -> Any:
    return w.prepare(tenant=T2, rfq_id="rfq-9", vendor_id="v-9", **kw)


def text(w: World, prepared: Any) -> str:
    return w.send.preview(prepared).text


# ---------------------------------------------------------------- TenantIdentities


def test_a_tenant_gets_only_its_own_lines() -> None:
    b = book()
    assert b.identity_for(T1) == IDENT_T1 and b.identity_for(T2) == IDENT_T2
    assert b.identity_for("t-nobody") == ()
    assert isinstance(b.identity_for(T1), tuple)


@pytest.mark.parametrize("probe", ["T-ACME", "t-acme ", " t-acme", "t-acm", "t-acme2", "", "t-", None, 5, b"t-acme"])
def test_lookup_is_exact_on_the_tenant_id(probe: Any) -> None:
    assert book().identity_for(probe) == ()


def test_mutating_what_was_passed_in_changes_nothing() -> None:
    inner1, inner2 = list(IDENT_T1), list(IDENT_T2)
    outer = {T1: inner1, T2: inner2}
    b = TenantIdentities(outer)
    inner1[0] = ("Company name", "EVIL LTD")  # inner, replace
    inner1.append(("Extra", "x"))  # inner, grow
    inner2.clear()  # inner, empty
    outer[T1] = [("Company name", "ALSO EVIL")]  # outer, replace
    del outer[T2]  # outer, delete
    outer["t-new"] = [("Company name", "NEW")]  # outer, add
    assert b.identity_for(T1) == IDENT_T1
    assert b.identity_for(T2) == IDENT_T2
    assert b.identity_for("t-new") == ()


def test_two_tenants_sharing_one_inner_list_cannot_leak_a_later_change() -> None:
    shared = [("Company name", "Shared Ltd")]
    b = TenantIdentities({T1: shared, T2: shared})
    shared[0] = ("Company name", "CHANGED AFTER")
    shared.append(("Company number", "99"))
    assert b.identity_for(T1) == b.identity_for(T2) == (("Company name", "Shared Ltd"),)


def test_the_provider_never_prints_or_lists_values() -> None:
    b = TenantIdentities({T1: [("Company name", SECRET)]})
    assert SECRET not in repr(b) and SECRET not in str(b) and SECRET not in f"{b!r:>80}"
    assert "1" in repr(b)  # counts only
    assert [n for n in dir(b) if not n.startswith("_")] == ["identity_for"]  # no way to enumerate
    with pytest.raises(TypeError):
        iter(b)  # type: ignore[call-overload]
    with pytest.raises(TypeError):
        b[T1]  # type: ignore[index]
    with pytest.raises(AttributeError):
        b.extra = 1  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "bad",
    [{"": [("a", "b")]}, {"  ": [("a", "b")]}, {5: [("a", "b")]}, {T1: [("a",)]}, {T1: [("a", "b", "c")]},
     {T1: [("a", 5)]}, {T1: [(5, "b")]}, {T1: [None]}, {T1: 7}],
)
def test_construction_refuses_malformed_input(bad: Any) -> None:
    with pytest.raises((ValueError, TypeError)):
        TenantIdentities(bad)


def test_an_empty_book_is_valid_and_gives_nothing() -> None:
    assert TenantIdentities({}).identity_for(T1) == ()


# ---------------------------------------------------------------- SendService with a provider


def test_prepare_renders_the_rfq_tenants_lines_without_the_caller_passing_any() -> None:
    w = world_with(book())
    p1, p2 = w.prepare(), prepare_t2(w)
    assert identity_pairs(w.send.preview(p1)) == list(IDENT_T1)
    assert identity_pairs(w.send.preview(p2)) == list(IDENT_T2)
    assert not any(value in text(w, p1) for _, value in IDENT_T2)
    assert not any(value in text(w, p2) for _, value in IDENT_T1)


def test_prepare_for_t1_never_renders_t2_lines_even_if_the_caller_passes_them() -> None:
    w = world_with(book())
    with pytest.raises(TenantMismatch) as exc:
        w.prepare(identity=IDENT_T2)
    assert not any(value in str(exc.value) for _, value in IDENT_T2)  # names no value
    with pytest.raises(TenantMismatch):
        prepare_t2(w, identity=IDENT_T1)
    assert w.transport.delivered == []


def test_a_mix_of_both_tenants_lines_is_refused_too() -> None:
    w = world_with(book())
    mixed = (IDENT_T1[0], *IDENT_T2[1:])
    with pytest.raises(TenantMismatch):
        w.prepare(identity=mixed)


def test_an_identity_equal_to_the_tenants_own_is_accepted_and_changes_nothing() -> None:
    w = world_with(book())
    plain = w.prepare()
    for given in (IDENT_T1, list(IDENT_T1), iter(IDENT_T1), [list(pair) for pair in IDENT_T1],
                  tuple((label, f"  {value}  ") for label, value in IDENT_T1)):
        assert w.prepare(identity=given).mime_bytes == plain.mime_bytes


@pytest.mark.parametrize(
    "given",
    [IDENT_T1[:3], IDENT_T1[::-1], (*IDENT_T1, ("VAT number", "GB000000000")),
     (("Company name", "Acme Plant Limited"), *IDENT_T1[1:])],
    ids=["subset", "reordered", "extra-line", "changed-value"],
)
def test_any_difference_from_the_tenants_own_lines_is_refused(given: Any) -> None:
    with pytest.raises(TenantMismatch):
        world_with(book()).prepare(identity=given)


def test_malformed_pairs_are_still_a_malformed_message() -> None:
    w = world_with(book())
    for bad in ("Company name: Acme", (("only-one",),), (("Company name", f"{SECRET}\nBcc: x@y.example"),)):
        with pytest.raises(MalformedMessage) as exc:
            w.prepare(identity=bad)
        assert SECRET not in str(exc.value)


def test_a_tenant_the_provider_does_not_know_is_missing_its_identity() -> None:
    w = world_with(TenantIdentities({T2: IDENT_T2}))
    with pytest.raises(IdentityMissing):
        w.prepare()  # T1 has no lines and the labels are required
    with pytest.raises(TenantMismatch):
        w.prepare(identity=IDENT_T2)  # and another tenant's lines do not stand in for them
    assert identity_pairs(w.send.preview(prepare_t2(w))) == list(IDENT_T2)


def test_nothing_required_and_nothing_known_is_the_plain_message() -> None:
    w = world_with(TenantIdentities({}), labels=())
    assert w.prepare().mime_hash == GOLDEN_PLAIN_RFQ


def test_a_provider_with_lines_but_no_requirement_adds_them_as_an_optional_block() -> None:
    w = world_with(book(), labels=())
    assert identity_pairs(w.send.preview(w.prepare())) == list(IDENT_T1)


def test_without_a_provider_the_identity_argument_works_as_before() -> None:
    w = world_with(None)
    assert w.send.identity_provider is None
    assert identity_pairs(w.send.preview(w.prepare(identity=IDENT_T2))) == list(IDENT_T2)


def test_any_object_with_identity_for_can_be_the_provider() -> None:
    class Fixed:
        def identity_for(self, tenant_id: str) -> list[tuple[str, str]]:
            return [("Company name", f"Ltd of {tenant_id}")]

    w = world_with(Fixed(), labels=("Company name",))
    assert identity_pairs(w.send.preview(w.prepare())) == [("Company name", "Ltd of t-acme")]
    for bad in (object(), 5, "identity_for"):
        with pytest.raises(ValueError, match="identity_provider"):
            world_with(bad)  # type: ignore[arg-type]


def test_a_provider_that_answers_with_text_is_a_malformed_message() -> None:
    class Wrong:
        def identity_for(self, tenant_id: str) -> str:
            return "Company name: Acme"

    with pytest.raises(MalformedMessage):
        world_with(Wrong()).prepare()  # type: ignore[arg-type]


def test_the_provider_is_exposed_read_only() -> None:
    b = book()
    w = world_with(b)
    assert w.send.identity_provider is b
    with pytest.raises(AttributeError):
        w.send.identity_provider = None  # type: ignore[misc]


def test_the_approved_bytes_are_what_was_prepared_and_sent() -> None:
    w = world_with(book())
    p = w.prepare()
    w.send.send(p, w.approve(p))
    (sent,) = w.transport.delivered
    assert sent["raw_mime"] == p.mime_bytes
    assert identity_pairs(parse_message(sent["raw_mime"])) == list(IDENT_T1)


def test_follow_ups_keep_carrying_the_original_lines() -> None:
    w = world_with(book())
    p = w.prepare(follow_up=FollowUpSchedule(1, timedelta(hours=24)))
    w.send.send(p, w.approve(p))
    w.clock.advance(hours=24)
    assert len(w.send.run_due_follow_ups(T1)) == 1
    assert identity_pairs(parse_message(w.transport.delivered[1]["raw_mime"])) == list(IDENT_T1)


# ---------------------------------------------------------------- SendService.from_profile


def derived(profile_id: str, **kw: Any) -> tuple[World, SendService]:
    w = build_world()
    send = SendService.from_profile(
        load_profile(profile_id), w.transport, w.clock, w.store, w.log, **kw)
    return w, send


@pytest.mark.parametrize("pid", ["uk", "uk-scotland", "uk-ni"])
def test_from_profile_requires_what_a_requiring_profile_requires(pid: str) -> None:
    _, send = derived(pid)
    prof = load_profile(pid).profile
    assert send.required_identity_labels == LABELS
    assert send.footer_template == prof.legal.disclosure_footer
    assert send._max_recipients == prof.comms.max_vendors  # noqa: SLF001


def test_from_profile_for_a_profile_that_does_not_require_it_requires_nothing() -> None:
    _, send = derived("us")
    assert send.required_identity_labels == ()
    assert send.footer_template == load_profile("us").profile.legal.disclosure_footer


def test_from_profile_can_only_add_required_labels() -> None:
    _, uk = derived("uk", required_identity_labels=("VAT number", "Company name"))
    assert uk.required_identity_labels == (*LABELS, "VAT number")  # the profile's, in order, then extras
    _, us = derived("us", required_identity_labels=["Company name"])
    assert us.required_identity_labels == ("Company name",)


@pytest.mark.parametrize("bad", [("Bad: label",), ("Phone",), ("x" * 41,), "Company name", (5,)])
def test_from_profile_rejects_invalid_extra_labels(bad: Any) -> None:
    with pytest.raises(ValueError, match="identity"):
        derived("uk", required_identity_labels=bad)


def test_from_profile_passes_the_other_collaborators_through() -> None:
    kill = KillSwitch()
    w, send = derived("us", max_recipients=2, kill_switch=kill, identity_provider=book())
    assert send._max_recipients == 2  # noqa: SLF001
    assert send.identity_provider is not None
    ts = w.store.for_tenant(T1)
    p = send.prepare(ts.rfqs.get("rfq-1"), ts.vendors.get("v-1"), BUYER, "+1 555 0100",
                     "buyer-acme@rfq.alias.example", "pat@acme-plant.example")
    kill.engage(T1)
    with pytest.raises(KillSwitchEngaged):
        send.send(p, w.approve(p))


def test_a_service_built_from_the_profile_enforces_the_profiles_footer_and_identity() -> None:
    w, send = derived("uk")
    ts = w.store.for_tenant(T1)
    args = (ts.rfqs.get("rfq-1"), ts.vendors.get("v-1"), BUYER, "+1 555 0100",
            "buyer-acme@rfq.alias.example", "pat@acme-plant.example")
    with pytest.raises(IdentityMissing):
        send.prepare(*args)
    p = send.prepare(*args, identity=IDENT_T1)
    footer = load_profile("uk").profile.legal.disclosure_footer.replace("{buyer}", BUYER)
    assert "on behalf of" in footer and send.preview(p).text.rstrip().endswith(footer)
    send.send(p, w.approve(p))
    assert len(w.transport.delivered) == 1
    # a message carrying the generic footer is not the profile's footer
    other = w.prepare(identity=IDENT_T1)
    with pytest.raises(FooterMissing):
        send.send(other, w.approve(other))


def test_from_profile_is_documented_for_deployments() -> None:
    readme = (ROOT / "apps/worker/README.md").read_text(encoding="utf-8")
    gaps = (ROOT / "docs/architecture/known-gaps.md").read_text(encoding="utf-8")
    for doc in (readme, gaps):
        assert "SendService.from_profile" in doc
    assert "send_service_factory" in readme and "required_identity_labels" in readme


def test_the_golden_plain_rfq_hash_is_still_what_it_was() -> None:
    assert hashlib.sha256(build_world().prepare().mime_bytes).hexdigest() == GOLDEN_PLAIN_RFQ
