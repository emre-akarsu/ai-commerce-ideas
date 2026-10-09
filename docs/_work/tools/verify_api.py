"""Executes the checks behind several fact-check findings against the real in-memory app (no network)."""
import io, json, os, sys
sys.path.insert(0, "/home/user/ai-commerce-ideas/packages"); sys.path.insert(0, "/home/user/ai-commerce-ideas")
os.environ.update({"ENV": "test", "AUTH_MODE": "test", "TEST_AUTH_SECRET": "x" * 40, "DEPLOYMENT_PROFILE": "uk", "QUOTE_DEMO_DATA": "1"})
from fastapi.testclient import TestClient
from apps.api.asgi import build_app
from apps.api.auth import make_test_token

app = build_app()
c = TestClient(app, raise_server_exceptions=False)
def tok(role, sub="alice", tenant="demo-tenant-a"):
    return {"Authorization": "Bearer " + make_test_token("x" * 40, sub=sub, tenant_id=tenant, role=role)}

def show(label, r, body=True):
    b = ""
    if body:
        try: b = json.dumps(r.json())[:200]
        except Exception: b = r.text[:200]
    print(f"{label}: {r.status_code} {b}")

# 04-11: unknown state filter
show("GET /v1/requests?state=BOGUS (requester)", c.get("/v1/requests?state=BOGUS", headers=tok("requester")))
# 04-5: headers on an unhandled 500
r = c.get("/v1/requests?state=BOGUS", headers=tok("requester"))
print("  500 headers:", {k: v for k, v in r.headers.items() if k.lower() in ("x-content-type-options", "cache-control", "content-security-policy", "x-frame-options")})
r2 = c.get("/v1/profile", headers=tok("requester"))
print("  200 headers:", {k: v for k, v in r2.headers.items() if k.lower() in ("x-content-type-options", "cache-control")})
# 04-3: approval decide as requester with bogus action
show("POST decide bogus action (requester)", c.post("/v1/approval-links/sometoken/decide", json={"action": "bogus"}, headers=tok("requester")))
show("POST decide valid action (requester)", c.post("/v1/approval-links/sometoken/decide", json={"action": "approve"}, headers=tok("requester")))
# 04-3b: role before body for a normal route (vendor create as requester with invalid body)
show("POST /v1/vendors invalid body (requester)", c.post("/v1/vendors", json={}, headers=tok("requester")))
# 04-4: csv size between 1,000,001 and 5,000,000 bytes on /v1/imports/csv and /v1/vendors/import
big = b"part_number\n" + b"X" * 1_100_000
show("POST /v1/imports/csv 1.1 MB (buyer)", c.post("/v1/imports/csv", files={"file": ("a.csv", big, "text/csv")}, headers=tok("buyer")))
big_v = b"name,domain,contact_email\n" + b"a,b.example,c@b.example\n" * 60000
print("  vendor csv bytes:", len(big_v))
show("POST /v1/vendors/import 1.4 MB (buyer)", c.post("/v1/vendors/import", files={"file": ("v.csv", big_v, "text/csv")}, headers=tok("buyer")))
huge = b"part_number\n" + b"X" * 5_100_000
show("POST /v1/imports/csv 5.1 MB (buyer)", c.post("/v1/imports/csv", files={"file": ("a.csv", huge, "text/csv")}, headers=tok("buyer")))
# 04-19: rfq-drafts for unknown merchant (needs a quote)
q = c.post("/v1/quotes", json={"scope_id": "bathroom_wc_only", "kit": {"answers": {}, "measurements": {}, "allowances": {}, "choices": {}, "lines": {}}}, headers=tok("buyer"))
show("POST /v1/quotes (buyer)", q, body=False)
if q.status_code == 200:
    qid = q.json()["id"]
    print("  quote response keys:", sorted(q.json().keys()))
    show("POST rfq-drafts unknown merchant", c.post(f"/v1/quotes/{qid}/rfq-drafts", json={"mode": "per_supplier", "merchant_ids": ["m-nope"]}, headers=tok("buyer")))
    o = c.get(f"/v1/quotes/{qid}/options?preferred=m-halden", headers=tok("requester"))
    show("GET options preferred only", o, body=False)
    try:
        d = o.json(); print("  option kinds with preferred only:", [x.get("kind") for x in d.get("options", [])])
    except Exception as e: print("  err", e)
    o2 = c.get(f"/v1/quotes/{qid}/options?budget=900", headers=tok("requester"))
    try:
        d2 = o2.json(); print("  option kinds with budget:", [x.get("kind") for x in d2.get("options", [])])
    except Exception as e: print("  err", e)
# 04-10 profile payload legal keys
p = c.get("/v1/profile", headers=tok("requester")).json()
print("  profile.legal keys:", sorted(p.get("legal", {}).keys()))
# resolve kit format
rk = c.post("/v1/kits/resolve", json={"scope_id": "bathroom_wc_only", "answers": {}, "measurements": {}, "allowances": {}, "choices": {}, "lines": {}}, headers=tok("requester"))
print("kits/resolve format:", rk.json().get("format") if rk.status_code == 200 else rk.status_code)

print("---- options structure")
if q.status_code == 200:
    for label, qs in (("none", ""), ("preferred", "?preferred=m-halden"), ("budget", "?budget=900"), ("all", "?budget=900&required_by=2026-10-12&max_deliveries=3&preferred=m-halden")):
        d = c.get(f"/v1/quotes/{qid}/options{qs}", headers=tok("requester")).json()
        opts = d.get("options", [])
        print(label, "keys:", sorted(d.keys())[:12], "| options:", [ (o.get("id") or o.get("objective") or o.get("kind") or list(o.keys())[:3]) for o in opts], "| balanced:", (d.get("balanced") or {}).get("status"))

print("---- option kinds")
for label, qs in (("none", ""), ("preferred", "?preferred=m-halden"), ("budget", "?budget=900"), ("all", "?budget=900&required_by=2026-10-12&max_deliveries=3&preferred=m-halden")):
    d = c.get(f"/v1/quotes/{qid}/options{qs}", headers=tok("requester")).json()
    print(label, [(o["label"], o["kinds"]) for o in d.get("options", [])], "| not_shown:", [n.get("kind") for n in d.get("not_shown", [])] if isinstance(d.get("not_shown"), list) else d.get("not_shown"))
