from urllib.parse import parse_qs, urlsplit

import pytest

from py_oauth import AccessToken, Amazon

REDIRECT_URI = "https://example.com/callback"


@pytest.fixture
def amazon(api):
    return Amazon("client-id", "client-secret", REDIRECT_URI, client=api.client)


def test_authorization_url(amazon):
    url = amazon.get_authorization_url("state")

    assert url.startswith(f"{Amazon.AUTHORIZATION_URL}?")
    assert parse_qs(urlsplit(url).query)["scope"] == ["profile"]


def test_fetch_user(api, amazon):
    data = {"user_id": "amzn1.account.X", "name": "Jane Doe", "email": "j@example.com"}
    api.add("GET", Amazon.USER_INFO_URL, json=data)

    user = amazon.fetch_user(AccessToken(token="token"))

    assert user.id == "amzn1.account.X"
    assert user.email == "j@example.com"
    assert user.email_verified is False
    assert user.name == "Jane Doe"
    assert user.username is None
    assert user.raw == data
    assert api.requests[0].headers["Authorization"] == "Bearer token"


def test_fetch_user_without_name(api, amazon):
    api.add("GET", Amazon.USER_INFO_URL, json={"user_id": "1"})

    user = amazon.fetch_user(AccessToken(token="token"))

    assert user.name == "Unknown"
    assert user.email is None
