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
