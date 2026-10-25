from py_oauth.exceptions import UserFetchError
from py_oauth.providers.base import OAuthProvider
from py_oauth.types import AccessToken, Identity


class Twitter(OAuthProvider):
    """OAuth 2.0 provider for X (formerly Twitter) sign-in.

    X requires PKCE: pass a ``code_verifier`` to ``get_authorization_url`` and
    ``get_access_token``.

    The email needs the ``users.email`` scope (requested by default) and the
    app's "Request email from users" permission enabled in the X Developer
    Console. X only returns confirmed emails, so ``Identity.email_verified`` is
    True whenever there's an email.

    Args:
        client_id (str): OAuth 2.0 client ID from the X Developer Console.
        client_secret (str): OAuth 2.0 client secret from the X Developer
            Console.
        redirect_uri (str): URI X redirects to after authorization. Must be
            listed under the app's callback URIs.
        client (httpx.Client | None): HTTP client to send requests with.
    """

    AUTHORIZATION_URL = "https://x.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.x.com/2/oauth2/token"
    # GET /2/users/me needs tweet.read as well as users.read.
    DEFAULT_SCOPES = ("tweet.read", "users.read", "users.email")
    CLIENT_AUTH = "basic"
    REQUIRES_PKCE = True
    USER_INFO_URL = "https://api.x.com/2/users/me"
    USER_FIELDS = "profile_image_url,confirmed_email"

    def fetch_user(self, token: AccessToken) -> Identity:
        response = self._get_user_info(
            self.USER_INFO_URL, token.token, params={"user.fields": self.USER_FIELDS}
        )
        data = response.get("data")
        if not isinstance(data, dict):
            raise UserFetchError(f"{self._name} user info response is missing data")

        email = self._get_str(data, "confirmed_email")
        username = self._get_str(data, "username")
        return Identity(
            id=self._get_user_id(data, "id"),
            email=email,
            email_verified=email is not None,
            name=self._get_str(data, "name") or username or "Unknown",
            username=username,
            avatar_url=self._get_str(data, "profile_image_url"),
            raw=response,
        )
