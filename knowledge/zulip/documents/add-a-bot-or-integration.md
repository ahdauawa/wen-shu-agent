# Add a bot or integration

<!-- WenShu conversion: MDX includes expanded; UI components rendered as text; related links omitted. See ../README.md. -->

By default, anyone other than guests can add a bot to a Zulip organization.
A bot that sends content to or from another product is often called an
[integration](/help/integrations-overview).

Organization administrators can also
[restrict bot creation](/help/restrict-bot-creation). Any bot that is added
is visible and available for anyone to use.

## Add a bot or integration

**Platform: Your bots**

1. Click the gear icon in the upper right of the web or desktop app.
1. Select **Personal settings**.
1. On the left, click **Bots**.

1. Click **Add a new bot**.
1. Fill out the fields, and click **Add**.

**Platform: All bots**

1. Click the gear icon in the upper right of the web or desktop app.
1. Select **Organization settings**.
1. On the left, click **Bots**.

1. Click **Add a new bot**.
1. Fill out the fields, and click **Add**.

See [bots overview](/help/bots-overview) for more information about
the various fields.
Nearly all third-party integrations should use **Incoming webhook**
as the **bot type**.

Depending on the type of bot you're creating, you may need to download its
[`zuliprc` configuration file](/help/manage-a-bot#download-zuliprc-configuration-file).
