"""Customer price file upload (docs/product/08, ladder level 2; hard rules R4, R5, R7).

A person hands over a CSV or XLSX of prices they may use for their own purchases. This module only
works on the BYTES it is given (nothing is fetched, no link in a cell is followed; R7, rule 4):

* the type is checked three ways (declared content type, extension, magic bytes); XLSX with macros,
  external references, embedded objects or zip-bomb proportions is refused; formulas are never
  evaluated (cached values only, `components.doc_parse`);
* rows go through the strict pricing ingest (`components.pricing.ingest`): Decimal only, explicit
  currency, VAT basis and pack; a bad row is quarantined with reason codes, never repaired;
* the VAT basis is a declared field of the upload (`inc` or `ex`), never guessed; a file whose rows
  state no basis and whose upload states none is refused;
* what the file means (tenant-private, attested or not, valid until) comes from the upload's
  declaration, not from its content: the offers are `trade_feed` / `trade_list`, so they are firm
  only with an attestation AND a validity date, otherwise indicative (`quote_line_eligible`);
* offers go to the tenant-scoped `OfferStore`, a summary to the tenant-scoped `ImportStore`; the
  file's bytes are not kept. One `price_file_loaded` event is appended through the `EventSink`.

Re-upload rule (documented in docs/architecture/pricebook.md terms): for one tenant and one
merchant the newest file replaces the earlier customer price files wholesale (SKUs absent from the
new file disappear). A file whose price date (`valid_from`, else the upload time) is OLDER than the
loaded one is refused with 409. A file that yields no offer replaces nothing.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import uuid
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any

from aiplat.ctx import Ctx
from components.doc_parse import LocalTextParser, ParserLimits
from components.imports.safety import echo, neutralise
from components.pricebook import ImportSummary, PriceBookError
from components.pricebook.models import check_merchant_id
from components.pricing import (
    CsvMapping,
    CsvPriceFileSource,
    OfferQuery,
    PricingConfig,
    PricingError,
    SourceKind,
    VatBasis,
    Visibility,
    ingest,
)
from components.pricing.eligibility import PriceType
from components.pricing.repository import MAX_LIMIT, OfferFilter
from components.pricing.sources import SourceDeclaration
from components.quoting.loading import CSV_FIELDS

from .quote_service import QuoteService

METHOD = "customer_price_file"  # Provenance.method of every offer loaded here
SOURCE_KIND_FIELD = "customer_price_file"  # the only accepted `source_kind` form value
LICENCE = "tenant-supplied-private"
CONFIDENCE = Decimal("0.90")
MAX_FILE_BYTES = 900_000  # below the API's 1 MB request cap (the route is not an upload_path)
MAX_QUARANTINE_ECHO = 1000
CSV_TYPES = frozenset({"text/csv", "application/csv", "application/vnd.ms-excel"})
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MAX_ZIP_ENTRIES = 200
MAX_UNZIPPED = 20 * 1024 * 1024
MAX_RATIO = 100
MAX_REL_PART = 1_000_000
_FORBIDDEN_PARTS = ("vbaproject", "externallinks/", "embeddings/", "activex/", "oleobject")
_ROW = re.compile(r"#row=(\d+)$")
_ISO_CUR = re.compile(r"[A-Z]{3}")


class PriceFileError(Exception):
    """A refused upload. `status` is the HTTP status; `message` never contains file content."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


@dataclass(frozen=True)
class Upload:
    filename: str
    content_type: str
    data: bytes


@dataclass(frozen=True)
class Declaration:
    merchant_id: str
    vat_basis: str
    attested: bool
    valid_from: str | None = None
    valid_until: str | None = None
    currency: str | None = None
    source_kind: str = SOURCE_KIND_FIELD


# --------------------------------------------------------------------------- validation


def _basis(value: str | None) -> VatBasis:
    key = (value or "").strip().lower()
    if key == "inc":
        return VatBasis.INC_TAX
    if key == "ex":
        return VatBasis.EX_TAX
    raise PriceFileError(422, "vat_basis_required",
                         "vat_basis must be stated as 'inc' or 'ex'; it is never guessed")


def _day(value: str | None, name: str) -> date | None:
    if value is None or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        raise PriceFileError(422, f"invalid_{name}", f"{name} must be an ISO date YYYY-MM-DD") \
            from None


@dataclass(frozen=True)
class _Terms:
    merchant: str
    basis: VatBasis
    attested: bool
    observed_at: datetime
    valid_from: date | None
    valid_until: datetime | None
    currency: str | None


