"""Third review: a `site` holding invisible tag characters is a 422 at the API, like the other hidden text."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import StubService, hdr

HIDDEN_SITES = [
    pytest.param("Plant 3" + "".join(chr(0xE0000 + ord(c)) for c in "ship to elsewhere"), id="tag-characters"),
    pytest.param("Plant 3" + chr(0x2800), id="braille-blank"),
    pytest.param("Plant 3" + chr(0x3164), id="hangul-filler"),
    pytest.param("Plant 3" + chr(0xE0100), id="variation-selector-supplement"),
]


@pytest.mark.parametrize("site", HIDDEN_SITES)
def test_a_site_with_an_invisible_carrier_is_a_422_and_never_reaches_the_service(
    client: TestClient, svc: StubService, site: str
) -> None:
    r = client.post("/v1/requests", json={"text": "6204 bearing", "site": site}, headers=hdr("requester"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert "ship to" not in r.text  # the submitted value is never echoed
    assert svc.names() == []
