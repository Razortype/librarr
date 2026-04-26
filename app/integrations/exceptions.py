from __future__ import annotations


class IntegrationError(Exception):
    """Base for all integration errors."""


class OpenLibraryError(IntegrationError):
    """Base for Open Library errors."""


class OLNotFoundError(OpenLibraryError):
    """Resource not found (404). Not retried."""


class OLServerError(OpenLibraryError):
    """5xx from Open Library."""

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"OL {status_code}: {message}")


class OLRateLimitError(OpenLibraryError):
    """429 from Open Library. Respect Retry-After if present."""

    def __init__(self, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(f"OL rate limited, retry_after={retry_after}")


class OLTimeoutError(OpenLibraryError):
    """Timeout connecting to or reading from Open Library."""


class CloudClientError(IntegrationError):
    """Base for librarr-cloud errors."""


class CloudTimeoutError(CloudClientError):
    """Timeout connecting to or reading from librarr-cloud."""


class CloudServerError(CloudClientError):
    """5xx from librarr-cloud."""

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"Cloud {status_code}: {message}")


class CloudRateLimitError(CloudClientError):
    """429 from librarr-cloud."""

    def __init__(self, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(f"Cloud rate limited, retry_after={retry_after}")


class CloudRequestError(CloudClientError):
    """4xx (non-429) from librarr-cloud — signals a programmer error."""

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(f"Cloud {status_code}: {message}")
