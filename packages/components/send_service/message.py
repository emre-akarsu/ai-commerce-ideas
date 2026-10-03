"""Building and parsing the outbound MIME message (R8, spec 4a).

The message is a single ``text/plain`` part: body, buyer signature, optional business-identity lines
(company particulars a deployment may require), then the non-removable AI-disclosure footer as the
LAST block. There is no HTML part, so the footer cannot be bypassed by a client that prefers another
alternative. Everything the send-service later trusts (recipient, RFQ reference, purpose, amount,
follow-up schedule, identity lines) lives in the hashed bytes the human approved.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from email import message_from_bytes, policy
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import format_datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, ClassVar, NoReturn, TypeVar

from .errors import MalformedMessage

_K = TypeVar("_K")
_V = TypeVar("_V")

# R8: mandated wording. {buyer} is the named buyer the message is sent in the name of.
FOOTER_TEMPLATE = (
    "Prepared with an AI assistant. It cannot accept terms or place orders; "
    "only a purchase order from {buyer} binds."
)
# A profile may localise the footer, but it must keep these clauses (mirrors aiplat.profile).
REQUIRED_FOOTER_CLAUSES = ("AI assistant", "cannot accept terms", "{buyer}")
MAX_BODY_CHARS = 20_000
MAX_SUBJECT_CHARS = 200
MAX_FOLLOW_UPS = 3

# Business identity ("company particulars"): "<label>: <value>" lines placed directly after the
# signature block. A deployment profile may require labels; this module only sees labels and values.
# These constants mirror aiplat.profile (the message layer has no run-time dependency on the profile
# package); tests/profiles keeps the two copies, and the two label validators, in step.
DEFAULT_IDENTITY_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "legal_name": "Company name",
        "registration_number": "Company number",
        "registered_office": "Registered office",
        "registered_in": "Registered in",
    }
)
MAX_IDENTITY_LABEL_CHARS = 40
MAX_IDENTITY_VALUE_CHARS = 200
MAX_IDENTITY_LINES = 8
# Lines this module already owns; an identity label equal to one of them would be ambiguous.
RESERVED_LINE_LABELS = ("Phone", "Reply to", "RFQ reference")
_LABEL_COLONS = ":\uff1a"  # ASCII and fullwidth colon: a line is "<label>: <value>"
_RFQ_REFERENCE_PREFIX = "RFQ reference: "
_FOOTER_SEPARATOR = "--"

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
# Everything that ends a "line" for SOME reader must stay out of a one-line field: C0 and C1
# controls (U+0085 NEL is in C1), DEL and the Unicode line and paragraph separators. Every check in
# this module splits on a literal "\n"; a renderer that splits like str.splitlines() (UAX #14) must
# see the same lines, or a value could show a forged "--" and footer ahead of the real one. The body
# may keep its own "\n" (and tabs); it refuses all the rest. Written with escapes: never a literal
# invisible character in this source (tests/sendservice/test_line_sanitiser.py checks that).
_CTRL_LINE = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]")
_CTRL_BODY = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u2028\u2029]")
# Zero-width and bidirectional formatting characters, the Arabic letter mark, the byte-order mark.
_HIDDEN = re.compile(r"[\u061c\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff]")
# Letters that draw nothing (Unicode Default_Ignorable_Code_Point) but still pass str.isalnum().
_BLANK_LETTERS = frozenset("\u115f\u1160\u3164\uffa0")
# Link-like text: a scheme, "www." or "mailto:". A company particular is never a link.
_LINK_LIKE = re.compile(r"://|www\.|mailto:", re.IGNORECASE)
_PHONE = re.compile(r"^[0-9+()\-.\sx#]{3,40}$")
_AMOUNT = re.compile(r"^(\d+(?:\.\d{1,6})?) ([A-Z]{3})$")
_FOLLOW = re.compile(r"^count=(\d+); interval_hours=(\d+)$")
_PHONE_PREFIX = "Phone: "
_REPLY_PREFIX = "Reply to: "


class ReadOnlyMap(Mapping[_K, _V]):
    """A small read-only mapping that owns a private copy of what it was given.

    It replaces ``types.MappingProxyType`` wherever a configuration object keeps company
    particulars: a mapping proxy cannot be pickled or deep-copied (so
    ``pickle.dumps(settings)``, ``copy.deepcopy`` and ``dataclasses.asdict`` raised
    ``TypeError``, and a spawn-based worker could not start), and this can.

    Nothing changes it: it has no mutator, item assignment and deletion raise ``TypeError``,
    attributes cannot be set, and the dict inside is private. Its repr shows a count only, so
    holding values in it does not print them. Equality is by content, like a dict. The copy is
    one level deep: a value that is itself mutable is shared with the caller, so nest
    ``ReadOnlyMap`` for nested mappings."""

    __slots__ = ("_data",)
    _data: dict[_K, _V]

    def __init__(self, data: Mapping[_K, _V] | Iterable[tuple[_K, _V]] = ()) -> None:
        object.__setattr__(self, "_data", dict(data))

    def __getitem__(self, key: _K) -> _V:
        return self._data[key]

    def __iter__(self) -> Iterator[_K]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, key: _K, value: _V) -> NoReturn:
        raise TypeError("ReadOnlyMap is read-only")

    def __delitem__(self, key: _K) -> NoReturn:
        raise TypeError("ReadOnlyMap is read-only")

    def __setattr__(self, name: str, value: object) -> NoReturn:
        raise AttributeError("ReadOnlyMap is read-only")

    def __delattr__(self, name: str) -> NoReturn:
        raise AttributeError("ReadOnlyMap is read-only")

    def __repr__(self) -> str:
        return f"ReadOnlyMap(items={len(self._data)})"

    def __reduce__(self) -> tuple[Any, ...]:
        return (type(self), (dict(self._data),))  # pickling and copying rebuild it from a copy


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
    reply_to_name: str = ""  # the Reply-To display name (a one-line text the recipient sees)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render_footer(template: str, buyer_name: str) -> str:
    return template.replace("{buyer}", buyer_name)


# ---------------------------------------------------------------- validation


def is_plain_line(text: object) -> bool:
    """True iff ``text`` is a string that is safe to place in a ONE-line field: no control character
    (C0 or C1, DEL), no line or paragraph separator, and no zero-width, bidirectional or
    byte-order-mark character. This is the single rule behind every one-line field (``_line``)
    and behind the ship-to ``site``, which ends up in the body: the API (422) and the pack
    (409) call it, so both agree with the message layer for every code point.

    It is stricter than the body rule on exactly three characters, newline, carriage return
    and tab, which a multi-line body may keep and a one-line field may not."""
    return isinstance(text, str) and not _CTRL_LINE.search(text) and not _HIDDEN.search(text)


def _line(value: object, name: str, max_len: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MalformedMessage(f"{name} is required")
    cleaned = value.strip()
    if len(cleaned) > max_len or not is_plain_line(cleaned):
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


def _label_key(label: str) -> str:
    return " ".join(label.lower().split())


_RESERVED_KEYS = frozenset(_label_key(r) for r in RESERVED_LINE_LABELS)


def _is_plain_label_text(label: str) -> bool:
    """No control, format, private-use or unassigned character and no space but the ASCII one. The
    same rule ``aiplat.profile`` applies to a profile's labels (tests/profiles keeps them equal)."""
    return not any(
        unicodedata.category(c)[0] == "C" or (c.isspace() and c != " ") for c in label
    )


