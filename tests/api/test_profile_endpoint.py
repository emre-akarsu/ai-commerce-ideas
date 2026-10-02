"""GET /v1/profile: any authenticated role, NON-SENSITIVE subset only."""

from __future__ import annotations

import json

import pytest
from apps.api.main import create_app
from fastapi.testclient import TestClient

from aiplat.profile import load_profile
from tests.api.conftest import hdr

ALLOWED = {"id", "digest", "locale", "money", "tax", "lead_time", "legal", "parts", "tiers", "ui",
           "features"}


def test_requires_authentication(client: TestClient) -> None:
    assert client.get("/v1/profile").status_code == 401


@pytest.mark.parametrize("role", ["requester", "buyer", "admin"])
def test_any_authenticated_role_gets_the_subset(client: TestClient, role: str) -> None:
    r = client.get("/v1/profile", headers=hdr(role))
    assert r.status_code == 200
    assert set(r.json()) == ALLOWED


def test_default_is_us_and_matches_the_loaded_profile(client: TestClient) -> None:
    body = client.get("/v1/profile", headers=hdr("requester")).json()
    prof = load_profile("us")
    assert body["id"] == "us" and body["digest"] == prof.digest
    assert body["money"]["base_currency"] == "USD"


def test_uk_profile_values_and_no_sensitive_data(svc, auth) -> None:  # type: ignore[no-untyped-def]
    uk = load_profile("uk", tenant_overrides={"approvals": {"threshold": "777"},
                                              "retention": {"raw_email_days": 31}}, tenant_id="acme")
    c = TestClient(create_app(svc, auth, profile=uk))
    r = c.get("/v1/profile", headers=hdr("requester"))
    b = r.json()
    assert b["locale"] == {"region": "GB", "language": "en-GB", "timezone": "Europe/London",
                           "date_format": "%d/%m/%Y"}
    assert b["money"]["accepted_currencies"] == ["GBP", "EUR", "USD"]
    assert b["tax"]["name"] == "VAT" and b["tax"]["quote_basis_default"] == "ex_tax"
    assert b["lead_time"] == {"default_unit": "working_days"}
    assert b["legal"]["jurisdiction"] and b["legal"]["notices"]
    assert set(b["legal"]) == {"jurisdiction", "notices"}  # no footer text, no data regime
    assert b["tiers"]["enabled"] == ["A", "B"] and b["ui"]["language"] == "en-GB"
    text = json.dumps(b)
    for secret in ("retention", "raw_email", "777", "threshold", "caps", "billing", "tenant:",
                   "provenance", "layers", "disclosure_footer", "po_records", "audit_years"):
        assert secret not in text, secret
