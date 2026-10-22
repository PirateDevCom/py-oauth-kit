"""PKCE helpers (RFC 7636)."""

import base64
import hashlib
import secrets


def generate_code_verifier() -> str:
    """Generate a random PKCE code verifier.

    Store it (e.g. in the user's session) between building the authorization
    URL and exchanging the code, and pass it to both calls.

    Returns:
        str: An 86-character URL-safe verifier, within RFC 7636's 43-128.
    """
    return secrets.token_urlsafe(64)


def code_challenge(code_verifier: str) -> str:
    """Derive the S256 code challenge for a code verifier.

    Args:
        code_verifier (str): Verifier from ``generate_code_verifier``.

    Returns:
        str: The base64url-encoded SHA-256 hash of the verifier, unpadded.
    """
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
