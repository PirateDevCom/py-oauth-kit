# Google setup

Create an OAuth client in Google Cloud to get a client ID and secret for `py_oauth.Google`.

## Steps

1. Go to the [Google Cloud console](https://console.cloud.google.com/) and create or select a project.
2. Open **Google Auth Platform** (or **APIs & Services > OAuth consent screen**) and set up the consent screen:
   - **Branding**: enter the following details, then click **Save**:
     - App name
     - User support email
     - App logo (optional): adding one means Google must verify your app before it can show the logo to users.
     - Application home page (optional)
     - Application privacy policy link (optional)
     - Application Terms of Service link (optional)
     - Authorized domains: your app's domain, e.g. `example.com`. The domains of the links above and of your `redirect_uri` must be listed here.
     - Developer contact email
   - **Audience**: choose **External** for any Google account. While the app is in **Testing**, add the accounts that may sign in under **Test users**.
   - **Data access**: click **Add or remove scopes**, add `openid`, `.../auth/userinfo.email` and `.../auth/userinfo.profile`, then click **Save**.
3. Open **Clients** (or **APIs & Services > Credentials**) and click **Create client**. Enter the following details, then click **Create**:
   - Application type: **Web application**
   - Name
   - Authorized redirect URIs: your `redirect_uri`, e.g. `https://example.com/auth/google/callback`
4. Copy the **Client ID** and **Client secret**. Save the secret right away, as Google may not show it again.
5. When you're ready for all users, set the publishing status to **In production** under **Audience**.

## Use with py-oauth-kit

```python
from py_oauth import Google

google = Google(
    client_id="....apps.googleusercontent.com",
    client_secret="...",
    redirect_uri="https://example.com/auth/google/callback",
)
```

## Notes

- py-oauth-kit requests the scopes as `openid`, `email` and `profile`, which are short names for the scopes added in **Data access**.
- These are non-sensitive scopes, so Google doesn't need to verify your app for them. Adding a logo still needs verification.
- In **Testing**, only test users can sign in, and refresh tokens expire after 7 days.
- A refresh token is only sent with `access_type=offline`. See the [README](../README.md#google).

## References

- [Using OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)
