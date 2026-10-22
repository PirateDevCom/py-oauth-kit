from py_oauth.providers.oidc import OIDCProvider


class LinkedIn(OIDCProvider):
    """OAuth 2.0 provider for Sign In with LinkedIn using OpenID Connect.

    The app must have the "Sign In with LinkedIn using OpenID Connect" product
    added in the LinkedIn developer portal, or LinkedIn rejects the default
    scopes.

    Args:
        client_id (str): Client ID from the LinkedIn developer portal.
        client_secret (str): Client secret from the LinkedIn developer portal.
        redirect_uri (str): URI LinkedIn redirects to after authorization.
            Must be listed under the app's authorized redirect URLs.
        client (httpx.Client | None): HTTP client to send requests with.
    """

    AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USER_INFO_URL = "https://api.linkedin.com/v2/userinfo"
