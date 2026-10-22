import hashlib
import hmac
from urllib.parse import parse_qs, urlsplit

import pytest

from py_oauth import AccessToken, Facebook, UserFetchError

REDIRECT_URI = "https://example.com/callback"


@pytest.fixture
def facebook(api):
    return Facebook("app-id", "app-secret", REDIRECT_URI, client=api.client)


def picture(url: str, *, silhouette: bool = False) -> dict:
    return {"data": {"url": url, "is_silhouette": silhouette}}


def test_authorization_url(facebook):
    url = facebook.get_authorization_url("state")

    assert url.startswith(f"https://www.facebook.com/{Facebook.API_VERSION}/")
    assert parse_qs(urlsplit(url).query)["scope"] == ["email,public_profile"]


def test_fetch_user(api, facebook):
    data = {
        "id": "10",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "picture": picture("https://example.com/jane.jpg"),
    }
    api.add("GET", Facebook.USER_INFO_URL, json=data)

    user = facebook.fetch_user(AccessToken(token="token"))

    assert user.id == "10"
    assert user.email == "jane@example.com"
    assert user.email_verified is False
    assert user.name == "Jane Doe"
    assert user.avatar_url == "https://example.com/jane.jpg"


def test_sends_fields_and_appsecret_proof(api, facebook):
    api.add("GET", Facebook.USER_INFO_URL, json={"id": "10"})

    facebook.fetch_user(AccessToken(token="token"))

    params = dict(api.requests[0].url.params)
    proof = hmac.new(b"app-secret", b"token", hashlib.sha256).hexdigest()
    assert params == {"fields": Facebook.USER_FIELDS, "appsecret_proof": proof}


def test_silhouette_has_no_avatar(api, facebook):
    data = {
        "id": "10",
        "picture": picture("https://example.com/s.jpg", silhouette=True),
    }
    api.add("GET", Facebook.USER_INFO_URL, json=data)

    user = facebook.fetch_user(AccessToken(token="token"))

    assert user.avatar_url is None
    assert user.name == "Unknown"


def test_graph_api_error(api, facebook):
    error = {
        "error": {"message": "Session expired", "type": "OAuthException", "code": 190}
    }
    api.add("GET", Facebook.USER_INFO_URL, status=400, json=error)

    with pytest.raises(UserFetchError) as exc_info:
        facebook.fetch_user(AccessToken(token="token"))

    assert exc_info.value.error == "190"
    assert exc_info.value.description == "Session expired"
