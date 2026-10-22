# X (Twitter) setup

Create an X app with OAuth 2.0 to get a client ID and secret for
`py_oauth.Twitter`.

## Steps

1. Sign in to the [X Developer Console](https://console.x.com) and create an
   app.
2. Open the app's **User authentication settings** and click **Set up** (or
   **Edit**):
   - **App permissions**: **Read**.
   - **Request email from users**: turn it on to get the user's email.
   - **Type of App**: **Web App, Automated App or Bot**. This makes it a
     confidential client, which gets a client secret.
   - **Callback URI / Redirect URL**: your `redirect_uri`, e.g.
     `https://example.com/auth/twitter/callback`. It must match exactly.
   - **Website URL**, and the **Terms of service** and **Privacy policy** URLs
     (needed to request email).
3. Save. Copy the **OAuth 2.0 Client ID** and **Client Secret** from **Keys and
   tokens**. Don't use the API Key and Secret: those are for OAuth 1.0a.

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
- Without **Request email from users**, `email` is `None`.
- Access tokens last two hours. For a refresh token, add the `offline.access`
  scope.
- Exchange the code quickly: X's authorization codes expire after 30 seconds.

## References

- [OAuth 2.0 Authorization Code Flow with PKCE](https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code)
- [Authentication overview](https://docs.x.com/fundamentals/authentication/oauth-2-0/overview)
