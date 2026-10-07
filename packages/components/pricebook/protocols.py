"""What the price book reads from a quote, as structural types.

The price book does not import the quoting package (a repository test keeps every other package
from importing it). The caller hands in the quoting package's `QuoteResult`, which has these
attributes; only reading is needed and nothing is re-priced. Buckets and units are compared by
their string `value`, so any enum with the same values works.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any, Protocol


class _HasValue(Protocol):
    @property
    def value(self) -> str: ...


class OfferLike(Protocol):
    @property
    def merchant_id(self) -> str: ...


class PricedOfferLike(Protocol):
    @property
    def offer(self) -> OfferLike: ...


class IndicativeLike(Protocol):
    @property
    def low(self) -> Decimal: ...

    @property
    def unit(self) -> Any: ...

    @property
    def offers(self) -> Sequence[PricedOfferLike]: ...


class KitLike(Protocol):
    @property
    def kit_line_id(self) -> str: ...


class RequestLike(Protocol):
    @property
    def text(self) -> str: ...

    @property
    def quantity(self) -> Decimal: ...

    @property
    def unit(self) -> _HasValue: ...

    @property
    def kit(self) -> KitLike | None: ...


class ReasonLike(Protocol):
    @property
    def code(self) -> str: ...


class PricedLineLike(Protocol):
    @property
    def status(self) -> _HasValue: ...


class LineResultLike(Protocol):
    @property
    def line_id(self) -> str: ...

    @property
    def bucket(self) -> _HasValue: ...

    @property
    def request(self) -> RequestLike: ...

    @property
    def firm_offers(self) -> Sequence[PricedOfferLike]: ...

    @property
    def indicative(self) -> IndicativeLike | None: ...

    @property
    def reasons(self) -> Sequence[ReasonLike]: ...

    @property
    def excluded_codes(self) -> Sequence[str]: ...

    @property
    def flags(self) -> Sequence[str]: ...

    @property
    def priced(self) -> PricedLineLike | None: ...


class QuoteLike(Protocol):
    @property
    def tenant_id(self) -> str: ...

    @property
    def results(self) -> Sequence[LineResultLike]: ...
