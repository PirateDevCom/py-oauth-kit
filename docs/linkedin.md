# LinkedIn setup

Create a LinkedIn app with Sign In with LinkedIn using OpenID Connect to get a client ID and secret for `py_oauth.LinkedIn`.

## Steps

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps) and click **"Create app"**.
2. Enter the following details, accept the legal agreement, then click **Create app**:
   - App name
   - LinkedIn Page: your company page. The page's admin may need to verify the app.
   - Privacy policy URL (optional)
   - App logo
3. Open the **"Products"** tab and click **"Request access"** next to **Sign In with LinkedIn using OpenID Connect**.
4. Open the **"Auth"** tab. Under **"Authorized redirect URLs for your app"**, add your `redirect_uri`, e.g. `https://example.com/auth/linkedin/callback`. Click **Update**.
5. Copy the **Client ID** and **Primary Client Secret** from the **"Auth"** tab.

## Use with py-oauth-kit

```python
from py_oauth import LinkedIn

linkedin = LinkedIn(
    client_id="...",
    client_secret="...",
    redirect_uri="https://example.com/auth/linkedin/callback",
)
```

## Notes

- Without the **Sign In with LinkedIn using OpenID Connect** product, LinkedIn rejects the default scopes (`openid`, `email`, `profile`).

## References

- [Sign In with LinkedIn using OpenID Connect](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2)
- [Authorization Code Flow](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow)
