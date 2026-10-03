"""Rule-based quote parser (FR-7, FR-8, FR-13, AI-7). Inbound text is untrusted data: it is read, never obeyed.

Every extracted field keeps the exact source span. Anything the rules cannot read stays empty and is chased;
nothing is guessed.
"""

from __future__ import annotations

import math
import re
from datetime import date, timedelta
from decimal import Decimal

from .model import VAT_RATE, Quote, QuoteLine

_MONEY = r"£\s?([\d,]+(?:\.\d{1,2})?)"
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_INJECTION = re.compile(
    r"ignore (?:all |any )?(?:previous|prior|above) (?:rules|instructions)|system\s*:|"
    r"mark (?:this|the) quote (?:as )?approved|you must (?:now )?accept|disregard (?:the )?(?:policy|mandate)",
    re.I)
_BANK_TERMS = re.compile(r"sort\s*code|account\s*(?:no|number)|iban|bank details", re.I)
_BANK_CHANGE = re.compile(r"chang|new |updat|amend|instead|no longer", re.I)
_NOT_LINE = re.compile(r"total|vat|deposit|balance|subtotal|sub-total|payment|valid", re.I)


def _money(s: str) -> Decimal:
    return Decimal(s.replace(",", ""))


def _first(pattern: str, text: str, flags: int = re.I | re.M) -> re.Match[str] | None:
    return re.search(pattern, text, flags)


