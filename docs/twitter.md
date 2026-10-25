# X (Twitter) setup

Create an X app with OAuth 2.0 to get a client ID and secret for `py_oauth.Twitter`.

## Steps

1. Sign in to the [X Developer Console](https://console.x.com). Open **"Projects"** under **"Access"** in the sidebar and create a project. Every app must belong to one.
2. Open **"Apps"** in the sidebar and click **"Create App"** to create an app in that project.
3. Click the app, open the **"Keys & Tokens"** tab, and under **"User authentication settings"** click **"Set up"**. Enter the following details, then click **Save**:
   - App permissions: **Read**
   - Request email from users: turn it on to get the user's email.
   - Type of App: **Web App, Automated App or Bot**. This makes it a confidential client, which gets a client secret.
   - Callback URI / Redirect URL: your `redirect_uri`, e.g. `https://example.com/auth/twitter/callback`. It must match exactly.
   - Website URL
   - Terms of service URL (needed to request email)
   - Privacy policy URL (needed to request email)
4. Copy the **OAuth 2.0 Client ID** and **Client Secret** from the **"Keys & Tokens"** tab. _Don't use the Consumer Key, Access Token or Bearer Token: the first two are for OAuth 1.0a, and the Bearer Token is for app-only access, not user sign-in._

## Use with py-oauth-kit

```python
from py_oauth import Twitter

twitter = Twitter(
    client_id="...",
    client_secret="...",
    redirect_uri="https://example.com/auth/twitter/callback",
)
```

X requires PKCE: pass a `code_verifier` to both calls. See [PKCE](../README.md#pkce) in the README.

## Notes

- The default scopes are `tweet.read`, `users.read` and `users.email`.
- Without **Request email from users**, `email` is `None`. X only returns confirmed emails, so `email_verified` is `True` whenever there's an email.
- Access tokens last two hours. For a refresh token, add the `offline.access` scope.
- Exchange the code quickly: X's authorization codes expire after 30 seconds.

## References

- [OAuth 2.0 Authorization Code Flow with PKCE](https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code)
- [Authentication overview](https://docs.x.com/fundamentals/authentication/oauth-2-0/overview)
