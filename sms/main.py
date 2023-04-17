import configparser

from itertools import accumulate

import asyncio
import httpx
import asyncstdlib as a

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.routing import Route


config = None
async def parse_config():
    global config
    config = configparser.ConfigParser()
    config.read('../config.ini')


app = Starlette(debug=True, on_startup=[parse_config])
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
    
    if len(number) == 5 and number[0] != 0:
        return f"44{number}"

    if len(number) == 10 and number[0] in digits[2:]:  # US
        return f"1{number}"

    # otherwise, either number is long form already or we trust user
    return number


patternkey = {'X': digits, 'Z': digits[1:], 'N': digits[2:]}
async def number_matches_pattern(number, pattern):
    global patternkey
    pattern = pattern.lstrip('_')
    if pattern.endswith('!'):  # prefix with 0 or more digits afterwards
        if len(number) < len(pattern)-1:
            return False

        number = number[:len(pattern)]
    elif pattern.endswith('.'):  # prefix with 1 or more digits afterwards
        if len(number) < len(pattern):
            return False

        number = number[:len(pattern)]
    elif len(number) != len(pattern):  # exact match
        return False

    for n, p in zip(number, pattern):
        if p in ('N', 'X'):
            if n not in patternkey[p]:  # not constraint matches
                return False
        elif n != p:  # not exact match
            return False

    return True


async def match_provider(number, providers):
    """
    Find the provider with the longest matching pattern
    When a tie break occurs, the first is returned
    """
    longest_match = 0
    longest_match_provider = None
    for provider_name in providers:
        provider = config[f"smsgateway.provider.{provider_name}"]
        patterns = provider['patterns'].split(',')
        for pattern in patterns:
            nmp = await number_matches_pattern(number, pattern)
            if nmp and \
                len(pattern) > longest_match:
                longest_match = len(pattern)
                longest_match_provider = provider

    return longest_match_provider


@app.route('/sms/receive')
async def receive_sms(request):
    global config
    from_number = await prefix_country(request.query_params['oa'].replace('+', ''))
    to_number = await prefix_country(request.query_params['da'].replace('+', ''))
    body = request.query_params['ud']

    webhooks = config['smsgateway']['webhooks'].split(',')
    async with httpx.AsyncClient() as client:
        for url in webhooks:
            message = {"from": from_number,
                       "to": to_number,
                       "body": body}

            r = await client.post(url, json=message)

    return PlainTextResponse('', status_code=201)


@app.route('/sms/send', methods=["POST"])
async def send_sms(request):
    message = await request.json()
    to_number = await prefix_country(message['to'])

    # Determine which provider to use to send this sms
    provider = await match_provider(to_number, config['smsgateway']['providers'].split(','))
    if provider is None:
        return JSONResponse({'error': f"no provider accepts number {to_number}"},
                             status_code=403)

    bodies = [message["body"]]
    if len(message) > 153:
        loop = asyncio.get_event_loop()
        messages = await loop.run_in_executor(None, msgsplitter, message["body"])

    async for i, body in a.enumerate(bodies):
        message['to'] = to_number
        message['apikey'] = provider['apikey']
        message['prefix'] = provider['prefix']

        bodies_len = len(bodies)
        if bodies_len == 1:
            print(f"Sending SMS {message['from']} -> {message['to']} via {provider['description']}")
        else:
            print(f"Sending SMS chunk i/{bodies_len} {message['from']} -> {message['to']} via {provider['description']}")
            message["body"] = body

        async with httpx.AsyncClient() as client:
            msg = provider['url'].format(**message)
            r = await client.get(msg)
            print(msg, r.status_code, r.text)

    return JSONResponse({}, status_code=202)


@app.route('/healthcheck', methods=["GET", "HEAD"])
async def healthcheck(request):
    return PlainTextResponse('', status_code=200)
