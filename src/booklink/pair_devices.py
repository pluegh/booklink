"""Defines resources for pairing process"""

import threading
from typing import Optional

from booklink.channel import Channel
from booklink.client import Client
from booklink.utils import (
    human_friendly_pairing_code,
    now_unixutc,
    url_friendly_code,
)

MAX_RANDOM_DRAWS = 10


class TooManyClientsError(RuntimeError):
    """Error for exceeding maximum number of clients in pairing process"""


class PairingError(RuntimeError):
    """Error for invalid pairing"""


class ClientNotFoundError(RuntimeError):
    """Error for invalid client"""


class PairingRegister:
    """Manage clients in pairing process"""

    def __init__(
        self,
        client_expiration_seconds: int = 300,
        max_clients_in_pairing: int = 100,
        max_random_draws: int = 10,
    ):
        self.client_expiration_seconds = client_expiration_seconds
        self.max_clients_in_pairing = max_clients_in_pairing
        self.max_random_draws = max_random_draws

        self._clients_in_pairing: dict[str, Client] = {}  # Access by pairing code
        self._channels_for: dict[str, list[Channel]] = {}  # Access by client id

        self.__clients_lock = threading.Lock()
        self.__channels_lock = threading.Lock()

    def new_client(self, friendly_name: Optional[str] = None) -> tuple[str, Client]:
        """Generate a new client in the register"""
        pairing_code = self._unique_pairing_code()
        client = Client.make(friendly_name=friendly_name or f"device-{pairing_code}")
        self._clients_in_pairing.update({pairing_code: client})
        self.prune_data()  # After adding the new client to avoid collisions
        return pairing_code, client

    def prune_data(self):
        """Prune expired clients"""
        with self.__clients_lock:
            for pairing_code, client in self._clients_in_pairing.copy().items():
                if now_unixutc() - client.created_at_unixutc > self.client_expiration_seconds:
                    expired_client = self._clients_in_pairing.pop(pairing_code)
                    with self.__channels_lock:
                        self._channels_for.pop(expired_client.id, None)

    def _unique_pairing_code(self):
        """Generate a unique pairing code"""
        if len(self._clients_in_pairing) >= self.max_clients_in_pairing:
            raise TooManyClientsError("Exceeding maximum number of clients in pairing process")
        with self.__clients_lock:
            for _ in range(MAX_RANDOM_DRAWS):
                code = human_friendly_pairing_code()
                if code in self._clients_in_pairing:
                    continue
                return code
        raise RuntimeError("Failed to generate a unique pairing code")

    def get_client_by_pairing_code(self, pairing_code: str):
        """Get the client from the given pairing code"""
        with self.__clients_lock:
            client = self._clients_in_pairing.get(pairing_code)
        if client is None:
            raise ClientNotFoundError(f"Client with pairing code {pairing_code} not found")
        return client

    def new_channel(self, requester_client_id: str, pairing_code_ereader: str):
        """Pair sender device with e-reader"""
        client_sender = self.get_client_by_id(requester_client_id)
        client_ereader = self.get_client_by_pairing_code(pairing_code_ereader)

        channel = Channel.make(
            self._unique_channel_id(), client_sender.friendly_name, client_ereader.friendly_name
        )
        self.register_channel_for_ereader(client_ereader.id, channel)
        return channel

    def get_client_by_id(self, client_id: str):
        """Get the client from the given id"""
        with self.__clients_lock:
            for client in self._clients_in_pairing.values():
                if client.id == client_id:
                    return client
        raise ClientNotFoundError(f"Client with id {client_id} not found")

    def register_channel_for_ereader(self, ereader_pairing_code: str, new_channel: Channel):
        """Register a channel for the given e-reader"""
        with self.__channels_lock:
            existing_channels = self._channels_for.get(ereader_pairing_code) or []
            self._channels_for[ereader_pairing_code] = existing_channels + [new_channel]

    def _unique_channel_id(self):
        """Generate a unique channel id"""
        with self.__channels_lock:
            for _ in range(MAX_RANDOM_DRAWS):
                channel_id = url_friendly_code()
                if channel_id in self._channels_for:
                    continue
                return channel_id
        raise RuntimeError("Failed to generate a unique channel id")

    def channels_for(self, client_id: str):
        """Get the channel for the given pairing code"""
        with self.__channels_lock:
            return self._channels_for.get(client_id, [])

    @property
    def all_clients_in_pairing(self):
        """Return a copy of the clients in pairing process"""
        return self._clients_in_pairing.copy()

    def client_is_in_pairing(self, pairing_code: str):
        """Check if a client is in pairing process"""
        try:
            self.get_client_by_pairing_code(pairing_code)
            return True
        except ClientNotFoundError:
            return False
