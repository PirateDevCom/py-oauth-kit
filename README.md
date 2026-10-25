# py-oauth-kit

Simple OAuth 2.0 helpers for Python: build the sign-in URL, exchange the code for a token and fetch the user's details. Works with Django, DRF, Flask, FastAPI or plain Python. The only dependency is [httpx](https://www.python-httpx.org/).

**Supported providers:**

- Amazon
- Apple
- Discord
- Facebook
- GitHub
- Google
- LinkedIn
- Microsoft
- Reddit
- X (Twitter)
- Yahoo

## Installation

Requires Python 3.13+.

```sh
pip install py-oauth-kit
```

For Sign in with Apple, install the `apple` extra:

```sh
pip install "py-oauth-kit[apple]"
```

## Usage

### Basic flow

Sign-in takes three steps: send the user to the provider, exchange the code the provider sends back for a token, then fetch the user. Every provider works the same way; only the constructor differs (see below).

```python
import secrets

from py_oauth import GitHub, OAuthError

github = GitHub(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="https://example.com/auth/github/callback",
)

# 1. Redirect the user to the provider.
state = secrets.token_urlsafe()
session["oauth_state"] = state  # save it, e.g. in the user's session
url = github.get_authorization_url(state)

# 2. The provider redirects back to redirect_uri with ?code=...&state=...
if request.args["state"] != session.pop("oauth_state"):
    raise PermissionError("Invalid state")

try:
    token = github.get_access_token(request.args["code"])
    # 3. Fetch the user.
    user = github.fetch_user(token)
except OAuthError as exc:
    ...  # the provider rejected the request, or it failed

print(user.id, user.email, user.email_verified, user.name, user.username)
```

`session` and `request` stand for your framework's session and request objects.

The `redirect_uri` must be registered with the provider. Each provider section below links to a setup guide.

### Amazon

Setup guide: [docs/amazon.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/amazon.md)

```python
from py_oauth import Amazon

amazon = Amazon(client_id, client_secret, redirect_uri)
```

- Amazon has no username, so `name` is `"Unknown"` when the profile has no name.
- `email_verified` is always `False`.

### Apple

Setup guide: [docs/apple.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/apple.md)

```python
from py_oauth import Apple

apple = Apple(
    client_id="com.example.signin",  # your Services ID
    redirect_uri=redirect_uri,
    team_id="ABCDE12345",
    key_id="FGHIJ67890",
    private_key=open("AuthKey_FGHIJ67890.p8").read(),
)
```

- Requires a paid Apple Developer Program membership.
- Needs the `apple` extra (see Installation).
- There's no client secret: py-oauth-kit signs one with your `.p8` key.
- Apple redirects back with a **POST**, so your callback must accept POST. Browsers don't send `SameSite=Lax` cookies (Django's default) with it, so store the state in a `SameSite=None; Secure` cookie.
- Apple sends the user's name only on their **first** sign-in, in the `user` form field. Pass it on, and save the name then, as later sign-ins don't include it:

  ```python
  user = apple.fetch_user(token, user=request.POST.get("user"))
  ```

- Reuse one `Apple` instance across requests: it caches Apple's public keys.

### Discord

Setup guide: [docs/discord.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/discord.md)

```python
from py_oauth import Discord

discord = Discord(client_id, client_secret, redirect_uri)
```

### Facebook

Setup guide: [docs/facebook.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/facebook.md)

```python
from py_oauth import Facebook

facebook = Facebook(client_id, client_secret, redirect_uri)
```

- `email_verified` is always `False`.
- The email is `None` if the user has none or declines to share it.

### GitHub

Setup guide: [docs/github.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/github.md)

```python
from py_oauth import GitHub

github = GitHub(client_id, client_secret, redirect_uri)
```

- Supports OAuth Apps, not GitHub Apps.
- OAuth App tokens don't expire by default (`expires_in` is `None`); they stay valid until revoked or they go unused for a year.
- The email is the user's primary address. Without the `user:email` scope (requested by default), it falls back to the public profile email, which may be `None`.

### Google

Setup guide: [docs/google.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/google.md)

```python
from py_oauth import Google

google = Google(client_id, client_secret, redirect_uri)
```

- A refresh token is only sent with `access_type=offline`, and only on the user's first consent. Add `prompt=consent` to get one again:

  ```python
  url = google.get_authorization_url(
      state, extra_params={"access_type": "offline", "prompt": "consent"}
  )
  ```

### LinkedIn

Setup guide: [docs/linkedin.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/linkedin.md)

```python
from py_oauth import LinkedIn

linkedin = LinkedIn(client_id, client_secret, redirect_uri)
```

- Add the "Sign In with LinkedIn using OpenID Connect" product to your app in the LinkedIn developer portal, or sign-in fails.

