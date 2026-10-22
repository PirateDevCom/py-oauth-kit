import secrets
from collections.abc import Mapping, Sequence

from py_oauth.providers.oidc import OIDCProvider


class Yahoo(OIDCProvider):
    """OAuth 2.0 provider for Yahoo sign-in.

    The app must have the OpenID Connect permissions (Email, Profile) enabled
    in the Yahoo developer console, or Yahoo rejects the default scopes.

    Args:
        client_id (str): Client ID from the Yahoo developer console.
        client_secret (str): Client secret from the Yahoo developer console.
        redirect_uri (str): URI Yahoo redirects to after authorization. Must
            match the app's redirect URI.
        client (httpx.Client | None): HTTP client to send requests with.
    """

    AUTHORIZATION_URL = "https://api.login.yahoo.com/oauth2/request_auth"
    TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
    USER_INFO_URL = "https://api.login.yahoo.com/openid/v1/userinfo"

    def get_authorization_url(
        self,
        state: str,
        *,
        scopes: Sequence[str] | None = None,
        extra_params: Mapping[str, str] | None = None,
        code_verifier: str | None = None,
    ) -> str:
        # Yahoo requires a nonce. The ID token isn't used (fetch_user calls the
        # userinfo endpoint), so a random one is enough.
        return super().get_authorization_url(
            state,
            scopes=scopes,
            extra_params={"nonce": secrets.token_urlsafe(), **(extra_params or {})},
            code_verifier=code_verifier,
        )
