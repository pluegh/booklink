"""
Defines resources for pairing process.
"""
import threading

from BookLink.channel import Channel
from BookLink.client import Client
from BookLink.utils import (
    now_unixutc,
    human_friendly_pairing_code,
    url_friendly_code,
)

MAX_RANDOM_DRAWS = 10

class TooManyClientsError(RuntimeError):
    "Error for exceeding maximum number of clients in pairing process"

class PairingError(RuntimeError):
    "Error for invalid pairing"

class ClientNotFoundError(RuntimeError):
    "Error for invalid client"

class PairingRegister:
    "Manage clients in pairing process"

    def __init__(
            self,
            client_expiration_seconds: int = 300,
            max_clients_in_pairing: int = 100,
            max_random_draws: int = 10,
        ):
        self.client_expiration_seconds = client_expiration_seconds
        self.max_clients_in_pairing = max_clients_in_pairing
        self.max_random_draws = max_random_draws

        self._clients_in_pairing = {}  # pairing_code -> Client
        self._channels_for = {}  # pairing_code of e-reader -> channel

        self.__clients_lock = threading.Lock()
        self.__channels_lock = threading.Lock()

    def new_client(self, friendly_name=None):
        "Generate a new client in the register"
        code = self._unique_pairing_code()
        client = Client.make(code, friendly_name=friendly_name or '')
        self._clients_in_pairing.update({
            code: client
        })
        # Peform pruning after adding the new client to avoid collisions
        self.prune_expired_clients()
        return client

    def prune_expired_clients(self):
        "Prune expired clients"
        for client in list(self._clients_in_pairing.values()):
            self.expire_client(client)

    def expire_client(self, client: Client):
        "Expire the given client if needed, removing it from the registers"
        is_expired = False
        with self.__clients_lock:
            if now_unixutc() - client.created_at_unixutc > self.client_expiration_seconds:
                self._clients_in_pairing.pop(client.pairing_code)
                is_expired = True
        if is_expired:
            self._channels_for.pop(client.pairing_code, None)
        return is_expired

    def _unique_pairing_code(self):
        "Generate a unique pairing code"
        if len(self._clients_in_pairing) >= self.max_clients_in_pairing:
            raise TooManyClientsError("Exceeding maximum number of clients in pairing process")
        with self.__clients_lock:
            for _ in range(MAX_RANDOM_DRAWS):
                code = human_friendly_pairing_code()
                if code in self._clients_in_pairing:
                    continue
                return code
        raise RuntimeError("Failed to generate a unique pairing code")

    def retrieve_client(self, pairing_code: str):
        "Get the client from the given pairing code"
        with self.__clients_lock:
            client = self._clients_in_pairing.get(pairing_code)
        if client is None:
            raise ClientNotFoundError(f"Client with pairing code {pairing_code} not found")
        return client

    def new_channel(self, pairing_code_sender: str, pairing_code_ereader: str):
        "Pair sender device with e-reader"
        client_sender = self.retrieve_client(pairing_code_sender)
        client_ereader = self.retrieve_client(pairing_code_ereader)

        if client_sender is None or client_ereader is None:
            raise PairingError("Invalid pairing codes")

        channel = Channel.make(
            self._unique_channel_id(),
            client_sender.friendly_name,
            client_ereader.friendly_name
        )
        self.register_channel_for_ereader(pairing_code_ereader, channel)
        return channel

    def register_channel_for_ereader(self, ereader_pairing_code: str, new_channel: Channel):
        "Register a channel for the given e-reader"
        with self.__channels_lock:
            existing_channels = self._channels_for.get(ereader_pairing_code) or []
            self._channels_for[ereader_pairing_code] = existing_channels + [new_channel]

    def _unique_channel_id(self):
        "Generate a unique channel id"
        with self.__channels_lock:
            for _ in range(MAX_RANDOM_DRAWS):
                channel_id =  url_friendly_code()
                if channel_id in self._channels_for:
                    continue
                return channel_id
        raise RuntimeError("Failed to generate a unique channel id")

    def channels_for(self, pairing_code: str):
        "Get the channel for the given pairing code"
        with self.__channels_lock:
            return self._channels_for.get(pairing_code) or []

    @property
    def all_clients_in_pairing(self):
        "Return a copy of the clients in pairing process"
        return self._clients_in_pairing.copy()

    def client_is_in_pairing(self, pairing_code: str):
        "Check if a client is in pairing process"
        try:
            self.retrieve_client(pairing_code)
            return True
        except ClientNotFoundError:
            return False
