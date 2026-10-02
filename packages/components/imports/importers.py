"""CSV importers for parts lists, asset lists and PO history (stack-map U11, spec F5/F11).

Each importer returns an ``ImportResult``: typed accepted rows plus reject-with-reason entries.
``ImportResult.summary()`` is a plain dict compatible with
``employees.purchasing.views.ImportSummary`` (rows, accepted, rejected, errors).
Nothing is written anywhere here; persistence is the caller's job through tenant repositories.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from components.core.domain import UoM, Vendor

from .safety import clean_text, echo
from .vendors import VendorIndex

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 50_000
MAX_CELL = 2_000
MAX_COLS = 100
MAX_PRICE = Decimal("100000000")
CURRENCIES = frozenset({"USD", "CAD", "EUR", "GBP", "MXN"})

_UOM_ALIASES = {
    "each": UoM.EACH, "ea": UoM.EACH, "pc": UoM.EACH, "pcs": UoM.EACH, "piece": UoM.EACH,
    "unit": UoM.EACH, "1": UoM.EACH,
    "per_100": UoM.PER_100, "per 100": UoM.PER_100, "100": UoM.PER_100, "c": UoM.PER_100,
    "hundred": UoM.PER_100, "/100": UoM.PER_100,
    "per_1000": UoM.PER_1000, "per 1000": UoM.PER_1000, "1000": UoM.PER_1000,
    "m": UoM.PER_1000, "/1000": UoM.PER_1000,
}


@dataclass(frozen=True)
class PartRow:
    row: int
    part_number: str
    description: str
    manufacturer: str | None
    uom: UoM
    min_order_qty: int | None


@dataclass(frozen=True)
class AssetRow:
    row: int
    asset_tag: str
    name: str
    site: str | None
    location: str | None
    critical: bool


@dataclass(frozen=True)
class PoHistoryRow:
    row: int
    po_number: str
    vendor_id: str
    part_number: str
    quantity: int
    unit_price: Decimal
    currency: str
    uom: UoM
    po_date: date


@dataclass(frozen=True)
class RowError:
    row: int
    field: str
    reason: str
    value: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"row": self.row, "field": self.field, "reason": self.reason, "value": self.value}


@dataclass
class ImportResult:
    kind: str
    accepted: list[Any] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)
    rows: int = 0
    rejected_rows: int = 0
    flags: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "accepted": len(self.accepted),
            "rejected": self.rejected_rows,
            "errors": [e.as_dict() for e in self.errors],
        }


class _Reject(Exception):  # noqa: N818 - control flow inside one row
    def __init__(self, field_: str, reason: str, value: object = "") -> None:
        self.field, self.reason, self.value = field_, reason, value


# ------------------------------------------------------------------ csv reading

def _norm_header(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", h.casefold()).strip("_")


def _read(content: bytes, aliases: dict[str, tuple[str, ...]], required: Iterable[str],
          result: ImportResult) -> list[tuple[int, dict[str, str]]] | None:
    if len(content) > MAX_BYTES:
        result.errors.append(RowError(0, "file", "file_too_large"))
        return None
    if b"\x00" in content:
        result.errors.append(RowError(0, "file", "binary_content"))
        return None
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("cp1252", errors="replace")
        result.flags.append("decoded_as_cp1252")
    head = text[:4096].split("\n", 1)[0]
    delim = max((",", ";", "\t"), key=head.count)
    csv.field_size_limit(MAX_CELL * 4)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delim)
    try:
        header = next(reader)
    except (StopIteration, csv.Error):
        result.errors.append(RowError(0, "file", "empty_file"))
        return None
    index: dict[str, int] = {}
    for canon, names in aliases.items():
        for i, h in enumerate(header[:MAX_COLS]):
            if _norm_header(h) in (canon, *names):
                index.setdefault(canon, i)
    missing = [c for c in required if c not in index]
    if missing:
        result.errors.append(RowError(0, "header", "missing_columns:" + ",".join(missing)))
        return None
    out: list[tuple[int, dict[str, str]]] = []
    try:
        for n, rec in enumerate(reader, start=2):  # row numbers match the spreadsheet
            if not any(c.strip() for c in rec):
                continue
            if len(out) >= MAX_ROWS:
                result.flags.append("truncated:max_rows")
                break
            out.append((n, {k: (rec[i].strip() if i < len(rec) else "") for k, i in index.items()}))
    except csv.Error:
        result.flags.append("error:malformed_csv")
    return out


# ------------------------------------------------------------------ field parsers

def _text(rec: dict[str, str], key: str, *, required: bool = True, limit: int = 500) -> str | None:
    raw = rec.get(key, "")
    if len(raw) > MAX_CELL:
        raise _Reject(key, "cell_too_long")
    val = clean_text(raw, limit=limit)
    if not val:
        if required:
            raise _Reject(key, "required", raw)
        return None
    return val


def parse_money(raw: str, field_: str = "unit_price") -> Decimal:
    s = raw.strip().replace(",", "").replace("$", "").replace("€", "").replace("£", "")
    s = s.strip()
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        raise _Reject(field_, "invalid_amount", raw)
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise _Reject(field_, "invalid_amount", raw) from None
    if d <= 0 or d > MAX_PRICE or -d.as_tuple().exponent > 6:  # type: ignore[operator]
        raise _Reject(field_, "amount_out_of_range", raw)
    return d


def parse_uom(raw: str, default: UoM | None) -> UoM:
    key = raw.strip().casefold()
    if not key:
        if default is None:
            raise _Reject("uom", "uom_required")
        return default
    try:
        return _UOM_ALIASES[key]
    except KeyError:
        raise _Reject("uom", "unknown_uom", raw) from None


def parse_int(raw: str, field_: str, *, minimum: int = 1, maximum: int = 10_000_000) -> int:
    s = raw.strip().replace(",", "")
    if not re.fullmatch(r"\d+(\.0+)?", s):
        raise _Reject(field_, "invalid_integer", raw)
    n = int(s.split(".")[0])
    if not minimum <= n <= maximum:
        raise _Reject(field_, "out_of_range", raw)
    return n


def parse_date(raw: str) -> date:
    s = raw.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):  # no day-first guessing: ambiguous dates are not accepted
        try:
            return datetime.strptime(s, fmt).date()  # noqa: DTZ007
        except ValueError:
            continue
    raise _Reject("po_date", "invalid_date", raw)


def _currency(rec: dict[str, str], default: str | None) -> str:
    cur = (rec.get("currency", "") or default or "").strip().upper()
    if not cur:
        raise _Reject("currency", "currency_required")
    if cur not in CURRENCIES:
        raise _Reject("currency", "unknown_currency", cur)
    return cur


# ------------------------------------------------------------------ driver

def _run(result: ImportResult, rows: list[tuple[int, dict[str, str]]] | None,
         build: Callable[[int, dict[str, str]], Any]) -> ImportResult:
    if rows is None:
        return result
    for n, rec in rows:
        result.rows += 1
        try:
            result.accepted.append(build(n, rec))
        except _Reject as r:
            result.rejected_rows += 1
            result.errors.append(RowError(n, r.field, r.reason, echo(r.value) if r.value != ""
                                          else ""))
    return result


def import_parts(content: bytes) -> ImportResult:
    result = ImportResult("parts")
    seen: set[str] = set()
    aliases = {
        "part_number": ("part", "part_no", "mpn", "item", "item_number", "sku"),
        "description": ("desc", "item_description", "name"),
        "manufacturer": ("mfr", "mfg", "brand", "make"),
        "uom": ("unit", "unit_of_measure", "price_uom"),
        "min_order_qty": ("moq", "min_qty"),
    }

    def build(n: int, rec: dict[str, str]) -> PartRow:
        pn = _text(rec, "part_number", limit=80)
        assert pn is not None
        key = pn.casefold()
        if key in seen:
            raise _Reject("part_number", "duplicate_in_file", pn)
        desc = _text(rec, "description") or ""
        mfr = _text(rec, "manufacturer", required=False, limit=120)
        uom = parse_uom(rec.get("uom", ""), UoM.EACH)
        moq = parse_int(rec["min_order_qty"], "min_order_qty") if rec.get("min_order_qty") else None
        seen.add(key)
        return PartRow(n, pn, desc, mfr, uom, moq)

    return _run(result, _read(content, aliases, ("part_number", "description"), result), build)


def import_assets(content: bytes) -> ImportResult:
    result = ImportResult("assets")
    seen: set[str] = set()
    aliases = {
        "asset_tag": ("tag", "asset_id", "asset", "equipment_id", "asset_number"),
        "name": ("asset_name", "description", "equipment"),
        "site": ("plant", "facility"),
        "location": ("area", "line"),
        "critical": ("criticality", "is_critical"),
    }

    def build(n: int, rec: dict[str, str]) -> AssetRow:
        tag = _text(rec, "asset_tag", limit=80)
        assert tag is not None
        if tag.casefold() in seen:
            raise _Reject("asset_tag", "duplicate_in_file", tag)
        name = _text(rec, "name") or ""
        crit = rec.get("critical", "").strip().casefold()
        if crit not in ("", "y", "yes", "true", "1", "n", "no", "false", "0", "high", "low",
                        "medium", "critical"):
            raise _Reject("critical", "invalid_flag", crit)
        seen.add(tag.casefold())
        return AssetRow(n, tag, name, _text(rec, "site", required=False, limit=120),
                        _text(rec, "location", required=False, limit=120),
                        crit in ("y", "yes", "true", "1", "high", "critical"))

    return _run(result, _read(content, aliases, ("asset_tag", "name"), result), build)


def import_po_history(
    content: bytes, vendors: Iterable[Vendor], *, default_currency: str | None = None,
    default_uom: UoM | None = None,
) -> ImportResult:
    """``vendors`` must be the importing tenant's vendors (read via the tenant-scoped repo)."""
    result = ImportResult("po_history")
    index = VendorIndex(vendors)
    aliases = {
        "po_number": ("po", "po_no", "purchase_order", "order_number"),
        "vendor": ("supplier", "vendor_name", "supplier_name"),
        "part_number": ("part", "part_no", "mpn", "item", "item_number", "sku"),
        "quantity": ("qty", "quantity_ordered"),
        "unit_price": ("price", "unit_cost", "cost"),
        "currency": ("curr", "currency_code"),
        "uom": ("unit", "price_uom", "unit_of_measure"),
        "po_date": ("date", "order_date", "ordered"),
    }

    def build(n: int, rec: dict[str, str]) -> PoHistoryRow:
        po = _text(rec, "po_number", limit=60)
        pn = _text(rec, "part_number", limit=80)
        vname = _text(rec, "vendor", limit=200)
        assert po and pn and vname
        vendor_id, why = index.match(vname)
        if vendor_id is None:
            raise _Reject("vendor", why or "unknown_vendor", vname)
        return PoHistoryRow(
            n, po, vendor_id, pn, parse_int(rec.get("quantity", ""), "quantity"),
            parse_money(rec.get("unit_price", "")), _currency(rec, default_currency),
            parse_uom(rec.get("uom", ""), default_uom), parse_date(rec.get("po_date", "")),
        )

    required = ("po_number", "vendor", "part_number", "quantity", "unit_price", "po_date")
    return _run(result, _read(content, aliases, required, result), build)
