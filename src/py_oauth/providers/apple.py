import base64
import json
import time
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

import httpx

from py_oauth.exceptions import UserFetchError
from py_oauth.providers.base import OAuthProvider
from py_oauth.types import AccessToken, Identity

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey


class Apple(OAuthProvider):
    """OAuth 2.0 provider for Sign in with Apple.

    Needs the ``apple`` extra (``pip install "py-oauth-kit[apple]"``) to sign the
    client secret, a short-lived JWT generated for each token request.

    Apple redirects back with a POST (``response_mode=form_post``), as it
    requires when requesting the name or email scopes, so the redirect URI
    must accept POST requests. The POST is cross-site, so browsers don't send
    ``SameSite=Lax`` cookies with it (Django's session cookie default): store
    the ``state`` (and any PKCE verifier) in a ``SameSite=None; Secure``
    cookie, or the redirect can't read them.

    Apple has no user info API: ``fetch_user`` reads the ID token from the
    token response. It verifies the token's signature against Apple's public
    keys, which are fetched on first use and cached by the instance, so reuse
    one instance across requests.

    Apple sends the user's name only on their first sign-in, in the ``user``
    form field posted to the redirect URI. Pass it to ``fetch_user`` to set
    ``Identity.name``, which is ``"Unknown"`` otherwise.

    Args:
        client_id (str): The Services ID (e.g. ``"com.example.signin"``).
        redirect_uri (str): URI Apple redirects to after authorization. Must
            be listed under the Services ID's return URLs.
        team_id (str): The 10-character Team ID of the Apple developer
            account.
        key_id (str): The 10-character ID of the Sign in with Apple key.
        private_key (str | bytes): Contents of the key's ``.p8`` file.
        client (httpx.Client | None): HTTP client to send requests with.

    Raises:
        ImportError: If the ``apple`` extra isn't installed.
        TypeError: If ``private_key`` isn't a P-256 (ES256) key.
        ValueError: If ``private_key`` isn't a valid unencrypted PEM private key.
    """

    AUTHORIZATION_URL = "https://appleid.apple.com/auth/authorize"
    TOKEN_URL = "https://appleid.apple.com/auth/token"
    DEFAULT_SCOPES = ("name", "email")
    KEYS_URL = "https://appleid.apple.com/auth/keys"
    ISSUER = "https://appleid.apple.com"
    # Apple allows up to 6 months, but each token request signs a new one.
    CLIENT_SECRET_LIFETIME = 300
    # Seconds of clock skew between this server and Apple tolerated on exp.
    CLOCK_SKEW = 60
    # Minimum seconds between key fetches, so tokens with unknown key IDs
    # can't trigger a request to Apple every time.
    KEYS_REFETCH_INTERVAL = 60

    def __init__(
        self,
        client_id: str,
        redirect_uri: str,
        *,
        team_id: str,
        key_id: str,
        private_key: str | bytes,
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(client_id, "", redirect_uri, client=client)
        self._team_id = team_id
        self._key_id = key_id
        self._private_key = _load_private_key(private_key)
        self._public_keys: dict[str, RSAPublicKey] = {}
        self._keys_fetched_at: float | None = None

    def get_authorization_url(
        self,
        state: str,
        *,
        scopes: Sequence[str] | None = None,
        extra_params: Mapping[str, str] | None = None,
        code_verifier: str | None = None,
    ) -> str:
        return super().get_authorization_url(
            state,
            scopes=scopes,
            extra_params={"response_mode": "form_post", **(extra_params or {})},
            code_verifier=code_verifier,
        )

    def fetch_user(
        self, token: AccessToken, *, user: str | Mapping[str, Any] | None = None
    ) -> Identity:
        """Read the user's details from the token response's ID token.

        Args:
            token (AccessToken): Token from ``get_access_token``.
            user (str | Mapping[str, Any] | None): The ``user`` form field
                Apple posts to the redirect URI on the first sign-in, as the
                raw JSON string or parsed. Only its name is used: its email
                isn't signed by Apple.

        Returns:
            Identity: The user's identity from the ID token.

        Raises:
            UserFetchError: If the ID token is missing, malformed, wrongly
                signed, expired or not issued for this client, or Apple's
                public keys can't be fetched.
        """
        claims = self._decode_id_token(token)
        return Identity(
            id=self._get_user_id(claims, "sub"),
            email=self._get_str(claims, "email"),
            email_verified=self._get_bool(claims, "email_verified"),
            name=self._get_name(user) or "Unknown",
            raw=claims,
        )

    def _get_client_secret(self) -> str:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.asymmetric.utils import (
            decode_dss_signature,
        )

        now = int(time.time())
        header = {"alg": "ES256", "kid": self._key_id}
        payload = {
            "iss": self._team_id,
            "iat": now,
            "exp": now + self.CLIENT_SECRET_LIFETIME,
            "aud": self.ISSUER,
            "sub": self._client_id,
        }
        signing_input = f"{_b64encode_json(header)}.{_b64encode_json(payload)}"
        der = self._private_key.sign(signing_input.encode(), ec.ECDSA(hashes.SHA256()))
        # JWS wants the raw 64-byte r || s, not the DER that cryptography returns.
        r, s = decode_dss_signature(der)
        signature = _b64encode(r.to_bytes(32) + s.to_bytes(32))
        return f"{signing_input}.{signature}"

    def _decode_id_token(self, token: AccessToken) -> dict[str, Any]:
        """Verify the ID token and return its claims.

        Args:
            token (AccessToken): Token from ``get_access_token``.

        Returns:
            dict[str, Any]: The ID token's claims.

        Raises:
            UserFetchError: If the ID token is missing, malformed, wrongly
                signed, expired or not issued for this client, or Apple's
                public keys can't be fetched.
        """
        id_token = self._get_str(token.raw, "id_token")
        if id_token is None:
            raise UserFetchError(f"{self._name} token response is missing id_token")
        malformed = UserFetchError(f"{self._name} id_token is malformed")
        try:
            encoded_header, encoded_claims, encoded_signature = id_token.split(".")
            header = json.loads(_b64decode(encoded_header))
            claims = json.loads(_b64decode(encoded_claims))
            signature = _b64decode(encoded_signature)
        except ValueError as exc:
            raise malformed from exc
        if not isinstance(header, dict) or not isinstance(claims, dict):
            raise malformed
        key_id = header.get("kid")
        # Checking alg stops a token from choosing a weaker algorithm (or none).
        if header.get("alg") != "RS256" or not isinstance(key_id, str):
            raise malformed
        self._verify_signature(
            f"{encoded_header}.{encoded_claims}".encode(), signature, key_id
        )

        audience = claims.get("aud")
        audiences = audience if isinstance(audience, list) else [audience]
        if claims.get("iss") != self.ISSUER or self._client_id not in audiences:
            raise UserFetchError(f"{self._name} id_token wasn't issued for this client")
        expires_at = claims.get("exp")
        if (
            not isinstance(expires_at, int | float)
            or expires_at <= time.time() - self.CLOCK_SKEW
        ):
            raise UserFetchError(f"{self._name} id_token has expired")
        return claims

    def _verify_signature(self, message: bytes, signature: bytes, key_id: str) -> None:
        """Check the ID token's RS256 signature against Apple's public key.

        Args:
            message (bytes): The signed part of the token, header and claims.
            signature (bytes): The decoded signature.
            key_id (str): The ``kid`` from the token's header.

        Raises:
            UserFetchError: If the key is unknown, the signature is invalid,
                or Apple's public keys can't be fetched.
        """
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        # Apple rotates its keys, so refetch them when the token uses a new one,
        # at most once per KEYS_REFETCH_INTERVAL.
        now = time.monotonic()
        if key_id not in self._public_keys and (
            self._keys_fetched_at is None
            or now - self._keys_fetched_at >= self.KEYS_REFETCH_INTERVAL
        ):
            # Set first, so failed fetches are throttled too.
            self._keys_fetched_at = now
            self._public_keys = self._fetch_public_keys()
        key = self._public_keys.get(key_id)
        if key is None:
            raise UserFetchError(f"{self._name} id_token is signed with an unknown key")
        try:
            key.verify(signature, message, padding.PKCS1v15(), hashes.SHA256())
        except InvalidSignature as exc:
            raise UserFetchError(
                f"{self._name} id_token has an invalid signature"
            ) from exc

    def _fetch_public_keys(self) -> dict[str, "RSAPublicKey"]:
        """Fetch Apple's ID token signing keys (a JWK Set).

        Returns:
            dict[str, RSAPublicKey]: The RSA keys, by key ID. Malformed keys
                are skipped.

        Raises:
            UserFetchError: If the request fails or the response is an error.
        """
        from cryptography.hazmat.primitives.asymmetric import rsa

        data = self._request(
            "GET",
            self.KEYS_URL,
            error_cls=UserFetchError,
            action=f"{self._name} keys request",
        )
        jwks = data.get("keys")
        keys: dict[str, RSAPublicKey] = {}
        for jwk in jwks if isinstance(jwks, list) else []:
            if not isinstance(jwk, dict) or jwk.get("kty") != "RSA":
                continue
            key_id = self._get_str(jwk, "kid")
            modulus, exponent = self._get_str(jwk, "n"), self._get_str(jwk, "e")
            if key_id is None or modulus is None or exponent is None:
                continue
            try:
                numbers = rsa.RSAPublicNumbers(
                    int.from_bytes(_b64decode(exponent)),
                    int.from_bytes(_b64decode(modulus)),
                )
                keys[key_id] = numbers.public_key()
            except ValueError:
                continue
        return keys

    def _get_name(self, user: str | Mapping[str, Any] | None) -> str | None:
        """Return the full name from the first sign-in's ``user`` field.

        The field comes from the browser, so malformed values are ignored.

        Args:
            user (str | Mapping[str, Any] | None): The ``user`` form field.

        Returns:
            str | None: The first and last name, or None if there's none.
        """
        if isinstance(user, str):
            try:
                user = json.loads(user)
            # Deeply nested JSON raises RecursionError, not ValueError.
            except (ValueError, RecursionError):
                return None
        name = user.get("name") if isinstance(user, Mapping) else None
        if not isinstance(name, Mapping):
            return None
        parts = (self._get_str(name, "firstName"), self._get_str(name, "lastName"))
        return " ".join(p for p in parts if p) or None


def _load_private_key(private_key: str | bytes) -> "EllipticCurvePrivateKey":
    """Load the Sign in with Apple key from its ``.p8`` contents.

    Args:
        private_key (str | bytes): PEM-encoded P-256 private key.

    Returns:
        EllipticCurvePrivateKey: The loaded key.

    Raises:
        ImportError: If the ``apple`` extra isn't installed.
        TypeError: If the key isn't a P-256 (ES256) key.
        ValueError: If the key isn't a valid unencrypted PEM private key.
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
    except ImportError as exc:
        raise ImportError(
            'Apple needs the "apple" extra: pip install "py-oauth-kit[apple]"'
        ) from exc

    if isinstance(private_key, str):
        private_key = private_key.encode()
    try:
        key = serialization.load_pem_private_key(private_key, password=None)
    except TypeError as exc:
        # Raised for encrypted keys. Apple's .p8 files aren't encrypted.
        raise ValueError("Apple private_key must not be encrypted") from exc
    if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(
        key.curve, ec.SECP256R1
    ):
        raise TypeError("Apple private_key must be a P-256 (ES256) key")
    return key


def _b64encode(data: bytes) -> str:
    """Return unpadded base64url, as used in JWTs."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    """Decode unpadded base64url, as used in JWTs.

    Raises:
        ValueError: If ``data`` isn't valid base64url.
    """
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _b64encode_json(data: Mapping[str, Any]) -> str:
    """Return a JWT segment: compact JSON, unpadded base64url."""
    return _b64encode(json.dumps(data, separators=(",", ":")).encode())
