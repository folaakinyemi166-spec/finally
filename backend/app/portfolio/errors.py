"""Domain errors for trade execution."""

from __future__ import annotations


class PortfolioError(Exception):
    """Base class for portfolio domain errors."""


class UnknownTickerError(PortfolioError):
    """Raised when a trade references a ticker with no known price."""


class InsufficientCashError(PortfolioError):
    """Raised when a buy would cost more than the available cash balance."""


class InsufficientSharesError(PortfolioError):
    """Raised when a sell quantity exceeds the shares currently held."""
