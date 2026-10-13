# Logging in

<!-- WenShu conversion: MDX includes expanded; UI components rendered as text; related links omitted. See ../README.md. -->

By default, Zulip allows logging in via email/password as well as
various social authentication providers like Google, GitHub, GitLab, Discord
and Apple.

Organization administrators can
[add other authentication methods](/help/configure-authentication-methods),
including the SAML and LDAP integrations, or disable any of the methods above.

You can log in with any method allowed by your organization, regardless of
how you signed up. For example, if you originally signed up using your Google
account, you can later log in using GitHub, as long as your Google account
and GitHub account use the same email address.

## Find the Zulip log in URL

Here are some ways to find the URL for your Zulip organization.

**Platform: If you are logged out**

* If your organization is hosted on [Zulip Cloud](https://zulip.com/zulip-cloud/)
(usually at `*.zulipchat.com`), go to the [**Find your
accounts**](https://zulip.com/accounts/find/) page and enter the email address
that you signed up with. You will receive an email with the sign-in
information for any Zulip organizations associated with your email address.
* Search your email account for a registration email from Zulip. The subject
line will include `Zulip: Your new account details` or `Zulip: Your new
organization details`. This email provides your organization's log in URL.
* If you have visited your organization's log in page in the past, try reviewing
your browser's history. Searching for `zulipchat.com` should find the right
page if your Zulip organization is hosted on [Zulip
Cloud](https://zulip.com/zulip-cloud/).
* You can ask your organization administrators for your Zulip URL.

**Platform: If you are logged in**

* If using Zulip in the browser, your organization's Zulip log in URL is the first part
of what you see in the URL bar (e.g., `<organization-name>.zulipchat.com` for
[Zulip Cloud](https://zulip.com/zulip-cloud/) organizations).
* In the Desktop app, select **Copy Zulip URL** from the **Zulip** menu to
copy the URL of the currently active organization. You can also access the
**Copy Zulip URL** option by right-clicking on an organization logo in the
**organizations sidebar** on the left.
* In the Mobile app, tap your **profile picture** in the bottom right corner of
the app, then tap  **Switch account** to see the URLs
for all the organizations you are logged in to.
* On [Zulip Cloud](https://zulip.com/zulip-cloud/) and other Zulip servers updated to
[Zulip 6.0 or
higher](https://zulip.readthedocs.io/en/stable/overview/changelog.html#zulip-6-x-series),
click the **gear** () icon in the upper right
corner of the web or desktop app. Your organization's log in URL is shown in the top
section of the menu.

## Log in to a new organization

**Platform: Mobile**

1. Tap the **menu** () tab in the bottom right corner of the app.

1. Tap the **switch account** () button.

1. Tap **Add new account**.
1. Enter the Zulip URL of the organization, and tap **Continue**.
1. Follow the on-screen instructions.

**Platform: Desktop**

If you are having trouble connecting, you may need to set your
[proxy settings](/help/connect-through-a-proxy) or add a
[custom certificate](/help/custom-certificates).

1. Click the **add organization** () icon in the
**organizations sidebar** on the left. You can also select **Add Organization**
from the **Zulip** menu in the top menu bar.
1. Enter the Zulip URL of the organization, and click **Connect**.
1. Follow the on-screen instructions.

To show or hide the **organizations sidebar** on the left, select
**Toggle Sidebar** from the **View** menu in the top menu bar.

**Platform: Web**

1. Go to the Zulip URL of the organization.
1. Follow the on-screen instructions.

## Switch between organizations

**Platform: Mobile**

1. Tap the **menu** () tab in the bottom right corner of the app.

1. Tap the **switch account** () button.

1. Tap on the desired Zulip organization.

**Platform: Desktop**

1. Click on a logo in the **organizations sidebar** on the left, or choose
an organization from the **Window** menu in the top menu bar.

To show or hide the **organizations sidebar** on the left, select
**Toggle Sidebar** from the **View** menu in the top menu bar.

**Platform: Web**

You can log in to multiple Zulip organizations by opening multiple tabs, and
logging into one Zulip organization in each tab. To switch Zulip organizations,
just switch tabs.

## Set or reset your password

If you signed up using passwordless authentication and want to start logging in
via email/password, you will need to create a password by following the instructions below. You can also reset a
forgotten password.

1. If you are logged in, start by [logging out](/help/logging-out).
1. Go to your organization's login page at `https://<organization-url>/login/`.
1. Click the **Forgot your password?** link below the **Log in** button or
buttons.
1. Enter your email address, and click **Send reset link**.
1. You will receive a confirmation email within a few minutes. Open it and click
**Reset password**.
