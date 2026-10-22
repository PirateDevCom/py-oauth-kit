import pytest

from py_oauth import OAuthError, TokenExchangeError, UserFetchError


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, "Request failed"),
        ({"error": "invalid_grant"}, "Request failed (invalid_grant)"),
        ({"description": "Code expired"}, "Request failed (Code expired)"),
        (
            {"error": "invalid_grant", "description": "Code expired"},
            "Request failed (invalid_grant: Code expired)",
        ),
    ],
)
def test_str(kwargs, expected):
    assert str(OAuthError("Request failed", **kwargs)) == expected


def test_attributes():
    exc = OAuthError("Request failed", error="e", description="d", status_code=400)
    assert (exc.error, exc.description, exc.status_code) == ("e", "d", 400)


@pytest.mark.parametrize("cls", [TokenExchangeError, UserFetchError])
def test_subclasses(cls):
    assert issubclass(cls, OAuthError)
