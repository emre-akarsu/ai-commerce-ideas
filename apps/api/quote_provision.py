"""Provision the SYNTHETIC demo tenants and price files into a migrated Postgres database.

Uses the platform write paths, nothing else: tenants are created with the owner role
(`aidb.migrate.create_tenant`), shared price files go through `PgSharedOfferWriter` (owner engine),
and a tenant's own files through that tenant's `PgOfferStore` and `PgImportStore` (`app_user`).
Files are parsed by the same strict price-file adapter as the in-memory demo (`ingest`: a bad row is
quarantined, never repaired). Every offer carries `provenance.synthetic = true`. Idempotent: a file
whose first offer already exists is skipped. The data is fictional, not licensed price data.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import Engine

from aidb import migrate
from aidb.session import make_engine
from aidb.stage2 import PgImportStore, PgOfferStore, PgSharedOfferWriter
from aiplat.profile import ResolvedProfile
from components.core.ports import Clock
from components.pricebook import ImportSummary
from components.pricing import (
    CsvPriceFileSource,
    InMemoryOfferStore,
    OfferQuery,
    PricingConfig,
    Visibility,
    ingest,
)
from components.quoting.loading import (
    LoadReport,
    PriceFileSpec,
    load_price_files,
    specs_from_manifest,
)

from .quote_service import DATA, demo_manifest


@dataclass(frozen=True)
class ProvisionReport:
    tenants: tuple[str, ...]
    loaded: tuple[str, ...]  # source ids written in this run
    skipped: tuple[str, ...]  # source ids already present


def demo_specs() -> tuple[tuple[PriceFileSpec, ...], Mapping[str, str]]:
    manifest = demo_manifest()
    qdir = DATA / "quoting"
    texts = {f["file"]: (qdir / f["file"]).read_text(encoding="utf-8") for f in manifest["files"]}
    by_source = {f["source_id"]: f["merchant_id"] for f in manifest["files"]}
    return specs_from_manifest(manifest, texts), by_source


def demo_reports(pricing: PricingConfig) -> tuple[LoadReport, ...]:
    """Dry-run every demo file into a scratch store, for the reports (counts, quarantine)."""
    specs, _ = demo_specs()
    return load_price_files(InMemoryOfferStore(pricing), specs, pricing)


def demo_shared_summaries(pricing: PricingConfig) -> tuple[ImportSummary, ...]:
    """Import summaries of the shared demo files (the Pg import store keeps tenant rows only)."""
    from components.pricebook import summaries_from_reports

    _, by_source = demo_specs()
    return tuple(s for s in summaries_from_reports(demo_reports(pricing), by_source)
                 if s.tenant_id is None)


def provision_demo(admin_url: str, app_url: str, profile: ResolvedProfile,
                   clock: Clock) -> ProvisionReport:
    """`admin_url`: owner role (tenants, shared offers). `app_url`: the `app_user` role."""
    del clock  # offers carry the manifest's own observed_at; no wall-clock value is written
    pricing = PricingConfig.from_mapping(profile.profile.model_dump(mode="json"))
    specs, by_source = demo_specs()
    manifest = demo_manifest()
    tenants = tuple(manifest["tenants"])
    for tenant in tenants:
        migrate.create_tenant(admin_url, tenant, f"{tenant} (synthetic demo tenant)")
    admin, app = make_engine(admin_url), make_engine(app_url)
    try:
        loaded: list[str] = []
        skipped: list[str] = []
        for spec in specs:
            (loaded if _provision_file(admin, app, pricing, spec, by_source)
             else skipped).append(spec.source_id)
    finally:
        admin.dispose()
        app.dispose()
    return ProvisionReport(tenants, tuple(loaded), tuple(skipped))


def _provision_file(admin: Engine, app: Engine, pricing: PricingConfig, spec: PriceFileSpec,
                    by_source: Mapping[str, str]) -> bool:
    decl = spec.declaration
    source = CsvPriceFileSource(spec.text, spec.mapping, source_id=spec.source_id, kind=spec.kind,
                                origin=spec.origin)
    report = ingest(source, OfferQuery(), decl, pricing)
    offers = list(report.offers)
    if not offers:
        return False
    if decl.visibility is Visibility.SHARED:
        probe = PgOfferStore(app, pricing).for_tenant(_any_tenant(admin))
        if probe.get(offers[0].offer_id) is not None:
            return False
        PgSharedOfferWriter(admin, pricing).add_many_shared(offers)
        return True  # shared summaries are handed to the app at start (quote_pg.PgImportAdapter)
    assert decl.tenant_id is not None
    repo = PgOfferStore(app, pricing).for_tenant(decl.tenant_id)
    if repo.get(offers[0].offer_id) is not None:
        return False
    repo.add_many(offers)
    PgImportStore(app).for_tenant(decl.tenant_id).add(ImportSummary(
        by_source[spec.source_id], decl.tenant_id, "tenant_private", len(offers),
        len(report.quarantined)))
    return True


def _any_tenant(admin: Engine) -> str:
    """A tenant id to read shared offers through (shared rows are visible to every tenant)."""
    from sqlalchemy import text

    with admin.connect() as conn:
        found = conn.execute(text("SELECT id FROM tenants ORDER BY id LIMIT 1")).scalar_one()
    return str(found)


__all__ = ["ProvisionReport", "demo_shared_summaries", "demo_specs", "provision_demo"]
