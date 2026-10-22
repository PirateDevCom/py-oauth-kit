import re
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar, Literal
from urllib.parse import quote_plus, urlencode

import httpx

from py_oauth.exceptions import OAuthError, TokenExchangeError, UserFetchError
from py_oauth.pkce import code_challenge
from py_oauth.types import AccessToken, Identity


class OAuthProvider(ABC):
    """Base class for OAuth 2.0 providers.

    Implements the standard authorization code flow. Subclasses set the class
    attributes below and implement ``fetch_user``. They override the other
    methods only where the provider differs from the standard.

    Attributes:
        AUTHORIZATION_URL (str): The provider's authorization endpoint.
        TOKEN_URL (str): The provider's token endpoint.
        DEFAULT_SCOPES (tuple[str, ...]): Scopes requested when none are given.
        SCOPE_SEPARATOR (str): Separator for scopes in the authorization URL.
        CLIENT_AUTH (Literal["body", "basic"]): How the token request sends
            the client credentials: in the request parameters, or as HTTP
            Basic auth.
        REQUIRES_PKCE (bool): Whether the provider rejects requests without
            a PKCE code verifier.

    Args:
        client_id (str): Client ID issued by the provider.
        client_secret (str): Client secret issued by the provider.
        redirect_uri (str): URI the provider redirects to after authorization.
            Must match the one registered with the provider.
        client (httpx.Client | None): HTTP client to send requests with, e.g.
            to set timeouts or proxies, or to reuse connections. If None, each
            request uses a new connection with httpx's defaults.
    """

    # Not ClassVars, so a provider can set them per instance (e.g. Microsoft's
    # tenant).
    AUTHORIZATION_URL: str
    TOKEN_URL: str
    DEFAULT_SCOPES: ClassVar[tuple[str, ...]] = ()
    SCOPE_SEPARATOR: ClassVar[str] = " "
    CLIENT_AUTH: ClassVar[Literal["body", "basic"]] = "body"
    REQUIRES_PKCE: ClassVar[bool] = False

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._client = client

    def get_authorization_url(
        self,
        state: str,
        *,
        scopes: Sequence[str] | None = None,
        extra_params: Mapping[str, str] | None = None,
        code_verifier: str | None = None,
    ) -> str:
        """Build the URL to redirect the user to for authorization.

        Args:
            state (str): Opaque value to protect against CSRF. Verify it matches
                the ``state`` returned to the redirect URI.
            scopes (Sequence[str] | None): Scopes to request. Uses the
                provider's defaults if None.
            extra_params (Mapping[str, str] | None): Extra query parameters
                for the provider, e.g. ``{"prompt": "consent"}``. They can't
                override the standard parameters (``client_id``, ``state``,
                etc.).
            code_verifier (str | None): PKCE code verifier, e.g. from
                ``py_oauth.pkce.generate_code_verifier``. Pass the same one to
                ``get_access_token``. Required if ``REQUIRES_PKCE`` is set.

        Returns:
            str: The provider's authorization URL.

        Raises:
            TypeError: If ``scopes`` is a string instead of a sequence of
                strings.
            ValueError: If the provider requires PKCE and no
                ``code_verifier`` is given.
        """
        # A str is a Sequence[str] too, so it would be split into characters.
        if isinstance(scopes, str):
            raise TypeError("scopes must be a sequence of strings, not a str")
        self._check_pkce(code_verifier)
        params = {
            **(extra_params or {}),
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "state": state,
        }
        scope = self.SCOPE_SEPARATOR.join(
            self.DEFAULT_SCOPES if scopes is None else scopes
        )
        if scope:
            params["scope"] = scope
        if code_verifier is not None:
            params["code_challenge"] = code_challenge(code_verifier)
            params["code_challenge_method"] = "S256"
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    def get_access_token(
        self, code: str, *, code_verifier: str | None = None
    ) -> AccessToken:
        """Exchange an authorization code for an access token.

        Args:
            code (str): Authorization code returned to the redirect URI.
            code_verifier (str | None): The PKCE code verifier passed to
                ``get_authorization_url``, if one was.

        Returns:
            AccessToken: The access token issued by the provider.

        Raises:
            TokenExchangeError: If the provider rejects the code or the
                request fails.
            ValueError: If the provider requires PKCE and no
                ``code_verifier`` is given.
        """
        self._check_pkce(code_verifier)
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._redirect_uri,
        }
        if code_verifier is not None:
            params["code_verifier"] = code_verifier

        kwargs: dict[str, Any] = {}
        if self.CLIENT_AUTH == "basic":
            # RFC 6749 §2.3.1: form-encode the credentials before Basic auth.
            kwargs["auth"] = (
                quote_plus(self._client_id),
                quote_plus(self._get_client_secret()),
            )
        else:
            params["client_id"] = self._client_id
            params["client_secret"] = self._get_client_secret()

        data = self._request(
            "POST",
            self.TOKEN_URL,
            error_cls=TokenExchangeError,
            action=f"{self._name} token request",
            # Without it, some providers (e.g. GitHub) reply form-encoded.
            headers={"Accept": "application/json"},
            data=params,
            **kwargs,
        )
        return self._parse_access_token(data)

    @abstractmethod
    def fetch_user(self, token: AccessToken) -> Identity:
        """Fetch the authenticated user's details from the provider.

        Args:
            token (AccessToken): Token from ``get_access_token``. To use a
                stored token value, wrap it: ``AccessToken(token=value)``.

        Returns:
            Identity: The user's identity as reported by the provider.

        Raises:
            UserFetchError: If the provider rejects the token or the request
                fails.
        """

    @property
    def _name(self) -> str:
        """Provider name used in error messages, e.g. ``"Google"``."""
        return type(self).__name__

    def _get_client_secret(self) -> str:
        """Return the client secret to send in the token request.

        Override it for providers whose secret is generated per request, such
        as Apple's signed JWT.

        Returns:
            str: The client secret.
        """
        return self._client_secret

    def _check_pkce(self, code_verifier: str | None) -> None:
        """Raise if the provider requires PKCE and no verifier is given.

        Args:
            code_verifier (str | None): The caller's PKCE code verifier.

        Raises:
            ValueError: If ``REQUIRES_PKCE`` is set and ``code_verifier`` is
                None.
        """
        if self.REQUIRES_PKCE and code_verifier is None:
            raise ValueError(f"{self._name} requires a PKCE code_verifier")

    def _get_user_info(
        self, url: str, access_token: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Fetch a JSON object from a user API with a Bearer token.

        Args:
            url (str): The user API endpoint.
            access_token (str): Access token value.
            **kwargs (Any): Passed through to ``_request``. Any ``headers`` are
                merged with the ``Authorization`` header.

        Returns:
            dict[str, Any]: The parsed JSON body.

        Raises:
            UserFetchError: If the request fails or the response is an error.
        """
        return self._request(
            "GET",
            url,
            error_cls=UserFetchError,
            action=f"{self._name} user info request",
            headers={
                "Authorization": f"Bearer {access_token}",
                **kwargs.pop("headers", {}),
            },
            **kwargs,
        )

    def _get_user_id(self, data: Mapping[str, Any], key: str) -> str:
        """Return the user's ID from a user info response, as a string.

        Args:
            data (Mapping[str, Any]): Parsed user info response.
            key (str): Field that holds the ID, e.g. ``"sub"``.

        Returns:
            str: The ID. Numeric IDs (e.g. GitHub's) are converted to strings.

        Raises:
            UserFetchError: If the field is missing or empty.
        """
        value = data.get(key)
        if isinstance(value, bool) or not isinstance(value, str | int) or value == "":
            raise UserFetchError(f"{self._name} user info response is missing {key}")
        return str(value)

    @staticmethod
    def _get_str(data: Mapping[str, Any], key: str) -> str | None:
        """Return a string field from a provider response.

        Args:
            data (Mapping[str, Any]): Parsed provider response.
            key (str): Field to read, e.g. ``"email"``.

        Returns:
            str | None: The value, or None if it's missing, empty or not a
                string.
        """
        value = data.get(key)
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _get_bool(data: Mapping[str, Any], key: str) -> bool:
        """Return whether a boolean field is true, accepting ``"true"`` too.

        Some providers (e.g. Apple) send boolean claims as strings.

        Args:
            data (Mapping[str, Any]): Parsed provider response.
            key (str): Field to read, e.g. ``"email_verified"``.

        Returns:
            bool: True only for ``True`` or a case-insensitive ``"true"``.
        """
        value = data.get(key)
        return value is True or (isinstance(value, str) and value.lower() == "true")

    def _request(
        self,
        method: str,
        url: str,
        *,
        error_cls: type[OAuthError],
        action: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a request and return its JSON object body, or raise ``error_cls``.

        Args:
            method (str): HTTP method, e.g. ``"POST"``.
            url (str): URL to send the request to.
            error_cls (type[OAuthError]): Exception class to raise on failure.
            action (str): What the request is, used in error messages.
            **kwargs (Any): Passed through to ``httpx.Client.request``.

        Returns:
            dict[str, Any]: The parsed JSON body.

        Raises:
            OAuthError: An instance of ``error_cls`` if the request can't be
                sent, the response is an error, or its body isn't a JSON
                object.
        """
        data = self._send(method, url, error_cls=error_cls, action=action, **kwargs)
        if not isinstance(data, dict):
            raise error_cls(f"{action} returned an invalid response")
        return data

    def _request_list(
        self,
        method: str,
        url: str,
        *,
        error_cls: type[OAuthError],
        action: str,
        **kwargs: Any,
    ) -> list[Any]:
        """Like ``_request``, for endpoints that return a JSON array.

        Args:
            method (str): HTTP method, e.g. ``"GET"``.
            url (str): URL to send the request to.
            error_cls (type[OAuthError]): Exception class to raise on failure.
            action (str): What the request is, used in error messages.
            **kwargs (Any): Passed through to ``httpx.Client.request``.

        Returns:
            list[Any]: The parsed JSON body.

        Raises:
            OAuthError: An instance of ``error_cls`` if the request can't be
                sent, the response is an error, or its body isn't a JSON
                array.
        """
        data = self._send(method, url, error_cls=error_cls, action=action, **kwargs)
        if not isinstance(data, list):
            raise error_cls(f"{action} returned an invalid response")
        return data

    def _send(
        self,
        method: str,
        url: str,
        *,
        error_cls: type[OAuthError],
        action: str,
        **kwargs: Any,
    ) -> Any:
        """Send a request and return its parsed JSON body, or raise ``error_cls``.

        Args:
            method (str): HTTP method, e.g. ``"POST"``.
            url (str): URL to send the request to.
            error_cls (type[OAuthError]): Exception class to raise on failure.
            action (str): What the request is, used in error messages.
            **kwargs (Any): Passed through to ``httpx.Client.request``.

        Returns:
            Any: The parsed JSON body, or None if it isn't valid JSON.

        Raises:
            OAuthError: An instance of ``error_cls`` if the request can't be
                sent or the response is an error.
        """
        # httpx raises UnicodeEncodeError for non-ASCII header values, e.g. a
        # malformed stored token.
        try:
            if self._client is None:
                response = httpx.request(method, url, **kwargs)
            else:
                response = self._client.request(method, url, **kwargs)
        except (httpx.HTTPError, UnicodeEncodeError) as exc:
            raise error_cls(f"{action} failed") from exc

        return self._parse_response(response, error_cls, action)

    def _parse_response(
        self, response: httpx.Response, error_cls: type[OAuthError], action: str
    ) -> Any:
        """Return the parsed JSON body of a response, or raise ``error_cls``.

        A successful status with an error in the body (as GitHub's token
        endpoint returns) is also treated as a failure.

        Args:
            response (httpx.Response): Response from the provider.
            error_cls (type[OAuthError]): Exception class to raise on failure.
            action (str): What the request was, used in the error message.

        Returns:
            Any: The parsed JSON body, or None if it isn't valid JSON.

        Raises:
            OAuthError: An instance of ``error_cls`` if the response is an
                error.
        """
        try:
            data = response.json()
        except ValueError:
            data = None

        error, description = self._extract_error(data)
        if response.is_error or error is not None:
            raise error_cls(
                f"{action} failed with status {response.status_code}",
                error=error,
                description=description,
                status_code=response.status_code,
            )
        return data

    def _extract_error(self, data: Any) -> tuple[str | None, str | None]:
        """Pull the error code and description out of a response body.

        The default handles the standard OAuth shape (RFC 6749 §5.2),
        ``{"error": "...", "error_description": "..."}``. Without an
        ``error_description``, a top-level ``message`` (as GitHub's and
        Discord's APIs return) or ``detail`` (RFC 9457, as X's API returns) is
        used as the description. An ``error`` object with a ``code`` and
        ``message`` (as Facebook's and Microsoft Graph's APIs return) is also
        handled. Override it for providers that use a different shape.

        It's also called on successful responses, so it must return
        ``(None, None)`` when the body isn't an error.

        Args:
            data (Any): Parsed JSON body, or None if it wasn't valid JSON.

        Returns:
            tuple[str | None, str | None]: The error code and description.
        """
        if not isinstance(data, dict):
            return None, None

        error = data.get("error")
        if isinstance(error, dict):
            data, code = error, error.get("code")
            error = str(code) if isinstance(code, str | int) else None
        description = (
            data.get("error_description") or data.get("message") or data.get("detail")
        )
        return (
            error if isinstance(error, str) else None,
            description if isinstance(description, str) else None,
        )

    def _parse_access_token(self, data: dict[str, Any]) -> AccessToken:
        """Build an ``AccessToken`` from a standard token response.

        Override it for providers whose token response differs from
        RFC 6749 §5.1.

        Args:
            data (dict[str, Any]): Parsed JSON body of the token response.

        Returns:
            AccessToken: The parsed token.

        Raises:
            TokenExchangeError: If ``access_token`` is missing.
        """
        token = self._get_str(data, "access_token")
        if token is None:
            raise TokenExchangeError(
                f"{self._name} token response is missing access_token"
            )

        # A malformed lifetime is treated as unknown: the token is still valid.
        expires_in = data.get("expires_in")
        expires_at = None
        try:
            # bool is an int subclass, but True isn't a lifetime.
            if expires_in is None or isinstance(expires_in, bool):
                raise TypeError
            expires_in = int(expires_in)
            if expires_in < 0:
                raise ValueError
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        except (TypeError, ValueError, OverflowError):
            expires_in = expires_at = None

        # Most providers separate scopes with spaces, but some use commas.
        scope = data.get("scope")
        scopes = re.split(r"[\s,]+", scope) if isinstance(scope, str) else []

        return AccessToken(
            token=token,
            expires_in=expires_in,
            expires_at=expires_at,
            refresh_token=self._get_str(data, "refresh_token"),
            scopes=tuple(s for s in scopes if s),
            raw=data,
        )
