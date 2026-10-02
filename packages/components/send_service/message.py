"""Building and parsing the outbound MIME message (R8, spec 4a).

The message is a single ``text/plain`` part: body, buyer signature, then the non-removable
AI-disclosure footer as the LAST block. There is no HTML part, so the footer cannot be bypassed by
a client that prefers another alternative. Everything the send-service later trusts (recipient,
RFQ reference, purpose, amount, follow-up schedule) lives in the hashed bytes the human approved.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from email import message_from_bytes, policy
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import format_datetime
from enum import StrEnum
from typing import ClassVar

from .errors import MalformedMessage

# R8: mandated wording. {buyer} is the named buyer the message is sent in the name of.
FOOTER_TEMPLATE = (
    "Prepared with an AI assistant. It cannot accept terms or place orders; "
    "only a purchase order from {buyer} binds."
)
MAX_BODY_CHARS = 20_000
MAX_SUBJECT_CHARS = 200
MAX_FOLLOW_UPS = 3

H_RFQ = "X-Purchasing-Agent-RFQ"
H_PURPOSE = "X-Purchasing-Agent-Purpose"
H_AMOUNT = "X-Purchasing-Agent-Amount"
H_FOLLOW_UP = "X-Purchasing-Agent-Follow-Up"
H_FOLLOW_UP_SEQ = "X-Purchasing-Agent-Follow-Up-Seq"

# Headers that could widen the recipient set or confuse a downstream provider's parser.
_FORBIDDEN_HEADERS = (
    "cc", "bcc", "resent-to", "resent-cc", "resent-bcc", "resent-from", "resent-sender",
    "resent-date", "resent-message-id", "apparently-to", "delivered-to", "x-original-to",
    "envelope-to",
)
_CTRL_LINE = re.compile(r"[\x00-\x1f\x7f]")
_CTRL_BODY = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HIDDEN = re.compile("[​-‏‪-‮⁠-⁤⁦-⁩﻿]")
_PHONE = re.compile(r"^[0-9+()\-.\sx#]{3,40}$")
_AMOUNT = re.compile(r"^(\d+(?:\.\d{1,6})?) ([A-Z]{3})$")
_FOLLOW = re.compile(r"^count=(\d+); interval_hours=(\d+)$")
_PHONE_LINE = re.compile(r"^Phone: (.+)$", re.MULTILINE)


class MessagePurpose(StrEnum):
    RFQ = "rfq"
    PO = "po"


@dataclass(frozen=True)
class FollowUpSchedule:
    """A pre-approved follow-up schedule. Default (``NONE``): no follow-ups."""

    count: int = 0
    interval: timedelta = timedelta(hours=48)
    NONE: ClassVar[FollowUpSchedule]

    def __post_init__(self) -> None:
        if isinstance(self.count, bool) or not isinstance(self.count, int):
            raise ValueError("follow-up count must be an integer")
        if not 0 <= self.count <= MAX_FOLLOW_UPS:
            raise ValueError(f"follow-up count must be 0..{MAX_FOLLOW_UPS}")
        if self.count and not (
            timedelta(hours=24) <= self.interval <= timedelta(days=14)
            and self.interval % timedelta(hours=1) == timedelta(0)
        ):
            raise ValueError("follow-up interval must be a whole number of hours, 24h to 14 days")


FollowUpSchedule.NONE = FollowUpSchedule()
NO_FOLLOW_UPS = FollowUpSchedule.NONE


@dataclass(frozen=True)
class PreparedMessage:
    """Output of ``SendService.prepare``. ``mime_hash`` is the sha256 of ``mime_bytes``.

    The send-service never trusts the metadata fields: it recomputes the hash and re-derives
    everything else from the bytes the human approved."""

    mime_bytes: bytes
    mime_hash: str
    to: str
    tenant_id: str = ""
    rfq_id: str = ""
    vendor_id: str = ""
    subject: str = ""
    purpose: MessagePurpose = MessagePurpose.RFQ


@dataclass(frozen=True)
class ParsedMessage:
    """What the send-service sees when it re-reads the bytes (also the approval-screen preview)."""

    to: str
    to_domain: str
    from_name: str
    from_addr: str
    reply_to: str
    subject: str
    text: str
    message_id: str
    rfq_id: str
    purpose: MessagePurpose
    amount: Decimal | None
    currency: str | None
    follow_up: FollowUpSchedule
    followup_seq: int | None
    in_reply_to: str | None
    buyer_phone: str | None


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render_footer(template: str, buyer_name: str) -> str:
    return template.replace("{buyer}", buyer_name)


# ---------------------------------------------------------------- validation


def _line(value: object, name: str, max_len: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MalformedMessage(f"{name} is required")
    cleaned = value.strip()
    if len(cleaned) > max_len or _CTRL_LINE.search(cleaned) or _HIDDEN.search(cleaned):
        raise MalformedMessage(f"{name} is too long or contains control/hidden characters")
    return cleaned


def _address(value: object, name: str) -> Address:
    text = _line(value, name, 254)
    if not text.isascii() or any(c in text for c in '<>,;" \t'):
        raise MalformedMessage(f"{name} must be a plain ASCII e-mail address")
    try:
        addr = Address(addr_spec=text)
    except (ValueError, IndexError) as exc:
        raise MalformedMessage(f"{name} is not a valid e-mail address") from exc
    if not addr.username or "." not in addr.domain or addr.addr_spec != text:
        raise MalformedMessage(f"{name} is not a valid e-mail address")
    return addr


def _clean_body(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MalformedMessage("message body is required")
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    if len(text) > MAX_BODY_CHARS:
        raise MalformedMessage("message body is too long")
    if _CTRL_BODY.search(text) or _HIDDEN.search(text):
        raise MalformedMessage("message body contains control or hidden characters")
    return text.strip()


def _clean_phone(value: object) -> str:
    phone = _line(value, "buyer_phone", 40)
    if not _PHONE.match(phone):
        raise MalformedMessage("buyer_phone has unexpected characters")
    return phone


def _msg_id_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "-", value)[:60] or "x"


# ---------------------------------------------------------------- build


def signature_block(buyer_name: str, buyer_phone: str, reply_to: str) -> str:
    return f"{buyer_name}\nPhone: {buyer_phone}\nReply to: {reply_to}"


def build_message(
    *,
    subject: str,
    body: str,
    to: str,
    buyer_name: str,
    buyer_phone: str,
    alias_address: str,
    reply_to: str,
    rfq_id: str,
    purpose: MessagePurpose,
    sent_at: datetime,
    footer_template: str,
    reply_token: str = "",
    amount: Decimal | None = None,
    currency: str | None = None,
    follow_up: FollowUpSchedule = NO_FOLLOW_UPS,
    in_reply_to: str | None = None,
    followup_seq: int | None = None,
) -> bytes:
    """Return the final MIME bytes (CRLF, 7-bit safe). Raises MalformedMessage on bad input."""
    subject_c = _line(subject, "subject", MAX_SUBJECT_CHARS)
    buyer_c = _line(buyer_name, "buyer_name", 100)
    phone_c = _clean_phone(buyer_phone)
    rcpt = _address(to, "recipient")
    alias = _address(alias_address, "alias_address")
    reply = _address(reply_to, "reply_to")
    body_c = _clean_body(body)
    rfq_c = _line(rfq_id, "rfq_id", 100)
    if purpose is MessagePurpose.PO and (amount is None or currency is None):
        raise MalformedMessage("a purchase order message needs an amount and currency")
    amount_header: str | None = None
    if amount is not None:
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount < 0:
            raise MalformedMessage("amount must be a finite non-negative Decimal")
        if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
            raise MalformedMessage("currency must be an ISO 4217 code such as USD")
        amount_header = f"{amount:f} {currency}"

    lines = [body_c, "", signature_block(buyer_c, phone_c, reply.addr_spec)]
    if reply_token:
        lines.append(f"RFQ reference: {_line(reply_token, 'reply_token', 200)}")
    lines += ["", "--", render_footer(footer_template, buyer_c), ""]
    text = "\n".join(lines)

    stamp = int(sent_at.timestamp())
    digest = sha256_hex(f"{rfq_c}|{subject_c}|{body_c}|{followup_seq}".encode())[:10]
    # 998 = RFC 5322 hard limit: keeps ASCII text 7bit so the footer sentence stays verbatim in the
    # hashed bytes instead of being quoted-printable soft-wrapped.
    msg = EmailMessage(policy=policy.SMTP.clone(max_line_length=998))
    try:
        msg["From"] = Address(display_name=buyer_c, addr_spec=alias.addr_spec)
        msg["To"] = rcpt
        msg["Reply-To"] = Address(display_name=buyer_c, addr_spec=reply.addr_spec)
        msg["Subject"] = subject_c
        msg["Date"] = format_datetime(sent_at)
        msg["Message-ID"] = f"<{_msg_id_part(rfq_c)}.{stamp}.{digest}@{alias.domain}>"
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to
        msg[H_RFQ] = rfq_c
        msg[H_PURPOSE] = purpose.value
        if amount_header:
            msg[H_AMOUNT] = amount_header
        if follow_up.count:
            hours = int(follow_up.interval.total_seconds() // 3600)
            msg[H_FOLLOW_UP] = f"count={follow_up.count}; interval_hours={hours}"
        if followup_seq is not None:
            msg[H_FOLLOW_UP_SEQ] = str(followup_seq)
        msg.set_content(text)
    except (ValueError, TypeError) as exc:
        raise MalformedMessage("message could not be encoded safely") from exc
    return msg.as_bytes()


# ---------------------------------------------------------------- parse


def _one_header(msg: EmailMessage, name: str, *, required: bool = True) -> str | None:
    values = msg.get_all(name)
    if not values:
        if required:
            raise MalformedMessage(f"header {name} is missing")
        return None
    if len(values) != 1:
        raise MalformedMessage(f"header {name} appears more than once")
    return str(values[0])


def _one_address(msg: EmailMessage, name: str) -> Address:
    _one_header(msg, name)
    header = msg[name]
    if getattr(header, "defects", None):
        raise MalformedMessage(f"header {name} is malformed")
    addresses = getattr(header, "addresses", ())
    groups = getattr(header, "groups", ())
    if len(addresses) != 1 or len(groups) != 1 or groups[0].display_name is not None:
        raise MalformedMessage(f"header {name} must contain exactly one plain address")
    address = addresses[0]
    if not address.username or not address.domain:
        raise MalformedMessage(f"header {name} has an invalid address")
    return address  # type: ignore[no-any-return]


def parse_message(raw: bytes) -> ParsedMessage:
    """Re-read final bytes strictly. Anything unexpected is refused, never guessed."""
    if not isinstance(raw, bytes) or not raw:
        raise MalformedMessage("message bytes are required")
    try:
        msg = message_from_bytes(raw, policy=policy.SMTP)
    except Exception as exc:  # noqa: BLE001 - any parser failure means refuse
        raise MalformedMessage("message cannot be parsed") from exc
    if msg.is_multipart() or msg.get_content_type() != "text/plain":
        raise MalformedMessage("only a single text/plain part is accepted")
    for name in _FORBIDDEN_HEADERS:
        if name in msg:
            raise MalformedMessage(f"header {name} is not allowed")
    to = _one_address(msg, "To")
    sender = _one_address(msg, "From")
    reply = _one_address(msg, "Reply-To")
    subject = _one_header(msg, "Subject") or ""
    message_id = _one_header(msg, "Message-ID") or ""
    rfq_id = _one_header(msg, H_RFQ) or ""
    if not rfq_id:
        raise MalformedMessage("message does not reference an RFQ")
    try:
        purpose = MessagePurpose(_one_header(msg, H_PURPOSE))
    except ValueError as exc:
        raise MalformedMessage("message purpose is missing or unknown") from exc
    amount, currency = _parse_amount(_one_header(msg, H_AMOUNT, required=False))
    follow_up = _parse_follow_up(_one_header(msg, H_FOLLOW_UP, required=False))
    seq_raw = _one_header(msg, H_FOLLOW_UP_SEQ, required=False)
    try:
        text = msg.get_content().replace("\r\n", "\n")
    except Exception as exc:  # noqa: BLE001
        raise MalformedMessage("message body cannot be decoded") from exc
    phone = _PHONE_LINE.search(text)
    return ParsedMessage(
        to=to.addr_spec,
        to_domain=to.domain,
        from_name=sender.display_name,
        from_addr=sender.addr_spec,
        reply_to=reply.addr_spec,
        subject=subject,
        text=text,
        message_id=message_id,
        rfq_id=rfq_id,
        purpose=purpose,
        amount=amount,
        currency=currency,
        follow_up=follow_up,
        followup_seq=int(seq_raw) if seq_raw and seq_raw.isdigit() else None,
        in_reply_to=_one_header(msg, "In-Reply-To", required=False),
        buyer_phone=phone.group(1) if phone else None,
    )


def _parse_amount(value: str | None) -> tuple[Decimal | None, str | None]:
    if value is None:
        return None, None
    match = _AMOUNT.match(value)
    if not match:
        raise MalformedMessage("amount header is malformed")
    try:
        return Decimal(match.group(1)), match.group(2)
    except InvalidOperation as exc:
        raise MalformedMessage("amount header is malformed") from exc


def _parse_follow_up(value: str | None) -> FollowUpSchedule:
    if value is None:
        return NO_FOLLOW_UPS
    match = _FOLLOW.match(value)
    if not match:
        raise MalformedMessage("follow-up header is malformed")
    try:
        return FollowUpSchedule(int(match.group(1)), timedelta(hours=int(match.group(2))))
    except ValueError as exc:
        raise MalformedMessage("follow-up schedule is invalid") from exc


def has_footer(parsed: ParsedMessage, footer_template: str) -> bool:
    """True iff the text ends with the mandated footer naming the sender (R8)."""
    if not parsed.from_name:
        return False
    footer = render_footer(footer_template, parsed.from_name)
    text = parsed.text.rstrip()
    return text == footer or text.endswith("\n" + footer)
