# Change the privacy of a channel

<!-- WenShu conversion: MDX includes expanded; UI components rendered as text; related links omitted. See ../README.md. -->

There are three types of channels in Zulip:

* [Private channels](/help/channel-permissions#private-channels)
(indicated by ), where
joining and viewing messages requires being invited. You can choose
whether new subscribers can see messages sent before they were
subscribed.
* [Public channels](/help/channel-permissions#public-channels)
(indicated by ), which
are open to everyone in your organization other than guests.
* [Web-public channels](/help/channel-permissions#web-public-channels)
(indicated by ), where
anyone on the Internet can see messages without creating an account.

Organization administrators and [channel
administrators](/help/configure-who-can-administer-a-channel) can always make a
channel private. However, they can only make a private channel public or
web-public if they have content access to it:

* They are subscribed to the channel, or
* They have the permission to add subscribers
([themselves](/help/configure-who-can-subscribe) or
[others](/help/configure-who-can-invite-to-channels#configure-who-can-subscribe-anyone-to-a-specific-channel))
to the channel.

**Warning**: Be careful making a private channel public. All past messages
will become accessible, even if the channel previously had protected history.

**Platform: Desktop/Web**

1. Click the **gear** icon in the upper right of the app.
1. Select **Channel settings**.
1. Select **All**.

1. Select a channel.

1. Select the **Permissions** tab on the right.

1. Under **Subscription permissions**, configure **Who can access this channel**.

1. Click **Save changes**.

You can also click on a channel name in the navigation bar at the top of the
app to access its settings, or use the **ellipsis** ()
next to the channel name in the left sidebar.

**Platform: Mobile**

Access this feature by following the web app instructions in your
mobile device browser.

Implementation of this feature in the mobile app is tracked [on
GitHub](https://github.com/zulip/zulip-flutter/issues/1102). If
you're interested in this feature, please react to the issue's
description with 👍.
