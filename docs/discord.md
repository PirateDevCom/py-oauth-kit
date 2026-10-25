# Discord setup

Create a Discord application to get a client ID and secret for `py_oauth.Discord`.

## Steps

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**. Enter a name, accept the terms, then click **Create**.
2. (Optional) On **General Information**, fill in the following details, then click **Save Changes**. Discord shows them to users on the authorization screen:
   - App Icon
   - Terms of Service URL
   - Privacy Policy URL
3. Open **OAuth2** in the sidebar.
4. Under **Redirects**, click **Add Redirect** and enter your `redirect_uri`, e.g. `https://example.com/auth/discord/callback`. Click **Save Changes**.
5. Copy the **Client ID**. Click **Reset Secret** to get the **Client Secret**, and copy it. Discord shows it only once.

## Use with py-oauth-kit

```python
from py_oauth import Discord

discord = Discord(
    client_id="...",
    client_secret="...",
    redirect_uri="https://example.com/auth/discord/callback",
)
```

## Notes

- The default scopes are `identify` and `email`. Without `email`, `email` is `None` and `email_verified` is always `False`.
- `name` is the user's display name, or their username if they haven't set one.

## References

- [OAuth2 documentation](https://discord.com/developers/docs/topics/oauth2)
- [Get Current User](https://discord.com/developers/docs/resources/user#get-current-user)
