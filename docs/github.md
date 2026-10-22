# GitHub setup

Create a GitHub OAuth App to get a client ID and secret for `py_oauth.GitHub`.

py-oauth-kit supports OAuth Apps, not GitHub Apps.

## Steps

1. Go to **Settings > Developer settings > OAuth Apps**
   ([direct link](https://github.com/settings/developers)) and click **New OAuth
   App**. For an organization, use the organization's settings instead.
2. Fill in:
   - **Application name** and **Homepage URL**.
   - **Authorization callback URL**: your `redirect_uri`, e.g.
     `https://example.com/auth/github/callback`.
3. Click **Register application**.
4. Copy the **Client ID**. Click **Generate a new client secret** and copy it.
   GitHub shows it only once.

## Use with py-oauth-kit

```python
from py_oauth import GitHub

github = GitHub(
    client_id="...",
    client_secret="...",
    redirect_uri="https://example.com/auth/github/callback",
)
```

## Notes

- An OAuth App has one callback URL. Create separate apps for development and
  production.
- OAuth App tokens don't expire by default (`expires_in` is `None`). They stay
  valid until the user revokes them, or they go unused for a year.
- The default scopes are `read:user` and `user:email`. `user:email` gives the
  user's primary email, even if it's private.

## References

- [Creating an OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app)
- [Authorizing OAuth Apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
- [Scopes for OAuth Apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps)
- [Token expiration and revocation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/token-expiration-and-revocation)
