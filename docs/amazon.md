# Amazon setup

Set up Login with Amazon to get a client ID and secret for `py_oauth.Amazon`.

## Steps

1. Sign in to the [Login with Amazon console](https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html) with an Amazon Developer account.
2. Click **"Create a New Security Profile"**. Enter the following details, then click **Save**:
   - Security Profile Name
   - Security Profile Description
   - Consent Privacy Notice URL
   - Consent Logo Image (optional)
3. Open the security profile's **"Web Settings"** and click **Edit**.
4. (Optional) Under **"Allowed Origins"**, add the origins of pages that use the Login with Amazon JavaScript SDK, e.g. `https://example.com`. Not needed when your backend redirects users to Amazon.
5. Under **"Allowed Return URLs"**, add your `redirect_uri` (HTTPS), e.g. `https://example.com/auth/amazon/callback`. Click **Save**.
6. Copy the **Client ID** and **Client Secret** from **"Web Settings"**.

## Use with py-oauth-kit

```python
from py_oauth import Amazon

amazon = Amazon(
    client_id="amzn1.application-oa2-client....",
    client_secret="...",
    redirect_uri="https://example.com/auth/amazon/callback",
)
```

## Notes

- The default `profile` scope gives the user's ID, name and email.
- Amazon doesn't say whether the email is verified, so `email_verified` is always `False`.
- Amazon has no username, so `name` is `"Unknown"` when the profile has no name.

## References

- [Register for Login with Amazon](https://developer.amazon.com/docs/login-with-amazon/register-web.html)
- [Authorization code grant](https://developer.amazon.com/docs/login-with-amazon/authorization-code-grant.html)
- [Obtain customer profile information](https://developer.amazon.com/docs/login-with-amazon/obtain-customer-profile.html)
