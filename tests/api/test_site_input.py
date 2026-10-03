"""`site` is one line of plain text (finding L6). It goes into the RFQ body, so a line break in it could
add lines to the message, such as a forged "Phone:" line that a follow-up would later reuse."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import StubService, hdr

BAD_SITES = [
    pytest.param("Plant 4\nPhone: +44 7000 000000", id="newline"),
    pytest.param("Plant 4\r\nPhone: 1", id="crlf"),
    pytest.param("Plant 4" + chr(0x85) + "x", id="next-line"),
    pytest.param("Plant 4" + chr(0x2028) + "x", id="line-separator"),
    pytest.param("Plant 4" + chr(0x2029) + "x", id="paragraph-separator"),
    pytest.param("Plant 4\x00", id="nul"),
    pytest.param("Plant 4\x7f", id="del"),
    pytest.param("Plant 4" + chr(0x9F), id="c1"),
    pytest.param("Plant\t4", id="tab"),
]


@pytest.mark.parametrize("site", BAD_SITES)
def test_a_site_with_a_control_or_line_break_character_is_a_422_and_never_reaches_the_service(
    client: TestClient, svc: StubService, site: str
) -> None:
    r = client.post("/v1/requests", json={"text": "6204 bearing", "site": site}, headers=hdr("requester"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert "site" in r.json()["error"]["message"]
    assert "Phone" not in r.text and "7000" not in r.text  # the submitted value is never echoed
    assert svc.names() == []


@pytest.mark.parametrize("site", ["Plant 4, Bay 2", "Site (north) / dock 7", "", None])
def test_an_ordinary_or_missing_site_is_passed_through_unchanged(
    client: TestClient, svc: StubService, site: str | None
) -> None:
    body = {"text": "6204 bearing", **({} if site is None else {"site": site})}
    r = client.post("/v1/requests", json=body, headers=hdr("requester"))
    assert r.status_code == 200
    ((name, _, kwargs),) = svc.calls
    assert name == "create_request" and kwargs["site"] == site


def test_the_length_limit_still_applies(client: TestClient, svc: StubService) -> None:
    r = client.post("/v1/requests", json={"text": "x", "site": "s" * 201}, headers=hdr("requester"))
    assert r.status_code == 422 and svc.names() == []


# ---- second review, finding F4: the same rule as every other one-line field, hidden characters included

# U+061C, U+200B-U+200F, U+202A-U+202E, U+2060-U+2064, U+2066-U+2069, U+FEFF: 21 code points that passed
# this validator and then failed late, in the message layer, leaving the request stuck.
HIDDEN = [0x061C, *range(0x200B, 0x2010), *range(0x202A, 0x202F), *range(0x2060, 0x2065),
          *range(0x2066, 0x206A), 0xFEFF]


@pytest.mark.parametrize("cp", [pytest.param(cp, id=f"U+{cp:04X}") for cp in HIDDEN])
def test_a_site_with_a_hidden_or_bidirectional_character_is_a_422_and_never_reaches_the_service(
    client: TestClient, svc: StubService, cp: int
) -> None:
    site = "Plant" + chr(cp) + "4"
    r = client.post("/v1/requests", json={"text": "6204 bearing", "site": site}, headers=hdr("requester"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert "site" in r.json()["error"]["message"]
    assert "Plant" not in r.text  # the submitted value is never echoed
    assert svc.names() == []


def test_the_count_of_hidden_code_points_is_the_one_in_the_review() -> None:
    assert len(HIDDEN) == 21


LEGITIMATE = [
    pytest.param("Z" + chr(0xFC) + "rich Werk 3", id="accents"),
    pytest.param("O'Brien's yard", id="apostrophes"),
    pytest.param("Plant 4, Bay 2", id="comma"),
    pytest.param(chr(0x65E5) + chr(0x672C) + chr(0x5DE5) + chr(0x5834) + " 3", id="cjk"),
    pytest.param("Dock 7 " + chr(0x1F6A2), id="emoji"),
    pytest.param(chr(0x2018) + "North" + chr(0x2019) + " dock " + chr(0x2013) + " 7", id="smart-quotes"),
    pytest.param("Plant" + chr(0xA0) + "4", id="no-break-space"),
]


@pytest.mark.parametrize("site", LEGITIMATE)
def test_a_legitimate_site_is_still_passed_through_unchanged(
    client: TestClient, svc: StubService, site: str
) -> None:
    r = client.post("/v1/requests", json={"text": "6204 bearing", "site": site}, headers=hdr("requester"))
    assert r.status_code == 200, r.text
    ((name, _, kwargs),) = svc.calls
    assert name == "create_request" and kwargs["site"] == site
