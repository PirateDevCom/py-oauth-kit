# Facebook setup

Create a Meta app with Facebook Login to get an App ID and App secret for `py_oauth.Facebook`.

## Steps

1. Go to [Meta for Developers](https://developers.facebook.com/apps) and click **"Create App"**.
2. Go through the following tabs, then click **Create app**:
   - **"App details"**: enter the **App name** and **App contact email**.
   - **"Use cases"**: choose **Authenticate and request data from users with Facebook Login**.
   - **"Business"**: select or create a business profile. Meta requires every app to have one, and it must be verified before you can publish the app. You can verify it later.
   - **"Requirements"**: shows what's needed to publish (**Business verification** and **App Review**). Nothing to do here yet.
   - **"Overview"**: check the details and click **"Create app"**.
3. In the app dashboard, open **"Use cases"**, then click **"Customize"** next to Facebook Login:
   - Under **"Permissions"**, make sure `email` and `public_profile` are added.
   - Under **"Settings"**, add your `redirect_uri` to **Valid OAuth Redirect URIs**, e.g. `https://example.com/auth/facebook/callback`. Click **Save Changes**.
4. Open **"App settings > Basic"**. Copy the **App ID**, and click **"Show"** to copy the **App secret**.
5. On the same page, enter the following details, then click **Save changes**. Meta needs them before you can publish the app:
   - App icon
   - Privacy policy URL
   - Terms of Service URL (optional)
   - User data deletion: a data deletion instructions URL or callback URL
   - Category
6. Verify your business profile, complete the publishing requirements, then publish the app. Until then, only people with a role on the app (admins, developers and testers) can sign in.

## Use with py-oauth-kit

```python
from py_oauth import Facebook

facebook = Facebook(
    client_id="...",  # App ID
    client_secret="...",  # App secret
    redirect_uri="https://example.com/auth/facebook/callback",
)
```

## Notes

- Facebook doesn't say whether the email is verified, so `email_verified` is always `False`.
- The email is `None` if the user has none or declines to share it.
- py-oauth-kit uses Graph API `v26.0`. Each version is supported for about two years.

## References

- [Manually Build a Login Flow](https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow)
- [Graph API versions](https://developers.facebook.com/docs/graph-api/changelog/versions)
