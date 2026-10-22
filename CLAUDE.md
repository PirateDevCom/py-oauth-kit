# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Reusable OAuth helpers, mainly functions that wrap the OAuth API calls. It's meant to be used from Django, DRF and other Python projects, so keep the core free of framework dependencies.

## Project state

Early development. Providers: Amazon, Apple, Discord, Facebook, GitHub, Google, LinkedIn, Microsoft, Reddit, Twitter, Yahoo. Tests use pytest (dev dependency); no linter or type checker is configured yet.

## Tooling

- Python 3.13 (pinned in `.python-version`, `requires-python >= 3.13`).
- Managed with `uv`; build backend is `uv_build`.
- HTTP client: `httpx` (the only required runtime dependency). Django/DRF extras are deferred, so don't add them yet.
- Optional `apple` extra: `cryptography`, to sign Apple's client secret. `apple.py` imports it lazily, so `py_oauth` imports without it.

```sh
uv sync --frozen     # create .venv and install from uv.lock
uv add <pkg>         # add a runtime dependency (rewrites uv.lock: ask first)
uv add --dev <pkg>   # add a dev dependency (e.g. pytest, ruff)
uv run --frozen python -c "import py_oauth"
uv run --frozen pytest   # run the tests
uv build             # build sdist + wheel into dist/
```

## Layout

- `src/` layout: import package is `py_oauth`, distribution name is `py-oauth-kit` (`py-oauth` is too similar to PyPI's `pyoauth`), so `[tool.uv.build-backend] module-name` sets the import package.
- `py.typed` marks the package as typed (PEP 561), so public APIs should carry type hints.
- `types.py`: `AccessToken` and `Identity`, frozen dataclasses returned by providers. `raw` keeps the provider's full response.
- `exceptions.py`: `OAuthError` base, with `TokenExchangeError` and `UserFetchError`. httpx errors are wrapped, so callers never catch httpx exceptions.
- `providers/base.py`: `OAuthProvider` implements the standard authorization code flow (RFC 6749). It covers the authorization URL, token exchange, response/error parsing (`_request` for JSON objects, `_request_list` for arrays, `_parse_response`, `_extract_error`) and token parsing (`_parse_access_token`). `fetch_user(token: AccessToken)` takes the whole token (Apple needs `raw["id_token"]`). User-API helpers for `fetch_user`: `_get_user_info(url, access_token)` (Bearer GET, raises `UserFetchError`), `_get_user_id(data, key)` (ID as `str`, raises if missing) `_get_str(data, key)` (string field, or None if missing, empty or not a string) and `_get_bool(data, key)` (true for `True` or `"true"`).
- `providers/<name>.py`: one class per provider, named after it (e.g. `Google`). A provider sets `AUTHORIZATION_URL`, `TOKEN_URL`, `DEFAULT_SCOPES` (and `SCOPE_SEPARATOR` if not a space), and implements `fetch_user`. Token-request differences are class attributes: `CLIENT_AUTH` (`"body"`/`"basic"`), `REQUIRES_PKCE` (e.g. Twitter). A per-request secret (Apple's JWT) overrides `_get_client_secret()`. URLs that depend on constructor arguments are set per instance in `__init__` (Microsoft's tenant). Default authorization parameters are added by overriding `get_authorization_url` and merging under `extra_params` (Reddit's `duration`, Apple's `response_mode`, Yahoo's `nonce`); extra headers on every request by overriding `_send` (Reddit's User-Agent). Anything else overrides base methods only where the provider differs from the standard.
- `providers/oidc.py`: `OIDCProvider` implements `fetch_user` for providers with a standard OpenID Connect userinfo endpoint (Google, LinkedIn, Microsoft, Yahoo); subclasses set `USER_INFO_URL` alongside the usual URLs, and override only where the provider differs (Microsoft's tenant and unverified email, Yahoo's `nonce`).
- `pkce.py`: `generate_code_verifier()` and `code_challenge()` (RFC 7636, S256). Callers pass the same verifier to `get_authorization_url` and `get_access_token`.
- `tests/`: pytest, mirroring `src/` (`tests/providers/test_<name>.py`). `conftest.py`'s `api` fixture is a fake provider API built on `httpx.MockTransport`: register responses with `api.add(method, url, json=...)`, pass `api.client` to the provider and inspect `api.requests`. No real network calls.
- Public names are re-exported from `py_oauth/__init__.py` and `providers/__init__.py`.

## Conventions

- Google-style docstrings with types in `Args`/`Returns`/`Attributes`.
- Lines at most 88 characters.
- `Identity.name` falls back to another account handle when the provider's display name is missing (e.g. username/login), never to email. With no handle (e.g. Amazon), it falls back to `"Unknown"`.

## Provider notes

- **Facebook:** `API_VERSION` is pinned (`v26.0`); Graph API versions expire about two years after release, so bump it before then.
- **Apple:** `fetch_user` verifies the ID token's RS256 signature against Apple's JWKS (cached per instance, refetched on an unknown `kid` at most once per `KEYS_REFETCH_INTERVAL`), then checks `iss`, `aud` and `exp`.
