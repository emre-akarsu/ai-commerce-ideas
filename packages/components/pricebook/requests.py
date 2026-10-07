"""Request-your-price-file drafts (strategy step 1.4): templated text only, no model text.

The templates are data (`profiles/data/pricebook/request_templates.yaml`, parsed by the caller and
handed in as a mapping). A draft is the template with four placeholders filled: `merchant_name`,
`buyer_name`, `buyer_company` and `account_reference`. Safety rules, all tested:

* an unknown placeholder, a format spec, a conversion, an attribute or index access, or a stray
  brace in a template is refused when the template is loaded;
* a placeholder VALUE with a URL, a domain name, an e-mail address, HTML, markup brackets, braces
  or control characters is refused; nothing is repaired;
* a rendered draft contains no URL and no HTML (checked once more on the final text);
* there is no legal footer here and nothing is sent: a draft is data. The existing approval and
  send-service flow adds the footer and sends only after a person approves the exact text (R1).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from string import Formatter
from typing import Any

from .errors import RequestTemplateError
from .models import MerchantBook, MerchantStatus, check_merchant_id

PLACEHOLDERS = frozenset({"merchant_name", "buyer_name", "buyer_company", "account_reference"})
ACCOUNT_REFERENCE_MISSING = "[account reference to be added]"
DRAFT_STATUSES = (MerchantStatus.MISSING, MerchantStatus.STALE, MerchantStatus.INDICATIVE_ONLY)
VALUE_MAX = 120
TEXT_MAX = 600
_DOMAIN = re.compile(r"[A-Za-z0-9-]\.(?:com|net|org|co|uk|io|info|biz|eu|app|dev|de|fr|ie|me|us)\b",
                     re.IGNORECASE)
_ENTITY = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[A-Za-z]{2,8});")
_BAD_TEXT = re.compile(r"[<>\[\]{}`|\\@]|://|\bwww\.|\bmailto:", re.IGNORECASE)
_VARIANT_KEYS = ("missing", "stale", "indicative_only")


def _plain(text: str, where: str, limit: int, *, braces_ok: bool) -> None:
    if not isinstance(text, str) or not text.strip() or len(text) > limit:
        raise RequestTemplateError(f"{where}: must be 1-{limit} characters")
    if any(ord(c) < 32 and c != "\n" for c in text) or "\x7f" in text:
        raise RequestTemplateError(f"{where}: control characters are not allowed")
    check = text.replace("{", "").replace("}", "") if braces_ok else text
    if _BAD_TEXT.search(check) or _DOMAIN.search(text) or _ENTITY.search(text) \
            or "http" in text.lower():
        raise RequestTemplateError(f"{where}: links, markup or addresses are not allowed")


def _check_fields(text: str, where: str) -> None:
    """Only plain `{name}` fields with a known name; no braces anywhere else."""
    try:
        parts = list(Formatter().parse(text))
    except ValueError as exc:
        raise RequestTemplateError(f"{where}: bad braces ({exc})") from None
    for literal, name, spec, conv in parts:
        if "{" in literal or "}" in literal:
            raise RequestTemplateError(f"{where}: literal braces are not allowed")
        if name is None:
            continue
        if name not in PLACEHOLDERS:
            raise RequestTemplateError(f"{where}: unknown placeholder {name!r}")
        if spec or conv:
            raise RequestTemplateError(f"{where}: placeholders take no format or conversion")


def _text(raw: Mapping[str, Any], key: str, where: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise RequestTemplateError(f"{where}.{key}: must be text")
    _plain(value, f"{where}.{key}", TEXT_MAX, braces_ok=True)
    _check_fields(value, f"{where}.{key}")
    return value


@dataclass(frozen=True)
class RequestTemplate:
    template_id: str
    label: str
    language: str
    greeting: str
    ask_heading: str
    asks: tuple[str, ...]
    closing: str
    sign_off: str
    subjects: Mapping[str, str]
    intros: Mapping[str, str]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> RequestTemplate:
        if not isinstance(raw, Mapping):
            raise RequestTemplateError("template must be a mapping")
        known = {"id", "label", "language", "greeting", "ask_heading", "asks", "closing",
                 "sign_off", "variants"}
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
        asks = []
        for i, a in enumerate(asks_raw):
            if not isinstance(a, str):
                raise RequestTemplateError(f"asks[{i}]: must be text")
            _plain(a, f"asks[{i}]", TEXT_MAX, braces_ok=True)
            _check_fields(a, f"asks[{i}]")
            asks.append(a)
        variants = raw.get("variants")
        if not isinstance(variants, Mapping) or set(variants) != set(_VARIANT_KEYS):
            raise RequestTemplateError(f"variants: must have exactly {list(_VARIANT_KEYS)}")
        subjects, intros = {}, {}
        for key in _VARIANT_KEYS:
            v = variants[key]
            if not isinstance(v, Mapping) or set(v) != {"subject", "intro"}:
                raise RequestTemplateError(f"variants.{key}: needs subject and intro")
            subjects[key] = _text(v, "subject", f"variants.{key}")
            intros[key] = _text(v, "intro", f"variants.{key}")
        return cls(
            template_id=tid, label=label, language=language,
            greeting=_text(raw, "greeting", "template"),
            ask_heading=_text(raw, "ask_heading", "template"), asks=tuple(asks),
            closing=_text(raw, "closing", "template"), sign_off=_text(raw, "sign_off", "template"),
            subjects=subjects, intros=intros)


def check_value(name: str, value: str) -> str:
    """A placeholder value is accepted exactly as given (after trimming) or refused."""
    if name not in PLACEHOLDERS:
        raise RequestTemplateError(f"unknown placeholder {name!r}")
    if not isinstance(value, str):
        raise RequestTemplateError(f"{name}: must be text")
    text = value.strip()
    _plain(text, name, VALUE_MAX, braces_ok=False)
    if "\n" in text:
        raise RequestTemplateError(f"{name}: must be one line")
    return text


@dataclass(frozen=True)
class RequestContext:
    """Who is asking: filled by the caller (the tenant's user and company; the account reference
    per merchant, which only the tenant knows)."""

    buyer_name: str
    buyer_company: str
    account_references: Mapping[str, str]


@dataclass(frozen=True)
class RequestDraft:
    merchant_id: str
    subject: str
    body: str
    status: str = "draft_not_sent"  # a draft is never sent here (R1)


def _fill(template: str, values: Mapping[str, str]) -> str:
    return template.format(**values)


def draft_request(template: RequestTemplate, merchant: MerchantBook, ctx: RequestContext
                  ) -> RequestDraft:
    """The drafted request for one merchant whose status is missing, stale or indicative only."""
    if merchant.status not in DRAFT_STATUSES:
        raise RequestTemplateError("no request is drafted for a merchant whose prices are current")
    key = merchant.status.value
    values = {
        "merchant_name": check_value("merchant_name", merchant.name),
        "buyer_name": check_value("buyer_name", ctx.buyer_name),
        "buyer_company": check_value("buyer_company", ctx.buyer_company),
        "account_reference": check_value("account_reference", ctx.account_references[
            merchant.merchant_id]) if merchant.merchant_id in ctx.account_references
        else ACCOUNT_REFERENCE_MISSING,
    }
    asks = "\n".join(f"- {_fill(a, values)}" for a in template.asks)
    body = "\n\n".join([
        _fill(template.greeting, values), _fill(template.intros[key], values),
        f"{_fill(template.ask_heading, values)}\n{asks}", _fill(template.closing, values),
        _fill(template.sign_off, values)])
    subject = _fill(template.subjects[key], values)
    for where, text in (("subject", subject), ("body", body)):
        if re.search(r"://|\bwww\.|<[^>]*>|\bhttp", text, re.IGNORECASE):
            raise RequestTemplateError(f"{where}: the rendered text contains a link or markup")
    return RequestDraft(merchant_id=merchant.merchant_id, subject=subject, body=body)


def draft_requests(template: RequestTemplate, merchants: tuple[MerchantBook, ...],
                   ctx: RequestContext) -> tuple[RequestDraft, ...]:
    """One draft per merchant that is not current, in merchant id order."""
    return tuple(draft_request(template, m, ctx) for m in merchants
                 if m.status in DRAFT_STATUSES)
