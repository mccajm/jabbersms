import configparser

import aiosmtplib

from email.mime.text import MIMEText

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, JSONResponse


config = None
async def parse_config():
    global config
    config = configparser.ConfigParser()
    config.read('../config.ini')


app = Starlette(debug=True, on_startup=[parse_config])
@app.route('/email/send', methods=["POST"])
async def send_email(request):
    global config
    message = await request.json()
    email_for_hosted_number = dict(((k, v.split(',')[1]) for k, v in config.items('numbers')))

    if message['to'] not in email_for_hosted_number.keys() and \
        not message['to'].endswith(config['smsgateway']['domain']):
        return JSONResponse({'error': 'Not an open relay. To or From must match a hosted account'},
                             status_code=403)

    msg = MIMEText(message['body'])
    msg['From'] = f"{str(message['from']).replace(' ', '')}@{config['smsgateway']['domain']}"
    msg['To'] = email_for_hosted_number[message['to']]
    msg['Subject'] = f"SMS to {message['to']}"

    print(f"Emailing {msg['From']} -> {msg['To']}: {msg['Subject']}")
    # Contact SMTP server and send Message
    smtp = aiosmtplib.SMTP(hostname=config['email']['host'], port=config['email']['port'],
                           use_tls=config['email']['tls'] == 'yes')
    await smtp.connect()
    await smtp.send_message(msg)
    await smtp.quit()

    return JSONResponse({}, status_code=202)
