# ruff: noqa: E501
"""Pure rules: stop-request detection and the supplier CSV parser (FR-SU-1).

Both treat their input as untrusted text. The CSV parser never raises for a bad ROW: every data row is
either returned as a ``VendorRow`` or listed in ``rejected`` with its row number and a fixed reason
that does not echo the offending value. Only a problem with the FILE (not UTF-8, bad header, too many
rows) raises ``ValueError``. Row numbers match a spreadsheet: the header is row 1.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import get_args

from components.send_service.message import is_plain_line

from .models import AccountType, ContactKind

REQUIRED = ("name", "domain", "contact_email")
OPTIONAL = ("phone", "account_number", "account_type", "credit_days", "quote_validity_days",
            "contact_kind")
COLUMNS = (*REQUIRED, *OPTIONAL)
MAX_VALUE = 200
MAX_EMAIL = 254
MAX_DOMAIN = 253

_STOP = re.compile(r"^(?:please\s+)?(?:stop|unsubscribe|remove\s+me)(?:\s+please)?$")
_TRAILING = re.compile(r"[\s.!,;:]+$")
_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+$")


def is_stop_request(text: object) -> bool:
    """True when a reply is nothing but a stop request: "stop", "unsubscribe" or "remove me"
    (case-insensitive, with an optional "please" and trailing punctuation). A quote that merely
    contains the word is not a stop request."""
    if not isinstance(text, str) or len(text) > 100:  # noqa: PLR2004
        return False
    cleaned = _TRAILING.sub("", " ".join(text.lower().split()))
    return bool(_STOP.match(cleaned))


@dataclass(frozen=True)
class VendorRow:
    row: int
    name: str
    domain: str
    contact_email: str
    phone: str | None = None
    account_number: str | None = None
    account_type: AccountType | None = None
    credit_days: int | None = None
    quote_validity_days: int | None = None
    contact_kind: ContactKind | None = None


@dataclass(frozen=True)
class RejectedRow:
    row: int
    reason: str


@dataclass
class ParsedVendors:
    rows: list[VendorRow] = field(default_factory=list)
    rejected: list[RejectedRow] = field(default_factory=list)


class _BadCell(Exception):  # noqa: N818 - carries the column name only
    pass


def valid_domain(value: str) -> bool:
    if not value or len(value) > MAX_DOMAIN or value != value.lower() or not value.isascii():
        return False
    labels = value.split(".")
    return len(labels) >= 2 and all(_LABEL.match(label) for label in labels)  # noqa: PLR2004


def valid_email(value: str) -> bool:
    if not value or len(value) > MAX_EMAIL or not value.isascii():
        return False
    local, _, domain = value.rpartition("@")
    return bool(_EMAIL.match(value)) and bool(local) and ".." not in value and valid_domain(
        domain.lower())


def _text(cells: dict[str, str], name: str, *, required: bool = False) -> str | None:
    raw = cells.get(name, "").strip()
    if not raw:
        if required:
            raise _BadCell(name)
        return None
    if len(raw) > MAX_VALUE or not is_plain_line(raw):
        raise _BadCell(name)
    return raw


def _int(cells: dict[str, str], name: str, low: int, high: int) -> int | None:
    raw = _text(cells, name)
    if raw is None:
        return None
    if not raw.isascii() or not raw.isdigit() or not low <= int(raw) <= high:
        raise _BadCell(name)
    return int(raw)


def _choice(cells: dict[str, str], name: str, allowed: tuple[str, ...]) -> str | None:
    raw = _text(cells, name)
    if raw is None:
        return None
    if raw.lower() not in allowed:
        raise _BadCell(name)
    return raw.lower()


def _row(number: int, cells: dict[str, str]) -> VendorRow:
    name = _text(cells, "name", required=True)
    domain = (_text(cells, "domain", required=True) or "").lower()
    email = (_text(cells, "contact_email", required=True) or "").lower()
    if not valid_domain(domain):
        raise _BadCell("domain")
    if not valid_email(email):
        raise _BadCell("contact_email")
    assert name is not None
    return VendorRow(
        row=number, name=name, domain=domain, contact_email=email,
        phone=_text(cells, "phone"), account_number=_text(cells, "account_number"),
        account_type=_choice(cells, "account_type", get_args(AccountType)),  # type: ignore[arg-type]
        credit_days=_int(cells, "credit_days", 0, 3650),
        quote_validity_days=_int(cells, "quote_validity_days", 1, 3650),
        contact_kind=_choice(cells, "contact_kind", get_args(ContactKind)),  # type: ignore[arg-type]
    )


def _header(first: list[str]) -> list[str]:
    names = [c.strip().lower() for c in first]
    if len(set(names)) != len(names):
        raise ValueError("duplicate column in header")
    unknown = [n for n in names if n not in COLUMNS]
    if unknown:
        raise ValueError(f"unknown column(s): {', '.join(_safe(u) for u in unknown)}")
    missing = [c for c in REQUIRED if c not in names]
    if missing:
        raise ValueError(f"missing required column(s): {', '.join(missing)}")
    return names


def _safe(name: str) -> str:
    return name[:40] if is_plain_line(name) and name.isprintable() else "?"


def parse_vendor_csv(data: bytes, *, max_rows: int) -> ParsedVendors:
    """Parse a supplier CSV. Raises ``ValueError`` for a file-level problem."""
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("not a UTF-8 CSV file") from exc
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        first = next(reader)
    except StopIteration:
        raise ValueError("the file is empty: a header row is required") from None
    except csv.Error as exc:
        raise ValueError("not a readable CSV file") from exc
    names = _header(first)
    out = ParsedVendors()
    seen = 0
    while True:
        start = reader.line_num + 1
        try:
            cells = next(reader)
        except StopIteration:
            break
        except csv.Error:
            out.rejected.append(RejectedRow(start, "unreadable CSV row"))
            break
        if not cells:  # a blank line is not a row
            continue
        seen += 1
        if seen > max_rows:
            raise ValueError(f"too many rows (at most {max_rows})")
        if len(cells) != len(names):
            out.rejected.append(RejectedRow(start, f"expected {len(names)} cells, found {len(cells)}"))
            continue
        try:
            out.rows.append(_row(start, dict(zip(names, cells, strict=True))))
        except _BadCell as bad:
            out.rejected.append(RejectedRow(start, f"{bad}: missing, too long, or not valid"))
    return out
