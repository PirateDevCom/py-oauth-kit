import hashlib
import hmac

from py_oauth.providers.base import OAuthProvider
from py_oauth.types import AccessToken, Identity


class Facebook(OAuthProvider):
    """OAuth 2.0 provider for Facebook Login.

    Facebook doesn't report whether the user's email is verified, so
    ``Identity.email_verified`` is always False. The email is None if the
    user has none or declined to share it.

    User info requests include an ``appsecret_proof``, so they work with the
    app's "Require App Secret" setting enabled.

    Args:
        client_id (str): App ID from the Meta app dashboard.
        client_secret (str): App secret from the Meta app dashboard.
        redirect_uri (str): URI Facebook redirects to after authorization.
            Must be listed under the app's valid OAuth redirect URIs.
        client (httpx.Client | None): HTTP client to send requests with.
    """

    # Unversioned calls use the app's oldest available version, so pin one.
    API_VERSION = "v26.0"
    AUTHORIZATION_URL = f"https://www.facebook.com/{API_VERSION}/dialog/oauth"
    TOKEN_URL = f"https://graph.facebook.com/{API_VERSION}/oauth/access_token"
    DEFAULT_SCOPES = ("email", "public_profile")
    SCOPE_SEPARATOR = ","
    USER_INFO_URL = f"https://graph.facebook.com/{API_VERSION}/me"
    USER_FIELDS = "id,name,email,picture.type(large)"

    def fetch_user(self, token: AccessToken) -> Identity:
        proof = hmac.new(
            self._client_secret.encode(), token.token.encode(), hashlib.sha256
        ).hexdigest()
        data = self._get_user_info(
            self.USER_INFO_URL,
            token.token,
            params={"fields": self.USER_FIELDS, "appsecret_proof": proof},
        )

        picture = data.get("picture")
        picture = picture.get("data") if isinstance(picture, dict) else None
        avatar_url = None
        # Users without a profile picture get a generic silhouette.
        if isinstance(picture, dict) and picture.get("is_silhouette") is not True:
            avatar_url = self._get_str(picture, "url")

        return Identity(
            id=self._get_user_id(data, "id"),
            email=self._get_str(data, "email"),
            name=self._get_str(data, "name") or "Unknown",
            avatar_url=avatar_url,
            raw=data,
        )
