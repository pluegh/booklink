import io
from typing import Generator

import pytest

from booklink.application_service import (
    ApplicationService,
    ApplicationServiceConfig,
    ChannelResponse,
    ClientResponse,
)


class TestApplicationService:
    "Test the ApplicationService class"

    @pytest.fixture
    def app_config(self) -> Generator[ApplicationServiceConfig, None, None]:
        "Return an ApplicationServiceConfig for testing"
        yield ApplicationServiceConfig(
            client_jwt_secret="test_secret",
            channel_jwt_secret="test_secret",
            max_clients_in_pairing=10,
            max_files_in_channel=10,
            client_expiration=60 * 60 * 24,  # 1 day
        )

    @pytest.fixture
    def app(self, app_config: ApplicationServiceConfig) -> ApplicationService:
        "Return the ApplicationService"
        return ApplicationService(app_config)

    def test_initialize(self, app: ApplicationService):
        "Test initialization of the ApplicationService"
        assert app is not None

    def test_request_new_client_with_name(self, app: ApplicationService):
        """When a new client is created,
        then the pairing code and client is returned.
        """
        new_client = app.new_client("Bob")
        assert isinstance(new_client, ClientResponse)
        assert isinstance(new_client.id, str)
        assert isinstance(new_client.pairing_code, str)
        assert isinstance(new_client.token, str)

    def test_pair_device_with_ereader(self, app: ApplicationService):
        """Given two users,
        when the users are paired,
        then a channel is created.
        """
        client_a = app.new_client("Alice")
        _ = app.new_client("Bob")

        new_channel = app.new_channel_using_code(
            client_a.id,
            client_a.token,
            client_a.pairing_code,
        )

        assert isinstance(new_channel, ChannelResponse)
        assert isinstance(new_channel.id, str)
        assert isinstance(new_channel.token, str)

    def test_channels_for_client(self, app: ApplicationService):
        """Given an app
        When two clients are paired
        Then the channel can be retrieved
        """
        client_a = app.new_client("Alice")
        client_b = app.new_client("Bob")
        channel_from_a = app.new_channel_using_code(
            client_a.id, client_a.token, client_b.pairing_code
        )

        channels_for_b = app.channels_for_client(client_b.id, client_b.token)
        assert len(channels_for_b) == 1

        # Check channel id match since tokens are different per client
        assert [c.id for c in channels_for_b] == [channel_from_a.id]

    def test_store_file_for_channel(self, app: ApplicationService):
        """Test storing a file for a channel"""
        client_a = app.new_client("Alice")
        client_b = app.new_client("Bob")

        channel = app.new_channel_using_code(client_a.id, client_a.token, client_b.pairing_code)

        app.store_file_for_channel(
            channel.id, client_a.id, channel.token, "test.epub", io.BytesIO(b"test_file_content")
        )

    def test_get_files_for_channel(self, app: ApplicationService):
        """Test retrieving files for a channel"""
        client_a = app.new_client("Alice")
        client_b = app.new_client("Bob")

        channel_from_a = app.new_channel_using_code(
            client_a.id, client_a.token, client_b.pairing_code
        )  # pylint: disable=unused-variable
        channel_for_b = app.channels_for_client(client_b.id, client_b.token)[0]

        for i in range(3):
            app.store_file_for_channel(
                channel_from_a.id,
                client_a.id,
                channel_from_a.token,
                f"test_{i}.epub",
                io.BytesIO(b"test_file_content"),
            )

        files = app.get_files_for_channel(channel_for_b.id, client_b.id, channel_for_b.token)
        assert len(files) == 3

    def test_get_file(self, app: ApplicationService):
        """Test retrieving a file"""
        client_a = app.new_client("Alice")
        client_b = app.new_client("Bob")

        channel_from_a = app.new_channel_using_code(
            client_a.id, client_a.token, client_b.pairing_code
        )
        channel_for_b = app.channels_for_client(client_b.id, client_b.token)[0]

        file_id = app.store_file_for_channel(
            channel_from_a.id,
            client_a.id,
            channel_from_a.token,
            filename="test.epub",
            file_content=io.BytesIO(b"test_file_content"),
        )

        file = app.get_file(channel_for_b.id, client_b.id, channel_for_b.token, file_id)
        assert file.name == "test.epub"
        assert file.data.read() == b"test_file_content"
