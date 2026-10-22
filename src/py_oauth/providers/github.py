from collections.abc import Mapping
from typing import ClassVar

from py_oauth.exceptions import UserFetchError
from py_oauth.providers.base import OAuthProvider
from py_oauth.types import AccessToken, Identity


class GitHub(OAuthProvider):
    """OAuth 2.0 provider for GitHub sign-in (OAuth Apps).

    The email comes from the user's primary address, which needs the
    ``user:email`` scope (requested by default). Without that scope, it falls
    back to the public profile email, which may be None, and
    ``Identity.email_verified`` is False.

    Args:
        client_id (str): Client ID from the OAuth App's settings.
        client_secret (str): Client secret from the OAuth App's settings.
        redirect_uri (str): URI GitHub redirects to after authorization.
            Must match or be under the app's authorization callback URL.
        client (httpx.Client | None): HTTP client to send requests with.
    """

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    DEFAULT_SCOPES = ("read:user", "user:email")
    USER_INFO_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    _API_HEADERS: ClassVar[Mapping[str, str]] = {
        "Accept": "application/vnd.github+json"
    }

    def fetch_user(self, token: AccessToken) -> Identity:
        data = self._get_user_info(
            self.USER_INFO_URL, token.token, headers=self._API_HEADERS
        )
        email, email_verified = self._get_primary_email(token.token)
        if email is None:
            email, email_verified = self._get_str(data, "email"), False

        login = self._get_str(data, "login")
        return Identity(
            id=self._get_user_id(data, "id"),
            email=email,
            email_verified=email_verified,
            name=self._get_str(data, "name") or login or "Unknown",
            username=login,
            avatar_url=self._get_str(data, "avatar_url"),
            raw=data,
        )

    def _get_primary_email(self, access_token: str) -> tuple[str | None, bool]:
        """Return the user's primary email and whether it's verified.

        Args:
            access_token (str): Access token value.

        Returns:
            tuple[str | None, bool]: The primary email and its verified
                status, or ``(None, False)`` if the token lacks the
                ``user:email`` scope or there's no primary email.

        Raises:
            UserFetchError: If the request fails for another reason.
        """
        try:
            emails = self._request_list(
                "GET",
                self.EMAILS_URL,
                error_cls=UserFetchError,
                action=f"{self._name} emails request",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    **self._API_HEADERS,
                },
                params={"per_page": 100},
            )
        except UserFetchError as exc:
            # GitHub returns 403 or 404 when the token lacks user:email, but
            # also 403 when rate limited, which mustn't look like a missing scope.
            rate_limited = "rate limit" in (exc.description or "").lower()
            if exc.status_code in (403, 404) and not rate_limited:
                return None, False
            raise

        for entry in emails:
            if isinstance(entry, dict) and entry.get("primary") is True:
                email = self._get_str(entry, "email")
                if email is not None:
                    return email, entry.get("verified") is True
        return None, False