### Microsoft

Setup guide: [docs/microsoft.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/microsoft.md)

```python
from py_oauth import Microsoft

microsoft = Microsoft(client_id, client_secret, redirect_uri, tenant="common")
```

- `tenant` sets who can sign in: `"common"` (default, "Any Entra ID Tenant + Personal Microsoft accounts"), `"organizations"` (Multiple Entra ID tenants), `"consumers"` (Personal accounts only) or your tenant ID. Single-tenant apps must pass their tenant.
- `email_verified` is always `False`, as Microsoft doesn't verify emails.
- `avatar_url` is always `None`.

### Reddit

Setup guide: [docs/reddit.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/reddit.md)

```python
from py_oauth import Reddit

reddit = Reddit(
    client_id,
    client_secret,
    redirect_uri,
    user_agent="web:com.example.app:1.0 (by /u/your_username)",
)
```

- Doesn't share the user's email, so `email` is always `None`.
- Requires a `user_agent`. Reddit blocks generic ones; use the format `<platform>:<app ID>:<version> (by /u/<username>)`.

### X (Twitter)

Setup guide: [docs/twitter.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/twitter.md)

```python
from py_oauth import Twitter

twitter = Twitter(client_id, client_secret, redirect_uri)
```

- Requires PKCE (see PKCE under Options).
- To get the email, enable "Request email from users" in your app's user authentication settings in the X Developer Console. Without it, `email` is `None`.

### Yahoo

Setup guide: [docs/yahoo.md](https://github.com/PirateDevCom/py-oauth-kit/blob/main/docs/yahoo.md)

```python
from py_oauth import Yahoo

yahoo = Yahoo(client_id, client_secret, redirect_uri)
```

- Enable the OpenID Connect permissions (Email, Profile) for your app in the Yahoo developer console, or sign-in fails.

## What you get back

`get_access_token` returns an `AccessToken`:

| Field           | Description                                   |
| --------------- | --------------------------------------------- |
| `token`         | The access token.                             |
| `expires_in`    | Lifetime in seconds, or `None` if not given.  |
| `expires_at`    | When it expires (UTC), or `None`.             |
| `refresh_token` | Refresh token, if the provider sent one.      |
| `scopes`        | Scopes granted, if the provider reports them. |
| `raw`           | The provider's full response.                 |

`fetch_user` returns an `Identity`:

| Field            | Description                                      |
| ---------------- | ------------------------------------------------ |
| `id`             | The user's ID at the provider (always a string). |
| `email`          | Email address, or `None`.                        |
| `email_verified` | Whether the provider verified the email.         |
| `name`           | Display name (see Names).                        |
| `username`       | Handle or login, or `None`.                      |
| `avatar_url`     | Profile picture URL, or `None`.                  |
| `raw`            | The provider's full response.                    |

To use a stored token later, wrap it: `github.fetch_user(AccessToken(token=value))`.

### Names

`name` is the user's display name. If the provider has none, it falls back to their username (e.g. GitHub login), and then to `"Unknown"`. It never falls back to the email.

### Emails

- `email` can be `None`: the user may have no email, or may not share it.
- Only trust `email` to match users to existing accounts when `email_verified` is `True`.

### Tokens

py-oauth-kit doesn't refresh tokens. If a provider sends a `refresh_token`, it's available on the `AccessToken`, but you refresh it yourself.

## Options

### Scopes and extra parameters

Each provider requests sensible default scopes. To change them, or to add extra query parameters:

```python
url = google.get_authorization_url(
    state,
    scopes=["openid", "email"],
    extra_params={"prompt": "select_account"},
)
```

### PKCE

PKCE adds extra protection to the sign-in. X (Twitter) requires it; other providers accept it. Generate a verifier, save it with the state, and pass it to both calls:

```python
from py_oauth import Twitter, generate_code_verifier

verifier = generate_code_verifier()
session["oauth_verifier"] = verifier
url = twitter.get_authorization_url(state, code_verifier=verifier)

# On the callback:
token = twitter.get_access_token(code, code_verifier=session.pop("oauth_verifier"))
```

### HTTP client

By default each request opens a new connection. To reuse connections, or set timeouts or proxies, pass your own `httpx.Client`:

```python
import httpx

client = httpx.Client(timeout=10)
github = GitHub(client_id, client_secret, redirect_uri, client=client)
```

## Errors

All errors inherit from `OAuthError`, so you never need to catch httpx errors:

- `TokenExchangeError`: exchanging the code failed (e.g. the code expired).
- `UserFetchError`: fetching the user failed (e.g. the token was revoked).

Each error has `error`, `description` and `status_code` from the provider, when available.

## License

MIT
