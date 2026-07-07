"""ISMS client exceptions."""

from __future__ import annotations


class IsmsError(Exception):
    """Base class for all ISMS client errors."""


class IsmsHTTPError(IsmsError):
    """Raised when the ISMS API returns a non-2xx status."""

    def __init__(self, status: int, message: str, body: str | None = None) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message
        self.body = body


class IsmsAuthError(IsmsHTTPError):
    """Raised on 401/403 responses."""


class IsmsNotFoundError(IsmsHTTPError):
    """Raised on 404 responses."""


class IsmsValidationError(IsmsHTTPError):
    """Raised on 400/422 responses."""
