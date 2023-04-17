import subprocess

import configparser

from slixmpp import ClientXMPP
from slixmpp.componentxmpp import ComponentXMPP
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from component import XMPPComponent


config = None
async def parse_config():
    global config
    config = configparser.ConfigParser()
    config.read('../config.ini')


xmpp = None
async def connect_xmpp():
    global xmpp
    xmpp = XMPPComponent(config)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0060') # PubSub
    xmpp.register_plugin('xep_0199', {"keepalive": True}) # XMPP Ping
    
    xmpp.connect()


app = Starlette(debug=True, on_startup=[parse_config, connect_xmpp])


def stringify(numbers):
    return list(f"{i}" for i in numbers)


digits = stringify(range(0, 10))
async def prefix_country(number):
    """
    Prefix numbers with country code.
    As we only have UK and US local numbers, we can cheat
    """
    global digits

    if number[0] == 0:  # UK
        return f"44{number[1:]}"

    if len(number) == 10 and number[0] in digits[2:]:  # US
        return f"1{number}"

    # otherwise, either number is long form already or we trust user
    return number


@app.route("/xmpp/send", methods=["POST"])
async def send_message(request):
    global config
    message = await request.json()
    from_number = await prefix_country(message['from'])
    hosted_jid_for_number = dict(((k, v.split(',')[0]) for k, v in config.items('numbers')))

    #xmpp.send_message(hosted_jid_for_number[message['to']], message['body'],
    #                  mfrom=f"{from_number}@{config['smsgateway']['domain']}",
    #                  mnick=from_number)

    dst = hosted_jid_for_number[message['to']]
    src = f"{from_number}@{config['smsgateway']['domain']}"
    print(f"Sending XMPP message from {src} -> {dst}")

    subprocess.run(['sudo', '/usr/sbin/ejabberdctl', 'send_message', 'normal', src, dst, "", message['body']])


    return JSONResponse({}, status_code=201)