def parse_quote(text: str, rfq_id: str, supplier_id: str, channel: str, received: date) -> Quote:
    q = Quote(rfq_id=rfq_id, supplier_id=supplier_id, channel=channel, received=received)

    if _INJECTION.search(text):
        q.flags.append("instruction_in_mail")
        q.spans["instruction_in_mail"] = _INJECTION.search(text).group(0)  # type: ignore[union-attr]
        q.quarantined = True
    if _BANK_TERMS.search(text) and _BANK_CHANGE.search(text):
        q.flags.append("bank_details_change")
        q.spans["bank_details_change"] = _BANK_TERMS.search(text).group(0)  # type: ignore[union-attr]
        q.quarantined = True

    lines = []
    for raw in text.splitlines():
        m = re.match(rf"^\s*[-*•]?\s*(.+?)\s*[:\-–—]?\s*{_MONEY}\s*(?:\+\s*VAT|ex\s*VAT)?\s*$", raw, re.I)
        if m and not _NOT_LINE.search(m.group(1)) and len(m.group(1)) > 3:
            lines.append(QuoteLine(m.group(1).strip(" :-"), _money(m.group(2))))
    q.lines = tuple(lines)

    total = None
    for m in re.finditer(rf"^.*\b(?:total|all in|price|quote)\b[^\n£]*{_MONEY}[^\n]*$", text, re.I | re.M):
        if re.search(r"sub-?total|deposit", m.group(0), re.I):
            continue
        total = m
    if total is None:
        m2 = _first(rf"{_MONEY}\s*(?:\+\s*VAT|plus VAT|inc(?:l|luding)?\.? VAT|all in)", text)
        total = m2
    if total is not None:
        q.total_stated = _money(total.group(1))
        q.spans["total"] = total.group(0).strip()
        q.confidence["total"] = 0.97

    basis_src = (total.group(0) if total is not None else "") + "\n" + text
    after = total.group(0)[total.end(1) - total.start():] if total is not None else ""
    if re.match(r"\s*(?:\+\s*vat|plus vat|ex(?:cl(?:uding)?)?\.?\s*vat)", after, re.I):
        q.vat_basis, q.spans["vat_basis"] = "ex", after.strip()[:12].strip()
    elif re.match(r"\s*(?:inc(?:l|luding|lusive)?\.?\s*(?:of\s*)?vat)", after, re.I):
        q.vat_basis, q.spans["vat_basis"] = "inc", after.strip()[:14].strip()
    elif re.search(r"not vat registered|no vat", text, re.I):
        q.vat_basis, q.spans["vat_basis"] = "none", _first(r"not vat registered|no vat", text).group(0)  # type: ignore[union-attr]
    elif re.search(r"inc(?:l|luding|lusive)?\.?\s*(?:of\s*)?vat|vat inc", basis_src, re.I):
        q.vat_basis, q.spans["vat_basis"] = "inc", _first(r"inc(?:l|luding|lusive)?\.?\s*(?:of\s*)?vat|vat inc", basis_src).group(0)  # type: ignore[union-attr]
    elif re.search(r"\+\s*vat|plus vat|ex(?:cl(?:uding)?)?\.?\s*vat|vat extra", basis_src, re.I):
        q.vat_basis, q.spans["vat_basis"] = "ex", _first(r"\+\s*vat|plus vat|ex(?:cl(?:uding)?)?\.?\s*vat|vat extra", basis_src).group(0)  # type: ignore[union-attr]
    if q.vat_basis != "unknown":
        q.confidence["vat_basis"] = 0.95

    if q.total_stated is not None:
        if q.vat_basis == "inc":
            q.total_ex_vat = (q.total_stated / (1 + VAT_RATE)).quantize(Decimal("0.01"))
        elif q.vat_basis in ("ex", "none"):
            q.total_ex_vat = q.total_stated
        # unknown basis: no normalised price; a human decides (never assume)

    text_lt = text.replace("approx.", "approx")
    m = _first(r"(?:start|lead time|available|ready|completed?|turnaround)[^.\n]*?(\d+)\s*(working days|days|weeks?)", text_lt)
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        q.lead_time_days = n * 7 if unit.startswith("week") else (math.ceil(n * 7 / 5) if "working" in unit else n)
        q.spans["lead_time"] = m.group(0).strip()
        q.confidence["lead_time"] = 0.9
    else:
        m = _first(r"w/c\s*(\d{1,2})(?:st|nd|rd|th)?\s*([a-z]{3})", text)
        if m and m.group(2).lower() in _MONTHS:
            d = date(received.year, _MONTHS[m.group(2).lower()], int(m.group(1)))
            if d < received:
                d = d.replace(year=d.year + 1)
            q.lead_time_days = (d - received).days
            q.spans["lead_time"] = m.group(0)
            q.confidence["lead_time"] = 0.9

    m = _first(r"valid (?:for|up to)\s+(\d+)\s*days", text)
    if m:
        q.valid_until = received + timedelta(days=int(m.group(1)))
        q.spans["valid_until"] = m.group(0)
        q.confidence["valid_until"] = 0.95
    else:
        m = _first(r"valid (?:until|to)\s+(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]{3})[a-z]*\s+(\d{4})", text)
        if m and m.group(2).lower() in _MONTHS:
            q.valid_until = date(int(m.group(3)), _MONTHS[m.group(2).lower()], int(m.group(1)))
            q.spans["valid_until"] = m.group(0)
            q.confidence["valid_until"] = 0.97

    m = _first(r"^.*(?:deposit|balance|stage payment|payment terms)[^\n]*$", text)
    if m:
        q.payment_terms = m.group(0).strip()
        q.spans["payment_terms"] = q.payment_terms

    if re.search(r"or equivalent|alternative brand|substitut", text, re.I):
        q.substitutions = True
        q.spans["substitutions"] = _first(r"[^\n]*(?:or equivalent|alternative brand|substitut)[^\n]*", text).group(0).strip()  # type: ignore[union-attr]

    # AI-7: line prices must reconcile to the stated total (ex-VAT lines) within £1.
    if q.lines and q.total_stated is not None and q.vat_basis in ("ex", "none"):
        gap = abs(sum((ln.amount for ln in q.lines), Decimal(0)) - q.total_stated)
        if gap > Decimal("1"):
            q.flags.append("arithmetic_mismatch")
            q.confidence["total"] = 0.55
    return q
