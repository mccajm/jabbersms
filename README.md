# JabberSMS

JabberSMS is an system for sending SMS via XMPP and email to and from a Bulk SMS HTTP API. It supports multiple numbers and multiple SMS providers. I have been using JabberSMS in production for 5 years, but do not provide any guarantees should you choose to do the same.

I wrote JabberSMS because I travel frequently, and need my numbers to work regardless of where I am. I have US and UK VOIP numbers, meaning I can be contacted as long as I have a data connection. JabberSMS adds SMS functionality: inbound SMS are delivered to my email and my phone via XMPP (I use ejabberd as the server, although prosody would work) and an XMPP client. To send outbound SMS, I can reply to inbound messages directly, or send XMPP or email to <phone number>@sms.example.com, where example.com is my domain.

Jabber SMS is written in Asynchronous Python and has been tested in Python 3.8.10 on Ubuntu 22.04 LTS. It has a modular design, and additional interfaces can be easily added via webhooks.

Configuration is via config.ini, which defined interfaces, SMS providers, and routing.

## Modules

### SMS

SMS implements communication with the Bulk SMS HTTP APIs. It handles chunking of messages >160 characters. It exposes two HTTP methods: /sms/send and /sms/receive.

### XMPP

SMS implements communication with an XMPP server. It implements a component which is registered to receive any message directed to sms.example.com. It also implements a sender, which will deliver an SMS message to an XMPP user. It exposes one HTTP method: /xmpp/send for sending SMS to an XMPP user.

### Email

Email implements communcation with an Email server. It exposes one HTTP method: /email/send for sending SMS to an email inbox.
