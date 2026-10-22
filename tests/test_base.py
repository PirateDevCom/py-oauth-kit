import base64
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from py_oauth import AccessToken, Identity, OAuthProvider, TokenExchangeError
from py_oauth.exceptions import UserFetchError
from py_oauth.pkce import code_challenge

AUTHORIZATION_URL = "https://auth.example.com/authorize"
TOKEN_URL = "https://auth.example.com/token"
REDIRECT_URI = "https://example.com/callback"


class Example(OAuthProvider):
    AUTHORIZATION_URL = AUTHORIZATION_URL
    TOKEN_URL = TOKEN_URL
    DEFAULT_SCOPES = ("read", "email")

    def fetch_user(self, token: AccessToken) -> Identity:
        return Identity(id="1")


class BasicAuthExample(Example):
    CLIENT_AUTH = "basic"


class PKCEExample(Example):
    REQUIRES_PKCE = True


@pytest.fixture
def provider(api):
    return Example("client-id", "client-secret", REDIRECT_URI, client=api.client)


def query(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


def form(request: httpx.Request) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(request.content.decode()).items()}


class TestAuthorizationURL:
    def test_standard_params(self, provider):
        url = provider.get_authorization_url("state-123")

        assert url.startswith(f"{AUTHORIZATION_URL}?")
        assert query(url) == {
            "client_id": "client-id",
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "state": "state-123",
            "scope": "read email",
        }

    def test_custom_scopes(self, provider):
        url = provider.get_authorization_url("state", scopes=["a", "b"])
        assert query(url)["scope"] == "a b"

    def test_empty_scopes_omit_scope(self, provider):
        url = provider.get_authorization_url("state", scopes=[])
        assert "scope" not in query(url)

    def test_str_scopes_rejected(self, provider):
        with pytest.raises(TypeError):
            provider.get_authorization_url("state", scopes="read")

    def test_extra_params(self, provider):
        url = provider.get_authorization_url(
            "state", extra_params={"prompt": "consent"}
        )
        assert query(url)["prompt"] == "consent"

    def test_extra_params_cant_override_standard_params(self, provider):
        url = provider.get_authorization_url(
            "state", extra_params={"client_id": "evil", "state": "evil"}
        )
        params = query(url)
        assert params["client_id"] == "client-id"
        assert params["state"] == "state"

    def test_pkce(self, provider):
        url = provider.get_authorization_url("state", code_verifier="verifier")
        params = query(url)
        assert params["code_challenge"] == code_challenge("verifier")
        assert params["code_challenge_method"] == "S256"

    def test_required_pkce(self):
        provider = PKCEExample("id", "secret", REDIRECT_URI)
        with pytest.raises(ValueError):
            provider.get_authorization_url("state")
        with pytest.raises(ValueError):
            provider.get_access_token("code")


