from py_oauth.providers.base import OAuthProvider
from py_oauth.types import AccessToken, Identity


class Discord(OAuthProvider):
    """OAuth 2.0 provider for Discord sign-in.

    Args:
        client_id (str): Client ID from the Discord developer portal.
        client_secret (str): Client secret from the Discord developer portal.
        redirect_uri (str): URI Discord redirects to after authorization.
            Must be listed under the app's OAuth2 redirects.
        client (httpx.Client | None): HTTP client to send requests with.
    """

    AUTHORIZATION_URL = "https://discord.com/oauth2/authorize"
    TOKEN_URL = "https://discord.com/api/oauth2/token"
    DEFAULT_SCOPES = ("identify", "email")
    USER_INFO_URL = "https://discord.com/api/v10/users/@me"
    AVATAR_URL = "https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{ext}"

    def fetch_user(self, token: AccessToken) -> Identity:
        data = self._get_user_info(self.USER_INFO_URL, token.token)
        user_id = self._get_user_id(data, "id")

        avatar = self._get_str(data, "avatar")
        avatar_url = None
        if avatar is not None:
            # Animated avatars have an "a_" prefix and are served as GIFs.
            ext = "gif" if avatar.startswith("a_") else "png"
            avatar_url = self.AVATAR_URL.format(user_id=user_id, avatar=avatar, ext=ext)

        username = self._get_str(data, "username")
        return Identity(
            id=user_id,
            email=self._get_str(data, "email"),
            # "verified" is only returned with the email scope.
            email_verified=data.get("verified") is True,
            name=self._get_str(data, "global_name") or username or "Unknown",
            username=username,
            avatar_url=avatar_url,
            raw=data,
        )
