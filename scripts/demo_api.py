#!/usr/bin/env python3
"""Local demo API: `make demo-api`. SYNTHETIC DATA ONLY. Nothing real is sent, called or stored.

Starts the API on 127.0.0.1 with the in-memory purchasing service (state is lost on exit), test
authentication (`AUTH_MODE=test`), the UK deployment profile with a synthetic business identity, a
recording transport (no email leaves the process, the transport is held by the send-service only),
a fake LLM (no model call), and CORS for http://localhost:3000. It prints one development bearer
token per role. It refuses to start when ENV is production. It makes no network call of its own.

The seeded tenant, suppliers and requests are illustrative and are NOT licensed or real data.
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for sub in ("packages", "."):
    path = str(ROOT / sub)
    if path not in sys.path:
        sys.path.insert(0, path)

PROD_ENVS = frozenset({"production", "prod"})
TENANT = "demo-synthetic-tenant"
CORS_ORIGINS = ["http://localhost:3000"]
DEMO_CHAIN_KEY = b"demo-audit-chain-key-synthetic-not-secret"  # lets scripts/verify_audit_export.py run
SYNTHETIC_IDENTITY = {
    "legal_name": "SYNTHETIC Demo Plant Ltd",
    "registration_number": "00000000",
    "registered_office": "1 Example Street, Exampletown, EX1 1AA",
    "registered_in": "England and Wales",
}
USERS = {"requester": "demo-requester", "buyer": "demo-buyer", "admin": "demo-admin"}
REQUEST_MID_FLOW = (
    "SYNTHETIC demo request: bearing 6205-2RS, normal clearance CN. "
    "Manufacturer: SynthCo Alpha MPN: AL6205-2RS. Need 10 pcs by 2026-12-01."
)
REQUEST_NEEDS_CONFIRM = REQUEST_MID_FLOW.replace("SYNTHETIC demo request: ", "SYNTHETIC demo request 2: ")
REQUEST_STATED = REQUEST_MID_FLOW.replace("CN.", "CN, precision class P0.")


class ProductionRefusal(RuntimeError):
    pass


def refuse_in_production(env: dict[str, str] | None = None) -> None:
    e = os.environ if env is None else env
    if e.get("ENV", "").strip().lower() in PROD_ENVS:
        raise ProductionRefusal("refusing to start the demo API: ENV is production")


@dataclass(frozen=True)
class Demo:
    app: Any
    tokens: dict[str, str]
    service: Any
    transport: Any
    secret: str


def _seed(svc: Any, ctxs: dict[str, Any]) -> None:
    from components.core.domain import Vendor

    admin, buyer, requester = ctxs["admin"], ctxs["buyer"], ctxs["requester"]
    spec = [  # id, name, domain, attested, kind, suppressed
        ("demo-alpha", "SYNTHETIC Alpha Supply Ltd", "alpha-supply.example", True, "company", False),
        ("demo-bravo", "SYNTHETIC Bravo Bearings Ltd", "bravo-bearings.example", True, "company", False),
        ("demo-charlie", "SYNTHETIC Charlie Traders (unverified)", "charlie-traders.example",
         False, "unknown", False),
        ("demo-delta", "SYNTHETIC Delta Sole Trader", "delta-trader.example", True, "individual", False),
        ("demo-echo", "SYNTHETIC Echo Parts (suppressed)", "echo-parts.example", True, "company", True),
    ]
    for vid, name, domain, attested, kind, suppressed in spec:
        svc.upsert_vendor(admin, Vendor(
            id=vid, tenant_id=TENANT, name=name, domain=domain,
            contact_email=f"sales@{domain}", phone=None))
        svc.set_supplier_profile(buyer, vid, contact_kind=kind, account_type="credit", credit_days=30)
        if attested:
            svc.attest_vendor(admin, vid, note="synthetic demo attestation")
        if suppressed:
            svc.suppress_vendor(buyer, vid)
    # request 1: waiting on a critical assumption (precision class defaulted)
    svc.create_request(requester, text=REQUEST_NEEDS_CONFIRM)
    # request 2: assumptions closed, RFQs prepared and waiting for a person to approve (nothing sent)
    rid = svc.create_request(requester, text=REQUEST_STATED).request.id
    svc.prepare_rfqs(buyer, rid, vendor_ids=["demo-alpha", "demo-bravo"])


def build_demo(env: dict[str, str] | None = None) -> Demo:
    refuse_in_production(env)
    from apps.api.auth import JwtAuthenticator, make_test_token
    from apps.api.main import create_app
    from employees.purchasing.service import Settings, build_in_memory_service

    from aiplat.ctx import Ctx, Role
    from aiplat.profile import load_profile
    from components.core.fakes import FakeLLM, RecordingTransport

    profile = load_profile("uk")
    transport = RecordingTransport()
    settings = Settings(
        business_identities={TENANT: SYNTHETIC_IDENTITY}, approvers=("user:demo-admin",),
        buyer_names={"demo-buyer": "Demo Buyer (synthetic)"}, alias_address="rfq@alias.example",
        reply_to_domain="buyer.example", buyer_phone="+44 20 7946 0000")
    svc = build_in_memory_service(
        profile=profile, settings=settings, transport=transport, llm=FakeLLM([]),
        audit_key=DEMO_CHAIN_KEY, approval_secret=secrets.token_bytes(32))
    secret = secrets.token_hex(32)
    ctxs = {r: Ctx(TENANT, USERS[r], Role(r)) for r in USERS}
    _seed(svc, ctxs)
    tokens = {r: make_test_token(secret, sub=USERS[r], tenant_id=TENANT, role=r, ttl=8 * 3600)
              for r in USERS}
    app = create_app(svc, JwtAuthenticator(key=secret, algorithms=("HS256",)),
                     cors_origins=CORS_ORIGINS, profile=profile)
    return Demo(app, tokens, svc, transport, secret)


def banner(demo: Demo, host: str, port: int) -> str:
    lines = [
        "",
        "SYNTHETIC DEMO: data is illustrative, in memory, and lost on exit. Nothing is sent.",
        f"API: http://{host}:{port}   CORS: {', '.join(CORS_ORIGINS)}   profile: uk",
        f"Tenant: {TENANT}   audit chain key (demo only): {DEMO_CHAIN_KEY.decode()}",
        "Development bearer tokens (valid 8 hours):",
    ]
    lines += [f"  {role:<10} {token}" for role, token in demo.tokens.items()]
    lines += ["", f'Try: curl -H "Authorization: Bearer <token>" http://{host}:{port}/v1/requests', ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args(argv)
    os.environ.setdefault("ENV", "dev")
    os.environ["AUTH_MODE"] = "test"
    try:
        demo = build_demo()
    except ProductionRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(banner(demo, args.host, args.port), flush=True)
    try:
        import uvicorn
    except ImportError:
        print("uvicorn is not installed: run `make setup` (it is a declared dependency)", file=sys.stderr)
        return 2
    uvicorn.run(demo.app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
