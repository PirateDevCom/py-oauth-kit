class OAuthError(Exception):
    """Base class for all py-oauth-kit errors.

    ``str()`` of the error includes the provider's error code and description,
    when present.

    Args:
        message (str): Human-readable summary of the error.
        error (str | None): OAuth error code from the provider, e.g.
            ``"invalid_grant"``.
        description (str | None): Error description from the provider.
        status_code (int | None): HTTP status code of the provider's
            response, if there was one.

    Attributes:
        error (str | None): OAuth error code from the provider.
        description (str | None): Error description from the provider.
        status_code (int | None): HTTP status code of the provider's response.
    """

    def __init__(
        self,
        message: str,
        *,
        error: str | None = None,
        description: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.error = error
        self.description = description
        self.status_code = status_code

    def __str__(self) -> str:
        message = super().__str__()
        details = [d for d in (self.error, self.description) if d]
        return f"{message} ({': '.join(details)})" if details else message


class TokenExchangeError(OAuthError):
    """Exchanging the authorization code for an access token failed."""


class UserFetchError(OAuthError):
    """Fetching the user's details from the provider failed."""