def _terms(decl: Declaration, now: datetime, cfg: PricingConfig) -> _Terms:
    if decl.source_kind != SOURCE_KIND_FIELD:
        raise PriceFileError(422, "invalid_source_kind", "source_kind must be customer_price_file")
    try:
        merchant = check_merchant_id(decl.merchant_id)
    except PriceBookError as exc:
        raise PriceFileError(422, "invalid_merchant_id", str(exc)) from None
    basis = _basis(decl.vat_basis)
    start, end = _day(decl.valid_from, "valid_from"), _day(decl.valid_until, "valid_until")
    observed = now
    if start is not None:
        observed = datetime.combine(start, time.min, UTC)
        if observed > now:
            raise PriceFileError(422, "valid_from_in_future",
                                 "valid_from is later than today; upload the file on or after it")
    until = None
    if end is not None:
        until = datetime.combine(end, time(23, 59, 59), UTC)  # inclusive of the named day, UTC
        if start is not None and end < start:
            raise PriceFileError(422, "validity_inverted", "valid_until is before valid_from")
        if until < now:
            raise PriceFileError(422, "valid_until_in_past", "valid_until has already passed")
    currency = (decl.currency or "").strip().upper() or None
    if currency is not None and (_ISO_CUR.fullmatch(currency) is None
                                 or currency not in cfg.accepted_currencies):
        raise PriceFileError(422, "invalid_currency", "currency is not accepted by this deployment")
    return _Terms(merchant, basis, decl.attested, observed, start, until, currency)


# --------------------------------------------------------------------------- reading bytes


def _kind_of(up: Upload) -> str:
    ctype = up.content_type.split(";", 1)[0].strip().lower()
    name = up.filename.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if ctype in CSV_TYPES and name.endswith(".csv"):
        kind = "csv"
    elif ctype == XLSX_TYPE and name.endswith(".xlsx"):
        kind = "xlsx"
    else:
        raise PriceFileError(415, "unsupported_file_type",
                             "only .csv (text/csv) and .xlsx files are accepted")
    if kind == "csv" and (up.data[:2] == b"PK" or b"\x00" in up.data):
        raise PriceFileError(415, "unsupported_file_type", "the file is not a plain CSV")
    if kind == "xlsx" and up.data[:4] != b"PK\x03\x04":
        raise PriceFileError(415, "unsupported_file_type", "the file is not an xlsx workbook")
    return kind


def _csv_rows(data: bytes) -> list[list[str]]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise PriceFileError(422, "not_utf8", "the CSV must be UTF-8") from None
    try:
        return list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error:
        raise PriceFileError(422, "malformed_csv", "the CSV is malformed") from None


def _check_xlsx_zip(data: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = zf.infolist()
            total = sum(i.file_size for i in infos)
            if len(infos) > MAX_ZIP_ENTRIES or total > MAX_UNZIPPED or any(
                    i.compress_size and i.file_size / i.compress_size > MAX_RATIO and
                    i.file_size > 1_000_000 for i in infos):
                raise PriceFileError(422, "archive_too_large", "the workbook is not acceptable")
            for info in infos:
                name = info.filename.lower()
                if any(p in name for p in _FORBIDDEN_PARTS) or name.endswith(".bin"):
                    raise PriceFileError(422, "active_content",
                                         "workbooks with macros, embedded objects or external "
                                         "links are refused")
                if name.endswith(".rels"):
                    if info.file_size > MAX_REL_PART:
                        raise PriceFileError(422, "archive_too_large", "workbook part too large")
                    with zf.open(info) as fh:
                        body = fh.read(MAX_REL_PART + 1)
                    if len(body) > MAX_REL_PART or b'TargetMode="External"' in body \
                            or b"TargetMode='External'" in body:
                        raise PriceFileError(422, "external_reference",
                                             "workbooks with external references are refused")
    except zipfile.BadZipFile:
        raise PriceFileError(415, "unsupported_file_type", "the file is not an xlsx workbook") \
            from None


def _xlsx_rows(up: Upload) -> list[list[str]]:
    _check_xlsx_zip(up.data)
    doc = LocalTextParser(ParserLimits(max_bytes=MAX_FILE_BYTES)).parse(
        up.data, filename=up.filename, content_type=up.content_type)
    bad = [f for f in doc.flags if f.split(":", 1)[0] in ("rejected", "error", "unsupported",
                                                        "truncated")]
    if bad:
        raise PriceFileError(422, "unreadable_workbook", f"the workbook was refused ({bad[0]})")
    if len(doc.tables) != 1:
        raise PriceFileError(422, "one_sheet_only",
                             "the workbook must have exactly one visible sheet")
    return [list(r) for r in doc.tables[0]]


def _table(up: Upload) -> list[list[str]]:
    return _csv_rows(up.data) if _kind_of(up) == "csv" else _xlsx_rows(up)


# --------------------------------------------------------------------------- ingest


def _mapping(header: Sequence[str]) -> CsvMapping:
    present = {h.strip() for h in header}
    cols = {n: n for n in (*CSV_FIELDS, "currency") if n in present}
    try:
        return CsvMapping(columns=cols)
    except PricingError:
        raise PriceFileError(422, "missing_columns",
                             "the file needs a header row with at least sku and a price column "
                             "(price, price_ex_vat or price_inc_vat)") from None


def _origin(filename: str) -> str:
    base = filename.replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"[^A-Za-z0-9._ -]", "_", base)[:60] or "upload"


