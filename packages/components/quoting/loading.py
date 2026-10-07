"""Load price files into the offer store, only through the pricing engine's CSV adapter.

Hard rule R7: nothing here opens a file or reaches a network. A caller (the demo script, a test, a
future upload endpoint) reads the file and hands over its TEXT; `CsvPriceFileSource` parses it,
`ingest` validates every row strictly (a bad row is quarantined with a reason code, never repaired)
and the offers go into the store: a tenant-private file into that tenant's namespace, a shared
file through the platform-only shared writer. What a file means (who may see it, whether the
tenant attests it, its licence, its validity) comes from a declaration, not from the file's own
content, so a price file cannot declare itself firm.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from components.pricing import (
    CsvMapping,
    CsvPriceFileSource,
    InMemoryOfferStore,
    OfferQuery,
    PricingConfig,
    QuarantinedRecord,
    SourceKind,
    VatBasis,
    Visibility,
    ingest,
)
from components.pricing.eligibility import PriceType
from components.pricing.sources import SourceDeclaration

from .errors import QuotingError

CSV_FIELDS = (
    "sku", "price_ex_vat", "price_inc_vat", "price", "vat_basis", "price_per", "uom", "pack_size",
    "pack_unit", "min_order_qty", "order_multiple", "stock", "lead_time_days", "delivery_fee",
    "free_delivery_over", "observed_at", "valid_until",
)
STANDARD_MAPPING = CsvMapping(columns={name: name for name in CSV_FIELDS})


@dataclass(frozen=True)
class PriceFileSpec:
    """One price file handed over as text, with what the loader declares about it."""

    origin: str  # a label such as the file name; shown in provenance, never opened
    text: str
    source_id: str
    kind: SourceKind
    declaration: SourceDeclaration
    mapping: CsvMapping = STANDARD_MAPPING


@dataclass(frozen=True)
class LoadReport:
    source_id: str
    origin: str
    visibility: str
    tenant_id: str | None
    offers: int
    quarantined: tuple[QuarantinedRecord, ...]

    @property
    def reason_counts(self) -> tuple[tuple[str, int], ...]:
        counts: dict[str, int] = {}
        for q in self.quarantined:
            for reason in q.reasons:
                counts[reason] = counts.get(reason, 0) + 1
        return tuple(sorted(counts.items()))


def _when(value: object, name: str) -> datetime | None:
    if value is None:
        return None
    try:
        moment = datetime.fromisoformat(str(value))
    except ValueError:
        raise QuotingError(f"manifest {name} is not an ISO date-time") from None
    if moment.tzinfo is None:
        raise QuotingError(f"manifest {name} needs a time zone")
    return moment


def _declaration(entry: Mapping[str, object]) -> SourceDeclaration:
    observed = _when(entry.get("observed_at"), "observed_at")
    if observed is None:
        raise QuotingError("manifest entry needs observed_at")
    try:
        return SourceDeclaration(
            licence=str(entry["licence"]), confidence=Decimal(str(entry["confidence"])),
            observed_at=observed, method=str(entry.get("method", "file_row")),
            synthetic=bool(entry.get("synthetic", False)),
            visibility=Visibility(str(entry["visibility"])),
            tenant_id=None if entry.get("tenant_id") is None else str(entry["tenant_id"]),
            merchant_id=str(entry["merchant_id"]),
            default_currency=str(entry.get("default_currency", "")) or None,
            default_vat_basis=VatBasis(str(entry.get("default_vat_basis", "unknown"))),
            default_valid_until=_when(entry.get("default_valid_until"), "default_valid_until"),
            price_type=PriceType(str(entry["price_type"])),
            account_specific=bool(entry.get("account_specific", False)),
            tenant_attested=bool(entry.get("tenant_attested", False)))
    except (KeyError, ValueError) as exc:
        raise QuotingError(f"bad manifest entry: {exc}") from exc


def specs_from_manifest(manifest: Mapping[str, object], texts: Mapping[str, str]
                        ) -> tuple[PriceFileSpec, ...]:
    """Price file specs from a manifest and the TEXT of each listed file (read by the caller)."""
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise QuotingError("manifest has no files list")
    specs = []
    for entry in entries:
        name = str(entry["file"])
        if name not in texts:
            raise QuotingError(f"no text was handed over for {name}")
        specs.append(PriceFileSpec(
            origin=name.rsplit("/", 1)[-1], text=texts[name], source_id=str(entry["source_id"]),
            kind=SourceKind(str(entry["kind"])), declaration=_declaration(entry)))
    return tuple(specs)


def load_price_file(store: InMemoryOfferStore, spec: PriceFileSpec, cfg: PricingConfig
                    ) -> LoadReport:
    source = CsvPriceFileSource(spec.text, spec.mapping, source_id=spec.source_id,
                                kind=spec.kind, origin=spec.origin)
    report = ingest(source, OfferQuery(), spec.declaration, cfg)
    decl = spec.declaration
    if decl.visibility is Visibility.SHARED:
        store.shared_writer().add_many_shared(report.offers)
    elif decl.tenant_id is not None:
        store.for_tenant(decl.tenant_id).add_many(report.offers)
    return LoadReport(spec.source_id, spec.origin, decl.visibility.value, decl.tenant_id,
                      len(report.offers), report.quarantined)


def load_price_files(store: InMemoryOfferStore, specs: Sequence[PriceFileSpec],
                     cfg: PricingConfig) -> tuple[LoadReport, ...]:
    return tuple(load_price_file(store, s, cfg) for s in specs)
