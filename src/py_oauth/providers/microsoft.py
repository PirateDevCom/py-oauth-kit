import re
from dataclasses import replace

import httpx

from py_oauth.providers.oidc import OIDCProvider
from py_oauth.types import AccessToken, Identity


class Microsoft(OIDCProvider):
    """OAuth 2.0 provider for Microsoft sign-in (Microsoft identity platform).

    ``Identity.id`` is the OpenID Connect ``sub``, which is unique to your
    app: it differs from the user's object ID in Microsoft Graph.

    Microsoft doesn't verify the ``email`` claim, and in other tenants it's set
    by their admins, so ``Identity.email_verified`` is always False. Don't use
    the email to match users to existing accounts.

    The userinfo ``picture`` is a Microsoft Graph URL that needs the access
    token to download, so ``Identity.avatar_url`` is always None.

    Args:
        client_id (str): Application (client) ID from the Microsoft Entra
            admin center.
        client_secret (str): Client secret from the app registration.
        redirect_uri (str): URI Microsoft redirects to after authorization.
            Must be listed under the app registration's redirect URIs.
        tenant (str): Who can sign in: ``"common"`` (work, school and
            personal accounts), ``"organizations"`` (work and school),
            ``"consumers"`` (personal) or a tenant ID or domain. Single-tenant
            apps must pass their tenant.
        client (httpx.Client | None): HTTP client to send requests with.

    Raises:
        ValueError: If ``tenant`` isn't a tenant name, ID or domain.
    """

    AUTHORIZATION_URL = (
        "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
    )
    TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    USER_INFO_URL = "https://graph.microsoft.com/oidc/userinfo"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        *,
        tenant: str = "common",
        client: httpx.Client | None = None,
    ) -> None:
        # The tenant is part of the URL path, so a "/" or "?" would break it.
        if not re.fullmatch(r"[A-Za-z0-9.-]+", tenant):
            raise ValueError(f"Invalid Microsoft tenant: {tenant!r}")
        super().__init__(client_id, client_secret, redirect_uri, client=client)
        self.AUTHORIZATION_URL = self.AUTHORIZATION_URL.format(tenant=tenant)
        self.TOKEN_URL = self.TOKEN_URL.format(tenant=tenant)

    def fetch_user(self, token: AccessToken) -> Identity:
        identity = super().fetch_user(token)
        return replace(identity, email_verified=False, avatar_url=None)