def _declaration(t: _Terms, tenant_id: str) -> SourceDeclaration:
    return SourceDeclaration(
        licence=LICENCE, confidence=CONFIDENCE, observed_at=t.observed_at, method=METHOD,
        visibility=Visibility.TENANT_PRIVATE, tenant_id=tenant_id, merchant_id=t.merchant,
        default_currency=t.currency, default_vat_basis=t.basis, default_valid_until=t.valid_until,
        price_type=PriceType.TRADE_LIST, account_specific=False, tenant_attested=t.attested)


def _numbered(rows: list[list[str]]) -> tuple[list[list[str]], list[int]]:
    """Drop blank rows but remember each kept row's spreadsheet row number (header = row 1)."""
    kept: list[list[str]] = []
    numbers: list[int] = []
    for n, row in enumerate(rows, start=1):
        if any(c.strip() for c in row):
            while row and not row[-1].strip():  # sheet dimensions pad rows with empty cells
                row = row[:-1]
            kept.append(row)
            numbers.append(n)
    return kept, numbers


@dataclass(frozen=True)
class _Parsed:
    offers: tuple[Any, ...]
    quarantine: tuple[dict[str, Any], ...]
    rows: int


def _parse(up: Upload, terms: _Terms, tenant_id: str, cfg: PricingConfig, load_id: str) -> _Parsed:
    rows, numbers = _numbered(_table(up))
    if len(rows) < 2:
        raise PriceFileError(422, "empty_file", "the file has no data rows")
    try:
        source = CsvPriceFileSource(rows, _mapping(rows[0]), source_id=load_id,
                                    kind=SourceKind.TRADE_FEED, origin=_origin(up.filename))
        report = ingest(source, OfferQuery(), _declaration(terms, tenant_id), cfg)
    except PricingError as exc:
        raise PriceFileError(422, "unreadable_file", _safe_message(exc)) from None
    skus = {r.index: str(r.fields.get("sku", "")) for r in source.fetch(OfferQuery())}
    quarantine = [_q(q.index, numbers, q.reasons, skus) for q in report.quarantined]
    offers = []
    for o in report.offers:
        if o.price.vat_basis is VatBasis.UNKNOWN:  # a row's own unreadable basis text: never guess
            m = _ROW.search(o.source_ref)
            idx = int(m.group(1)) if m else 0
            quarantine.append(_q(idx, numbers, ("vat_basis_unknown",), skus))
        else:
            offers.append(o)
    quarantine.sort(key=lambda q: q["row"])
    return _Parsed(tuple(offers), tuple(quarantine), len(rows) - 1)


def _safe_message(exc: Exception) -> str:
    return re.sub(r"[^A-Za-z0-9 ,.:;()'_-]", "?", str(exc))[:160]


def _q(index: int, numbers: list[int], reasons: Sequence[str],
       skus: dict[int, str]) -> dict[str, Any]:
    row = numbers[index] if 0 < index < len(numbers) else index
    sku = skus.get(index, "")
    return {"row": row, "reasons": list(reasons), "sku": echo(sku) if sku else ""}


# --------------------------------------------------------------------------- the load


