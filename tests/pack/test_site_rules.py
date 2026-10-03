"""Second review, finding F4: ``site`` is validated by the same rule as every other one-line field.

The ship-to ``site`` goes into the RFQ body. Its two checks (the API's field validator and the pack's regex)
refused controls and line breaks but not the 21 hidden and bidirectional code points the message layer refuses
(U+061C, U+200B-U+200F, U+202A-U+202E, U+2060-U+2064, U+2066-U+2069, U+FEFF). A site holding one of them was
accepted at both layers, then failed late in ``prepare_rfqs`` with a 409; by then an RFQ row had been added with
no event, and the request was stuck (there is no edit endpoint).

There is now ONE public predicate, ``message.is_plain_line``: the message layer's single-line rule. The API (422)
and the pack (``Conflict``) both use it, so they agree with ``_line`` for every code point.

Newline, carriage return and tab are the only difference between a site and a body. A body may keep them (a
body is multi-line text and tabs are fine in it); a site is ONE line and refuses them.
"""

from __future__ import annotations

import employees.purchasing.service as pack
import pytest
from apps.api.main import CreateRequestIn
from employees.purchasing.service_port import Conflict
from pydantic import ValidationError

from components.send_service import message
from components.send_service.errors import MalformedMessage
from components.send_service.message import _clean_body, _line
from tests.pack.conftest import REQUEST_TEXT, T1, build_world

HIDDEN = [0x061C, *range(0x200B, 0x2010), *range(0x202A, 0x202F), *range(0x2060, 0x2065),
          *range(0x2066, 0x206A), 0xFEFF]
HIDDEN_PARAMS = [pytest.param(chr(cp), id=f"U+{cp:04X}") for cp in HIDDEN]
# Lone surrogates cannot be encoded as UTF-8, so they can never arrive in a JSON body.
BMP = [cp for cp in range(0x10000) if not 0xD800 <= cp <= 0xDFFF]
ABOVE_THE_BMP = [0x10000, 0x1D173, 0x1D17A, 0x1F6A2, 0x1F1E6, 0xE0001, 0xE0020, 0xE007F, 0xF0000, 0x10FFFF]
ONLY_A_BODY_MAY_HAVE = {0x09, 0x0A, 0x0D}  # tab, newline, carriage return


def site_around(cp: int) -> str:
    return f"Plant {chr(cp)} 4"  # in the middle, so that strip() cannot remove it


def accepted_by_line(text: str) -> bool:
    try:
        _line(text, "site", 200)
    except MalformedMessage:
        return False
    return True


def accepted_by_body(text: str) -> bool:
    try:
        _clean_body(f"Ship to: {text}")
    except MalformedMessage:
        return False
    return True


def accepted_by_api(text: str) -> bool:
    try:
        CreateRequestIn.model_validate({"text": "6204 bearing", "site": text})
    except ValidationError:
        return False
    return True


def accepted_by_pack(text: str) -> bool:
    try:
        pack.check_site(text)
    except Conflict:
        return False
    return True


# ---------------------------------------------------------------- the rule is one rule


def test_the_hidden_set_is_the_21_code_points_the_review_names() -> None:
    assert len(HIDDEN) == 21 and len(set(HIDDEN)) == 21


def test_every_code_point_is_decided_the_same_way_by_every_layer() -> None:
    disagreements: list[str] = []
    for cp in [*BMP, *ABOVE_THE_BMP]:
        text = site_around(cp)
        verdicts = {
            "is_plain_line": message.is_plain_line(text), "line": accepted_by_line(text),
            "api": accepted_by_api(text), "pack": accepted_by_pack(text),
        }
        if len(set(verdicts.values())) != 1:
            disagreements.append(f"U+{cp:04X} {verdicts}")
    assert disagreements == []


def test_a_site_is_accepted_exactly_when_a_body_would_accept_it_except_newline_cr_and_tab() -> None:
    """The bug: a site that passed both checks but failed in the body. The only allowed difference is the
    three characters a body may keep and a one-line site may not."""
    differ: dict[int, tuple[bool, bool]] = {}
    for cp in [*BMP, *ABOVE_THE_BMP]:
        text = site_around(cp)
        if accepted_by_pack(text) != accepted_by_body(text):
            differ[cp] = (accepted_by_pack(text), accepted_by_body(text))
    assert set(differ) == ONLY_A_BODY_MAY_HAVE
    assert all(site_ok is False and body_ok is True for site_ok, body_ok in differ.values())


