from py_oauth.providers.base import OAuthProvider
from py_oauth.types import AccessToken, Identity


class Amazon(OAuthProvider):
    """OAuth 2.0 provider for Login with Amazon.

    Amazon doesn't report whether the user's email is verified, so
    ``Identity.email_verified`` is always False. Amazon has no username, so
    ``Identity.name`` is ``"Unknown"`` if the profile has no name.

    Args:
        client_id (str): Client ID from the Login with Amazon console.
        client_secret (str): Client secret from the Login with Amazon console.
        redirect_uri (str): URI Amazon redirects to after authorization. Must
            be listed under the security profile's allowed return URLs.
        client (httpx.Client | None): HTTP client to send requests with.
    """

    AUTHORIZATION_URL = "https://www.amazon.com/ap/oa"
    # Any regional token endpoint works; apps aren't tied to a region.
    TOKEN_URL = "https://api.amazon.com/auth/o2/token"
    DEFAULT_SCOPES = ("profile",)
    USER_INFO_URL = "https://api.amazon.com/user/profile"

    def fetch_user(self, token: AccessToken) -> Identity:
        data = self._get_user_info(self.USER_INFO_URL, token.token)
        return Identity(
            id=self._get_user_id(data, "user_id"),
            email=self._get_str(data, "email"),
            name=self._get_str(data, "name") or "Unknown",
            raw=data,
        )
