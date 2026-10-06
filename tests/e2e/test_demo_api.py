"""The demo entry builds offline, is labelled synthetic, sends nothing and refuses production."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "demo_api.py"


def load():
    spec = importlib.util.spec_from_file_location("demo_api", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["demo_api"] = mod  # dataclasses look the module up by name
    spec.loader.exec_module(mod)
    return mod


def h(demo, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {demo.tokens[role]}"}


def test_demo_serves_seeded_synthetic_data_and_sends_nothing() -> None:
    mod = load()
    demo = mod.build_demo({"ENV": "dev"})
    c = TestClient(demo.app)
    assert set(demo.tokens) == {"requester", "buyer", "admin"}
    vendors = c.get("/v1/vendors", headers=h(demo, "buyer")).json()
    assert len(vendors) == 5 and all(v["name"].startswith("SYNTHETIC") for v in vendors)
    states = {v["profile"]["verification"]["state"] for v in vendors}
    assert states == {"attested", "unverified"}
    assert any(v["profile"]["suppressed"] for v in vendors)
    reqs = c.get("/v1/requests", headers=h(demo, "requester")).json()
    assert len(reqs) == 2
    prepared = [c.get(f"/v1/requests/{r['id']}/rfqs/prepared", headers=h(demo, "buyer")).json()
                for r in reqs]
    assert sorted(len(p) for p in prepared) == [0, 2]
    assert demo.transport.delivered == []  # prepared, never sent
    assert c.get("/v1/profile", headers=h(demo, "requester")).json()["id"] == "uk"
    setup = c.get("/v1/setup", headers=h(demo, "admin")).json()
    assert {i["id"]: i["status"] for i in setup["items"]}["business_identity"] == "done"


def test_demo_cors_allows_only_the_local_web_app() -> None:
    demo = load().build_demo({"ENV": "dev"})
    c = TestClient(demo.app)
    ok = c.get("/healthz", headers={"Origin": "http://localhost:3000"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in c.get(
        "/healthz", headers={"Origin": "https://evil.example"}).headers


def test_demo_refuses_production() -> None:
    mod = load()
    for env in ("production", "prod", " Production "):
        with pytest.raises(mod.ProductionRefusal):
            mod.build_demo({"ENV": env})
    r = subprocess.run(  # noqa: S603 - our own script, fixed arguments
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, check=False,
        env={"PATH": "/usr/bin:/bin", "ENV": "production"})
    assert r.returncode == 2 and "refusing" in r.stderr


def test_demo_export_verifies_offline_with_the_demo_key() -> None:
    import json

    mod = load()
    demo = mod.build_demo({"ENV": "dev"})
    doc = TestClient(demo.app).get("/v1/audit/export", headers=h(demo, "admin")).json()
    spec = importlib.util.spec_from_file_location("v", SCRIPT.parent / "verify_audit_export.py")
    v = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(v)  # type: ignore[union-attr]
    assert doc["chain_valid"] is True
    assert v.verify(json.loads(json.dumps(doc)), mod.DEMO_CHAIN_KEY) == []