class TestAccessToken:
    def test_body_auth(self, api, provider):
        api.add("POST", TOKEN_URL, json={"access_token": "token"})

        provider.get_access_token("code-123")

        request = api.requests[0]
        assert form(request) == {
            "grant_type": "authorization_code",
            "code": "code-123",
            "redirect_uri": REDIRECT_URI,
            "client_id": "client-id",
            "client_secret": "client-secret",
        }
        assert request.headers["Accept"] == "application/json"
        assert "Authorization" not in request.headers

    def test_basic_auth_form_encodes_credentials(self, api):
        api.add("POST", TOKEN_URL, json={"access_token": "token"})
        provider = BasicAuthExample("id:1", "secret &", REDIRECT_URI, client=api.client)

        provider.get_access_token("code")

        request = api.requests[0]
        expected = base64.b64encode(b"id%3A1:secret+%26").decode()
        assert request.headers["Authorization"] == f"Basic {expected}"
        assert "client_secret" not in form(request)

    def test_code_verifier(self, api, provider):
        api.add("POST", TOKEN_URL, json={"access_token": "token"})

        provider.get_access_token("code", code_verifier="verifier")

        assert form(api.requests[0])["code_verifier"] == "verifier"

    def test_parses_token(self, api, provider):
        data = {
            "access_token": "token",
            "expires_in": 3600,
            "refresh_token": "refresh",
            "scope": "read email",
        }
        api.add("POST", TOKEN_URL, json=data)

        before = datetime.now(UTC)
        token = provider.get_access_token("code")

        assert token.token == "token"
        assert token.expires_in == 3600
        assert token.expires_at is not None
        assert (
            before + timedelta(seconds=3600)
            <= token.expires_at
            <= datetime.now(UTC) + timedelta(seconds=3600)
        )
        assert token.refresh_token == "refresh"
        assert token.scopes == ("read", "email")
        assert token.raw == data

    def test_minimal_token(self, api, provider):
        api.add("POST", TOKEN_URL, json={"access_token": "token"})

        token = provider.get_access_token("code")

        assert token.expires_in is None
        assert token.expires_at is None
        assert token.refresh_token is None
        assert token.scopes == ()

    def test_string_expires_in(self, api, provider):
        api.add("POST", TOKEN_URL, json={"access_token": "token", "expires_in": "60"})
        assert provider.get_access_token("code").expires_in == 60

    @pytest.mark.parametrize(
        "expires_in", ['"soon"', "true", "-1", "1.5e400", "Infinity", "[]", "null"]
    )
    def test_malformed_expires_in_is_unknown(self, api, provider, expires_in):
        body = f'{{"access_token": "token", "expires_in": {expires_in}}}'
        api.add("POST", TOKEN_URL, text=body)

        token = provider.get_access_token("code")

        assert token.expires_in is None
        assert token.expires_at is None

    @pytest.mark.parametrize("scope", ["read,email", "read, email", " read  email "])
    def test_scope_separators(self, api, provider, scope):
        api.add("POST", TOKEN_URL, json={"access_token": "token", "scope": scope})
        assert provider.get_access_token("code").scopes == ("read", "email")

    @pytest.mark.parametrize("data", [{}, {"access_token": ""}, {"access_token": 1}])
    def test_missing_access_token(self, api, provider, data):
        api.add("POST", TOKEN_URL, json=data)

        with pytest.raises(TokenExchangeError, match="missing access_token"):
            provider.get_access_token("code")

    def test_error_response(self, api, provider):
        api.add(
            "POST",
            TOKEN_URL,
            status=400,
            json={"error": "invalid_grant", "error_description": "Code expired"},
        )

        with pytest.raises(TokenExchangeError) as exc_info:
            provider.get_access_token("code")

        exc = exc_info.value
        assert exc.error == "invalid_grant"
        assert exc.description == "Code expired"
        assert exc.status_code == 400
        assert str(exc) == (
            "Example token request failed with status 400 (invalid_grant: Code expired)"
        )

    def test_error_in_successful_response(self, api, provider):
        api.add("POST", TOKEN_URL, json={"error": "bad_verification_code"})

        with pytest.raises(TokenExchangeError) as exc_info:
            provider.get_access_token("code")

        assert exc_info.value.error == "bad_verification_code"
        assert exc_info.value.status_code == 200

    def test_non_json_error(self, api, provider):
        api.add("POST", TOKEN_URL, status=502, text="Bad Gateway")

        with pytest.raises(TokenExchangeError) as exc_info:
            provider.get_access_token("code")

        assert exc_info.value.status_code == 502
        assert exc_info.value.error is None

    @pytest.mark.parametrize("body", ["not json", "[]", '"token"'])
    def test_invalid_successful_response(self, api, provider, body):
        api.add("POST", TOKEN_URL, text=body)

        with pytest.raises(TokenExchangeError, match="invalid response"):
            provider.get_access_token("code")

    def test_network_error_is_wrapped(self, api, provider):
        api.fail("POST", TOKEN_URL, httpx.ConnectError("Connection refused"))

        with pytest.raises(TokenExchangeError, match="failed") as exc_info:
            provider.get_access_token("code")

        assert isinstance(exc_info.value.__cause__, httpx.ConnectError)

    def test_without_client_uses_httpx_request(self, monkeypatch):
        calls: list[tuple[str, str]] = []

        def request(method: str, url: str, **kwargs: Any) -> httpx.Response:
            calls.append((method, url))
            return httpx.Response(200, json={"access_token": "token"})

        monkeypatch.setattr(httpx, "request", request)
        provider = Example("id", "secret", REDIRECT_URI)

        assert provider.get_access_token("code").token == "token"
        assert calls == [("POST", TOKEN_URL)]


class TestExtractError:
    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            ({"error": "e", "error_description": "d"}, ("e", "d")),
            ({"error": "e"}, ("e", None)),
            ({"message": "Bad credentials"}, (None, "Bad credentials")),
            ({"detail": "Unauthorized"}, (None, "Unauthorized")),
            ({"error": {"code": 190, "message": "Expired"}}, ("190", "Expired")),
            ({"error": {"code": "InvalidToken"}}, ("InvalidToken", None)),
            ({"error": 1, "error_description": 2}, (None, None)),
            ({"access_token": "token"}, (None, None)),
            ([], (None, None)),
            (None, (None, None)),
        ],
    )
    def test_shapes(self, provider, data, expected):
        assert provider._extract_error(data) == expected


class TestUserHelpers:
    def test_get_user_info_sends_bearer_token(self, api, provider):
        url = "https://api.example.com/me"
        api.add("GET", url, json={"id": 1})

        data = provider._get_user_info(url, "token", headers={"X-Extra": "1"})

        assert data == {"id": 1}
        assert api.requests[0].headers["Authorization"] == "Bearer token"
        assert api.requests[0].headers["X-Extra"] == "1"

    def test_get_user_info_error(self, api, provider):
        url = "https://api.example.com/me"
        api.add("GET", url, status=401, json={"message": "Bad credentials"})

        with pytest.raises(UserFetchError) as exc_info:
            provider._get_user_info(url, "token")

        assert exc_info.value.description == "Bad credentials"

    def test_non_ascii_token(self, api, provider):
        with pytest.raises(UserFetchError):
            provider._get_user_info("https://api.example.com/me", "tökén")

    @pytest.mark.parametrize(("value", "expected"), [("abc", "abc"), (123, "123")])
    def test_get_user_id(self, provider, value, expected):
        assert provider._get_user_id({"id": value}, "id") == expected

    @pytest.mark.parametrize("data", [{}, {"id": ""}, {"id": None}, {"id": True}])
    def test_get_user_id_missing(self, provider, data):
        with pytest.raises(UserFetchError, match="missing id"):
            provider._get_user_id(data, "id")

    @pytest.mark.parametrize(
        ("data", "expected"),
        [({"k": "v"}, "v"), ({"k": ""}, None), ({"k": 1}, None), ({}, None)],
    )
    def test_get_str(self, data, expected):
        assert OAuthProvider._get_str(data, "k") == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (True, True),
            ("true", True),
            ("TRUE", True),
            (False, False),
            ("false", False),
            ("yes", False),
            (1, False),
            (None, False),
        ],
    )
    def test_get_bool(self, value, expected):
        assert OAuthProvider._get_bool({"k": value}, "k") is expected
