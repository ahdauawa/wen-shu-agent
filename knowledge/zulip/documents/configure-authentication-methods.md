# Configure authentication methods

<!-- WenShu conversion: MDX includes expanded; UI components rendered as text; related links omitted. See ../README.md. -->

This feature is only available to organization owners.

You can choose which authentication methods to enable for users to log in to
your organization. The following options are available on all
[plans](https://zulip.com/plans/):

* Email and password
* Social authentication: Google, GitHub, GitLab, Apple, Discord

The following options are available for organizations on Zulip Cloud Standard,
Zulip Cloud Plus, and all self-hosted Zulip servers:

* Oauth2 with Microsoft Entra ID (AzureAD)

The following options are available for organizations on Zulip Cloud Plus, and all self-hosted Zulip servers:

* [SAML authentication](/help/saml-authentication), including Okta, OneLogin, Entra ID (AzureAD), Keycloak, Auth0
* [OpenID
Connect](https://zulip.readthedocs.io/en/stable/production/authentication-methods.html#openid-connect)
* [SCIM provisioning](/help/scim)

The following authentication and identity management options are available for
all self-hosted servers. If you are interested in one of these options for a
Zulip Cloud organization, contact [support@zulip.com](mailto:support@zulip.com)
to inquire.

* [AD/LDAP user
sync](https://zulip.readthedocs.io/en/stable/production/authentication-methods.html#ldap-including-active-directory)
* [AD/LDAP group
sync](https://zulip.readthedocs.io/en/stable/production/authentication-methods.html#ldap-including-active-directory)
* [Custom authentication
options](https://python-social-auth.readthedocs.io/en/latest/backends/index.html#social-backends)
with python-social-auth

### Configure authentication methods

For self-hosted organizations, some authentication options require
that you first [configure your
server](https://zulip.readthedocs.io/en/stable/production/authentication-methods.html)
to support the option.

Before disabling an authentication method, test that you can
successfully log in with one of the remaining authentication methods.
The [`change_auth_backends` management
command](https://zulip.readthedocs.io/en/stable/production/management-commands.html)
can help if you accidentally lock out all administrators.

1. Click the gear icon in the upper right of the web or desktop app.
1. Select **Organization settings**.
1. On the left, click **Authentication methods**.

1. To use SAML authentication or SCIM provisioning, Zulip Cloud organizations
must upgrade to [Zulip Cloud Plus](https://zulip.com/plans/), and contact
[support@zulip.com](mailto:support@zulip.com) to enable these methods.
1. Toggle the checkboxes next to the available login options.

1. Click **Save changes**.