def _identity_label(raw: object) -> str:
    """A label is plain single-line text: no surrounding spaces, no colon, no control or hidden
    character, not a reserved line."""
    label = _line(raw, "identity label", MAX_IDENTITY_LABEL_CHARS)
    if (
        label != raw
        or any(c in _LABEL_COLONS for c in label)
        or not _is_plain_label_text(label)
        or _label_key(label) in _RESERVED_KEYS
    ):
        raise MalformedMessage(
            "identity label must be plain text without surrounding spaces or a colon, "
            "and not a reserved line label"
        )
    return label


def has_visible_text(value: object) -> bool:
    """True iff ``value`` is text with at least one letter or digit that is actually drawn.
    Whitespace, punctuation, format characters and letters that render as nothing (the Hangul
    fillers) do not count: a required company particular made only of those is not there."""
    return isinstance(value, str) and any(c.isalnum() and c not in _BLANK_LETTERS for c in value)


def _identity_value(label: str, raw: object) -> str:
    """One line of company particulars: single-line text with a visible letter or digit that is not
    link-like. Errors name the label, never the value."""
    name = f"identity value for {label!r}"
    value = _line(raw, name, MAX_IDENTITY_VALUE_CHARS)
    if not has_visible_text(value):
        raise MalformedMessage(f"{name} must contain a letter or digit")
    if _LINK_LIKE.search(value):
        raise MalformedMessage(f"{name} must not look like a link")
    return value


def as_identity_pairs(identity: object) -> list[Any]:
    """Materialise the caller's pairs once. Any iterable of items is accepted (list, tuple,
    ``dict.items()``, ...) except text, bytes and mappings, which are not a sequence of pairs.
    The items themselves are checked later, by ``build_message``."""
    if isinstance(identity, (str, bytes, Mapping)) or not isinstance(identity, Iterable):
        raise MalformedMessage("identity must be a sequence of (label, value) pairs")
    return list(identity)


