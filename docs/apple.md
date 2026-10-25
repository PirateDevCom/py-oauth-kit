# Apple setup

Set up Sign in with Apple for the web to get the values for `py_oauth.Apple`: a Services ID, a Team ID, a Key ID and a private key (`.p8` file).

## Requirements

- A paid [Apple Developer Program](https://developer.apple.com/programs/) membership.
- The `apple` extra: `pip install "py-oauth-kit[apple]"`.
- A public HTTPS domain for the redirect URI. For local development, use a tunnel (e.g. ngrok) rather than `localhost`.

## Steps

All steps are in [Certificates, Identifiers & Profiles](https://developer.apple.com/account/resources).

### 1. Create an App ID

Sign in with Apple for the web must be linked to a primary App ID. Skip this if you already have an App ID with Sign in with Apple enabled.

1. Go to **"Identifiers"** and click **"+"**. Choose **App IDs**, click **Continue**, choose **App**, then click **Continue**.
2. Enter the following details, then click **Continue** and **Register**:
   - Description
   - Bundle ID: **Explicit**, e.g. `com.example.app`
   - Capabilities: enable **Sign in with Apple**

### 2. Create a Services ID

The Services ID is your `client_id`.

1. Go to **"Identifiers"** and click **"+"**. Choose **Services IDs**, then click **Continue**.
2. Enter the following details, then click **Continue** and **Register**:
   - Description: users see it on the consent screen, so use your app's name.
   - Identifier, e.g. `com.example.signin`
3. Open the new Services ID, enable **Sign in with Apple** and click **"Configure"**. Enter the following details, then click **Done**:
   - Primary App ID: the App ID from step 1
   - Domains and Subdomains: your domain, e.g. `example.com` (without `https://`)
   - Return URLs: your full `redirect_uri`, e.g. `https://example.com/auth/apple/callback`
4. Click **Continue**, then **Save**.

### 3. Create a key

1. Go to **"Keys"** and click **"+"**.
2. Enter a key name, enable **Sign in with Apple** and click **"Configure"**. Select your primary App ID, then click **Save**.
3. Click **Continue** and **Register**, then **download the `.p8` file**. You can only download it once.
4. Note the **Key ID** shown on the key's page.

### 4. Find your Team ID

Your Team ID is shown in the top right of the developer account, and under **"Membership details"**.

## Use with py-oauth-kit

```python
from py_oauth import Apple

apple = Apple(
    client_id="com.example.signin",  # Services ID
    redirect_uri="https://example.com/auth/apple/callback",
    team_id="ABCDE12345",
    key_id="FGHIJ67890",
    private_key=open("AuthKey_FGHIJ67890.p8").read(),
)
```

Keep the `.p8` file secret, like a password: load it from an environment variable or a secrets manager rather than committing it.

## Notes

- Apple redirects back with a **POST**, so the callback must accept POST. Store the state in a `SameSite=None; Secure` cookie, as browsers don't send `SameSite=Lax` cookies with this POST.
- Users can choose to hide their email. Apple then gives a private relay address (`...@privaterelay.appleid.com`). To send email to it, register your sending domain under **Sign in with Apple for Email Communication**.
- Apple sends the user's name only on their first sign-in, in the `user` form field. Pass it to `fetch_user(token, user=...)` and save it then. Otherwise `name` is `"Unknown"`.

## References

- [Configuring your environment for Sign in with Apple](https://developer.apple.com/documentation/signinwithapple/configuring-your-environment-for-sign-in-with-apple)
- [Configure Sign in with Apple for the web](https://developer.apple.com/help/account/configure-app-capabilities/configure-sign-in-with-apple-for-the-web)
- [Create a private key](https://developer.apple.com/help/account/keys/create-a-private-key)
