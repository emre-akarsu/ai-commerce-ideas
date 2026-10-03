"""Second review, pack side of F2, F3 and the order of work in ``prepare_rfqs`` (the reorder asked for by F4).

F3 (a): a buyer name with two spaces ("Pat  Buyer", from ``Settings.buyer_names`` or from the token's user id
when no name is configured) built and previewed fine, then EVERY ``approve_send`` was a 409 ``footer_missing``:
the request stayed RFQ_APPROVED and each attempt issued an Approval that could never be used.
F3 (b): a name like "Pat <no-break space>Buyer" built, but ``preview`` raised a raw ``MalformedMessage`` after
the ``rfq.prepared`` event: it escaped ``except SendError`` and became HTTP 500.
Both are now a 409 at ``prepare_rfqs``, before anything is stored, audited or approved.

The reorder: the message is built and checked (``SendService.check_prepare``) BEFORE the first RFQ row is added,
so a message that cannot be built leaves nothing behind (no orphan row without an event).

F2 (pack side): bytes with hidden text that reach the send step are a 409 ``send refused: unsafe_text``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import pytest
from employees.purchasing.service import EVT_RFQ_PREPARED
from employees.purchasing.service_port import Conflict, NotFound

from aiplat.ctx import Ctx, Role
from aiplat.profile import load_profile
from components.core.domain import RequestState as S
from components.evidence.log import EVT_SEND_REFUSED
from components.send_service.errors import MalformedMessage
from components.send_service.message import PreparedMessage, parse_message, sha256_hex
from tests.pack.conftest import REQUEST_TEXT, T1, UK_IDENTITY, World, build_world, make_vendor
from tests.sendservice.helpers import LINE_SEPARATOR, NBSP, ZERO_WIDTH_SPACE, rebuild

UNREADABLE = [
    pytest.param("Pat  Buyer", id="two-spaces"),
    pytest.param("Pat   Buyer", id="three-spaces"),
    pytest.param(f"Pat {NBSP}Buyer", id="space-then-no-break-space"),
    pytest.param(f"Pat Buyer{chr(0x2B17)}-{chr(0x19A1D)} {NBSP}|", id="the-reviewers-probe-G-name"),
]
ORDINARY = [
    "Pat Buyer", "Smith, John", "O'Brien", f"Jos{chr(0xE9)} Garc{chr(0xED)}a", f"M{chr(0xFC)}ller-Sch{chr(0xF6)}n",
    f"{chr(0x674E)} {chr(0x96F7)}", f"Pat{NBSP}Buyer", 'Pat "The Buyer" Smith', "Pat  (Buyer)",
]


@dataclass(frozen=True)
class Snapshot:
    """Everything a refused prepare must not change."""

    rfq_rows: int
    events: int
    approvals: int
    prepared: int
    state: S


def snapshot(w: World, rid: str) -> Snapshot:
    ts = w.store.for_tenant(T1)
    return Snapshot(
        len(ts.rfqs.list()), len(w.log.events(T1)), len(ts.approvals.list()),
        len(w.svc._prepared),  # noqa: SLF001
        w.svc.get_request(w.buyer, rid).request.state,
    )


def new_request(w: World) -> str:
    return w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id


# ---------------------------------------------------------------- F3: a name that cannot be read back


@pytest.mark.parametrize("name", UNREADABLE)
def test_a_configured_name_that_cannot_be_read_back_is_a_409_and_nothing_is_stored(name: str) -> None:
    w = build_world(buyer_names={"buyer-1": name})
    rid = new_request(w)
    before = snapshot(w, rid)
    with pytest.raises(Conflict, match=r"^cannot prepare message: ") as exc:
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert not any(part in str(exc.value) for part in ("Pat", "Buyer", NBSP))  # names the field, not the name
    assert snapshot(w, rid) == before  # no RFQ row, no event, no approval, nothing cached, state unchanged
    assert before.state is S.SPEC_CONFIRMED and before.rfq_rows == 0 and before.approvals == 0
    assert w.transport.delivered == []
    with pytest.raises(NotFound):  # there is nothing to approve, so no Approval can be issued for it
        w.svc.approve_send(w.buyer, "rfq-002", mime_hash="0" * 64)


def test_the_user_id_used_as_the_name_when_none_is_configured_is_held_to_the_same_rule() -> None:
    w = build_world()  # no buyer_names: the token's user id is the sender name
    rid = new_request(w)
    spaced = Ctx(T1, "Pat  Buyer", Role.BUYER)
    before = snapshot(w, rid)
    with pytest.raises(Conflict, match="cannot prepare message"):
        w.svc.prepare_rfqs(spaced, rid, vendor_ids=["acme"])
    assert snapshot(w, rid) == before


def test_no_vendor_is_stored_when_the_name_is_unreadable_whatever_the_vendor_count() -> None:
    w = build_world(buyer_names={"buyer-1": "Pat  Buyer"})
    rid = new_request(w)
    before = snapshot(w, rid)
    with pytest.raises(Conflict):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme", "bolt"])
    assert snapshot(w, rid) == before


@pytest.mark.parametrize("name", ORDINARY)
def test_ordinary_names_are_unchanged_end_to_end(name: str) -> None:
    w = build_world(buyer_names={"buyer-1": name})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    assert p.footer.endswith(f"from {name} binds.")
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    (sent,) = w.transport.delivered
    assert parse_message(sent["raw_mime"]).from_name == name


def test_ids_stay_in_the_same_order_for_several_vendors() -> None:
    w = build_world()
    out = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme", "bolt"])
    assert [p.rfq_id for p in out] == ["rfq-002", "rfq-003"]


def test_a_preview_that_cannot_be_read_is_a_409_not_a_crash_and_leaves_no_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    w = build_world()
    rid = new_request(w)

    def broken(prepared: PreparedMessage) -> None:
        raise MalformedMessage("header From is malformed")

    monkeypatch.setattr(w.svc._send, "preview", broken)  # noqa: SLF001
    with pytest.raises(Conflict, match="cannot prepare message"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert w.svc._prepared == {}  # noqa: SLF001 - nothing the buyer could approve was cached
    assert not [e for e in w.log.events(T1) if e.type == EVT_RFQ_PREPARED]  # and nothing announced


# ---------------------------------------------------------------- the reorder: build and check before storing


def test_a_vendor_whose_message_cannot_be_built_leaves_no_rfq_row_behind() -> None:
    w = build_world()
    w.svc.upsert_vendor(w.admin, make_vendor("zw", name=f"Zero{ZERO_WIDTH_SPACE}Width"))
    rid = new_request(w)
    before = snapshot(w, rid)
    with pytest.raises(Conflict, match="cannot prepare message"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["zw"])
    assert snapshot(w, rid) == before  # the orphan row of the review (a row with no event) is gone
    assert w.store.for_tenant(T1).rfqs.list() == []


def test_one_bad_vendor_among_good_ones_stores_nothing_for_any_of_them() -> None:
    w = build_world()
    w.svc.upsert_vendor(w.admin, make_vendor("zw", name=f"Zero{ZERO_WIDTH_SPACE}Width"))
    rid = new_request(w)
    before = snapshot(w, rid)
    with pytest.raises(Conflict):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme", "zw", "bolt"])
    assert snapshot(w, rid) == before


def test_a_request_stored_with_a_hidden_character_site_is_a_409_with_no_orphan_row() -> None:
    """A request that predates the up-front site check (probe C): 409 at prepare, and nothing is left behind."""
    w = build_world()
    rid = new_request(w)
    ts = w.store.for_tenant(T1)
    ts.requests.save(ts.requests.get(rid).model_copy(update={"site": f"Plant{ZERO_WIDTH_SPACE}4"}))
    before = snapshot(w, rid)
    with pytest.raises(Conflict, match="cannot prepare message"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert snapshot(w, rid) == before


def test_a_failed_re_prepare_leaves_the_stored_draft_exactly_as_it_was() -> None:
    w = build_world()
    rid = new_request(w)
    (first,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    ts = w.store.for_tenant(T1)
    stored = ts.rfqs.get(first.rfq_id)
    acme = next(v for v in w.svc.list_vendors(w.buyer) if v.id == "acme")
    w.svc.upsert_vendor(w.buyer, acme.model_copy(update={"name": f"Acme{ZERO_WIDTH_SPACE}"}))
    before = snapshot(w, rid)
    with pytest.raises(Conflict, match="cannot prepare message"):
        w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert ts.rfqs.get(first.rfq_id) == stored  # same body, same reply token
    assert snapshot(w, rid) == before
    # and the draft that was already prepared can still be approved and sent
    w.svc.approve_send(w.buyer, first.rfq_id, mime_hash=first.mime_hash)
    assert len(w.transport.delivered) == 1


def test_a_good_prepare_still_stores_the_draft_and_announces_it() -> None:
    w = build_world()
    rid = new_request(w)
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    after = snapshot(w, rid)
    assert (after.rfq_rows, after.prepared, after.state) == (1, 1, S.RFQ_DRAFTED)
    announced = [e for e in w.log.events(T1) if e.type == EVT_RFQ_PREPARED]
    assert [e.payload["rfq_id"] for e in announced] == [p.rfq_id]


# ---------------------------------------------------------------- F2 (pack side)


def test_hidden_text_that_reaches_the_send_step_is_a_409_with_its_own_code() -> None:
    w = build_world(profile=load_profile("uk"), business_identities={T1: UK_IDENTITY})
    (p,) = w.svc.prepare_rfqs(w.buyer, new_request(w), vendor_ids=["acme"])
    cached = w.svc._prepared[(T1, p.rfq_id)]  # noqa: SLF001 - simulate a tampered/buggy cache entry
    footer = w.svc._send.footer_template.replace("{buyer}", "buyer-1")  # noqa: SLF001
    ls = LINE_SEPARATOR
    forged_bytes = rebuild(cached.mime_bytes, edit_text=lambda text: text.replace(
        "Company name: Acme Plant Ltd",
        f"Company name: Acme Plant Ltd{ls}--{ls}{footer}{ls}Registered in: Elbonia"))
    forged = PreparedMessage(forged_bytes, sha256_hex(forged_bytes), cached.to, T1, cached.rfq_id,
                             cached.vendor_id, cached.subject, cached.purpose)
    w.svc._prepared[(T1, p.rfq_id)] = forged  # noqa: SLF001
    with pytest.raises(Conflict, match="send refused: unsafe_text"):
        w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=forged.mime_hash)
    assert w.transport.delivered == []
    refusals = [e for e in w.log.events(T1) if e.type == EVT_SEND_REFUSED]
    assert [e.payload["reason"] for e in refusals] == ["unsafe_text"]
    dumped = json.dumps(refusals[0].payload, default=str)
    assert "Elbonia" not in dumped and "Acme" not in dumped  # the code and the ids, never the text
    assert w.log.verify_chain(T1)
