import pytest

from py_oauth import AccessToken, Discord

REDIRECT_URI = "https://example.com/callback"


@pytest.fixture
def discord(api):
    return Discord("client-id", "client-secret", REDIRECT_URI, client=api.client)


def test_fetch_user(api, discord):
    data = {
        "id": "80351110224678912",
        "username": "nelly",
        "global_name": "Nelly",
        "email": "nelly@example.com",
        "verified": True,
        "avatar": "8342729096ea3675442027381ff50dfe",
    }
    api.add("GET", Discord.USER_INFO_URL, json=data)

    user = discord.fetch_user(AccessToken(token="token"))

    assert user.id == "80351110224678912"
    assert user.email == "nelly@example.com"
    assert user.email_verified is True
    assert user.name == "Nelly"
    assert user.username == "nelly"
    assert user.avatar_url == (
        "https://cdn.discordapp.com/avatars/80351110224678912/"
        "8342729096ea3675442027381ff50dfe.png"
    )


def test_animated_avatar(api, discord):
    api.add("GET", Discord.USER_INFO_URL, json={"id": "1", "avatar": "a_123"})

    user = discord.fetch_user(AccessToken(token="token"))

    assert user.avatar_url == "https://cdn.discordapp.com/avatars/1/a_123.gif"


def test_minimal_user(api, discord):
    api.add("GET", Discord.USER_INFO_URL, json={"id": "1", "username": "nelly"})

    user = discord.fetch_user(AccessToken(token="token"))

    assert user.name == "nelly"
    assert user.email is None
    assert user.email_verified is False
    assert user.avatar_url is None


def test_verified_must_be_true(api, discord):
    api.add("GET", Discord.USER_INFO_URL, json={"id": "1", "verified": "true"})
    assert discord.fetch_user(AccessToken(token="token")).email_verified is False
