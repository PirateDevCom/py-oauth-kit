import pytest

from py_oauth import AccessToken, GitHub, TokenExchangeError, UserFetchError

REDIRECT_URI = "https://example.com/callback"
USER = {
    "id": 583231,
    "login": "octocat",
    "name": "The Octocat",
    "email": "public@example.com",
    "avatar_url": "https://avatars.githubusercontent.com/u/583231",
}


@pytest.fixture
def github(api):
    return GitHub("client-id", "client-secret", REDIRECT_URI, client=api.client)


def fetch(github):
    return github.fetch_user(AccessToken(token="token"))


def test_fetch_user(api, github):
    api.add("GET", GitHub.USER_INFO_URL, json=USER)
    api.add(
        "GET",
        GitHub.EMAILS_URL,
        json=[
            {"email": "other@example.com", "primary": False, "verified": True},
            {"email": "primary@example.com", "primary": True, "verified": True},
        ],
    )

    user = fetch(github)

    assert user.id == "583231"
    assert user.email == "primary@example.com"
    assert user.email_verified is True
    assert user.name == "The Octocat"
    assert user.username == "octocat"
    assert user.avatar_url == USER["avatar_url"]
    assert all(
        r.headers["Accept"] == "application/vnd.github+json" for r in api.requests
    )


def test_name_falls_back_to_login(api, github):
    api.add("GET", GitHub.USER_INFO_URL, json={**USER, "name": None})
    api.add("GET", GitHub.EMAILS_URL, json=[])

    assert fetch(github).name == "octocat"


def test_no_primary_email_falls_back_to_public_email(api, github):
    api.add("GET", GitHub.USER_INFO_URL, json=USER)
    api.add(
        "GET", GitHub.EMAILS_URL, json=[{"email": "x@example.com", "primary": False}]
    )

    user = fetch(github)

    assert user.email == "public@example.com"
    assert user.email_verified is False


@pytest.mark.parametrize("status", [403, 404])
def test_missing_email_scope_falls_back_to_public_email(api, github, status):
    api.add("GET", GitHub.USER_INFO_URL, json=USER)
    api.add("GET", GitHub.EMAILS_URL, status=status, json={"message": "Not Found"})

    user = fetch(github)

    assert user.email == "public@example.com"
    assert user.email_verified is False


def test_rate_limit_on_emails_raises(api, github):
    api.add("GET", GitHub.USER_INFO_URL, json=USER)
    api.add(
        "GET",
        GitHub.EMAILS_URL,
        status=403,
        json={"message": "API rate limit exceeded for user ID 1."},
    )

    with pytest.raises(UserFetchError):
        fetch(github)


def test_server_error_on_emails_raises(api, github):
    api.add("GET", GitHub.USER_INFO_URL, json=USER)
    api.add("GET", GitHub.EMAILS_URL, status=500, json={})

    with pytest.raises(UserFetchError):
        fetch(github)


def test_token_error_with_200_status(api, github):
    api.add(
        "POST",
        GitHub.TOKEN_URL,
        json={
            "error": "bad_verification_code",
            "error_description": "The code passed is incorrect or expired.",
        },
    )

    with pytest.raises(TokenExchangeError) as exc_info:
        github.get_access_token("code")

    assert exc_info.value.error == "bad_verification_code"


def test_token_without_expiry(api, github):
    api.add(
        "POST",
        GitHub.TOKEN_URL,
        json={
            "access_token": "gho_x",
            "token_type": "bearer",
            "scope": "read:user,user:email",
        },
    )

    token = github.get_access_token("code")

    assert token.expires_in is None
    assert token.scopes == ("read:user", "user:email")
