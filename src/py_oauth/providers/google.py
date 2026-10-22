from py_oauth.providers.oidc import OIDCProvider


class Google(OIDCProvider):
    """OAuth 2.0 provider for Google sign-in.

    Args:
        client_id (str): Client ID from the Google Cloud console.
        client_secret (str): Client secret from the Google Cloud console.
        redirect_uri (str): URI Google redirects to after authorization.
            Must be listed under the client's authorized redirect URIs.
        client (httpx.Client | None): HTTP client to send requests with.

    Google only returns a refresh token if the authorization URL includes
    ``access_type=offline``, and only on the user's first consent. To get one
    again, also pass ``prompt=consent``::

        provider.get_authorization_url(
            state, extra_params={"access_type": "offline", "prompt": "consent"}
        )
    """

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
