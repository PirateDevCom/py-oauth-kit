# Microsoft setup

Register an app in Microsoft Entra ID to get a client ID and secret for `py_oauth.Microsoft`.

## Steps

1. Sign in to the [Microsoft Entra admin center](https://entra.microsoft.com) (or the Azure portal) and go to **"App registrations > New registration"**.
2. Enter the following details, then click **Register**:
   - Name
   - Supported account types: who can sign in. This decides the `tenant` to use (see below).
   - Redirect URI: platform **Web**, and your `redirect_uri`, e.g. `https://example.com/auth/microsoft/callback`
3. On the **"Overview"** page, copy the **Application (client) ID** and, for single-tenant apps, the **Directory (tenant) ID**.
4. Go to **"Certificates & secrets > Client secrets"** and click **"New client secret"**. Enter a description, pick an expiry, then click **Add**. Copy the secret's **Value** (not its ID). It's shown only once, and it expires: create a new one before then.
5. (Optional) On **"Branding & properties"**, fill in the following details, then click **Save**. Microsoft shows them to users on the consent screen:
   - Logo
   - Home page URL
   - Terms of service URL
   - Privacy statement URL
   - Publisher domain

## Use with py-oauth-kit

```python
from py_oauth import Microsoft

microsoft = Microsoft(
    client_id="...",
    client_secret="...",
    redirect_uri="https://example.com/auth/microsoft/callback",
    tenant="common",
)
```

Pick `tenant` to match **Supported account types**:

| Supported account types                           | `tenant`                   |
| ------------------------------------------------- | -------------------------- |
| Any Entra ID Tenant + Personal Microsoft accounts | `"common"` (default)       |
| Multiple Entra ID tenants                         | `"organizations"`          |
| Personal accounts only                            | `"consumers"`              |
| Single tenant only - (your tenant name)           | Your Directory (tenant) ID |

## Notes

- Microsoft doesn't verify emails, so `email_verified` is always `False`. Don't use the email to match users to existing accounts.
- `Identity.id` is unique to your app; it isn't the user's Microsoft Graph object ID.
- The profile picture needs the access token to download, so `avatar_url` is always `None`.

## References

- [Register an application](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)
- [OAuth 2.0 authorization code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow)
- [UserInfo endpoint](https://learn.microsoft.com/en-us/entra/identity-platform/userinfo)
