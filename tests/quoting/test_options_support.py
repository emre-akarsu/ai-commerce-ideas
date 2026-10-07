"""Builders for the quote-options tests: hand-built firm offers priced by the real pricing engine.

No file, network or model is involved. Offers are synthetic; merchants are labels."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal

from components.core.fakes import FakeClock
from components.pricing import (
    DeliveryTerms,
    MatchedSku,
    Offer,
    PricedLine,
    PricingConfig,
    ResolvedLine,
    Unit,
    price_line_from_offers,
)
from components.quoting import OptionsConfig, OptionSet, build_options

from .conftest import NOW, PRICING_MAPPING, TENANT_A
from .helpers import offer

D = Decimal
FLAT10_FREE200 = DeliveryTerms(flat_fee=D("10.00"), free_over=D("200.00"))
FLAT5 = DeliveryTerms(flat_fee=D("5.00"))


def pcfg() -> PricingConfig:
    return PricingConfig.from_mapping(PRICING_MAPPING)


def mk_offer(sku: str, merchant: str, amount: str, *, lead: int | None = 1, tenant: str = TENANT_A,
             firm: bool = True, delivery: DeliveryTerms | None = FLAT5,
             offer_id: str | None = None, moq: int = 1) -> Offer:
    base = offer(sku, merchant, amount, tenant=tenant, firm=firm, delivery=delivery,
                 offer_id=offer_id, moq=moq)
    return replace(base, lead_time_days=lead)


def priced(line_id: str, offers: Sequence[Offer], qty: str = "1", cfg: PricingConfig | None = None
           ) -> PricedLine:
    skus = tuple(sorted({o.sku_id for o in offers}))
    line = ResolvedLine(line_id=line_id, skus=tuple(MatchedSku(s) for s in skus),
                        quantity=D(qty), unit=Unit.EACH, description=f"line {line_id}")
    return price_line_from_offers(line, list(offers), cfg or pcfg(), NOW)


def world(spec: Mapping[str, Mapping[str, tuple[str, int | None]]],
          delivery: Mapping[str, DeliveryTerms | None] | None = None, tenant: str = TENANT_A
          ) -> list[PricedLine]:
    """spec: line id -> {merchant: (price per piece, lead days or None)}; quantity is 1."""
    delivery = delivery or {}
    out = []
    for lid, merchants in spec.items():
        offers = [mk_offer(f"sku-{lid}", m, amount, lead=lead, tenant=tenant,
                           delivery=delivery.get(m, FLAT5))
                  for m, (amount, lead) in merchants.items()]
        out.append(priced(lid, offers))
    return out


def options(lines: Sequence[PricedLine], *, preferred: Sequence[str] = (),
            config: OptionsConfig | None = None, tenant: str = TENANT_A) -> OptionSet:
    return build_options(lines, pcfg(), tenant, FakeClock(NOW), preferred=preferred,
                         config=config)
