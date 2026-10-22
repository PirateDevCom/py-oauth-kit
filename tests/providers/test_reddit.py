from urllib.parse import parse_qs, urlsplit

import pytest

from py_oauth import AccessToken, Reddit

REDIRECT_URI = "https://example.com/callback"
USER_AGENT = "web:com.example.app:1.0 (by /u/example)"


@pytest.fixture
def reddit(api):
    return Reddit(
        "client-id",
        "client-secret",
        REDIRECT_URI,
        user_agent=USER_AGENT,
        client=api.client,
    )


def query(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


def test_default_duration(reddit):
    assert query(reddit.get_authorization_url("state"))["duration"] == "temporary"


def test_duration_can_be_overridden(reddit):
    url = reddit.get_authorization_url("state", extra_params={"duration": "permanent"})
    assert query(url)["duration"] == "permanent"


def test_token_request(api, reddit):
    api.add("POST", Reddit.TOKEN_URL, json={"access_token": "token"})

    reddit.get_access_token("code")

    request = api.requests[0]
    assert request.headers["User-Agent"] == USER_AGENT
    assert request.headers["Authorization"].startswith("Basic ")


def test_fetch_user(api, reddit):
    api.add(
        "GET",
        Reddit.USER_INFO_URL,
        json={
            "id": "abc12",
            "name": "spez",
            "icon_img": "https://styles.redditmedia.com/i.png?width=256&amp;s=x",
            "subreddit": {"title": "Steve"},
        },
    )

    user = reddit.fetch_user(AccessToken(token="token"))

    assert user.id == "abc12"
    assert user.email is None
    assert user.name == "Steve"
    assert user.username == "spez"
    assert user.avatar_url == "https://styles.redditmedia.com/i.png?width=256&s=x"
    assert api.requests[0].headers["User-Agent"] == USER_AGENT


@pytest.mark.parametrize("subreddit", [None, {}, {"title": ""}, "spez"])
def test_name_falls_back_to_username(api, reddit, subreddit):
    api.add(
        "GET",
        Reddit.USER_INFO_URL,
        json={"id": "abc12", "name": "spez", "subreddit": subreddit},
    )

    user = reddit.fetch_user(AccessToken(token="token"))

    assert user.name == "spez"
    assert user.avatar_url is None