def clean_identity_pairs(identity: object) -> list[tuple[str, str]]:
    """The validated, trimmed ``(label, value)`` pairs ``build_message`` would render, in order.
    Values pass through the same single-line sanitiser as the other header-like text; errors name
    the label, never the value."""
    pairs = as_identity_pairs(identity)
    if len(pairs) > MAX_IDENTITY_LINES:
        raise MalformedMessage(f"identity has more than {MAX_IDENTITY_LINES} lines")
    cleaned: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in pairs:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise MalformedMessage("identity entries must be (label, value) pairs")
        label = _identity_label(item[0])
        value = _identity_value(label, item[1])
        if _label_key(label) in seen:
            raise MalformedMessage("identity labels must be unique")
        seen.add(_label_key(label))
        cleaned.append((label, value))
    return cleaned


def _identity_lines(identity: object) -> list[str]:
    """Render ``(label, value)`` pairs as ``"<label>: <value>"`` lines."""
    return [f"{label}: {value}" for label, value in clean_identity_pairs(identity)]


def validate_identity_pairs(identity: object) -> None:
    """Raise ``MalformedMessage`` unless ``build_message`` would accept these identity pairs."""
    clean_identity_pairs(identity)


def validate_identity_labels(labels: object) -> tuple[str, ...]:
    """The labels a deployment requires on every message. Raises ``ValueError`` (a configuration
    error, like a bad footer) unless they are distinct plain-text labels."""
    if not isinstance(labels, (list, tuple)):
        raise ValueError("required_identity_labels must be a tuple of identity labels")
    if len(labels) > MAX_IDENTITY_LINES:
        raise ValueError(f"required_identity_labels allows at most {MAX_IDENTITY_LINES} labels")
    seen: set[str] = set()
    for label in labels:
        try:
            _identity_label(label)
        except MalformedMessage as exc:
            raise ValueError("required_identity_labels holds an invalid identity label") from exc
        if _label_key(label) in seen:
            raise ValueError("required_identity_labels must be distinct identity labels")
        seen.add(_label_key(label))
    return tuple(labels)


def unfilled_identity_labels(identity: Iterable[object], labels: Sequence[str]) -> list[str]:
    """The required labels that have no value showing a letter or digit among the given
    ``(label, value)`` pairs (already materialised by ``as_identity_pairs``). Tolerant of bad
    entries, which ``build_message`` reports; never returns a value."""
    filled = {
        item[0]
        for item in identity
        if isinstance(item, (list, tuple)) and len(item) == 2
        and isinstance(item[0], str) and has_visible_text(item[1])
    }
    return [label for label in labels if label not in filled]


# ---------------------------------------------------------------- build


def signature_block(buyer_name: str, buyer_phone: str, reply_to: str) -> str:
    return f"{buyer_name}\n{_PHONE_PREFIX}{buyer_phone}\n{_REPLY_PREFIX}{reply_to}"


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
    identity: Sequence[tuple[str, str]] = (),
) -> bytes:
    """Return the final MIME bytes (CRLF, 7-bit safe). Raises MalformedMessage on bad input.

    ``identity`` is an ordered list of ``(label, value)`` pairs rendered one per line directly after
    the signature block, before the RFQ reference line and the footer (which stays the last block).
    """
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
    lines += _identity_lines(identity)
    if reply_token:
        lines.append(_RFQ_REFERENCE_PREFIX + _line(reply_token, "reply_token", 200))
    lines += ["", _FOOTER_SEPARATOR, render_footer(footer_template, buyer_c), ""]
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
    phone = _signature_phone(text, reply.addr_spec)
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
        buyer_phone=phone,
        reply_to_name=reply.display_name,
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


def _without_footer(parsed: ParsedMessage, footer_template: str) -> str:
    """The text with the mandated footer taken off its end. The footer is wording the deployment
    configures (``has_footer`` has already matched it exactly), not text a requester wrote."""
    footer = render_footer(footer_template, parsed.from_name)
    end = len(parsed.text.rstrip())
    start = end - len(footer)
    if parsed.from_name and start >= 0 and parsed.text[start:end] == footer:
        return parsed.text[:start] + parsed.text[end:]
    return parsed.text


