# Channel permissions

<!-- WenShu conversion: MDX includes expanded; UI components rendered as text; related links omitted. See ../README.md. -->

Channels organize conversations based on who needs to see them. For example,
it's common to have a channel for each team in an organization. Because Zulip
further organizes messages into conversations labeled with
[topics](/help/introduction-to-topics), there is generally no need to create
dedicated channels for specific projects.

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

## Configure channel permissions

You can configure the following permissions for each channel,
regardless of its type.

Subscription permissions:

* [Who can administer the channel](/help/configure-who-can-administer-a-channel)
* [Who can subscribe themselves](/help/configure-who-can-subscribe)
* [Who can subscribe anyone](/help/configure-who-can-invite-to-channels#configure-who-can-subscribe-anyone-to-a-specific-channel)
* [Who can unsubscribe anyone](/help/configure-who-can-unsubscribe-others)

Messaging permissions:

* [Who can send messages](/help/channel-posting-policy)
* [Who can start new topics](/help/configure-who-can-start-new-topics)
* [Whether topics are required](/help/require-topics)

Moderation permissions:

* [Who can move messages](/help/restrict-moving-messages)
* [Who can resolve topics](/help/restrict-resolving-topics)
* [Who can delete messages](/help/restrict-message-editing-and-deletion)

For the organization as a whole, you can:

* [Restrict channel creation](/help/configure-who-can-create-channels)
* [Restrict who can subscribe others to channels](/help/configure-who-can-invite-to-channels#configure-who-can-subscribe-others-to-channels-in-general)

Any permission, including whether a channel is private, public, or web-public,
can be modified after the channel is created.

## Private channels

[Private channels](#private-channels) (indicated by ) are for conversations that should be visible to users who
are specifically granted access. There are two types of private channels in
Zulip:

* In private channels with **shared history**, new subscribers can access the
channel's full message history. For example, a newly added team member can get
ramped up on a secret project by seeing prior discussions.
* In private channels with **protected history**, new subscribers can only see
messages sent after they join. For example, a new manager would not be able to
see past discussions regarding their own hiring process or performance management.

Organization administrators and [channel
administrators](/help/configure-who-can-administer-a-channel) can see and manage
metadata for private channels. However, if they aren't subscribed to a private
channel, they cannot gain access to its content, or grant access to others,
unless specifically permitted to do so.

This means organization administrators and [channel
administrators](/help/configure-who-can-administer-a-channel) can:

* See and modify the channel's [name](/help/rename-a-channel) and [description](/help/change-the-channel-description).
* See who is subscribed to the channel, and
[unsubscribe](/help/unsubscribe-users-from-a-channel) them.
* Move the channel to another [folder](/help/channel-folders).
* See the channel's permissions settings, and modify settings that do not affect
content access (e.g., [who can post](/help/channel-posting-policy) or [message
retention policy](/help/message-retention-policy)).
* See how much message traffic the channel gets (but not its contents).
* [Archive](/help/archive-a-channel) the channel.

However, the following actions require specific permissions.

* **Seeing messages and topics**: Restricted to channel subscribers, and user
who are allowed to subscribe themselves or any user.
* Subscribing [yourself](/help/configure-who-can-subscribe) or [other
users](/help/configure-who-can-invite-to-channels)
* Modifying settings that affect content access (e.g., making a channel
public, or changing who can add subscribers).
* Modifying settings that affect notifications (e.g., [enabling mobile
notifications for new subscribers](/help/enable-mobile-notifications-by-default)):
Restricted to organization administrators.

Administrators can [export](/help/export-your-organization) messages in private
channels only if [granted permission to do
so](/help/export-your-organization#configure-whether-administrators-can-export-your-private-data)
by a subscriber.

Users who do not have special permissions (they are not organization
administrators, and have not been granted access to channel metadata) cannot
easily see which private channels exist. They can find out that a channel exists
only by attempting to create a channel with the same name, if they have
[permission to create channels](/help/configure-who-can-create-channels). They
can't get any other information about private channels they are not subscribed
to.

If you create a [bot](/help/bots-overview) that is allowed to read messages
in a private channel (e.g., a **generic bot**, *not* an **incoming webhook bot**,
which is more limited), an administrator can in theory gain access to messages
in the channel by making themselves the bot's owner.

## Public channels

Public channels (indicated by ) are open to all members of your organization other than
[guests](/help/guest-users). Anyone who is not a guest can:

* See information about the channel, including its name, description, permission
settings, and subscribers.
* Subscribe or unsubscribe themselves to the channel.
* See all messages and topics, whether or not they are subscribed.

You can configure other permissions for public channels, such as [who is allowed
to post](/help/channel-posting-policy).

Guest users can't see public (or private) channels, unless they have been specifically
subscribed to the channel.

## Web-public channels

The public access option lets administrators configure selected channels to be
**web-public**. Web-public channels (indicated by a ) can be viewed by anyone on the Internet without creating
an account in your organization.

For example, you can [link to a Zulip
topic](/help/link-to-a-message-or-conversation) in a web-public channel
from a GitHub issue, a social media post, or a forum thread, and
anyone will be able to click the link and view the discussion in the
Zulip web application without needing to create an account.

To see this feature in action, you can [view web-public channels in the Zulip
development community](https://chat.zulip.org/?show_try_zulip_modal) without
logging in.

Users who wish to post content will need to create an account in order
to do so.

Web-public channels are indicated with a **globe** () icon.
