"""
Provides the API backend.
"""
import dataclasses
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
    request
)
import jwt

from BookLink.pairing import PairingRegister, TooManyClientsError
from BookLink.client import Client
from BookLink.channel import Channel
from BookLink.utils import now_unixutc

bp = Blueprint('api', __name__, url_prefix='/api')

def init_app(app):
    "Define registration of the blueprint with the app"
    current_app.pairing_register = PairingRegister(
        client_expiration_seconds=app.config['CLIENT_EXPIRATION_SECONDS'],
        max_clients_in_pairing=app.config['MAX_CLIENTS_IN_PAIRING'],
    )

def auth_client(f):
    "Authenticate client token for the route and store the client in g"
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return 'No token provided', 400
        try:
            payload = decode(token)
        except jwt.DecodeError:
            return 'Invalid token', 401

        client = Client(**payload)

        client_age_seconds = now_unixutc() - client.created_at_unixutc
        if client_age_seconds > current_app.config['CLIENT_EXPIRATION_SECONDS']:
            return 'Client token expired', 401

        g.authenticated_client = client
        return f(client, *args, **kwargs)
    return decorator

@bp.route('/new_client')
def new_client():
    "Generate a new client for pairing"
    name = request.args.get('friendly_name') or ''
    current_app.logger.debug('New client request (from %s)', name or 'unknown')
    try:
        client = current_app.pairing_register.new_client(friendly_name=name)
    except TooManyClientsError:
        current_app.logger.error('Deny new client due to too many clients')
        return 'Too many clients in pairing process', 500
    return jsonify({'client': add_token(client)})

@bp.route('/pair/<pairing_code_ereader>')
@auth_client
def pair_with_ereader(client, pairing_code_ereader):
    "Pair two clients"
    pairing_code_sender = client.pairing_code
    channel = current_app.pairing_register.new_channel(
        pairing_code_sender.lower(), pairing_code_ereader.lower()
    )
    return jsonify({'channel': add_token(channel)})

def add_token(data: dataclasses.dataclass):
    "Add token to data"
    data = dataclasses.asdict(data)
    data['token'] = encode(data)
    return data

def encode(payload):
    "Create token from a payload"
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')

def decode(token):
    "Decode token and return payload"
    return jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])

#
#   Channels
#

@bp.route('/channels_for_ereader')
@auth_client
def channels_for_ereader(client):
    "Return the results of pairings for a client"
    pairing_code = client.pairing_code
    channels = current_app.pairing_register.channels_for(pairing_code)
    # return channel_list_to_json(channels)
    return jsonify({'channels': [add_token(c) for c in channels]})

def auth_channel(f):
    "Authenticate client token for the route and store the client in g"
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return 'No token provided', 400
        payload = decode(token)
        channel = Channel(**payload)
        g.authenticated_channel = channel
        return f(channel, *args, **kwargs)
    return decorator
