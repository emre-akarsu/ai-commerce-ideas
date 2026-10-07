"""Which offers may feed a quote line (ADR-013 draft; legal notes risk ranking): a table."""

from __future__ import annotations

import dataclasses
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest

from components.pricing import (
    LineStatus,
    OfferValidationError,
    PriceType,
    SourceKind,
    TenantScopeError,
    quote_line_eligible,
)
from components.pricing.repository import InMemoryOfferStore

from .cfg import NOW, config
from .factories import line, offer

K = SourceKind
P = PriceType
D = Decimal

# (kind, price_type, account_specific, validity, attested) -> may feed a quote line
TABLE = [
    (K.MANUAL_QUOTE, P.QUOTED, True, True, True, True),
    (K.MANUAL_QUOTE, P.QUOTED, True, False, True, False),  # no validity
    (K.MANUAL_QUOTE, P.QUOTED, True, True, False, False),  # not confirmed by the tenant
    (K.TRADE_FEED, P.ACCOUNT_SPECIFIC, True, True, True, True),  # trade-account feed / EDI
    (K.TRADE_FEED, P.TRADE_LIST, False, True, True, True),  # user-supplied file, validity + attest
    (K.TRADE_FEED, P.TRADE_LIST, False, False, True, False),  # file without validity
    (K.TRADE_FEED, P.TRADE_LIST, False, True, False, False),  # file without attestation
    (K.TRADE_FEED, P.RETAIL, False, True, True, False),  # retail list price
    (K.MERCHANT_API, P.TRADE_LIST, False, True, True, False),  # public merchant API
    (K.MERCHANT_API, P.ACCOUNT_SPECIFIC, True, True, True, True),  # becomes a trade-account feed
    (K.MERCHANT_API, P.ACCOUNT_SPECIFIC, True, False, True, False),
    (K.AFFILIATE_FEED, P.RETAIL, False, True, True, False),
    (K.AFFILIATE_FEED, P.ACCOUNT_SPECIFIC, True, True, True, False),  # never, whatever it claims
    (K.SEARCH_SNAPSHOT, P.QUOTED, True, True, True, False),  # never
]


@pytest.mark.parametrize(("kind", "ptype", "acct", "validity", "attested", "expected"), TABLE)
def test_quote_line_eligibility_table(
    kind: K, ptype: P, acct: bool, validity: bool, attested: bool, expected: bool
) -> None:
    assert quote_line_eligible(kind, ptype, acct, validity, attested) is expected


def test_the_table_covers_every_source_kind() -> None:
    assert {row[0] for row in TABLE} == set(K)


@pytest.mark.parametrize(("kind", "ptype", "acct", "validity", "attested", "expected"), TABLE)
def test_offer_is_indicative_exactly_when_not_eligible(
    kind: K, ptype: P, acct: bool, validity: bool, attested: bool, expected: bool
) -> None:
    o = offer(kind=kind, price_type=ptype, account_specific=acct, attested=attested,
              valid_until=NOW + timedelta(days=1) if validity else None)
    assert o.is_indicative is (not expected)


def test_new_offer_fields_are_validated() -> None:
    o = offer()
    for kw in ({"price_type": "retail"}, {"account_specific": 1}, {"tenant_attested": "yes"},
               {"visibility": "shared", "tenant_id": None}):  # private-only fields on shared
        with pytest.raises(OfferValidationError):
            dataclasses.replace(o, **kw)
    with pytest.raises(OfferValidationError):  # account_specific type needs the flag
        offer(price_type=P.ACCOUNT_SPECIFIC, account_specific=False)
    with pytest.raises(OfferValidationError):  # account-specific data is never shared
        offer(tenant=None, account_specific=True, attested=False)


def test_defaults_are_conservative_retail_unattested_so_indicative() -> None:
    from components.pricing import Offer
    fields = {f.name: f.default for f in dataclasses.fields(Offer)}
    assert fields["price_type"] is P.RETAIL
    assert fields["account_specific"] is False and fields["tenant_attested"] is False


@pytest.mark.parametrize("bad", [
    dict(account_specific=True), dict(price_type=P.ACCOUNT_SPECIFIC),
    dict(price_type=P.QUOTED), dict(kind=K.MANUAL_QUOTE), dict(licence="affiliate-terms"),
    dict(licence="merchant-agreement"),
])
def test_shared_writer_refuses_account_specific_quoted_and_unlicensed_offers(
    bad: dict[str, Any]
) -> None:
    w = InMemoryOfferStore(config()).shared_writer()
    kw: dict[str, Any] = {"tenant": None, "attested": False, **bad}
    try:
        built = offer("x", **kw)
    except OfferValidationError:  # some combinations cannot even be built as shared offers
        return
    with pytest.raises(TenantScopeError):
        w.add_shared(built)


def test_shared_writer_checks_the_licence_allows_shared_storage_not_just_a_token() -> None:
    w = InMemoryOfferStore(config()).shared_writer()
    w.add_shared(offer("ok", tenant=None, price_type=P.TRADE_LIST))
    custom = InMemoryOfferStore(config(), shareable_licences=frozenset({"open-licence"}))
    with pytest.raises(TenantScopeError, match="licence"):
        custom.shared_writer().add_shared(offer("syn", tenant=None))
    custom.shared_writer().add_shared(offer("op", tenant=None, licence="open-licence"))


def test_indicative_offers_are_priced_as_a_range_never_selected_or_totalled() -> None:
    from components.pricing import price_line_from_offers
    cfg = config()
    firm = offer("firm", amount="10.00", merchant="m1")
    cases = {
        "affiliate": offer("aff", amount="1.00", merchant="m2", kind=K.AFFILIATE_FEED),
        "public_api": offer("api", amount="1.00", merchant="m3", kind=K.MERCHANT_API),
        "no_validity": offer("nov", amount="1.00", merchant="m4", valid_until=None),
        "unattested": offer("una", amount="1.00", merchant="m5", attested=False),
    }
    for off in cases.values():
        res = price_line_from_offers(line(), [firm, off], cfg, NOW)
        assert res.best is not None and res.best.offer.offer_id == "firm"
        assert res.indicative is not None and res.indicative.count == 1
        assert res.indicative.offers[0].offer.offer_id == off.offer_id
        assert "indicative_only" in res.indicative.offers[0].flags
    only = price_line_from_offers(line(), list(cases.values()), cfg, NOW)
    assert only.status is LineStatus.INDICATIVE_ONLY and only.best is None
