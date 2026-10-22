from collections.abc import Mapping
from typing import Any, ClassVar

from py_oauth.providers.base import OAuthProvider
from py_oauth.types import AccessToken, Identity


class OIDCProvider(OAuthProvider):
    """Base class for providers with a standard OpenID Connect userinfo endpoint.

    ``fetch_user`` maps the standard claims (OpenID Connect Core §5.1) to an
    ``Identity``. Subclasses set ``USER_INFO_URL`` alongside the usual
    ``OAuthProvider`` attributes.

    Attributes:
        USER_INFO_URL (str): The provider's userinfo endpoint.
    """

    DEFAULT_SCOPES = ("openid", "email", "profile")
    USER_INFO_URL: ClassVar[str]

    def fetch_user(self, token: AccessToken) -> Identity:
        data = self._get_user_info(self.USER_INFO_URL, token.token)
        return Identity(
            id=self._get_user_id(data, "sub"),
            email=self._get_str(data, "email"),
            email_verified=self._get_bool(data, "email_verified"),
            name=self._get_display_name(data),
            username=self._get_str(data, "preferred_username"),
            avatar_url=self._get_str(data, "picture"),
            raw=data,
        )

    def _get_display_name(self, data: Mapping[str, Any]) -> str:
        """Return the user's display name from userinfo claims.

        Falls back to the given and family names, then the preferred username.

        Args:
            data (Mapping[str, Any]): Parsed userinfo response.

        Returns:
            str: The display name, or ``"Unknown"`` if no name claim is present.
        """
        if name := self._get_str(data, "name"):
            return name
        parts = (self._get_str(data, "given_name"), self._get_str(data, "family_name"))
        full_name = " ".join(p for p in parts if p)
        return full_name or self._get_str(data, "preferred_username") or "Unknown"
