# LinkedIn setup

Create a LinkedIn app with Sign In with LinkedIn using OpenID Connect to get a
client ID and secret for `py_oauth.LinkedIn`.

## Steps

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps) and
   click **Create app**.
2. Enter the app name, a LinkedIn Page (your company page) and a logo. Create
   the app. The page's admin may need to verify the app.
3. Open the **Products** tab and request **Sign In with LinkedIn using OpenID
   Connect**.
4. Open the **Auth** tab:
   - Under **Authorized redirect URLs for your app**, add your `redirect_uri`,
     e.g. `https://example.com/auth/linkedin/callback`.
   - Copy the **Client ID** and **Primary Client Secret**.

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

- Without the **Sign In with LinkedIn using OpenID Connect** product, LinkedIn
  rejects the default scopes (`openid`, `email`, `profile`).

## References

- [Sign In with LinkedIn using OpenID Connect](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2)
- [Authorization Code Flow](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow)
