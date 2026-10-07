"""Trade-off sentences of the quote options: fixed templates over codes and typed values.

Never model text (CLAUDE.md rule 3). Parameters are tokens, integers or Decimals; a parameter can
not carry free text or a link. Every price in a sentence is followed by the VAT basis (`{basis}`
takes `ex_tax` or `inc_tax` and is shown as "ex VAT" / "inc VAT"). A UI localises by `code`.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass
from decimal import Decimal

from .options_config import OptionsError

_SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:+#=-]{0,119}")
BASIS_LABEL = {"ex_tax": "ex VAT", "inc_tax": "inc VAT"}
LABELS = {
    "cheapest": "Lowest total cost", "single_supplier": "Single supplier",
    "fewest_deliveries": "Fewest deliveries", "fastest": "Fastest",
    "preferred": "Preferred suppliers", "balanced": "Balanced",
}

TEMPLATES: dict[str, str] = {
    "total_is_lowest": "Lowest total of all options: {total} {currency} {basis}.",
    "extra_vs_lowest": "{extra} {currency} {basis} more than the lowest total.",
    "total_within_tolerance": "The total is within {pct}% of the lowest total (limit {limit} "
                              "{currency} {basis}).",
    "saves_vs_dearest": "{amount} {currency} {basis} less than the most expensive option shown.",
    "deliveries_fewer": "{count} fewer delivery(ies) than the lowest-total option ({deliveries} "
                        "instead of {other}).",
    "deliveries_more": "{count} more delivery(ies) than the lowest-total option ({deliveries} "
                       "instead of {other}).",
    "deliveries_same": "{deliveries} delivery(ies), as many as the lowest-total option.",
    "lead_earlier": "Latest lead time {days} day(s), {diff} day(s) earlier than the lowest-total "
                    "option.",
    "lead_later": "Latest lead time {days} day(s), {diff} day(s) later than the lowest-total "
                  "option.",
    "lead_same": "Latest lead time {days} day(s), the same as the lowest-total option.",
    "lead_known": "Latest lead time {days} day(s).",
    "lead_unknown": "{count} line(s) state no lead time, so the latest lead time is unknown and "
                    "may be later than shown.",
    "delivery_terms_unknown": "{count} supplier(s) state no usable delivery terms; delivery for "
                              "them is not included in the total.",
    "preferred_coverage": "{covered} of {lines} line(s) come from your preferred suppliers.",
    "preferred_none": "No line comes from your preferred suppliers.",
    "single_supplier_covers": "{merchant_id} can supply {covered} of {lines} line(s).",
    "single_supplier_outside": "{outside} line(s) it cannot supply are bought elsewhere for "
                               "{remainder} {currency} {basis}.",
    "single_supplier_all": "{merchant_id} supplies every line.",
    "balanced_score": "Balanced score {score} (0 is best), measured against your own budget, "
                      "required-by date and delivery limit; the weights are unsourced "
                      "placeholders.",
    "no_buyer_references": "No budget, required-by date or delivery limit was given, so no "
                           "balanced score is computed and no balanced option is shown.",
    "over_budget": "The total is over your budget.",
    "after_required_date": "Delivery is after your required-by date, or its date is unknown.",
    "over_delivery_cap": "More deliveries than your limit.",
    "uncovered_lines": "{count} firm line(s) are not covered by this option.",
    "indicative_excluded": "Indicative prices exist for {count} line(s) and are shown apart; "
                           "they are in no option.",
    "not_proven_optimal": "The basket optimiser could not prove the lowest total; a lower total "
                          "may exist.",
    "search_incomplete": "The search for this option stopped at its limit; a better answer may "
                         "exist.",
    "same_as": "Same as {option}.",
    "no_preferred_list": "No preferred suppliers are set, so this option is not produced.",
    "no_firm_lines": "No line has a firm offer, so there are no options.",
    "max_options": "Not shown: the limit of {limit} options was reached.",
}


def _fmt(value: object, name: str) -> str:
    if isinstance(value, bool) or isinstance(value, float):
        raise OptionsError(f"reason parameter {name} must not be a bool or float")
    text = format(value, "f") if isinstance(value, Decimal) else str(value)
    if not isinstance(value, Decimal | int | str) or _SAFE.fullmatch(text) is None:
        raise OptionsError(f"reason parameter {name} is not a plain token or number")
    return text


@dataclass(frozen=True, slots=True)
class OptionReason:
    code: str
    params: tuple[tuple[str, str], ...] = ()

    @property
    def text(self) -> str:
        values = dict(self.params)
        if "basis" in values:
            values["basis"] = BASIS_LABEL.get(values["basis"], values["basis"])
        if "option" in values:
            values["option"] = LABELS.get(values["option"], values["option"])
        return TEMPLATES[self.code].format(**values)


def reason(code: str, **params: object) -> OptionReason:
    template = TEMPLATES.get(code)
    if template is None:
        raise OptionsError(f"unknown option reason {code!r}")
    needed = {f for _, f, _, _ in string.Formatter().parse(template) if f}
    if set(params) != needed:
        raise OptionsError(f"reason {code!r} needs exactly {sorted(needed)}")
    return OptionReason(code, tuple(sorted((k, _fmt(v, k)) for k, v in params.items())))
