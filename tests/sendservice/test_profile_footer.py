"""R8 with a profile-supplied footer: still non-removable, hashed, and bound to the approval."""

from __future__ import annotations

import pytest

from aiplat.profile import load_profile
from components.send_service.errors import FooterMissing, HashMismatch
from components.send_service.service import FOOTER_TEMPLATE, SendService
from tests.security.factories import BUYER, T1
from tests.security.world import World

UK_FOOTER = load_profile("uk").profile.legal.disclosure_footer


def uk_send(world: World) -> SendService:
    return SendService(world.transport, world.clock, world.store, world.log,
                       kill_switch=world.kill, caps=world.caps, footer_text=UK_FOOTER)


def test_default_footer_is_the_constant_and_us_profile_matches_it(world: World) -> None:
    assert world.send.footer_template == FOOTER_TEMPLATE
    assert load_profile("us").profile.legal.disclosure_footer == FOOTER_TEMPLATE


def test_uk_footer_is_last_block_and_changes_the_hash(world: World) -> None:
    us = world.prepare()
    uk = uk_send(world).prepare(
        world.store.for_tenant(T1).rfqs.get("rfq-1"),
        world.store.for_tenant(T1).vendors.get("v-1"), BUYER,
        "+1 555 010 0100", "rfq@alias.example", "buyer@buyer.example")
    assert uk.mime_hash != us.mime_hash
    text = uk.mime_bytes.decode().replace("\r\n", "\n")
    assert text.rstrip().endswith(UK_FOOTER.replace("{buyer}", BUYER))
    assert "on behalf of" in text


def _both(world: World):  # type: ignore[no-untyped-def]
    ts = world.store.for_tenant(T1)
    uk_svc = uk_send(world)
    uk = uk_svc.prepare(ts.rfqs.get("rfq-1"), ts.vendors.get("v-1"), BUYER, "+1 555 010 0100",
                        "rfq@alias.example", "buyer@buyer.example")
    return world.prepare(buyer_name=BUYER), uk, uk_svc


def test_approval_for_us_footer_bytes_is_refused_for_uk_footer_bytes(world: World) -> None:
    us, uk, uk_svc = _both(world)
    approval_for_us = world.approve(us)
    with pytest.raises(HashMismatch):
        uk_svc.send(uk, approval_for_us)
    assert world.transport.delivered == []


def test_uk_service_refuses_us_footer_bytes_even_with_a_matching_approval(world: World) -> None:
    us, _uk, uk_svc = _both(world)
    with pytest.raises(FooterMissing):
        uk_svc.send(us, world.approve(us))
    assert world.transport.delivered == []


def test_uk_footer_message_sends_with_its_own_approval(world: World) -> None:
    _us, uk, uk_svc = _both(world)
    uk_svc.send(uk, world.approve(uk))
    assert len(world.transport.delivered) == 1


@pytest.mark.parametrize("bad", ["", "Hello {buyer}", "AI assistant cannot accept terms", 5])
def test_constructor_rejects_footers_missing_required_clauses(world: World, bad: object) -> None:
    with pytest.raises(ValueError):
        SendService(world.transport, world.clock, world.store, world.log,
                    footer_text=bad)  # type: ignore[arg-type]
