"""Plain data builders for the control-plane tests (synthetic data only)."""

from __future__ import annotations

import hashlib
from datetime import timedelta
from decimal import Decimal

from components.core.domain import (
    RFQ,
    Approval,
    ApprovalKind,
    PurchaseOrderDraft,
    Quote,
    Request,
    StandingRule,
    Vendor,
)
from components.core.fakes import FakeClock

T1 = "t-acme"
T2 = "t-other"
VENDOR_DOMAIN = "bearings-direct.example"
VENDOR_EMAIL = f"quotes@{VENDOR_DOMAIN}"
ALIAS = "buyer-acme@rfq.alias.example"
BUYER = "Pat Buyer"
BUYER_EMAIL = "pat@acme-plant.example"
PHONE = "+1 555 0100"
PII_KEY = hashlib.sha256(b"test-pii-key").digest()
APPROVAL_KEY = hashlib.sha256(b"test-approval-signing-key").digest()


def sha(data: bytes | str) -> str:
    raw = data.encode() if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()


def make_vendor(
    id: str = "v-1",  # noqa: A002
    tenant: str = T1,
    domain: str = VENDOR_DOMAIN,
    email: str = VENDOR_EMAIL,
    **kw: object,
) -> Vendor:
    return Vendor(id=id, tenant_id=tenant, name=f"Vendor {id}", domain=domain,
                  contact_email=email, **kw)  # type: ignore[arg-type]


def make_request(id: str = "req-1", tenant: str = T1, **kw: object) -> Request:  # noqa: A002
    return Request(id=id, tenant_id=tenant, requester="user:tech-1", family="deep_groove_ball",
                   raw_text="need 6205-2RS", quantity=4, **kw)  # type: ignore[arg-type]


def make_rfq(
    id: str = "rfq-1",  # noqa: A002
    tenant: str = T1,
    request_id: str = "req-1",
    vendor_id: str = "v-1",
    body: str = "Please quote 4 x 6205-2RS (SKF or equal). Need by Friday.",
    **kw: object,
) -> RFQ:
    return RFQ(id=id, tenant_id=tenant, request_id=request_id, vendor_id=vendor_id,
               subject="RFQ: 6205-2RS x4", body=body, **kw)  # type: ignore[arg-type]


def make_quote(id: str = "q-1", tenant: str = T1, version: int = 1, **kw: object) -> Quote:  # noqa: A002
    return Quote(id=id, tenant_id=tenant, rfq_id="rfq-1", vendor_id="v-1", version=version,
                 unit_price_each=Decimal("4.20"), currency="USD", **kw)  # type: ignore[arg-type]


def make_rule(
    id: str = "rule-1",  # noqa: A002
    tenant: str = T1,
    clock: FakeClock | None = None,
    **kw: object,
) -> StandingRule:
    now = (clock or FakeClock()).now()
    data: dict[str, object] = {
        "id": id, "tenant_id": tenant, "vendor_id": "v-1", "family": "deep_groove_ball",
        "max_amount": Decimal("500"), "max_count": 3, "expires_at": now + timedelta(days=30),
        "created_by": "user:admin-1",
    }
    data.update(kw)
    return StandingRule(**data)  # type: ignore[arg-type]


def make_po(id: str = "po-1", tenant: str = T1, **kw: object) -> PurchaseOrderDraft:  # noqa: A002
    data: dict[str, object] = {
        "id": id, "tenant_id": tenant, "request_id": "req-1", "quote_id": "q-1",
        "quote_version": 1, "vendor_id": "v-1", "mpn": "6205-2RS", "quantity": 4,
        "unit_price_each": Decimal("4.20"), "currency": "USD", "total": Decimal("16.80"),
    }
    data.update(kw)
    return PurchaseOrderDraft(**data)  # type: ignore[arg-type]


def make_approval(
    id: str = "appr-1",  # noqa: A002
    tenant: str = T1,
    clock: FakeClock | None = None,
    **kw: object,
) -> Approval:
    now = (clock or FakeClock()).now()
    data: dict[str, object] = {
        "id": id, "tenant_id": tenant, "kind": ApprovalKind.PER_MESSAGE, "mime_hash": sha("m"),
        "approver": "user:buyer-1", "nonce": f"nonce-{id}", "expires_at": now + timedelta(hours=1),
    }
    data.update(kw)
    return Approval(**data)  # type: ignore[arg-type]
