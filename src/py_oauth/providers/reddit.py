import html
from collections.abc import Mapping, Sequence
from typing import Any

import httpx

from py_oauth.exceptions import OAuthError
from py_oauth.providers.base import OAuthProvider
from py_oauth.types import AccessToken, Identity


class Reddit(OAuthProvider):
    """OAuth 2.0 provider for Reddit sign-in.

    Reddit doesn't share the user's email, so ``Identity.email`` is always
    None.

    Args:
        client_id (str): Client ID from Reddit's app preferences.
        client_secret (str): Client secret from Reddit's app preferences.
        redirect_uri (str): URI Reddit redirects to after authorization. Must
            match the app's redirect URI.
        user_agent (str): User-Agent sent with every request. Reddit throttles
            or blocks generic ones, and asks for
            ``<platform>:<app ID>:<version> (by /u/<username>)``.
        client (httpx.Client | None): HTTP client to send requests with.
    """

    AUTHORIZATION_URL = "https://www.reddit.com/api/v1/authorize"
    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
    DEFAULT_SCOPES = ("identity",)
    CLIENT_AUTH = "basic"
    USER_INFO_URL = "https://oauth.reddit.com/api/v1/me"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        *,
        user_agent: str,
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(client_id, client_secret, redirect_uri, client=client)
        self._user_agent = user_agent

    def get_authorization_url(
        self,
        state: str,
        *,
        scopes: Sequence[str] | None = None,
        extra_params: Mapping[str, str] | None = None,
        code_verifier: str | None = None,
    ) -> str:
        # Reddit requires a duration; "permanent" also issues a refresh token.
        return super().get_authorization_url(
            state,
            scopes=scopes,
            extra_params={"duration": "temporary", **(extra_params or {})},
            code_verifier=code_verifier,
        )

    def fetch_user(self, token: AccessToken) -> Identity:
        data = self._get_user_info(self.USER_INFO_URL, token.token)
        username = self._get_str(data, "name")
        # The display name set on the user's profile, if any.
        profile = data.get("subreddit")
        title = self._get_str(profile, "title") if isinstance(profile, dict) else None
        # Reddit HTML-escapes the URL's query string ("&amp;").
        icon = self._get_str(data, "icon_img")

        return Identity(
            id=self._get_user_id(data, "id"),
            name=title or username or "Unknown",
            username=username,
            avatar_url=html.unescape(icon) if icon else None,
            raw=data,
        )

    def _send(
        self,
        method: str,
        url: str,
        *,
        error_cls: type[OAuthError],
        action: str,
        **kwargs: Any,
    ) -> Any:
        kwargs["headers"] = {
            "User-Agent": self._user_agent,
            **kwargs.get("headers", {}),
        }
        return super()._send(method, url, error_cls=error_cls, action=action, **kwargs)
