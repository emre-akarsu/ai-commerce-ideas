"""Exact money arithmetic helpers (hard rule: money is Decimal, never float).

Rounding policy used by the whole component (documented in docs/architecture/pricing-engine.md):

* Every price, quantity and fee is a ``Decimal`` (ints only for counts). Floats are rejected.
* Intermediate values are exact rationals (``fractions.Fraction``): VAT conversion, pack content
  and unit conversion never round. A result is rounded exactly once, when it becomes a money
  amount or a displayed unit price.
* Money amounts: half-up (a value exactly half way goes up) to the currency's minor unit
  (``PricingConfig.minor_unit_places``, default 2).
* Unit prices shown to people: 4 decimal places, half-up (the repo's ``inc_to_ex_tax`` uses the
  same 4 places).
* Pack counts: ceiling, computed exactly.
"""

from __future__ import annotations

from decimal import (
    ROUND_HALF_UP,
    Context,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    Overflow,
)
from fractions import Fraction

from .errors import OfferValidationError, PricingError

# A private, fixed context: results never depend on the global decimal context.
CTX = Context(
    prec=60, rounding=ROUND_HALF_UP, Emin=-999, Emax=999,
    traps=[InvalidOperation, DivisionByZero, Overflow],
)
MAX_VALUE = Decimal("1000000000")  # 1e9: far above any price, fee or quantity we handle
MAX_PLACES = 6
UNIT_PRICE_PLACES = 4


def check_decimal(
    value: object,
    name: str,
    *,
    minimum: Decimal | None = None,
    maximum: Decimal | None = None,
    min_exclusive: bool = False,
    max_places: int = MAX_PLACES,
    error: type[PricingError] = OfferValidationError,
) -> Decimal:
    """Return `value` if it is a finite Decimal inside the bounds, else raise `error`.

    Floats, ints, bools and strings are rejected on purpose: money and quantities are built from
    explicit Decimals so that no float ever enters a calculation."""
    if isinstance(value, bool) or not isinstance(value, Decimal):
        raise error(f"{name} must be a Decimal, got {type(value).__name__}")
    if not value.is_finite():
        raise error(f"{name} must be a finite number")
    exponent = value.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -max_places:
        raise error(f"{name} has more than {max_places} decimal places")
    if abs(value) > MAX_VALUE:
        raise error(f"{name} is out of range")
    if minimum is not None and (value < minimum or (min_exclusive and value == minimum)):
        raise error(f"{name} must be {'>' if min_exclusive else '>='} {minimum}")
    if maximum is not None and value > maximum:
        raise error(f"{name} must be <= {maximum}")
    if isinstance(exponent, int) and exponent > 0:
        value = value.quantize(Decimal(1), context=CTX)
    return value


def check_int(
    value: object,
    name: str,
    *,
    minimum: int,
    maximum: int,
    error: type[PricingError] = OfferValidationError,
) -> int:
    """Return `value` if it is a real int (not bool, float or Decimal) in [minimum, maximum]."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise error(f"{name} must be an integer, got {type(value).__name__}")
    if not minimum <= value <= maximum:
        raise error(f"{name} must be between {minimum} and {maximum}")
    return value


def frac_to_decimal(value: Fraction, places: int) -> Decimal:
    """Round the exact rational `value` (>= 0) half-up to `places` decimal places."""
    if value < 0:
        raise ValueError("negative amounts are not supported")
    scaled = value * 10**places
    rounded = (2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator)
    return Decimal(rounded).scaleb(-places, context=CTX)


def quantize_places(value: Decimal, places: int) -> Decimal:
    """Round a Decimal half-up to `places` decimal places (same rule as `frac_to_decimal`)."""
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP, context=CTX)


def ceil_div(numerator: Fraction, denominator: Fraction) -> int:
    """Exact ceiling of numerator / denominator for positive rationals."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return -((-numerator) // denominator)


def fraction_to_exact_decimal(value: Fraction) -> Decimal:
    """Decimal approximation of a rational at 60 significant digits (for comparisons only)."""
    return CTX.divide(Decimal(value.numerator), Decimal(value.denominator))


def median(values: list[Decimal]) -> Decimal:
    """Median; the mean of the two middle values for an even count (exact, a halving)."""
    if not values:
        raise ValueError("median of nothing")
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return CTX.divide(ordered[mid - 1] + ordered[mid], Decimal(2))
