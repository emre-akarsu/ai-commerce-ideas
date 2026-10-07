"""Explanations as fixed templates over typed values (CLAUDE.md rule 3: provenance, no free text).

Every sentence the engine produces comes from `TEMPLATES`, filled with ids, enum values, Decimals
and dates that the engine itself validated or computed. No vendor free text and no model output can
reach an explanation: a parameter is a plain token or number, never text with spaces or links.
A UI localises by `code`; the English text here is the default.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from .errors import PricingError

_SAFE_PARAM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:+#=-]{0,119}")

TEMPLATES: dict[str, str] = {
    # ---- facts about one offer (used as flags, and as the reason an offer was excluded)
    "stale": "Offer {offer_id} was observed {age_hours} h ago; the limit for {source_kind} is "
             "{max_hours} h.",
    "expired": "Offer {offer_id} was valid until {valid_until}, which has passed.",
    "observed_in_future": "Offer {offer_id} is dated later than the current time, so its date "
                          "cannot show that it is fresh.",
    "vat_basis_unknown": "Offer {offer_id} does not say whether its price includes VAT; a person "
                         "must confirm the basis before it can be compared.",
    "vat_basis_assumed": "Offer {offer_id} does not say whether its price includes VAT; the "
                         "deployment default ({basis}) was assumed.",
    "vat_rate_mismatch": "Offer {offer_id} states a VAT rate of {stated_rate} but this deployment "
                         "converts at {configured_rate}; a person must confirm the price basis.",
    "currency_not_comparable": "Offer {offer_id} is priced in {currency}; comparison uses "
                               "{base_currency} and no exchange rate is applied.",
    "out_of_stock": "Offer {offer_id} is out of stock.",
    "low_stock": "Offer {offer_id} is reported as low stock.",
    "stock_unknown": "Offer {offer_id} does not state stock availability.",
    "unit_not_convertible": "Offer {offer_id} cannot be converted from its pack unit "
                            "({pack_unit}) to the line unit ({line_unit}) with the catalogue "
                            "unit basis for SKU {sku_id}.",
    "price_outlier_low": "Offer {offer_id} has a unit price of {unit_price}, more than {ratio} "
                         "times below the median {median} of {peers} comparable offers.",
    "price_outlier_high": "Offer {offer_id} has a unit price of {unit_price}, more than {ratio} "
                          "times above the median {median} of {peers} comparable offers.",
    "index_band_low": "Offer {offer_id} has a unit price of {unit_price}, below the reference "
                      "band {low} to {high}.",
    "index_band_high": "Offer {offer_id} has a unit price of {unit_price}, above the reference "
                       "band {low} to {high}.",
    "substitution_not_approved": "Offer {offer_id} is for SKU {sku_id} (tier {tier}), which has "
                                 "no recorded substitution approval.",
    "indicative_only": "Offer {offer_id} is indicative only (its source, price type, validity or "
                       "attestation do not allow a quote line) and is never selected.",
    "below_moq": "The required quantity is below the minimum order of offer {offer_id}; "
                 "{packs} pack(s) must be bought (minimum {moq}).",
    "order_multiple_applied": "Offer {offer_id} is sold in multiples of {multiple} pack(s); "
                              "{packs} pack(s) must be bought.",
    "lead_time_unknown": "Offer {offer_id} does not state a lead time.",
    "delivery_unknown": "Offer {offer_id} states no delivery terms; delivery is not included in "
                        "its cost.",
    "delivery_basis_unknown": "The VAT basis of the delivery terms of offer {offer_id} is not "
                              "stated; delivery is not included in its cost.",
    "unit_converted": "Offer {offer_id}: one pack holds {pack_content} {unit} of SKU {sku_id} "
                      "through the catalogue unit basis.",
    "surplus": "Buying whole packs of offer {offer_id} gives {surplus} {unit} more than required.",
    # ---- the decision for one line
    "selected_lowest_landed_cost": "Offer {offer_id} from {merchant_id} (SKU {sku_id}) has the "
                                   "lowest landed cost: {landed} {currency} for {quantity} "
                                   "{unit} ({packs} pack(s); goods {goods}, delivery {delivery}; "
                                   "{basis}).",
    "selected_lowest_goods_cost": "Offer {offer_id} from {merchant_id} (SKU {sku_id}) has the "
                                  "lowest goods cost: {goods} {currency} for {quantity} {unit} "
                                  "({packs} pack(s); {basis}); delivery is not part of this "
                                  "comparison.",
    "selected_only_eligible": "Offer {offer_id} is the only eligible offer.",
    "tie_break": "Offers {winner_id} and {other_id} tie on cost; the {criterion} rule decides.",
    "indicative_range": "Indicative only, not a quote: {low} to {high} {currency} per {unit} "
                        "({basis}) from {count} search snapshot(s).",
    "basket_exact": "Basket solved exactly over {components} independent group(s) of lines.",
    "basket_heuristic": "Basket solved by greedy search with local improvement for {lines} "
                        "line(s) (exact search limit {limit} lines per group); the true optimum "
                        "is at most {gap} {currency} lower.",
    "no_offers": "No offers were found for the approved SKUs of line {line_id}.",
    "no_eligible_offer": "Offers exist for line {line_id} but none is eligible; see the excluded "
                         "offers.",
    "indicative_only_line": "Line {line_id} has only indicative prices and is excluded from firm "
                            "totals.",
}


def _fmt(value: object, name: str) -> str:
    if isinstance(value, bool) or isinstance(value, float):
        raise PricingError(f"reason parameter {name} must not be a bool or float")
    if isinstance(value, Enum):
        text = str(value.value)
    elif isinstance(value, Decimal):
        text = format(value, "f")
    elif isinstance(value, datetime | date):
        text = value.isoformat()
    elif isinstance(value, int | str):
        text = str(value)
    else:
        raise PricingError(f"reason parameter {name} has unsupported type {type(value).__name__}")
    if _SAFE_PARAM.fullmatch(text) is None:
        raise PricingError(f"reason parameter {name} is not a plain token or number")
    return text


def _fields(template: str) -> set[str]:
    return {field for _, field, _, _ in string.Formatter().parse(template) if field}


@dataclass(frozen=True, slots=True)
class Reason:
    code: str
    params: tuple[tuple[str, str], ...] = ()

    @property
    def text(self) -> str:
        return TEMPLATES[self.code].format(**dict(self.params))


def make_reason(code: str, **params: object) -> Reason:
    """Build a reason; the parameters must be exactly the fields of the code's template."""
    template = TEMPLATES.get(code)
    if template is None:
        raise PricingError(f"unknown reason code {code!r}")
    if set(params) != _fields(template):
        raise PricingError(f"reason {code!r} needs exactly {sorted(_fields(template))}")
    return Reason(code, tuple(sorted((k, _fmt(v, k)) for k, v in params.items())))
