"""Second review, finding F6b: ``SendService.from_profile`` takes its recipient limit from the profile.

Every shipped profile has ``comms.max_vendors = 4``, which is also the constructor's default, so a build that
ignored the profile's value passed every test (a mutant that did exactly that survived). A tenant override
(``comms.max_vendors`` is tenant-overridable, bounded 1..8) gives a profile whose limit is not 4.
"""

from __future__ import annotations

import pytest

from aiplat.profile import ResolvedProfile, load_profile
from components.send_service import SendService
from components.send_service.errors import RecipientLimitExceeded
from tests.security.factories import ALIAS, BUYER, BUYER_EMAIL, PHONE, T1, make_rfq, make_vendor
from tests.security.world import World, build_world


def profile_with_limit(limit: int, base: str = "us") -> ResolvedProfile:
    return load_profile(base, tenant_overrides={"comms": {"max_vendors": limit}}, tenant_id=T1)


def ids(i: int) -> tuple[str, str]:
    """(vendor id, RFQ id) of the i-th vendor; the first two come with the shared world."""
    return (f"v-{i}", f"rfq-{i}") if i <= 2 else (f"vx-{i}", f"rfqx-{i}")


def world_with_vendors(count: int) -> World:
    """Tenant 1 with ``count`` vendors, each with its own RFQ on the same request."""
    w = build_world()
    ts = w.store.for_tenant(T1)
    for i in range(3, count + 1):
        vendor_id, rfq_id = ids(i)
        ts.vendors.add(make_vendor(vendor_id, email=f"sales@vendor-{i}.example", domain=f"vendor-{i}.example"))
        ts.rfqs.add(make_rfq(rfq_id, vendor_id=vendor_id))
    return w


def send_one(w: World, send: SendService, i: int) -> str:
    ts = w.store.for_tenant(T1)
    vendor_id, rfq_id = ids(i)
    p = send.prepare(ts.rfqs.get(rfq_id), ts.vendors.get(vendor_id), BUYER, PHONE, ALIAS, BUYER_EMAIL)
    return send.send(p, w.approve(p))


@pytest.mark.parametrize("limit", [1, 2, 3, 4, 5, 8])
def test_from_profile_uses_the_profiles_vendor_limit_as_its_recipient_limit(limit: int) -> None:
    w = world_with_vendors(9)
    send = SendService.from_profile(profile_with_limit(limit), w.transport, w.clock, w.store, w.log)
    assert send.max_recipients == limit
    for i in range(1, limit + 1):  # exactly `limit` distinct vendors may be sent to ...
        send_one(w, send, i)
    with pytest.raises(RecipientLimitExceeded, match=f"at most {limit} vendors"):  # ... and not one more
        send_one(w, send, limit + 1)
    assert len(w.transport.delivered) == limit


def test_the_limit_is_the_profiles_not_the_constructors_default() -> None:
    w = world_with_vendors(5)
    stricter = SendService.from_profile(profile_with_limit(3), w.transport, w.clock, w.store, w.log)
    default = SendService(w.transport, w.clock, w.store, w.log)
    assert default.max_recipients == 4 and stricter.max_recipients == 3
    for i in (1, 2, 3):
        send_one(w, stricter, i)
    with pytest.raises(RecipientLimitExceeded):
        send_one(w, stricter, 4)  # the default (4) would have let this one through
    send_one(w, default, 4)


@pytest.mark.parametrize("profile_id", ["us", "uk", "uk-scotland", "uk-ni"])
def test_every_shipped_profile_maps_its_own_limit(profile_id: str) -> None:
    w = build_world()
    prof = load_profile(profile_id)
    assert SendService.from_profile(prof, w.transport, w.clock, w.store, w.log).max_recipients == (
        prof.profile.comms.max_vendors)


def test_an_explicit_limit_still_wins_over_the_profile() -> None:
    w = build_world()
    send = SendService.from_profile(profile_with_limit(3), w.transport, w.clock, w.store, w.log, max_recipients=2)
    assert send.max_recipients == 2


def test_the_limit_is_read_only() -> None:
    w = build_world()
    send = SendService(w.transport, w.clock, w.store, w.log)
    with pytest.raises(AttributeError):
        send.max_recipients = 99  # type: ignore[misc]
    assert send.max_recipients == 4