def test_newline_and_tab_are_rejected_by_a_site_but_allowed_in_a_body() -> None:
    for cp in (0x0A, 0x09):
        assert not accepted_by_pack(site_around(cp)) and not accepted_by_api(site_around(cp))
        assert accepted_by_body(site_around(cp))
    assert accepted_by_body("Ship to: Plant 4\nPhone: 1")  # a body is multi-line text


@pytest.mark.parametrize("ch", HIDDEN_PARAMS)
def test_each_hidden_code_point_is_refused_by_every_layer(ch: str) -> None:
    text = f"Plant{ch}4"
    assert not message.is_plain_line(text)
    assert not accepted_by_line(text) and not accepted_by_body(text)
    assert not accepted_by_api(text) and not accepted_by_pack(text)


def test_the_predicate_is_the_one_line_rule() -> None:
    assert message.is_plain_line("Plant 4, Bay 2") and message.is_plain_line("")
    assert not message.is_plain_line("a\nb") and not message.is_plain_line(f"a{chr(0x2028)}b")
    assert not message.is_plain_line(None) and not message.is_plain_line(5) and not message.is_plain_line(b"x")  # type: ignore[arg-type]


# ---------------------------------------------------------------- legitimate sites still pass


LEGITIMATE = [
    pytest.param("Plant 4, Bay 2", id="comma"),
    pytest.param("Z" + chr(0xFC) + "rich Werk 3", id="accents"),
    pytest.param("O'Brien's yard", id="apostrophes"),
    pytest.param(chr(0x2018) + "North" + chr(0x2019) + " dock " + chr(0x2013) + " 7", id="smart-quotes"),
    pytest.param(chr(0x65E5) + chr(0x672C) + chr(0x5DE5) + chr(0x5834) + " 3", id="cjk"),
    pytest.param("Dock 7 " + chr(0x1F6A2), id="emoji"),
    pytest.param("Dock " + chr(0x2022) + " 7", id="bullet"),
    pytest.param("Plant" + chr(0xA0) + "4", id="no-break-space"),
    pytest.param("Site (north) / dock 7 [B]", id="brackets"),
]


@pytest.mark.parametrize("site", LEGITIMATE)
def test_a_legitimate_site_passes_both_layers(site: str) -> None:
    assert accepted_by_api(site) and accepted_by_pack(site)


@pytest.mark.parametrize("site", LEGITIMATE)
def test_a_legitimate_site_reaches_the_rfq_body_unchanged(site: str) -> None:
    w = build_world()
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT, site=site).request.id
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    assert f"Ship to: {site}" in p.body_preview


def test_no_site_is_still_fine() -> None:
    assert accepted_by_api("") and accepted_by_pack("")  # empty is a line (the field is optional)
    w = build_world()
    assert w.svc.create_request(w.requester, text=REQUEST_TEXT, site=None).request.id


# ---------------------------------------------------------------- refused up front, with nothing stored


@pytest.mark.parametrize("ch", HIDDEN_PARAMS)
def test_a_hidden_character_site_is_refused_up_front_and_nothing_is_stored(ch: str) -> None:
    w = build_world()
    events_before = len(w.log.events(T1))
    with pytest.raises(Conflict, match="site"):
        w.svc.create_request(w.requester, text=REQUEST_TEXT, site=f"Plant{ch}4")
    assert w.svc.list_requests(w.requester) == []
    assert len(w.log.events(T1)) == events_before  # no request, no event
    assert w.store.for_tenant(T1).rfqs.list() == []


def test_the_refusal_names_the_field_and_never_echoes_the_value() -> None:
    w = build_world()
    with pytest.raises(Conflict) as exc:
        w.svc.create_request(w.requester, text=REQUEST_TEXT, site=f"SECRET-PLANT{chr(0x200B)}4")
    assert "site" in str(exc.value) and "SECRET-PLANT" not in str(exc.value)


def test_a_non_text_site_is_refused_too() -> None:
    w = build_world()
    for bad in (5, b"Plant 4", ["Plant 4"]):
        with pytest.raises(Conflict, match="site"):
            w.svc.create_request(w.requester, text=REQUEST_TEXT, site=bad)  # type: ignore[arg-type]
