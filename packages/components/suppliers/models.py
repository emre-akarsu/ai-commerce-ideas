"""Supplier and assumption records (api-contract-mvp.md sections 1 and 2).

These live beside the frozen ``domain.Vendor`` instead of inside it (``domain.py`` is frozen): a
``SupplierProfile`` is keyed by ``(tenant_id, vendor_id)`` and carries what the buyer knows about the
supplier (account, delivery threshold, contact kind), the admin attestation that the supplier was
checked, and the suppression flag. An ``Assumption`` is one row of the per-request ledger of values
the requester did not state.

Money uses ``Decimal`` with an explicit currency (R5). Nothing here reads or writes request state;
state changes happen in the workflow module.
"""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from components.send_service.message import is_plain_line

AccountType = Literal["cash", "credit"]
ContactKind = Literal["company", "individual", "unknown"]
VerificationState = Literal["unverified", "attested"]
AssumptionSource = Literal["user_said", "default_template", "model_inference", "public_source"]
Confidence = Literal["high", "medium", "low"]
AssumptionStatus = Literal["open", "confirmed", "invalidated"]

MAX_ONE_LINE = 200


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Money(_M):
    """An amount with an explicit currency. Never a float."""

    amount: Decimal
    currency: str = Field(pattern=r"^[A-Z]{3}$")

    @field_validator("amount")
    @classmethod
    def _non_negative_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value < 0:
            raise ValueError("amount must be a finite, non-negative decimal")
        return value


def _one_line(value: str | None) -> str | None:
    """Single-line plain text: the message layer's own rule (no control, line-break, zero-width or
    bidirectional character), the same one every other one-line field is held to."""
    if value is not None and not is_plain_line(value):
        raise ValueError("must be one line of plain text")
    return value


class Verification(_M):
    state: VerificationState = "unverified"
    attested_by: str | None = None
    attested_at: datetime | None = None
    note: str | None = Field(default=None, max_length=MAX_ONE_LINE)

    _plain_note = field_validator("note")(_one_line)

    @model_validator(mode="after")
    def _attested_has_who_and_when(self) -> Verification:
        if self.state == "attested" and (not self.attested_by or self.attested_at is None):
            raise ValueError("an attestation records who and when")
        return self


class SupplierProfile(_M):
    tenant_id: str
    vendor_id: str
    account_number: str | None = Field(default=None, max_length=MAX_ONE_LINE)
    account_type: AccountType | None = None
    credit_days: int | None = Field(default=None, ge=0, le=3650)
    delivery_threshold: Money | None = None
    quote_validity_days: int | None = Field(default=None, ge=1, le=3650)
    contact_kind: ContactKind = "unknown"
    verification: Verification = Field(default_factory=Verification)
    suppressed: bool = False

    _plain_number = field_validator("account_number")(_one_line)

    @property
    def id(self) -> str:  # repository key: one profile per (tenant, vendor)
        return self.vendor_id


class Assumption(_M):
    id: str
    tenant_id: str
    request_id: str
    statement: str = Field(max_length=500)
    source: AssumptionSource
    confidence: Confidence
    status: AssumptionStatus = "open"
    critical: bool
    gate: str | None = None
    created_at: datetime
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    attribute: str | None = None  # the request attribute the row is about (None: not an attribute)
    value: str | None = None

    @field_validator("statement")
    @classmethod
    def _one_line(cls, value: str) -> str:
        return " ".join(value.split())


def confidence_label(score: float) -> Confidence:
    if math.isnan(score):
        return "low"
    return "high" if score >= 0.9 else "medium" if score >= 0.6 else "low"  # noqa: PLR2004