def unsafe_text_fields(parsed: ParsedMessage, footer_template: str) -> list[str]:
    """The kinds of field in a parsed message that hold a character the single-line sanitiser
    keeps out of them. ``prepare`` builds nothing of the kind; the send-time gate calls this
    on bytes that may not have come from it, so that the invariant behind the footer check
    (``str.splitlines()`` and ``split("\\n")`` see the same lines) holds for those bytes too.

    ``"body"`` covers all text but the mandated footer: control and line-break characters (a
    newline and a tab are fine, a carriage return left after the parse is not), and zero-width
    or bidirectional characters. ``"subject"``, ``"sender name"`` and ``"reply-to name"`` are
    the one-line header texts, ``"address"`` the three addresses and ``"reference"`` the RFQ
    reference and message id. Returns kinds only, never text."""
    found: list[str] = []
    body = _without_footer(parsed, footer_template)
    if _CTRL_BODY.search(body) or "\r" in body or _HIDDEN.search(body):
        found.append("body")
    one_line = (
        ("subject", (parsed.subject,)),
        ("sender name", (parsed.from_name,)),
        ("reply-to name", (parsed.reply_to_name,)),
        ("address", (parsed.to, parsed.from_addr, parsed.reply_to)),
        ("reference", (parsed.rfq_id, parsed.message_id)),
    )
    found += [kind for kind, texts in one_line if not all(is_plain_line(t) for t in texts)]
    return found


# ---------------------------------------------------------------- the signature block (parse side)


def _signature_positions(lines: list[str], reply_to: str) -> tuple[int, int] | None:
    """Where the signature block sits: ``(index of its "Reply to:" line, index of the footer
    separator)``. Anchored from the END of the text: the LAST ``--`` line, then the LAST
    ``Phone:`` / ``Reply to: <this message's reply address>`` pair before it. Text in the body that
    merely looks like a signature comes earlier, so it is never the one selected. ``None`` when the
    text has no such block."""
    sep = next((i for i in range(len(lines) - 1, -1, -1) if lines[i] == _FOOTER_SEPARATOR), None)
    if sep is None:
        return None
    reply_line = _REPLY_PREFIX + reply_to
    reply = next(
        (k for k in range(sep - 1, 0, -1)
         if lines[k] == reply_line and lines[k - 1].startswith(_PHONE_PREFIX)),
        None,
    )
    return None if reply is None else (reply, sep)


def _signature_phone(text: str, reply_to: str) -> str | None:
    """The buyer's phone number as printed in the signature block, never a ``Phone:`` line that the
    body happens to contain (a follow-up reuses this value)."""
    lines = text.split("\n")
    spot = _signature_positions(lines, reply_to)
    if spot is None:
        return None
    return lines[spot[0] - 1][len(_PHONE_PREFIX):] or None


# ---------------------------------------------------------------- business identity (parse side)


def _identity_run(parsed: ParsedMessage) -> list[str]:
    """The ``"<label>: <value>"`` lines in the identity POSITION: directly after the signature
    block, before the RFQ reference line and the footer separator. Body text that merely looks like
    such a line is never in this run: the run is anchored on the LAST signature block before the
    LAST ``--`` separator, and ends at the first blank line, RFQ reference line or non-label line.
    """
    lines = parsed.text.split("\n")
    spot = _signature_positions(lines, parsed.reply_to)
    if spot is None:
        return []
    reply, sep = spot
    run: list[str] = []
    for line in lines[reply + 1 : sep]:
        # A blank line ends the run. (It has no ": " either, so the last test alone would end it
        # too; the first one says what is meant.)
        if not line or line.startswith(_RFQ_REFERENCE_PREFIX) or ": " not in line:
            break
        run.append(line)
    return run


def identity_pairs(parsed: ParsedMessage) -> list[tuple[str, str]]:
    """The ``(label, value)`` pairs in the identity position of a parsed message, in order."""
    out: list[tuple[str, str]] = []
    for line in _identity_run(parsed):
        label, _, value = line.partition(": ")
        out.append((label, value))
    return out


def missing_identity_labels(parsed: ParsedMessage, labels: Sequence[str]) -> list[str]:
    """Required labels without a ``"<label>: "`` line whose value shows a letter or digit, in the
    identity position. A value made only of spaces, punctuation or invisible characters counts as
    missing. Returns labels only, never values."""
    run = _identity_run(parsed)

    def filled(label: str) -> bool:
        prefix = f"{label}: "
        return any(ln.startswith(prefix) and has_visible_text(ln[len(prefix):]) for ln in run)

    return [label for label in labels if not filled(label)]


def has_identity(parsed: ParsedMessage, labels: Sequence[str]) -> bool:
    """True iff every required label appears as a line start ``"<label>: "`` with a value that shows
    a letter or digit, in the identity position, before the footer separator. No required labels:
    always True."""
    return not missing_identity_labels(parsed, labels)
