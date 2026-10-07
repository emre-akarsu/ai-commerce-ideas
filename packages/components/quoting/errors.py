"""Exceptions raised by the quoting component. All derive from ValueError."""

from __future__ import annotations


class QuotingError(ValueError):
    """Invalid input to the quoting integration (a kit unit, a choice, an approval, a file)."""


class QuotingConfigError(QuotingError):
    """The configuration mapping holds an unknown key or an out-of-range value."""
