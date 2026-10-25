# Yahoo setup

Create a Yahoo app to get a client ID and secret for `py_oauth.Yahoo`.

## Steps

1. Go to the [Yahoo Developer Network Apps page](https://developer.yahoo.com/apps/) and click **Create an App**.
2. Enter the following details, then click **Create App**:
   - Application Name
   - Description (optional)
   - Homepage URL (optional)
   - Redirect URI(s): your `redirect_uri`, e.g. `https://example.com/auth/yahoo/callback`
   - OAuth Client Type: **Confidential Client**
   - API Permissions: under **OpenID Connect Permissions**, check **Email** and **Profile**
3. Copy the **Client ID** and **Client Secret**.

## Use with py-oauth-kit

```python
from py_oauth import Yahoo

yahoo = Yahoo(
    client_id="...",
    client_secret="...",
    redirect_uri="https://example.com/auth/yahoo/callback",
)
```

## Notes

- Without the **Email** and **Profile** permissions, Yahoo rejects the default scopes (`openid`, `email`, `profile`).

## References

- [OAuth 2.0 guide](https://developer.yahoo.com/oauth2/guide/)
- [OpenID Connect](https://developer.yahoo.com/oauth2/guide/openid_connect/)
