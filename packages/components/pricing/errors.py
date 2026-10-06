"""Exceptions raised by the pricing component. All derive from ValueError."""

from __future__ import annotations


class PricingError(ValueError):
    """Base class: invalid input to the offer and best-price engine."""


class OfferValidationError(PricingError):
    """A model field failed strict validation (type, range, shape)."""


class PricingConfigError(PricingError):
    """The configuration mapping is missing a required key or holds an invalid value."""


class RepositoryError(PricingError):
    """An offer repository call was refused."""


class DuplicateOfferError(RepositoryError):
    """An offer with that id already exists in the namespace the caller can see."""


class TenantScopeError(RepositoryError):
    """A write that the calling capability is not allowed to make (R7: tenant isolation)."""


class SourceError(PricingError):
    """A source payload or its column mapping is unusable as a whole (not one bad record)."""
