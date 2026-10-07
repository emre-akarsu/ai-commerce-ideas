"""The two offline source adapters. Both work on data HANDED to them (spec R7: no fetching):

* `CsvPriceFileSource`: a merchant price file or affiliate-feed CSV as text or bytes (or a table of
  rows, e.g. an Excel sheet already parsed in the no-network sandbox by `components.doc_parse`),
  with a configurable column mapping, an ex/inc-VAT price column and a pack-size column.
* `JsonShoppingResultsSource`: pasted search-result style JSON; always `search_snapshot` (so
  indicative only, whatever the payload claims about itself).

Nothing reads a file, the network or the clock. Titles and URLs are never read or stored. Sizes are
bounded; a payload that cannot be read at all raises `SourceError`, one bad record is quarantined
later by `parse_raw_offer`.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from .errors import SourceError
from .models import SourceKind
from .sources import CANONICAL_FIELDS, INVALID_RECORD, OfferQuery, RawRecord
from .text import check_id, clean_text

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 50_000
MAX_COLS = 100
MAX_RESULTS = 5_000
_ORIGIN_MAX = 60


def _origin(label: str) -> str:
    """The file label shown in provenance; a link in it is replaced like any other text."""
    return clean_text(label, "origin", _ORIGIN_MAX) or "upload"


def _to_text(payload: str | bytes, what: str) -> str:
    if isinstance(payload, bytes):
        if len(payload) > MAX_BYTES:
            raise SourceError(f"{what} is too large")
        try:
            return payload.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise SourceError(f"{what} is not valid UTF-8") from None
    if not isinstance(payload, str):
        raise SourceError(f"{what} must be text or bytes")
    if len(payload) > MAX_BYTES:
        raise SourceError(f"{what} is too large")
    return payload


@dataclass(frozen=True)
class CsvMapping:
    """`columns` maps canonical field names to the file's column headers; `fixed` gives canonical
    fields a constant for the whole file (for example the currency or VAT basis it declares)."""

    columns: Mapping[str, str]
    fixed: Mapping[str, str] | None = None
    delimiter: str = ","

    def __post_init__(self) -> None:
        fixed = self.fixed or {}
        unknown = sorted((set(self.columns) | set(fixed)) - CANONICAL_FIELDS)
        if unknown:
            raise SourceError(
                f"unknown fields {unknown}: titles and links are never read, so they cannot be "
                "mapped")
        if "sku" not in self.columns:
            raise SourceError("the mapping needs a sku column")
        if not ({"price", "price_ex_vat", "price_inc_vat"} & (set(self.columns) | set(fixed))):
            raise SourceError("the mapping needs a price column")
        if len(self.delimiter) != 1 or self.delimiter in "\r\n\"":
            raise SourceError("the delimiter must be a single plain character")


def _records(
    rows: Sequence[Sequence[str]], mapping: CsvMapping, origin: str
) -> list[RawRecord]:
    if not rows:
        raise SourceError("the table is empty")
    if len(rows) - 1 > MAX_ROWS or any(len(r) > MAX_COLS for r in rows[:1]):
        raise SourceError("the table has too many rows or columns")
    header = [h.strip() for h in rows[0]]
    if len(set(header)) != len(header):
        raise SourceError("duplicate column headers")
    missing = sorted(set(mapping.columns.values()) - set(header))
    if missing:
        raise SourceError(f"mapped columns not found in the file: {missing}")
    position = {name: header.index(col) for name, col in mapping.columns.items()}
    label = _origin(origin)
    out: list[RawRecord] = []
    for number, row in enumerate(rows[1:], start=1):
        fields: dict[str, object] = dict(mapping.fixed or {})
        for name, pos in position.items():
            if pos < len(row) and row[pos].strip():
                fields[name] = row[pos]
        out.append(RawRecord(number, label, fields))
    return out


class CsvPriceFileSource:
    """An `OfferSource` over a CSV (or an already parsed table) that was handed in."""

    def __init__(
        self, payload: str | bytes | Sequence[Sequence[str]], mapping: CsvMapping, *,
        source_id: str, kind: SourceKind, origin: str = "upload",
    ) -> None:
        self._id = check_id(source_id, "source_id")
        if not isinstance(kind, SourceKind) or kind is SourceKind.SEARCH_SNAPSHOT:
            raise SourceError("a CSV file is a trade, API, affiliate or manual source")
        self._kind = kind
        self._records = (
            self.parse_rows(payload, mapping, origin=origin)
            if isinstance(payload, Sequence) and not isinstance(payload, str | bytes)
            else self.parse(payload, mapping, origin=origin)
        )

    @property
    def source_id(self) -> str:
        return self._id

    @property
    def kind(self) -> SourceKind:
        return self._kind

    @staticmethod
    def parse(
        payload: str | bytes, mapping: CsvMapping, *, origin: str = "upload"
    ) -> list[RawRecord]:
        text = _to_text(payload, "CSV payload")
        try:
            rows = list(csv.reader(io.StringIO(text), delimiter=mapping.delimiter, strict=True))
        except csv.Error:
            raise SourceError("the CSV is malformed") from None
        return _records([r for r in rows if r], mapping, origin)

    @staticmethod
    def parse_rows(
        rows: Sequence[Sequence[str]], mapping: CsvMapping, *, origin: str = "table"
    ) -> list[RawRecord]:
        """A table (first row = headers), e.g. a sheet parsed in the no-network sandbox."""
        if not all(isinstance(c, str) for r in rows for c in r):
            raise SourceError("table cells must be text")
        return _records(rows, mapping, origin)

    def fetch(self, query: OfferQuery) -> list[RawRecord]:
        if not query.sku_ids:
            return list(self._records)
        wanted = set(query.sku_ids)
        return [r for r in self._records if r.fields.get("sku") in wanted]


_JSON_FIELDS = {
    "merchant": "merchant", "seller": "merchant", "price": "price", "currency": "currency",
    "availability": "stock", "pack_size": "pack_size", "pack_unit": "pack_unit",
}


def _reject_constant(name: str) -> None:
    raise SourceError(f"JSON constant {name} is not allowed")


class JsonShoppingResultsSource:
    """An `OfferSource` over pasted search-result JSON: ``{"results": [{...}, ...]}``.

    Results are attached to `query_sku_id`, the SKU the search was run for; their relevance is NOT
    verified, which is exactly why they are always `search_snapshot` (indicative only). Numbers are
    read as Decimal (never float); titles, snippets and links are never read."""

    def __init__(
        self, payload: str | bytes, *, source_id: str, query_sku_id: str, origin: str = "json"
    ) -> None:
        self._id = check_id(source_id, "source_id")
        self._records = self.parse(payload, query_sku_id=query_sku_id, origin=origin)

    @property
    def source_id(self) -> str:
        return self._id

    @property
    def kind(self) -> SourceKind:
        return SourceKind.SEARCH_SNAPSHOT

    @staticmethod
    def parse(
        payload: str | bytes, *, query_sku_id: str, origin: str = "json"
    ) -> list[RawRecord]:
        check_id(query_sku_id, "query_sku_id")
        text = _to_text(payload, "JSON payload")
        try:
            data = json.loads(text, parse_float=Decimal, parse_int=int,
                              parse_constant=_reject_constant)
        except (json.JSONDecodeError, RecursionError):
            raise SourceError("the JSON is malformed") from None
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list):
            raise SourceError("expected an object with a results list")
        if len(results) > MAX_RESULTS:
            raise SourceError("too many results")
        label = _origin(origin)
        out: list[RawRecord] = []
        for number, item in enumerate(results, start=1):
            if not isinstance(item, dict):
                out.append(RawRecord(number, label, {INVALID_RECORD: "1"}))
                continue
            fields: dict[str, object] = {"sku": query_sku_id}
            for key, canonical in _JSON_FIELDS.items():
                if key in item:
                    fields[canonical] = item[key]
            out.append(RawRecord(number, label, fields))
        return out

    def fetch(self, query: OfferQuery) -> list[RawRecord]:
        if query.sku_ids and not set(query.sku_ids) & {r.fields["sku"] for r in self._records}:
            return []
        return list(self._records)