def load_price_file(svc: QuoteService, ctx: Ctx, up: Upload, decl: Declaration
                    ) -> dict[str, Any]:
    if len(up.data) > MAX_FILE_BYTES:
        raise PriceFileError(413, "payload_too_large", "file too large")
    if not up.data:
        raise PriceFileError(422, "empty_file", "the file is empty")
    now = svc.clock.now()
    terms = _terms(decl, now, svc.pricing)
    load_id = f"pf-{uuid.uuid4().hex[:20]}"
    parsed = _parse(up, terms, ctx.tenant_id, svc.pricing, load_id)
    repo = svc.stores.offers.for_tenant(ctx.tenant_id)
    superseded = 0
    if parsed.offers:
        prior = _prior(repo, ctx.tenant_id, terms.merchant)
        if prior and max(o.observed_at for o in prior) > terms.observed_at:
            raise PriceFileError(409, "older_than_loaded",
                                 "a price file with a newer price date is already loaded for "
                                 "this merchant")
        repo.add_many(parsed.offers)
        superseded = sum(1 for o in prior if repo.remove(o.offer_id))
    summary = ImportSummary(terms.merchant, ctx.tenant_id, "tenant_private", len(parsed.offers),
                            len(parsed.quarantine))
    svc.stores.imports.for_tenant(ctx.tenant_id).add(summary)
    firm = sum(1 for o in parsed.offers if not o.is_indicative)
    svc.events.append(ctx.tenant_id, "price_file_loaded", load_id, {
        "actor": ctx.actor, "merchant_id": terms.merchant, "offers": len(parsed.offers),
        "firm_offers": firm, "quarantined": len(parsed.quarantine), "superseded": superseded,
        "vat_basis": terms.basis.value, "attested": terms.attested,
        "valid_from": decl.valid_from or None, "valid_until": decl.valid_until or None,
        "sha256": hashlib.sha256(up.data).hexdigest(), "bytes": len(up.data),
        "source_kind": SOURCE_KIND_FIELD})
    return _response(load_id, summary, parsed, terms, firm, superseded)


def _prior(repo: Any, tenant_id: str, merchant: str) -> list[Any]:
    found = repo.search(OfferFilter(merchant_ids=frozenset({merchant}),
                                    source_kinds=frozenset({SourceKind.TRADE_FEED}),
                                    limit=MAX_LIMIT))
    return [o for o in found if o.tenant_id == tenant_id and o.provenance.method == METHOD]


def _reasons(terms: _Terms, offers: int, firm: int) -> list[str]:
    out = []
    if not terms.attested:
        out.append("not_attested")
    if offers and firm == 0 and terms.attested:
        out.append("no_validity")
    return out


def _response(load_id: str, summary: ImportSummary, parsed: _Parsed, terms: _Terms, firm: int,
              superseded: int) -> dict[str, Any]:
    offers = len(parsed.offers)
    counts: dict[str, int] = {}
    for q in parsed.quarantine:
        for r in q["reasons"]:
            counts[r] = counts.get(r, 0) + 1
    return {
        "load_id": load_id,
        "summary": {"merchant_id": summary.merchant_id, "tenant_id": summary.tenant_id,
                    "visibility": summary.visibility, "offers": summary.offers,
                    "quarantined": summary.quarantined},
        "counts": {"rows": parsed.rows, "accepted": offers, "firm": firm,
                   "indicative": offers - firm, "quarantined": len(parsed.quarantine),
                   "superseded_offers": superseded},
        "status": "firm" if firm else "indicative_only",
        "indicative_reasons": [] if firm == offers else _reasons(terms, offers, firm) or
        ["not_eligible"],
        "vat_basis": "inc" if terms.basis is VatBasis.INC_TAX else "ex",
        "attested": terms.attested,
        "valid_from": terms.valid_from.isoformat() if terms.valid_from else None,
        "valid_until": terms.valid_until.isoformat() if terms.valid_until else None,
        "price_date": terms.observed_at.isoformat(),
        "reason_counts": dict(sorted(counts.items())),
        "quarantine": list(parsed.quarantine[:MAX_QUARANTINE_ECHO]),
        "quarantine_truncated": len(parsed.quarantine) > MAX_QUARANTINE_ECHO,
        "notes": ["Prices are private to your organisation and are never pooled or shared.",
                  "The file itself was not kept."],
    }


def list_loads(svc: QuoteService, ctx: Ctx) -> list[dict[str, Any]]:
    own = [s for s in svc.stores.imports.for_tenant(ctx.tenant_id).list()
           if s.tenant_id == ctx.tenant_id]
    return [{"seq": i + 1, "merchant_id": neutralise(s.merchant_id), "visibility": s.visibility,
             "offers": s.offers, "quarantined": s.quarantined} for i, s in enumerate(own)]
