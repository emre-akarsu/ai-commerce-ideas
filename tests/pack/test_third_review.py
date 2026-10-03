"""Third review, pack side: hidden text in a ship-to site, one ``prepare_rfqs`` at a time per request, and the
payload of the RFQ_DRAFTED transition.

* A ship-to ``site`` is one line of plain text that ends up in the body the vendor reads. Unicode tag characters
  spell ASCII invisibly; a requester could hide text from the approver this way. They are now refused up front.
* Two ``prepare_rfqs`` calls for one request (a double click) could each pass the "no RFQ row yet" check and each
  add a row for the same vendor. The second call now waits for the first and then finds its draft.
* A mutant dropping ``rfq_ids`` from the RFQ_DRAFTED transition survived the whole suite.
"""

from __future__ import annotations

import threading

import pytest
from employees.purchasing.service_port import Conflict

from tests.pack.conftest import REQUEST_TEXT, T1, build_world
from tests.sendservice.helpers import NBSP

SMUGGLED = "Plant 3" + "".join(chr(0xE0000 + ord(c)) for c in "ship to elsewhere")


def new_request(w) -> str:  # type: ignore[no-untyped-def]
    return w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id


@pytest.mark.parametrize("site", [SMUGGLED, "Plant 3" + chr(0x2800), "Plant 3" + chr(0xE0100), "Plant" + chr(0xD800)])
def test_a_site_with_invisible_carriers_is_refused_up_front_and_nothing_is_stored(site: str) -> None:
    w = build_world()
    before = len(w.log.events(T1))
    with pytest.raises(Conflict, match="site must be one line of plain text"):
        w.svc.create_request(w.requester, text=REQUEST_TEXT, site=site)
    assert len(w.log.events(T1)) == before  # nothing was written


@pytest.mark.parametrize("site", ["Plant 3, Bay 2", "Caf" + chr(0xE9) + " d'Or, Z" + chr(0xFC) + "rich", "Plant" + NBSP + "3"])
def test_ordinary_sites_still_pass(site: str) -> None:
    w = build_world()
    request = w.svc.create_request(w.requester, text=REQUEST_TEXT, site=site).request
    assert request.site == site


def test_the_rfq_drafted_transition_records_the_rfq_ids() -> None:
    w = build_world()
    rid = new_request(w)
    prepared = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme", "bolt"])
    ids = [p.rfq_id for p in prepared]
    assert len(ids) == 2
    drafted = [e for e in w.log.events(T1, rid) if e.payload.get("rfq_ids")]
    assert [e.payload["rfq_ids"] for e in drafted] == [ids]


def test_two_concurrent_prepares_for_one_request_make_one_row_per_vendor() -> None:
    w = build_world()
    rid = new_request(w)
    entered, release = threading.Event(), threading.Event()
    calls: list[str] = []
    real_check = w.svc._check_messages  # noqa: SLF001

    def slow_check(ctx, drafts, identity):  # type: ignore[no-untyped-def]
        calls.append(threading.current_thread().name)
        if len(calls) == 1:  # the first caller waits here, between its read and its write
            entered.set()
            assert release.wait(timeout=10)
        return real_check(ctx, drafts, identity)

    w.svc._check_messages = slow_check  # type: ignore[method-assign]  # noqa: SLF001
    outcome: dict[str, object] = {}

    def run(name: str) -> None:
        try:
            outcome[name] = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
        except Exception as exc:  # noqa: BLE001
            outcome[name] = exc

    first = threading.Thread(target=run, args=("first",), name="first")
    second = threading.Thread(target=run, args=("second",), name="second")
    first.start()
    assert entered.wait(timeout=10)
    second.start()
    second.join(timeout=0.3)  # with a per-request lock the second caller is still waiting here
    release.set()
    first.join(timeout=10)
    second.join(timeout=10)
    assert not first.is_alive() and not second.is_alive()
    rows = [r for r in w.store.for_tenant(T1).rfqs.list() if r.vendor_id == "acme"]
    assert len(rows) == 1  # one draft row for the vendor, however the two calls interleave
    assert not any(isinstance(v, Exception) and not isinstance(v, Conflict) for v in outcome.values())


def test_prepares_for_different_requests_do_not_wait_for_each_other() -> None:
    w = build_world()
    r1, r2 = new_request(w), new_request(w)
    entered, release = threading.Event(), threading.Event()
    real_check = w.svc._check_messages  # noqa: SLF001
    first_call = threading.Event()

    def slow_check(ctx, drafts, identity):  # type: ignore[no-untyped-def]
        if not first_call.is_set():
            first_call.set()
            entered.set()
            assert release.wait(timeout=10)
        return real_check(ctx, drafts, identity)

    w.svc._check_messages = slow_check  # type: ignore[method-assign]  # noqa: SLF001
    t = threading.Thread(target=lambda: w.svc.prepare_rfqs(w.buyer, r1, vendor_ids=["acme"]))
    t.start()
    assert entered.wait(timeout=10)
    done = threading.Event()

    def other() -> None:
        w.svc.prepare_rfqs(w.buyer, r2, vendor_ids=["acme"])
        done.set()

    u = threading.Thread(target=other)
    u.start()
    finished_while_first_waits = done.wait(timeout=5)
    release.set()
    t.join(timeout=10)
    u.join(timeout=10)
    assert finished_while_first_waits  # a different request is not serialised behind the first


def test_the_per_request_lock_table_does_not_grow() -> None:
    w = build_world()
    for _ in range(3):
        w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert w.svc._prepare_locks == {}  # noqa: SLF001 - an entry lives only while a prepare for its request runs
