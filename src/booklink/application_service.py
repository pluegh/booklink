"""Combine all components to the application service layer.

This layer presents a boundary and should be self-contained in terms of in- and outgoing
data structures. Client code should import only the service layer.
The service layer interfaces with code that makes the application service available.
"""

import dataclasses
from typing import (
    Any,
    Tuple,
    Dict,
    List,
    Optional,
)

from booklink.pair_devices import PairingRegister
from booklink.client import Client
from booklink.ebookfile import InMemoryEbookFile
from booklink.storage import FileRegister
from booklink.channel import Channel
from booklink.security import Authenticator


@dataclasses.dataclass(frozen=True)
class ApplicationServiceConfig:
    "Configuration for the application service layer"

    client_jwt_secret: str
    channel_jwt_secret: str

    max_clients_in_pairing: int = 100

    max_files_in_channel: int = 20
    total_file_capacity_bytes: int = 1024 * 1024 * 100
    file_expiration: float = 60 * 2

    client_expiration: float = 60 * 60 * 24


class ApplicationService:
    "The application service layer for the BookLink application."

    def __init__(
        self,
        config: ApplicationServiceConfig,
    ):
        """Inits the application service."""
        self.config = config
        self.pairing_register = PairingRegister(
            client_expiration_seconds=config.client_expiration,
            max_clients_in_pairing=config.max_clients_in_pairing,
        )
        self.file_register = FileRegister(
            max_files_in_channel=config.max_files_in_channel,
            file_expiration_seconds=config.file_expiration,
            max_total_file_size_bytes=config.total_file_capacity_bytes,
            max_random_draws_file_id=10,
        )
        self.client_auth = Authenticator(jwt_secret=config.client_jwt_secret, id_factors={"id"})
        self.channel_auth = Authenticator(
            jwt_secret=config.channel_jwt_secret, id_factors={"channel_id", "client_id"}
        )

    def new_client(self, friendly_name: Optional[str] = None) -> Tuple[str, str, str]:
        """Generate a new client for pairing.

        Returns ID, pairing code, and authentification token.
        """
        pairing_code, client = self.pairing_register.new_client(friendly_name)
        token = self.client_auth.token(client.created_at_unixutc, id=client.id)

        return (client.id, pairing_code, token)

    def verify_channel_claim(self, channel_id: str, client_id: str, token: str):
        """Check if the client has access to the channel."""
        self.channel_auth.validate(token=token, channel_id=channel_id, client_id=client_id)

    def verify_client_claim(self, client_id: str, token: str):
        """Check if the client has access."""
        self.client_auth.validate(token=token, id=client_id)

    def pair_with_ereader(
        self,
        client_id: Client,
        token: str,  # pylint: disable=unused-argument
        pairing_code_ereader: str,
    ) -> Channel:
        """Create a channel for the client and the e-reader.

        Returns ID, token for client
        """
        self.verify_client_claim(client_id, token)

        channel = self.pairing_register.new_channel(client_id, pairing_code_ereader.lower())
        token = self.channel_auth.token(
            channel.created_at_unixutc, channel_id=channel.channel_id, client_id=client_id
        )

        return (channel.channel_id, token)

    def channels_for_client(
        self,
        client_id: str,
        token: str,  # pylint: disable=unused-argument
    ) -> List[Dict[str, str]]:
        """Get a list of new channels available for a client"""
        self.verify_client_claim(client_id, token)

        channels = self.pairing_register.channels_for(client_id)

        return [
            {
                "id": c.channel_id,
                "token": self.channel_auth.token(
                    c.created_at_unixutc, channel_id=c.channel_id, client_id=client_id
                ),
            }
            for c in channels
        ]

    def store_file_for_channel(
        self,
        channel_id: str,
        client_id: str,  # pylint: disable=unused-argument
        token: str,  # pylint: disable=unused-argument
        filename: str,
        file_content: Any,
    ) -> str:
        """Store a file for a channel"""
        self.verify_channel_claim(channel_id, client_id, token)

        file_id = self.file_register.add_file(
            channel_id, InMemoryEbookFile.make(name=filename, data=file_content)
        )
        return file_id

    def get_files_for_channel(
        self,
        channel_id: str,
        client_id: str,
        token: str,
    ) -> List[Dict[str, str]]:
        """Get a list of files for a channel"""
        self.verify_channel_claim(channel_id, client_id, token)

        file_ids = self.file_register.get_file_ids_for_channel(channel_id)
        file_descriptions = []
        for file_id in file_ids:
            file = self.file_register.get_file_for_channel(channel_id, file_id)
            size = file.size_bytes()
            expires_at_unixutc = file.created_at_unixutc + self.config.file_expiration
            file_descriptions.append(
                {
                    "name": file.name,
                    "id": file_id,
                    "size": size,
                    "expires_at_unixutc": expires_at_unixutc,
                }
            )

        return file_descriptions

    def get_file(
        self,
        channel_id: str,
        client_id: str,  # pylint: disable=unused-argument
        token: str,  # pylint: disable=unused-argument
        file_id: str,
    ) -> InMemoryEbookFile:
        """Get a file for a channel"""
        self.verify_channel_claim(channel_id, client_id, token)

        return self.file_register.get_file_for_channel(channel_id, file_id)

    def remove_file(
        self,
        channel_id: str,
        client_id: str,
        token: str,
        file_id: str,
    ):
        """Remove a file from a channel"""
        self.verify_channel_claim(channel_id, client_id, token)

        self.file_register.remove_file(file_id)
