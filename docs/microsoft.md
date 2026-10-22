# Microsoft setup

Register an app in Microsoft Entra ID to get a client ID and secret for
`py_oauth.Microsoft`.

## Steps

1. Sign in to the [Microsoft Entra admin center](https://entra.microsoft.com)
   (or the Azure portal) and go to **App registrations > New registration**.
2. Fill in:
   - **Name**.
   - **Supported account types**: who can sign in. This decides the `tenant`
     to use (see below).
   - **Redirect URI**: platform **Web**, and your `redirect_uri`, e.g.
     `https://example.com/auth/microsoft/callback`.
3. Click **Register**. On the **Overview** page, copy the **Application (client)
   ID** and, for single-tenant apps, the **Directory (tenant) ID**.
4. Go to **Certificates & secrets > Client secrets > New client secret**. Copy
   the secret's **Value** (not its ID). It's shown only once, and it expires:
   create a new one before then.

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

| Supported account types                            | `tenant`                   |
| -------------------------------------------------- | -------------------------- |
| Any organizational directory and personal accounts | `"common"` (default)       |
| Any organizational directory                       | `"organizations"`          |
| Personal Microsoft accounts only                   | `"consumers"`              |
| This organizational directory only                 | Your Directory (tenant) ID |

## Notes

- Microsoft doesn't verify emails, so `email_verified` is always `False`.
  Don't use the email to match users to existing accounts.
- `Identity.id` is unique to your app; it isn't the user's Microsoft Graph
  object ID.

## References

- [Register an application](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)
- [OAuth 2.0 authorization code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow)
- [UserInfo endpoint](https://learn.microsoft.com/en-us/entra/identity-platform/userinfo)
