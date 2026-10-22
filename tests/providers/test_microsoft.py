import pytest

from py_oauth import AccessToken, Microsoft

REDIRECT_URI = "https://example.com/callback"


def test_default_tenant():
    microsoft = Microsoft("id", "secret", REDIRECT_URI)

    assert microsoft.AUTHORIZATION_URL == (
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    )
    assert microsoft.TOKEN_URL == (
        "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    )


def test_tenant_is_per_instance():
    microsoft = Microsoft(
        "id", "secret", REDIRECT_URI, tenant="contoso.onmicrosoft.com"
    )

    assert "/contoso.onmicrosoft.com/" in microsoft.get_authorization_url("state")
    assert "/contoso.onmicrosoft.com/" in microsoft.TOKEN_URL
    assert "{tenant}" in Microsoft.TOKEN_URL


@pytest.mark.parametrize("tenant", ["", "a/b", "a?b", "a b", "../common"])
def test_invalid_tenant(tenant):
    with pytest.raises(ValueError):
        Microsoft("id", "secret", REDIRECT_URI, tenant=tenant)


def test_fetch_user_never_trusts_email_or_picture(api):
    microsoft = Microsoft("id", "secret", REDIRECT_URI, client=api.client)
    api.add(
        "GET",
        Microsoft.USER_INFO_URL,
        json={
            "sub": "abc",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "email_verified": True,
            "picture": "https://graph.microsoft.com/v1.0/me/photo/$value",
        },
    )

    user = microsoft.fetch_user(AccessToken(token="token"))

    assert user.id == "abc"
    assert user.email == "jane@example.com"
    assert user.email_verified is False
    assert user.avatar_url is None
