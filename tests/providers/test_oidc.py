from urllib.parse import parse_qs, urlsplit

import pytest

from py_oauth import AccessToken, Google, LinkedIn, Yahoo

REDIRECT_URI = "https://example.com/callback"


@pytest.fixture(params=[Google, LinkedIn, Yahoo])
def provider(request, api):
    return request.param("client-id", "client-secret", REDIRECT_URI, client=api.client)


def query(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


def test_default_scopes(provider):
    url = provider.get_authorization_url("state")
    assert query(url)["scope"] == "openid email profile"


def test_fetch_user(api, provider):
    data = {
        "sub": "1234",
        "email": "jane@example.com",
        "email_verified": True,
        "name": "Jane Doe",
        "preferred_username": "jane",
        "picture": "https://example.com/jane.jpg",
    }
    api.add("GET", provider.USER_INFO_URL, json=data)

    user = provider.fetch_user(AccessToken(token="token"))

    assert user.id == "1234"
    assert user.email == "jane@example.com"
    assert user.email_verified is True
    assert user.name == "Jane Doe"
    assert user.username == "jane"
    assert user.avatar_url == "https://example.com/jane.jpg"
    assert user.raw == data


@pytest.mark.parametrize(
    ("claims", "expected"),
    [
        ({"given_name": "Jane", "family_name": "Doe"}, "Jane Doe"),
        ({"given_name": "Jane"}, "Jane"),
        ({"preferred_username": "jane"}, "jane"),
        ({"email": "jane@example.com"}, "Unknown"),
    ],
)
def test_name_fallbacks(api, provider, claims, expected):
    api.add("GET", provider.USER_INFO_URL, json={"sub": "1", **claims})
    assert provider.fetch_user(AccessToken(token="token")).name == expected


def test_string_email_verified(api, provider):
    api.add("GET", provider.USER_INFO_URL, json={"sub": "1", "email_verified": "true"})
    assert provider.fetch_user(AccessToken(token="token")).email_verified is True


class TestYahoo:
    def test_random_nonce(self):
        yahoo = Yahoo("id", "secret", REDIRECT_URI)

        first = query(yahoo.get_authorization_url("state"))["nonce"]
        second = query(yahoo.get_authorization_url("state"))["nonce"]

        assert first and first != second

    def test_nonce_can_be_overridden(self):
        yahoo = Yahoo("id", "secret", REDIRECT_URI)
        url = yahoo.get_authorization_url("state", extra_params={"nonce": "mine"})
        assert query(url)["nonce"] == "mine"
