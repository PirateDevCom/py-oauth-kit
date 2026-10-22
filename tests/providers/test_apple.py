import base64
import json
import sys
import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import (
    encode_dss_signature,
)

from py_oauth import AccessToken, Apple, UserFetchError

CLIENT_ID = "com.example.signin"
REDIRECT_URI = "https://example.com/callback"
TEAM_ID = "TEAM123456"
KEY_ID = "KEY1234567"


def b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def b64encode_json(data: Any) -> str:
    return b64encode(json.dumps(data).encode())


def pem(key: Any) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


@pytest.fixture(scope="module")
def signing_key() -> ec.EllipticCurvePrivateKey:
    """The developer's Sign in with Apple key (the .p8 file)."""
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="module")
def apple_key() -> rsa.RSAPrivateKey:
    """Apple's ID token signing key."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def jwk(key: rsa.RSAPrivateKey, kid: str) -> dict[str, str]:
    numbers = key.public_key().public_numbers()
    return {
        "kty": "RSA",
        "kid": kid,
        "alg": "RS256",
        "n": b64encode(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8)),
        "e": b64encode(numbers.e.to_bytes(3)),
    }


def make_id_token(
    key: rsa.RSAPrivateKey,
    *,
    kid: str = "apple-key",
    alg: str = "RS256",
    **claims: Any,
) -> str:
    claims = {
        "iss": "https://appleid.apple.com",
        "aud": CLIENT_ID,
        "exp": int(time.time()) + 600,
        "sub": "001234.abcd",
        "email": "jane@privaterelay.appleid.com",
        "email_verified": "true",
        **claims,
    }
    signing_input = (
        f"{b64encode_json({'alg': alg, 'kid': kid})}.{b64encode_json(claims)}"
    )
    signature = key.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{signing_input}.{b64encode(signature)}"


def token(id_token: str) -> AccessToken:
    return AccessToken(token="access", raw={"id_token": id_token})


@pytest.fixture
def apple(api, signing_key, apple_key):
    api.add("GET", Apple.KEYS_URL, json={"keys": [jwk(apple_key, "apple-key")]})
    return Apple(
        CLIENT_ID,
        REDIRECT_URI,
        team_id=TEAM_ID,
        key_id=KEY_ID,
        private_key=pem(signing_key).decode(),
        client=api.client,
    )


class TestAuthorizationURL:
    def test_form_post_and_scopes(self, apple):
        url = apple.get_authorization_url("state")
        params = parse_qs(urlsplit(url).query)

        assert params["response_mode"] == ["form_post"]
        assert params["scope"] == ["name email"]

    def test_response_mode_can_be_overridden(self, apple):
        url = apple.get_authorization_url(
            "state", scopes=[], extra_params={"response_mode": "query"}
        )
        assert parse_qs(urlsplit(url).query)["response_mode"] == ["query"]


class TestClientSecret:
    def test_signed_jwt(self, api, apple, signing_key):
        api.add("POST", Apple.TOKEN_URL, json={"access_token": "access"})

        apple.get_access_token("code")

        form = parse_qs(api.requests[0].content.decode())
        secret = form["client_secret"][0]
        encoded_header, encoded_payload, encoded_signature = secret.split(".")
        header = json.loads(b64decode(encoded_header))
        payload = json.loads(b64decode(encoded_payload))

        assert header == {"alg": "ES256", "kid": KEY_ID}
        assert payload["iss"] == TEAM_ID
        assert payload["sub"] == CLIENT_ID
        assert payload["aud"] == "https://appleid.apple.com"
        assert payload["exp"] - payload["iat"] == Apple.CLIENT_SECRET_LIFETIME

        raw = b64decode(encoded_signature)
        assert len(raw) == 64
        signature = encode_dss_signature(
            int.from_bytes(raw[:32]), int.from_bytes(raw[32:])
        )
        signing_key.public_key().verify(
            signature,
            f"{encoded_header}.{encoded_payload}".encode(),
            ec.ECDSA(hashes.SHA256()),
        )

    def test_rsa_key_rejected(self, apple_key):
        with pytest.raises(TypeError):
            Apple(
                CLIENT_ID,
                REDIRECT_URI,
                team_id=TEAM_ID,
                key_id=KEY_ID,
                private_key=pem(apple_key),
            )

    def test_wrong_curve_rejected(self):
        key = ec.generate_private_key(ec.SECP384R1())
        with pytest.raises(TypeError):
            Apple(
                CLIENT_ID,
                REDIRECT_URI,
                team_id=TEAM_ID,
                key_id=KEY_ID,
                private_key=pem(key),
            )

    def test_encrypted_key_rejected(self, signing_key):
        encrypted = signing_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(b"password"),
        )
        with pytest.raises(ValueError, match="encrypted"):
            Apple(
                CLIENT_ID,
                REDIRECT_URI,
                team_id=TEAM_ID,
                key_id=KEY_ID,
                private_key=encrypted,
            )

    def test_invalid_key_rejected(self):
        with pytest.raises(ValueError):
            Apple(
                CLIENT_ID,
                REDIRECT_URI,
                team_id=TEAM_ID,
                key_id=KEY_ID,
                private_key="not a key",
            )

    def test_missing_extra(self, monkeypatch, signing_key):
        monkeypatch.setitem(sys.modules, "cryptography.hazmat.primitives", None)
        with pytest.raises(ImportError, match="apple"):
            Apple(
                CLIENT_ID,
                REDIRECT_URI,
                team_id=TEAM_ID,
                key_id=KEY_ID,
                private_key=pem(signing_key),
            )


class TestFetchUser:
    def test_valid_id_token(self, apple, apple_key):
        user = apple.fetch_user(token(make_id_token(apple_key)))

        assert user.id == "001234.abcd"
        assert user.email == "jane@privaterelay.appleid.com"
        assert user.email_verified is True
        assert user.name == "Unknown"
        assert user.raw["sub"] == "001234.abcd"

    @pytest.mark.parametrize(
        "user",
        [
            '{"name": {"firstName": "Jane", "lastName": "Doe"}}',
            {"name": {"firstName": "Jane", "lastName": "Doe"}},
        ],
    )
    def test_name_from_first_sign_in(self, apple, apple_key, user):
        identity = apple.fetch_user(token(make_id_token(apple_key)), user=user)
        assert identity.name == "Jane Doe"

    @pytest.mark.parametrize(
        "user",
        [
            "not json",
            "[" * 100_000 + "]" * 100_000,
            "[]",
            '{"name": "Jane"}',
            '{"name": {"firstName": ""}}',
            {"email": "jane@example.com"},
        ],
    )
    def test_malformed_user_is_ignored(self, apple, apple_key, user):
        identity = apple.fetch_user(token(make_id_token(apple_key)), user=user)
        assert identity.name == "Unknown"

    def test_audience_list(self, apple, apple_key):
        id_token = make_id_token(apple_key, aud=["other", CLIENT_ID])
        assert apple.fetch_user(token(id_token)).id == "001234.abcd"

    def test_missing_id_token(self, apple):
        with pytest.raises(UserFetchError, match="missing id_token"):
            apple.fetch_user(AccessToken(token="access"))

    @pytest.mark.parametrize(
        "id_token",
        [
            "abc",
            "a.b",
            "a.b.c.d",
            "!!!.!!!.!!!",
            f"{b64encode_json([])}.{b64encode_json({})}.sig",
            f"{b64encode_json({'alg': 'RS256'})}.{b64encode_json({})}.sig",
        ],
    )
    def test_malformed_id_token(self, apple, id_token):
        with pytest.raises(UserFetchError, match="malformed"):
            apple.fetch_user(token(id_token))

    @pytest.mark.parametrize("alg", ["none", "HS256", "ES256"])
    def test_other_algorithms_rejected(self, apple, apple_key, alg):
        with pytest.raises(UserFetchError, match="malformed"):
            apple.fetch_user(token(make_id_token(apple_key, alg=alg)))

    def test_wrong_signing_key(self, apple):
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with pytest.raises(UserFetchError, match="invalid signature"):
            apple.fetch_user(token(make_id_token(other_key)))

    def test_tampered_claims(self, apple, apple_key):
        header, _, signature = make_id_token(apple_key).split(".")
        claims = b64encode_json({"sub": "attacker", "aud": CLIENT_ID})
        with pytest.raises(UserFetchError, match="invalid signature"):
            apple.fetch_user(token(f"{header}.{claims}.{signature}"))

    @pytest.mark.parametrize(
        "claims",
        [{"aud": "com.other.app"}, {"aud": None}, {"iss": "https://evil.example.com"}],
    )
    def test_not_issued_for_client(self, apple, apple_key, claims):
        with pytest.raises(UserFetchError, match="wasn't issued for this client"):
            apple.fetch_user(token(make_id_token(apple_key, **claims)))

    @pytest.mark.parametrize("exp", [time.time() - 120, "9999999999", None])
    def test_expired(self, apple, apple_key, exp):
        with pytest.raises(UserFetchError, match="expired"):
            apple.fetch_user(token(make_id_token(apple_key, exp=exp)))

    def test_clock_skew_tolerated(self, apple, apple_key):
        id_token = make_id_token(apple_key, exp=int(time.time()) - 30)
        assert apple.fetch_user(token(id_token)).id == "001234.abcd"


class TestKeys:
    def test_keys_are_cached(self, api, apple, apple_key):
        apple.fetch_user(token(make_id_token(apple_key)))
        apple.fetch_user(token(make_id_token(apple_key)))

        assert api.count(Apple.KEYS_URL) == 1

    def test_unknown_key_refetch_is_throttled(self, api, apple, apple_key):
        apple.fetch_user(token(make_id_token(apple_key)))

        for _ in range(3):
            with pytest.raises(UserFetchError, match="unknown key"):
                apple.fetch_user(token(make_id_token(apple_key, kid="new-key")))

        assert api.count(Apple.KEYS_URL) == 1

    def test_rotated_key_is_fetched(self, api, apple, apple_key):
        apple.fetch_user(token(make_id_token(apple_key)))
        new_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        api.add("GET", Apple.KEYS_URL, json={"keys": [jwk(new_key, "new-key")]})
        # Pretend the refetch interval has passed.
        apple._keys_fetched_at -= Apple.KEYS_REFETCH_INTERVAL

        user = apple.fetch_user(token(make_id_token(new_key, kid="new-key")))

        assert user.id == "001234.abcd"
        assert api.count(Apple.KEYS_URL) == 2

    def test_failed_fetch_is_throttled(self, api, apple, apple_key):
        api.add("GET", Apple.KEYS_URL, status=503, text="Unavailable")

        with pytest.raises(UserFetchError, match="keys request"):
            apple.fetch_user(token(make_id_token(apple_key)))
        with pytest.raises(UserFetchError, match="unknown key"):
            apple.fetch_user(token(make_id_token(apple_key)))

        assert api.count(Apple.KEYS_URL) == 1

    def test_malformed_keys_are_skipped(self, api, apple, apple_key):
        api.add(
            "GET",
            Apple.KEYS_URL,
            json={
                "keys": [
                    "not a key",
                    {"kty": "EC", "kid": "ec"},
                    {"kty": "RSA", "kid": "no-modulus", "e": "AQAB"},
                    {"kty": "RSA", "kid": "bad", "n": "AA", "e": "AA"},
                    jwk(apple_key, "apple-key"),
                ]
            },
        )

        assert apple.fetch_user(token(make_id_token(apple_key))).id == "001234.abcd"
