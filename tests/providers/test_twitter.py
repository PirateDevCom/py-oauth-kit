from urllib.parse import parse_qs, urlsplit

import pytest

from py_oauth import AccessToken, Twitter, UserFetchError

REDIRECT_URI = "https://example.com/callback"


@pytest.fixture
def twitter(api):
    return Twitter("client-id", "client-secret", REDIRECT_URI, client=api.client)


def test_requires_pkce(twitter):
    with pytest.raises(ValueError):
        twitter.get_authorization_url("state")
    with pytest.raises(ValueError):
        twitter.get_access_token("code")


def test_authorization_url(twitter):
    url = twitter.get_authorization_url("state", code_verifier="verifier")
    params = {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}

    assert params["scope"] == "tweet.read users.read users.email"
    assert params["code_challenge_method"] == "S256"


def test_token_request(api, twitter):
    api.add("POST", Twitter.TOKEN_URL, json={"access_token": "token"})

    twitter.get_access_token("code", code_verifier="verifier")

    request = api.requests[0]
    assert request.headers["Authorization"].startswith("Basic ")
    assert "code_verifier=verifier" in request.content.decode()


def test_fetch_user(api, twitter):
    response = {
        "data": {
            "id": "2244994945",
            "name": "X Developers",
            "username": "XDevelopers",
            "profile_image_url": "https://pbs.twimg.com/profile.jpg",
            "confirmed_email": "dev@example.com",
        }
    }
    api.add("GET", Twitter.USER_INFO_URL, json=response)

    user = twitter.fetch_user(AccessToken(token="token"))

    assert user.id == "2244994945"
    assert user.email == "dev@example.com"
    assert user.email_verified is True
    assert user.name == "X Developers"
    assert user.username == "XDevelopers"
    assert user.avatar_url == "https://pbs.twimg.com/profile.jpg"
    assert user.raw == response
    assert api.requests[0].url.params["user.fields"] == Twitter.USER_FIELDS


def test_fetch_user_without_email(api, twitter):
    api.add("GET", Twitter.USER_INFO_URL, json={"data": {"id": "1", "username": "x"}})

    user = twitter.fetch_user(AccessToken(token="token"))

    assert user.email is None
    assert user.email_verified is False
    assert user.name == "x"


def test_fetch_user_missing_data(api, twitter):
    api.add("GET", Twitter.USER_INFO_URL, json={"errors": []})

    with pytest.raises(UserFetchError, match="missing data"):
        twitter.fetch_user(AccessToken(token="token"))


def test_problem_details_error(api, twitter):
    api.add(
        "GET",
        Twitter.USER_INFO_URL,
        status=401,
        json={"title": "Unauthorized", "detail": "Unauthorized", "status": 401},
    )

    with pytest.raises(UserFetchError) as exc_info:
        twitter.fetch_user(AccessToken(token="token"))

    assert exc_info.value.description == "Unauthorized"
    assert exc_info.value.status_code == 401
