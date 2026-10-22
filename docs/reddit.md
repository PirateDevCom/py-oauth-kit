# Reddit setup

Create a Reddit app to get a client ID and secret for `py_oauth.Reddit`.

## Requirements

Since November 2025, new Reddit API access needs Reddit's approval under its
Responsible Builder Policy. Request access before creating the app. Apps
created before then keep working.

## Steps

1. Go to [Reddit app preferences](https://www.reddit.com/prefs/apps) and click
   **Create another app**.
2. Fill in:
   - **Name**.
   - Type: **web app**.
   - **Redirect uri**: your `redirect_uri`, e.g.
     `https://example.com/auth/reddit/callback`.
3. Click **Create app**.
4. Copy the **client ID** (the string under the app's name) and the **secret**.

## Use with py-oauth-kit

```python
from py_oauth import Reddit

reddit = Reddit(
    client_id="...",
    client_secret="...",
    redirect_uri="https://example.com/auth/reddit/callback",
    user_agent="web:com.example.app:1.0 (by /u/your_username)",
)
```

## Notes

- Reddit throttles or blocks generic User-Agents. Use the format
  `<platform>:<app ID>:<version> (by /u/<username>)`.
- Reddit doesn't share the user's email, so `email` is always `None`.
- Access tokens last one hour.

## References

- [OAuth2 wiki](https://github.com/reddit-archive/reddit/wiki/OAuth2)
- [API rules (User-Agent)](https://github.com/reddit-archive/reddit/wiki/API)
- [Responsible Builder Policy announcement](https://www.reddit.com/r/redditdev/comments/1oug31u/introducing_the_responsible_builder_policy_new/)
