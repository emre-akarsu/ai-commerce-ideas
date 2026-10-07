"""Approved matches, price imports, kit templates, quote snapshots on real Postgres (0004)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from aidb.session import tenant_session
from aidb.stage2 import (
    MAX_TEMPLATES,
    PgApprovedMatchStore,
    PgImportStore,
    PgQuoteSnapshotStore,
    PgTemplateStore,
    TemplateLimitError,
    TemplateValidationError,
)
from components.core.fakes import FakeClock
from components.matching.approvals import ApprovedMatchStore
from components.pricebook import ImportSummary
from components.pricing import TenantScopeError

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)


# ---------------------------------------------------------------- approved matches


@pytest.fixture
def matches(app_engine):
    return PgApprovedMatchStore(app_engine, FakeClock(NOW))


def test_approved_matches_per_tenant(matches, tenants):
    a, b = tenants
    store: ApprovedMatchStore = matches
    rec = store.approve(a, "sig1:aaa", "M8 bolt", "bolt m8 zinc", ["sku-1", "sku-2"], "user:a")
    assert store.lookup(a, "sig1:aaa") == rec
    assert rec.sku_ids == ("sku-1", "sku-2") and rec.approved_at == NOW
    assert store.lookup(b, "sig1:aaa") is None
    assert store.count(b) == 0 and store.nearest(b, "bolt m8", 5) == []
    store.approve(b, "sig1:aaa", "x", "other", ["sku-9"], "user:b")  # same signature, no clash
    assert store.lookup(a, "sig1:aaa").sku_ids == ("sku-1", "sku-2")
    assert store.lookup(b, "sig1:aaa").sku_ids == ("sku-9",)


def test_approve_replaces_and_nearest_ranks(matches, tenants):
    a, _ = tenants
    matches.approve(a, "s1", "t1", "hex bolt m8 zinc", ["k1"], "u")
    matches.approve(a, "s2", "t2", "copper pipe 15mm", ["k2"], "u")
    matches.approve(a, "s1", "t1", "hex bolt m8 zinc", ["k3"], "u2")
    assert matches.count(a) == 2
    assert matches.lookup(a, "s1").sku_ids == ("k3",)
    assert matches.nearest(a, "hex bolt m8", 1)[0].signature == "s1"
    with pytest.raises(ValueError):
        matches.approve(a, "s3", "t", "r", [], "u")


def test_approved_matches_rls_blocks_foreign_write(app_engine, tenants):
    a, b = tenants
    with pytest.raises(DBAPIError), tenant_session(app_engine, b) as conn:
        conn.execute(text("INSERT INTO approved_matches (tenant_id, signature, data) "
                          "VALUES (:t, 'x', '{}')"), {"t": a})


# ---------------------------------------------------------------- imports


def summary(t: str | None, merchant: str = "m1", offers: int = 3) -> ImportSummary:
    return ImportSummary(merchant, t, "shared" if t is None else "tenant_private", offers, 1)


def test_imports_append_only_and_scoped(app_engine, tenants):
    a, b = tenants
    s = PgImportStore(app_engine)
    s.for_tenant(a).add(summary(a, "m1", 3))
    s.for_tenant(a).add(summary(a, "m1", 5))  # same merchant again is a new row
    assert [x.offers for x in s.for_tenant(a).list()] == [3, 5]
    assert s.for_tenant(b).list() == []
    with pytest.raises(TenantScopeError):
        s.for_tenant(b).add(summary(a))
    with pytest.raises(TenantScopeError):
        s.for_tenant(a).add(summary(None))
    for stmt in ("UPDATE price_imports SET merchant_id='z'", "DELETE FROM price_imports"):
        with pytest.raises(DBAPIError), tenant_session(app_engine, a) as conn:
            conn.execute(text(stmt))


# ---------------------------------------------------------------- templates


def tpl(i: str = "t1", name: str = "Bathroom", scope: str = "bathroom-refit", **kw):
    doc = {"format": "kit-template/1", "id": i, "name": name, "savedAt": "2026-10-05T09:00:00Z",
           "scopeId": scope, "jobType": "bathroom", "answers": {"finish_level": "premium",
           "tiled": True}, "measurements": {"floor_m2": "6.5"}, "allowances": {},
           "choices": {"l1": "o1"}, "lines": {"l2": "have"}}
    doc.update(kw)
    return doc


@pytest.fixture
def templates(app_engine):
    return PgTemplateStore(app_engine)


def test_templates_crud_and_isolation(templates, tenants):
    a, b = tenants
    ta, tb = templates.for_tenant(a), templates.for_tenant(b)
    assert ta.put(tpl())["name"] == "Bathroom"
    assert ta.list() == [tpl()]
    assert tb.list() == [] and tb.get("t1") is None
    assert tb.delete("t1") is False and len(ta.list()) == 1
    assert ta.delete("t1") is True and ta.list() == []


def test_template_same_name_and_scope_replaces(templates, tenants):
    a, _ = tenants
    ta = templates.for_tenant(a)
    ta.put(tpl("t1", "Quote", "s1", savedAt="2026-01-01T00:00:00Z"))
    ta.put(tpl("t2", "Quote", "s2"))  # different scope: both kept
    ta.put(tpl("t3", "Quote", "s1", savedAt="2026-02-01T00:00:00Z"))  # replaces t1
    assert {t["id"] for t in ta.list()} == {"t2", "t3"}
    ta.put(tpl("t3", "Renamed", "s1"))  # same id updates in place
    assert {t["name"] for t in ta.list()} == {"Quote", "Renamed"}
    ta.put(tpl("t2", "Renamed", "s1"))  # id t2 takes over name+scope of t3, which goes
    assert [t["id"] for t in ta.list()] == ["t2"]
    assert ta.list()[0]["scopeId"] == "s1"


def test_template_cap_30_per_tenant(templates, tenants):
    a, b = tenants
    ta = templates.for_tenant(a)
    for i in range(MAX_TEMPLATES):
        ta.put(tpl(f"t{i}", f"n{i}"))
    with pytest.raises(TemplateLimitError):
        ta.put(tpl("t-extra", "extra"))
    assert len(ta.list()) == MAX_TEMPLATES
    ta.put(tpl("t0", "n0"))  # update at the cap is fine
    ta.put(tpl("t-new", "n1"))  # replacing by name+scope at the cap is fine
    assert len(ta.list()) == MAX_TEMPLATES
    templates.for_tenant(b).put(tpl())  # the cap is per tenant
    ta.delete("t5")
    ta.put(tpl("t-extra", "extra"))


def test_template_validation(templates, tenants):
    a, _ = tenants
    ta = templates.for_tenant(a)
    for bad in (tpl(format="kit-template/2"), tpl(name="  <> "), tpl(unknown=1), tpl(i="a b"),
                tpl(lines={"l": "bogus"}), tpl(answers={"q": 1.5}), tpl(scope="")):
        with pytest.raises(TemplateValidationError):
            ta.put(bad)
    assert ta.put(tpl(name="  a\tb <x> "))["name"] == "a b x"
    assert ta.list()[0]["name"] == "a b x"


def test_templates_rls_blocks_foreign_write(app_engine, tenants):
    a, b = tenants
    with pytest.raises(DBAPIError), tenant_session(app_engine, b) as conn:
        conn.execute(text("INSERT INTO kit_templates (id, tenant_id, name, scope_id, data) "
                          "VALUES ('x', :t, 'n', 's', '{}')"), {"t": a})


# ---------------------------------------------------------------- snapshots


@pytest.fixture
def snaps(app_engine):
    return PgQuoteSnapshotStore(app_engine)


def doc(n: int = 1):
    return {"quote": {"format": "quote-draft-ui/1", "total": "123.4500"},
            "kit": {"scope_id": "s1", "answers": {"n": n}}}


def test_snapshots_versioned_and_isolated(snaps, tenants):
    a, b = tenants
    sa, sb = snaps.for_tenant(a), snaps.for_tenant(b)
    sid = sa.add(doc(1))
    rec = sa.get(sid)
    assert rec.version == 1 and rec.snapshot == doc(1)
    assert rec.snapshot["quote"]["total"] == "123.4500"  # money text kept exact
    assert sa.add(doc(2), snapshot_id=sid) == sid  # a new version, not an update
    assert sa.get(sid).snapshot == doc(2) and sa.get(sid).version == 2
    assert sa.get(sid, version=1).snapshot == doc(1)
    other = sa.add(doc(3))
    assert [r.id for r in sa.list(10)][:2] == [other, sid] or {r.id for r in sa.list(10)} >= {sid}
    assert len(sa.list(10)) == 2 and len(sa.list(1)) == 1
    assert sb.get(sid) is None and sb.list(10) == []
    assert sb.add(doc(9), snapshot_id=sid) == sid  # same id in b is independent
    assert sb.get(sid).version == 1


def test_snapshots_never_updated_or_deleted(snaps, app_engine, tenants):
    a, _ = tenants
    sid = snaps.for_tenant(a).add(doc())
    for stmt in ("UPDATE quote_snapshots SET data='{}'", "DELETE FROM quote_snapshots"):
        with pytest.raises(DBAPIError), tenant_session(app_engine, a) as conn:
            conn.execute(text(stmt))
    assert snaps.for_tenant(a).get(sid).snapshot == doc()


def test_snapshot_rejects_non_json_money(snaps, tenants):
    from decimal import Decimal

    a, _ = tenants
    with pytest.raises(TypeError):
        snaps.for_tenant(a).add({"total": Decimal("1.10")})  # money must be a string (rule 5)
    with pytest.raises(ValueError):
        snaps.for_tenant(a).add({"x": float("nan")})
    with pytest.raises(ValueError):
        snaps.for_tenant(a).list(0)


# ---------------------------------------------------------------- migration 0004


def test_0004_upgrades_and_downgrades_cleanly_from_empty(pg_db):
    import uuid

    from aidb import migrate
    from aidb.models import STAGE2_TABLES
    from aidb.session import make_engine
    from tests.aidb.conftest import ADMIN_URL, _with_db, ddl, root_engine

    name = f"aidb_s2_{uuid.uuid4().hex[:8]}"
    root = root_engine()
    ddl(root, f'CREATE DATABASE "{name}"')
    url = _with_db(ADMIN_URL, name)
    eng = make_engine(url)
    q = text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    try:
        migrate.upgrade(url, "0004")
        with eng.connect() as c:
            have = set(c.execute(q).scalars())
            forced = c.execute(text(
                "SELECT relname FROM pg_class WHERE relforcerowsecurity")).scalars().all()
        assert set(STAGE2_TABLES) | {"shared_offers"} <= have
        assert set(STAGE2_TABLES) <= set(forced) and "shared_offers" not in forced
        migrate.downgrade(url, "0003")
        with eng.connect() as c:
            assert not (set(STAGE2_TABLES) | {"shared_offers"}) & set(c.execute(q).scalars())
        migrate.upgrade(url, "0004")  # and up again
    finally:
        eng.dispose()
        ddl(root, f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
