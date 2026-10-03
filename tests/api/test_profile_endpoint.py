"""GET /v1/profile: any authenticated role, NON-SENSITIVE subset only."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml
from apps.api.main import create_app
from fastapi.testclient import TestClient

from aiplat.profile import PROFILES_DIR, load_profile
from tests.api.conftest import hdr

ALLOWED = {"id", "digest", "locale", "money", "tax", "lead_time", "legal", "parts", "tiers", "ui",
           "features"}
LEGAL_ALLOWED = {"jurisdiction", "notices", "business_identity"}
IDENTITY_ALLOWED = {"required", "fields", "labels"}
UK_IDENTITY_POLICY = {
    "required": True,
    "fields": ["legal_name", "registration_number", "registered_office", "registered_in"],
    "labels": {"legal_name": "Company name", "registration_number": "Company number",
               "registered_office": "Registered office", "registered_in": "Registered in"},
}


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
    assert set(b["legal"]) == LEGAL_ALLOWED  # no footer text, no data regime
    assert b["legal"]["business_identity"] == UK_IDENTITY_POLICY
    assert b["tiers"]["enabled"] == ["A", "B"] and b["ui"]["language"] == "en-GB"
    text = json.dumps(b)
    for secret in ("retention", "raw_email", "777", "threshold", "caps", "billing", "tenant:",
                   "provenance", "layers", "disclosure_footer", "po_records", "audit_years"):
        assert secret not in text, secret


# ---------------------------------------------------------------- legal.business_identity


def test_us_exposes_a_not_required_empty_policy(client: TestClient) -> None:
    body = client.get("/v1/profile", headers=hdr("requester")).json()
    assert set(body["legal"]) == LEGAL_ALLOWED
    assert body["legal"]["business_identity"] == {"required": False, "fields": [], "labels": {}}


@pytest.mark.parametrize("pid", ["uk", "uk-scotland", "uk-ni"])
def test_uk_profiles_expose_the_requirement_fields_and_labels(svc, auth, pid: str) -> None:  # type: ignore[no-untyped-def]
    c = TestClient(create_app(svc, auth, profile=load_profile(pid)))
    for role in ("requester", "buyer", "admin"):
        legal = c.get("/v1/profile", headers=hdr(role)).json()["legal"]
        assert legal["business_identity"] == UK_IDENTITY_POLICY
        assert set(legal["business_identity"]) == IDENTITY_ALLOWED


def test_exposed_labels_are_the_effective_ones_in_field_order(svc, auth, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    root = tmp_path / "profiles"
    shutil.copytree(PROFILES_DIR, root)
    us = root / "us.yaml"
    data = yaml.safe_load(us.read_text(encoding="utf-8"))
    data["legal"]["business_identity"] = {
        "required": False, "fields": ["registered_in", "legal_name"], "labels": {"legal_name": "Name"},
    }
    us.write_text(yaml.safe_dump(data), encoding="utf-8")
    c = TestClient(create_app(svc, auth, profile=load_profile("us", root=root)))
    bi = c.get("/v1/profile", headers=hdr("buyer")).json()["legal"]["business_identity"]
    assert bi == {"required": False, "fields": ["registered_in", "legal_name"],
                  "labels": {"registered_in": "Registered in", "legal_name": "Name"}}
    assert list(bi["labels"]) == bi["fields"]


def test_tenant_overrides_cannot_change_the_exposed_identity_policy(svc, auth) -> None:  # type: ignore[no-untyped-def]
    uk = load_profile("uk", tenant_overrides={"approvals": {"threshold": "777"}}, tenant_id="acme")
    c = TestClient(create_app(svc, auth, profile=uk))
    legal = c.get("/v1/profile", headers=hdr("requester")).json()["legal"]
    assert legal["business_identity"] == UK_IDENTITY_POLICY


def test_the_exposure_carries_no_footer_no_values_and_no_other_policy(svc, auth) -> None:  # type: ignore[no-untyped-def]
    uk = load_profile("uk")
    c = TestClient(create_app(svc, auth, profile=uk))
    body = c.get("/v1/profile", headers=hdr("requester")).json()
    dumped = json.dumps(body)
    assert uk.profile.legal.disclosure_footer not in dumped and "{buyer}" not in dumped
    assert set(body["legal"]["business_identity"]) == IDENTITY_ALLOWED
    for forbidden in ("business_identities", "registered_number", "01234567", "Acme Plant"):
        assert forbidden not in dumped, forbidden


def test_identity_cannot_be_supplied_by_a_request(client: TestClient, svc) -> None:  # type: ignore[no-untyped-def]
    for extra in ({"business_identity": {"legal_name": "Evil Ltd"}}, {"legal_name": "Evil Ltd"},
                  {"identity": [["Company name", "Evil Ltd"]]}, {"tenant_id": "t2"}):
        r = client.post("/v1/requests/r1/rfqs/prepare", json={"vendor_ids": ["v1"], **extra},
                        headers=hdr("buyer"))
        assert r.status_code == 422, extra
        assert "Evil" not in r.text
    assert "prepare_rfqs" not in svc.names()


def test_openapi_schema_lists_the_identity_policy() -> None:
    root = Path(__file__).resolve().parents[2]
    schemas = json.loads((root / "apps/api/openapi.json").read_text())["components"]["schemas"]
    assert "business_identity" in schemas["PublicLegal"]["properties"]
    assert set(schemas["PublicBusinessIdentity"]["properties"]) == IDENTITY_ALLOWED
