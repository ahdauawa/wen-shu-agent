# Configure default settings for new users

<!-- WenShu conversion: MDX includes expanded; UI components rendered as text; related links omitted. See ../README.md. -->

This feature is only available to organization owners and administrators.

You can configure the default values of personal preference settings for new
users joining your organization. This lets you customize the Zulip experience to
match how your organization is using Zulip.

Users will be able to customize their own settings once they join.
If needed, administrators can [reset settings for
users](/help/reset-settings-for-users) to the organization default.

Administrators can customize defaults for all personal preference
settings, including the following:

* Privacy settings:
* Displaying [availability](/help/status-and-availability) to other users
* Allowing others to see when the user has [read
messages](/help/read-receipts)
* Allowing others to see when the user is [typing a
message](/help/typing-notifications)

* Preferences:
* [Language](/help/change-your-language)
* [Time format](/help/change-the-time-format)
* [Light theme vs. dark theme](/help/dark-theme)
* [Font size](/help/font-size)
* [Line spacing](/help/line-spacing)
* [Emoji theme](/help/emoji-and-emoticons#change-your-emoji-set)
* [Home view](/help/configure-home-view)
([**Inbox**](/help/inbox) vs.
[**Recent conversations**](/help/recent-conversations) vs.
[**Combined feed**](/help/reading-strategies#combined-feed))
* Notification settings:
* What types of messages [trigger notifications][default-notifications]
* Which topics users will [automatically follow](/help/follow-a-topic). This
minimizes the need to [mention](/help/mention-a-user-or-group) other users
to get their attention.
* [Desktop](/help/desktop-notifications),
[mobile](/help/mobile-notifications), and
[email](/help/email-notifications) notification settings

[default-notifications]: /help/channel-notifications#configure-default-notifications-for-all-channels

## Configure default settings for new users

Users will have the initial settings that are configured at the time when they
accept the invitation, so there's no need to update or revoke invitations when
you change default settings.

1. Click the gear icon in the upper right of the web or desktop app.
1. Select **Organization settings**.
1. On the left, click **Default user settings**.

1. Review all settings and adjust as needed.

## Configure default language for new users

Your organization's [language](/help/configure-organization-language) will be
the default language for new users when Zulip cannot detect their language
preferences from their browser, including all users [created via the Zulip
API](/api/create-user).

1. Click the gear icon in the upper right of the web or desktop app.
1. Select **Organization settings**.
1. On the left, click **Organization settings**.

1. Under **Automated messages and emails**, change the **Language for
automated messages and invitation emails**.

1. Click **Save changes**.
