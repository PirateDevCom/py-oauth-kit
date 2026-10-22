from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class AccessToken:
    """Token issued by the provider's token endpoint.

    Attributes:
        token (str): The access token used to call the provider's APIs.
        expires_in (int | None): Lifetime of the token in seconds, if provided.
        expires_at (datetime | None): When the token expires (UTC), if known.
        refresh_token (str | None): Token used to get a new access token, if provided.
        scopes (tuple[str, ...]): Scopes granted by the provider. Empty if the
            provider doesn't report them (e.g. Amazon).
        raw (Mapping[str, Any]): The full token response from the provider.
    """

    token: str = field(repr=False)
    expires_in: int | None = None
    expires_at: datetime | None = None
    refresh_token: str | None = field(default=None, repr=False)
    scopes: tuple[str, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class Identity:
    """User details as reported by the provider.

    Attributes:
        id (str): The user's unique ID at the provider.
        email (str | None): The user's email address, if available.
        email_verified (bool): Whether the provider has verified the email.
        name (str): The user's display name. Falls back to their username, or
            ``"Unknown"`` if the provider has neither.
        username (str | None): The user's handle or login, if available.
        avatar_url (str | None): URL of the user's profile picture, if available.
        raw (Mapping[str, Any]): The full user response from the provider.
    """

    id: str
    email: str | None = None
    email_verified: bool = False
    name: str = "Unknown"
    username: str | None = None
    avatar_url: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
