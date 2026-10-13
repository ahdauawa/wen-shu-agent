# Protect your account

<!-- WenShu conversion: MDX includes expanded; UI components rendered as text; related links omitted. See ../README.md. -->

Every Zulip user has an API key, which can be used to do essentially everything
that you can do when you're logged in. You should treat your Zulip API key as
carefully as you treat your password. Integrations should use a [bot's API
key](/api/api-keys) rather than your own whenever possible.

Be sure to change both your password and API key immediately in the following
situations:

* Accidentally sharing your password or API key with someone else.
* Losing a device where you're logged in to Zulip (e.g., a cell phone or laptop).
* Losing a device that has a downloaded copy of your [`zuliprc`
file](/api/api-keys#download-a-zuliprc-file), which includes your API key.

Changing your API key will immediately log you out of Zulip on all mobile
devices.

## Change your password and API key

1. Click the gear icon in the upper right of the web or desktop app.
1. Select **Personal settings**.
1. On the left, click **Account & privacy**.

1. Under **Account**, click **Change your password**.
1. Enter your old password and your new password, and click **Change**.
1. Under **API key**, click **Manage your API key**.
1. Enter your new password, and click **Get API key**.
1. Click **Generate new API key**.

If you've forgotten your password, you can [reset
it](/help/change-your-password#if-youve-forgotten-or-never-had-a-password)
using your email account.
