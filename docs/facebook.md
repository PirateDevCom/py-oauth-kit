# Facebook setup

Create a Meta app with Facebook Login to get an App ID and App secret for
`py_oauth.Facebook`.

## Steps

1. Go to [Meta for Developers](https://developers.facebook.com/apps) and click
   **Create App**.
2. Choose the use case **Authenticate and request data from users with Facebook
   Login**, then finish creating the app.
3. In the app dashboard, open **Use cases**, then **Customize** next to Facebook
   Login.
   - Under **Permissions**, make sure `email` and `public_profile` are added.
   - Under **Settings**, add your `redirect_uri` to **Valid OAuth Redirect
     URIs**, e.g. `https://example.com/auth/facebook/callback`. Save.
4. Open **App settings > Basic**. Copy the **App ID** and **App secret**. Fill
   in the privacy policy URL and other required fields.
5. Publish the app. Until then, only people with a role on the app (admins,
   developers and testers) can sign in.

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

- Facebook doesn't say whether the email is verified, so `email_verified` is
  always `False`.
- The email is `None` if the user has none or declines to share it.
- py-oauth-kit uses Graph API `v26.0`. Each version is supported for about two
  years.

## References

- [Manually Build a Login Flow](https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow)
- [Graph API versions](https://developers.facebook.com/docs/graph-api/changelog/versions)
