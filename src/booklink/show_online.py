"""This module adds the functionality to show if a channel's client is online."""

from collections import OrderedDict
from threading import Lock
from typing import (
    Dict,
    Set,
)

from booklink.utils import Clock


class ClientsOnline:
    """This class manages the online clients.

    We assume that unique client IDs are used.
    """

    def __init__(
        self,
        clock: Clock = Clock(),
        timeout: float = 5,
    ):
        # We track clients last seen using an ordered dict.
        # The order allows more efficient purging of old clients.
        self._last_seen: OrderedDict[str, float] = (
            OrderedDict()
        )  # client_id -> timestamp when last seen
        # Tracking the clients per channel is done using private methods
        # that modify the followin dict of sets.
        self._clients_per_channel: Dict[str, Set[str]] = {}  # channel_id -> client_ids
        self._channel: Dict[str, str] = {}  # client_id -> channel_id

        self.lock = Lock()
        self._clock = clock
        self.timeout = timeout

    def refresh_last_seen(self, client_id: str, channel_id: str) -> None:
        """Update the last seen timestamp for a client."""
        self.purge()  # Remove old clients

        with self.lock:
            # If the client is already in the list, move them to the end
            if client_id in self._last_seen:
                self._last_seen.move_to_end(client_id)

            self._last_seen[client_id] = self._clock.now_unixutc()
            self._update_clients_of_channel(client_id, channel_id)
            self._channel[client_id] = channel_id

    def all(self) -> Set[str]:
        """Return a list of online clients."""
        self.purge()
        with self.lock:
            return set(self._last_seen.keys())

    def all_for_channel(self, channel_id: str) -> set[str]:
        """Return a list of online clients for a channel."""
        self.purge()
        with self.lock:
            return self._clients_per_channel.get(channel_id, set()).copy()

    def purge(self) -> None:
        """Remove clients who have not been seen for a while."""
        current_time = self._clock.now_unixutc()

        # Items are ordered by last seen time, so we remove the oldest ones first
        # and stop when we find a recent one.
        with self.lock:
            old_clients = []
            for client_id, last_seen in self._last_seen.items():
                if current_time - last_seen > self.timeout:
                    old_clients.append(client_id)
                    continue
                break

            for client_id in old_clients:
                self._last_seen.pop(client_id)
                self._remove_client_from_channel(client_id, self._channel[client_id])
                self._channel.pop(client_id)

    def _update_clients_of_channel(self, client_id: str, channel_id: str) -> None:
        """Add a client to a channel."""
        if channel_id not in self._clients_per_channel:
            self._clients_per_channel[channel_id] = {client_id}
            return

        self._clients_per_channel[channel_id].add(client_id)

    def _remove_client_from_channel(self, client_id: str, channel_id: str) -> None:
        """Remove a client from a channel."""
        if channel_id not in self._clients_per_channel:
            raise ValueError(f"Channel {channel_id} does not exist.")

        clients = self._clients_per_channel[channel_id]
        if client_id not in clients:
            raise ValueError(f"Client {client_id} is not in channel {channel_id}.")

        clients.remove(client_id)
        if len(clients) == 0:
            # Remove channel if no clients are left
            self._clients_per_channel.pop(channel_id)
