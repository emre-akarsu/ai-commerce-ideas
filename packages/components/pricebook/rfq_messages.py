"""Quote-request (RFQ) messages: ONE aggregated message per supplier by default, individual
per-line messages on request. Templated text only, no model text, nothing sent (R1).

A message lists the lines a supplier is asked to quote, each as `n. text - quantity unit`.
Line text is the buyer's own wording and is refused (never repaired) when it holds a link, an
address, markup, braces or control characters, exactly like a placeholder value. The template is
data (`profiles/data/pricebook/rfq_templates.yaml`) checked on load with the same rules as the
price-file template. A message is a draft: the approval and send-service flow approves the exact
text and sends it. The caller supplies the supplier name and account reference per supplier.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from .errors import RequestTemplateError
from .gaps import RfqGapGroup, RfqGapItem
from .models import check_merchant_id
from .requests import (
    ACCOUNT_REFERENCE_MISSING,
    TEXT_MAX,
    RequestContext,
    _plain,
    check_value,
)

RFQ_PLACEHOLDERS = frozenset({"merchant_name", "buyer_name", "buyer_company",
                              "account_reference", "line_count"})
LINE_TEXT_MAX = 300
MAX_LINES_PER_MESSAGE = 200


class RfqMode(StrEnum):
    PER_SUPPLIER = "per_supplier"   # the default: one aggregated message per supplier
    PER_ITEM = "per_item"           # on request: one message per line


def _check_fields(text: str, where: str) -> None:
    from string import Formatter
    try:
        parts = list(Formatter().parse(text))
    except ValueError as exc:
        raise RequestTemplateError(f"{where}: bad braces ({exc})") from None
    for literal, name, spec, conv in parts:
        if "{" in literal or "}" in literal:
            raise RequestTemplateError(f"{where}: literal braces are not allowed")
        if name is None:
            continue
        if name not in RFQ_PLACEHOLDERS:
            raise RequestTemplateError(f"{where}: unknown placeholder {name!r}")
        if spec or conv:
            raise RequestTemplateError(f"{where}: placeholders take no format or conversion")


def _txt(value: Any, where: str) -> str:
    if not isinstance(value, str):
        raise RequestTemplateError(f"{where}: must be text")
    _plain(value, where, TEXT_MAX, braces_ok=True)
    _check_fields(value, where)
    return value


@dataclass(frozen=True)
class RfqTemplate:
    template_id: str
    label: str
    language: str
    greeting: str
    subjects: Mapping[str, str]
    intros: Mapping[str, str]
    ask_heading: str
    asks: tuple[str, ...]
    closing: str
    sign_off: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> RfqTemplate:
        if not isinstance(raw, Mapping):
            raise RequestTemplateError("template must be a mapping")
        known = {"id", "label", "language", "greeting", "aggregated", "individual",
                 "ask_heading", "asks", "closing", "sign_off"}
        extra = sorted(set(raw) - known)
        if extra:
            raise RequestTemplateError(f"unknown template keys: {extra}")
        tid = str(raw.get("id", ""))
        check_merchant_id(tid)
        label = raw.get("label")
        if not isinstance(label, str):
            raise RequestTemplateError("label: must be text")
        _plain(label, "label", TEXT_MAX, braces_ok=False)
        language = raw.get("language")
        if not isinstance(language, str) or re.fullmatch(r"[a-z]{2}(-[A-Z]{2})?", language) is None:
            raise RequestTemplateError("language: must look like en-GB")
        asks_raw = raw.get("asks")
        if not isinstance(asks_raw, list) or not 1 <= len(asks_raw) <= 20:
            raise RequestTemplateError("asks: must be a list of 1-20 items")
        subjects: dict[str, str] = {}
        intros: dict[str, str] = {}
        for key in ("aggregated", "individual"):
            v = raw.get(key)
            if not isinstance(v, Mapping) or set(v) != {"subject", "intro"}:
                raise RequestTemplateError(f"{key}: needs subject and intro")
            subjects[key] = _txt(v["subject"], f"{key}.subject")
            intros[key] = _txt(v["intro"], f"{key}.intro")
        return cls(
            template_id=tid, label=label, language=language,
            greeting=_txt(raw.get("greeting"), "greeting"), subjects=subjects, intros=intros,
            ask_heading=_txt(raw.get("ask_heading"), "ask_heading"),
            asks=tuple(_txt(a, f"asks[{i}]") for i, a in enumerate(asks_raw)),
            closing=_txt(raw.get("closing"), "closing"),
            sign_off=_txt(raw.get("sign_off"), "sign_off"))


@dataclass(frozen=True)
class RfqMessage:
    merchant_id: str
    mode: str                      # "per_supplier" | "per_item"
    subject: str
    body: str
    line_ids: tuple[str, ...]
    status: str = "draft_not_sent"  # a draft is never sent here (R1)


def _qty(q: Decimal) -> str:
    text = format(q.normalize(), "f")
    return text if "." not in text else text.rstrip("0").rstrip(".")


def _line(n: int, item: RfqGapItem) -> str:
    text = item.text.strip() or item.kit_line_id or item.line_id
    text = " ".join(text.split())
    _plain(text, f"line {item.line_id}", LINE_TEXT_MAX, braces_ok=False)
    return f"{n}. {text} - quantity {_qty(item.quantity)} {item.unit}"


def _render(template: RfqTemplate, mode: RfqMode, merchant_id: str, name: str,
            items: Sequence[RfqGapItem], ctx: RequestContext) -> RfqMessage:
    if not items:
        raise RequestTemplateError("a quote request needs at least one line")
    if len(items) > MAX_LINES_PER_MESSAGE:
        raise RequestTemplateError(f"too many lines for one message (max {MAX_LINES_PER_MESSAGE})")
    key = "individual" if mode is RfqMode.PER_ITEM else "aggregated"
    ref = ctx.account_references.get(merchant_id)
    values = {
        "merchant_name": check_value("merchant_name", name),
        "buyer_name": check_value("buyer_name", ctx.buyer_name),
        "buyer_company": check_value("buyer_company", ctx.buyer_company),
        "account_reference": check_value("account_reference", ref) if ref is not None
        else ACCOUNT_REFERENCE_MISSING,
        "line_count": str(len(items)),
    }
    f = lambda t: t.format(**values)  # noqa: E731
    lines = "\n".join(_line(i, it) for i, it in enumerate(items, start=1))
    asks = "\n".join(f"- {f(a)}" for a in template.asks)
    body = "\n\n".join([f(template.greeting), f(template.intros[key]), lines,
                        f"{f(template.ask_heading)}\n{asks}", f(template.closing),
                        f(template.sign_off)])
    subject = f(template.subjects[key])
    for where, text in (("subject", subject), ("body", body)):
        if re.search(r"://|\bwww\.|<[^>]*>|\bhttp", text, re.IGNORECASE):
            raise RequestTemplateError(f"{where}: the rendered text contains a link or markup")
    return RfqMessage(merchant_id, mode.value, subject, body, tuple(i.line_id for i in items))


def draft_rfq_messages(template: RfqTemplate, groups: Sequence[RfqGapGroup],
                       names: Mapping[str, str], ctx: RequestContext,
                       mode: RfqMode = RfqMode.PER_SUPPLIER) -> tuple[RfqMessage, ...]:
    """Quote-request drafts for `groups` (lines per supplier, see `rfq_for_gaps`).

    PER_SUPPLIER (default): one message per supplier with all its lines.
    PER_ITEM: one message per line, in supplier id then rank order.
    Both modes ask for the same lines, so switching mode never drops or adds a line."""
    out: list[RfqMessage] = []
    for g in sorted(groups, key=lambda g: g.merchant_id):
        mid = check_merchant_id(g.merchant_id)
        if not g.items:
            continue
        name = names.get(mid, mid)
        if mode is RfqMode.PER_SUPPLIER:
            out.append(_render(template, mode, mid, name, g.items, ctx))
        else:
            out.extend(_render(template, mode, mid, name, (it,), ctx) for it in g.items)
    return tuple(out)
