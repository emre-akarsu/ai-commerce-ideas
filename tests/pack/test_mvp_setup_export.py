"""Setup and go-live, evidence export and the offline verifier (api-contract-mvp.md sections 3, 4)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from employees.purchasing.service_port import Conflict, NotFound

from aiplat.ctx import Ctx, Forbidden, Role
from aiplat.profile import load_profile
from components.evidence.log import EventLog
from tests.pack.conftest import REQUEST_TEXT, T1, UK_IDENTITY, World, build_world

ROOT = Path(__file__).resolve().parents[2]
KEY = b"k" * 32
SCRIPT = ROOT / "scripts" / "verify_audit_export.py"


def status(w: World) -> dict[str, str]:
    return {i.id: i.status for i in w.svc.get_setup(w.admin).items}


def test_setup_items_follow_the_tenant_state() -> None:
    w = build_world(profile=load_profile("uk"), business_identities={T1: {"legal_name": "Acme Ltd"}})
    items = {i.id: i for i in w.svc.get_setup(w.admin).items}
    assert set(items) == {"profile", "business_identity", "suppliers", "kill_switch", "dry_run",
                          "sending_domain"}
    assert items["profile"].detail.startswith("uk@") and items["profile"].status == "done"
    assert items["business_identity"].status == "todo"
    assert items["business_identity"].detail == (
        "missing: registration_number, registered_office, registered_in")
    assert "Acme Ltd" not in items["business_identity"].detail  # names only, never values
    assert items["suppliers"].status == "done"  # build_world attests some
    assert items["sending_domain"].status == "todo"
    assert items["sending_domain"].detail == "confirm SPF, DKIM and DMARC for the alias domain"
    assert items["dry_run"].status == "todo"


def test_business_identity_item_only_when_the_profile_requires_it() -> None:
    w = build_world()
    assert "business_identity" not in status(w)


def test_go_live_is_refused_until_ready_and_then_recorded_not_enforced() -> None:
    w = build_world()
    s = w.svc.get_setup(w.admin)
    assert s.ready is False and s.live is False
    with pytest.raises(Conflict, match="^not ready: dry_run$"):
        w.svc.go_live(w.admin)
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    s = w.svc.get_setup(w.admin)
    assert s.ready is True and s.live is False
    live = w.svc.go_live(w.admin)
    assert live.live is True
    assert [e.type for e in w.log.events(T1)].count("setup.go_live") == 1
    assert w.svc.go_live(w.admin).live is True  # again: recorded once
    assert [e.type for e in w.log.events(T1)].count("setup.go_live") == 1
    assert w.svc.get_setup(w.admin).live is True
    # not enforced: sending never consulted `live`, and was possible before it too
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    assert len(w.transport.delivered) == 1


def test_an_engaged_kill_switch_blocks_readiness() -> None:
    w = build_world()
    w.svc.create_request(w.requester, text=REQUEST_TEXT)
    w.svc.set_kill_switch(w.admin, engaged=True)
    assert status(w)["kill_switch"] == "blocked"
    with pytest.raises(Conflict, match="kill_switch"):
        w.svc.go_live(w.admin)
    w.svc.set_kill_switch(w.admin, engaged=False)
    assert status(w)["kill_switch"] == "done"


def test_a_tenant_without_attested_suppliers_is_not_ready_and_roles_are_checked() -> None:
    w = build_world()
    with pytest.raises(Forbidden):
        w.svc.get_setup(w.buyer)
    with pytest.raises(Forbidden):
        w.svc.go_live(w.buyer)
    assert status(w)["suppliers"] == "done"
    other = w.svc.get_setup(Ctx("tenant-2", "admin-2", Role.ADMIN))
    assert {i.id: i.status for i in other.items}["suppliers"] == "done"  # its own attested vendor


# ---- evidence export

def export_of(w: World, rid: str | None = None) -> dict:
    return json.loads(w.svc.audit_export(w.admin, rid).model_dump_json())


def flow(w: World) -> str:
    rid = w.svc.create_request(w.requester, text=REQUEST_TEXT).request.id
    (p,) = w.svc.prepare_rfqs(w.buyer, rid, vendor_ids=["acme"])
    w.svc.approve_send(w.buyer, p.rfq_id, mime_hash=p.mime_hash)
    return rid


def fresh() -> World:
    # the chain key is known to the test so the verifier can be run with it
    return build_world()


def test_export_shape_and_redaction() -> None:
    w = fresh()
    flow(w)
    doc = export_of(w)
    assert set(doc) == {"tenant", "generated_at", "profile", "chain_valid", "head_hash", "events",
                        "request_id"}
    assert doc["chain_valid"] is True and doc["tenant"] != T1 and len(doc["tenant"]) == 16
    assert doc["profile"].startswith("us@") and doc["head_hash"] == doc["events"][-1]["hash"]
    assert all("_pii" not in e["payload"] for e in doc["events"])
    assert any("_pii_digests" in e["payload"] for e in doc["events"])  # digests stay: chain verifiable
    assert "sales@acme.example" not in json.dumps(doc)


def test_export_is_admin_only_and_request_scoped_with_404_across_tenants() -> None:
    w = build_world()
    rid = flow(w)
    with pytest.raises(Forbidden):
        w.svc.audit_export(w.buyer)
    with pytest.raises(NotFound):
        w.svc.audit_export(Ctx("tenant-2", "admin-2", Role.ADMIN), rid)
    scoped = export_of(w, rid)
    assert scoped["request_id"] == rid and all(e["request_id"] == rid for e in scoped["events"])
    assert w.svc.audit_export(w.admin).chain_valid is True


def _verifier():
    spec = importlib.util.spec_from_file_location("verify_audit_export", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def keyed_world() -> World:
    """A world whose log uses a known chain key (conftest uses the default ephemeral one)."""
    w = build_world()
    return w


def test_verifier_accepts_a_real_export_with_the_key_and_matches_the_log(tmp_path: Path) -> None:
    w = keyed_world()
    flow(w)
    key = w.log._chain_key  # noqa: SLF001 - the deployment key, as the auditor would hold it
    doc = export_of(w)
    v = _verifier()
    assert v.verify(doc, key) == []
    assert v.verify(doc, None) == []  # linkage only
    # same answer as the log's own verifier for the same chain
    assert w.log.verify_chain(T1) is True
    scoped = export_of(w, doc["events"][-1]["request_id"] or None)
    assert v.verify(scoped, key) == []


def test_verifier_rejects_every_kind_of_tampering(tmp_path: Path) -> None:
    w = keyed_world()
    flow(w)
    key = w.log._chain_key  # noqa: SLF001
    good = export_of(w)
    v = _verifier()

    edited = json.loads(json.dumps(good))
    edited["events"][2]["payload"]["tampered"] = True
    assert any("hash mismatch" in p for p in v.verify(edited, key))
    assert v.verify(edited, None) == []  # linkage-only mode cannot see payload edits (documented)

    actor = json.loads(json.dumps(good))
    actor["events"][1]["actor"] = "user:someone-else"
    assert v.verify(actor, key)

    dropped = json.loads(json.dumps(good))
    del dropped["events"][3]
    assert v.verify(dropped, key) and v.verify(dropped, None)

    swapped = json.loads(json.dumps(good))
    swapped["events"][1], swapped["events"][2] = swapped["events"][2], swapped["events"][1]
    assert v.verify(swapped, None)

    truncated = json.loads(json.dumps(good))
    truncated["events"].pop()
    assert any("head_hash" in p for p in v.verify(truncated, None))

    assert v.verify(good, b"wrong-key-wrong-key-wrong-key-12") != []


def test_verifier_cli_exit_codes(tmp_path: Path) -> None:
    w = keyed_world()
    flow(w)
    f = tmp_path / "export.json"
    f.write_text(json.dumps(export_of(w)))
    env = {"PATH": "/usr/bin:/bin", "AUDIT_CHAIN_KEY": w.log._chain_key.decode()}  # noqa: SLF001

    def run(*args: str, e: dict | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True,  # noqa: S603
                              text=True, env=e if e is not None else env, check=False)

    assert run(str(f)).returncode == 0
    assert run(str(f), e={"PATH": "/usr/bin"}).returncode == 3  # no key, not linkage-only
    assert run(str(f), "--linkage-only", e={"PATH": "/usr/bin"}).returncode == 0
    doc = json.loads(f.read_text())
    doc["events"][1]["payload"]["x"] = 1
    f.write_text(json.dumps(doc))
    bad = run(str(f))
    assert bad.returncode == 1 and "FAILED" in bad.stdout
    assert run(str(tmp_path / "missing.json")).returncode == 2


def test_the_verifier_agrees_with_the_event_log_hash(tmp_path: Path) -> None:
    from components.core.fakes import FakeClock
    log = EventLog(FakeClock(), pii_key=KEY, chain_key=KEY)
    log.append("t", None, "user:a", "x.y", {"n": 1, "_pii": {"email": "a@b.example"}})
    log.append("t", "r1", "agent", "x.z", {"amount": __import__("decimal").Decimal("1.50")})
    events = [e.model_dump(mode="json") for e in log.events("t")]
    for e in events:
        e["payload"].pop("_pii", None)
    doc = {"events": events, "head_hash": events[-1]["hash"], "request_id": None}
    assert _verifier().verify(doc, KEY) == []


def test_uk_profile_stamp_in_export() -> None:
    w = build_world(profile=load_profile("uk"), business_identities={T1: UK_IDENTITY})
    w.svc.create_request(w.requester, text=REQUEST_TEXT)
    assert export_of(w)["profile"].startswith("uk@")
