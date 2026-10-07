"""Exceptions raised by the pricebook component. All derive from ValueError."""

from __future__ import annotations


class PriceBookError(ValueError):
    """Invalid input to the price book (a tenant mismatch, a bad merchant record, a bad file)."""


class RequestTemplateError(PriceBookError):
    """A request template or a placeholder value is not acceptable (unknown placeholder, URL,
    HTML, control characters). The draft is refused; nothing is repaired."""
