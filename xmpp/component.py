import httpx

from slixmpp.componentxmpp import ComponentXMPP


class XMPPComponent(ComponentXMPP):

    def __init__(self, config):
        ComponentXMPP.__init__(self, config['xmpp']['domain'],
                               config['xmpp']['password'],
                               config['xmpp']['server'],
                               config['xmpp']['port'])
        self.config = config

        self.add_event_handler('message', self.process_message)


    async def process_message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            to_number = str(msg['to']).split('@')[0]
            from_jid = str(msg['from']).split("/")[0]
            body = str(msg['body'])
            number_for_hosted_jid = dict(((v.split(',')[0], k) for k, v in self.config.items('numbers')))

            webhooks = self.config['xmpp']['webhooks'].split(',')
            async with httpx.AsyncClient() as client:
                for url in webhooks:
                    message = {"to": to_number,
                               "from": number_for_hosted_jid[from_jid], 
                               "body": body}

                    print(f"Sending SMS {message['from']} -> {message['to']}")
                    r = await client.post(url, json=message)
