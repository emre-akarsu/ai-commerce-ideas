"""Builders shared by the send-service tests of the second security review.

They produce bytes OUTSIDE ``SendService.prepare`` (what a buggy or hostile caller could hand to
``send``) and re-serialise built messages with edited headers or text, without the sanitiser.

This file is ASCII on purpose: every special character is written with ``chr(...)``, because a literal
invisible character in a test is as easy to miss as one in a value.
"""

from __future__ import annotations

import email
import hashlib
from collections.abc import Callable, Mapping
from email import policy
from email.headerregistry import Address
from email.message import EmailMessage
from typing import Any

from components.core.domain import Event
from components.core.fakes import FakeClock
from components.evidence.log import EVT_SEND_REFUSED
from components.send_service.message import (
    FOOTER_TEMPLATE,
    MessagePurpose,
    PreparedMessage,
    build_message,
)
from tests.security.factories import ALIAS, BUYER, BUYER_EMAIL, PHONE, T1, VENDOR_EMAIL
from tests.security.world import World

LABELS = ("Company name", "Company number", "Registered office", "Registered in")
IDENTITY = (
    ("Company name", "Acme Plant Ltd"),
    ("Company number", "01234567"),
    ("Registered office", "1 Example Street, London, EC1A 1AA"),
    ("Registered in", "England and Wales"),
)
FOOTER = FOOTER_TEMPLATE.replace("{buyer}", BUYER)

LINE_SEPARATOR = chr(0x2028)
PARAGRAPH_SEPARATOR = chr(0x2029)
NEXT_LINE = chr(0x85)
ZERO_WIDTH_SPACE = chr(0x200B)
RIGHT_TO_LEFT_OVERRIDE = chr(0x202E)
NBSP = chr(0xA0)
SMART_QUOTES = chr(0x2018) + chr(0x2019) + chr(0x201C) + chr(0x201D)
BULLET = chr(0x2022)
EN_DASH = chr(0x2013)
CJK = chr(0x65E5) + chr(0x672C)
EMOJI = chr(0x1F6A2)


def build(**overrides: Any) -> bytes:
    """Bytes from the message layer alone (no ``SendService.prepare``)."""
    args: dict[str, Any] = {
        "subject": "RFQ: 6205-2RS x4", "body": "Please quote.", "to": VENDOR_EMAIL,
        "buyer_name": BUYER, "buyer_phone": PHONE, "alias_address": ALIAS,
        "reply_to": BUYER_EMAIL, "rfq_id": "rfq-1", "purpose": MessagePurpose.RFQ,
        "sent_at": FakeClock().now(), "footer_template": FOOTER_TEMPLATE,
    }
    args.update(overrides)
    return build_message(**args)


def external(raw: bytes) -> PreparedMessage:
    """Wrap bytes that were not built by ``prepare`` the way a caller would."""
    return PreparedMessage(raw, hashlib.sha256(raw).hexdigest(), VENDOR_EMAIL)


def rebuild(
    raw: bytes,
    *,
    headers: Mapping[str, object] | None = None,
    edit_text: Callable[[str], str] | None = None,
) -> bytes:
    """The same message with some headers replaced and/or its text edited. Nothing is validated."""
    parsed = email.message_from_bytes(raw, policy=policy.SMTP)
    text = parsed.get_content().replace("\r\n", "\n")
    new_text = edit_text(text) if edit_text else text
    assert new_text != text or headers, "the edit changed nothing"
    out = EmailMessage(policy=policy.SMTP.clone(max_line_length=998))
    skipped = {"content-type", "content-transfer-encoding", "mime-version"}
    for name, value in parsed.items():
        if name.lower() in skipped:
            continue
        chosen = (headers or {}).get(name, str(value))
        # The standard library itself refuses a header value that str.splitlines() would split (U+2028,
        # U+0085, ...); a header object made by the factory is stored as it is and encoded as an
        # RFC 2047 word, which is how such bytes could reach ``send`` from outside ``prepare``.
        out[name] = policy.SMTP.header_factory(name, chosen) if isinstance(chosen, str) else chosen
    out.set_content(new_text)
    return out.as_bytes()


def display(name: str, addr_spec: str) -> Address:
    return Address(display_name=name, addr_spec=addr_spec)


def refusals(world: World, tenant: str = T1) -> list[Event]:
    return [e for e in world.log.events(tenant) if e.type == EVT_SEND_REFUSED]
