import pytest

from booklink.application_service import (
    ApplicationService,
    ApplicationServiceConfig,
)


class TestApplicationService:
    "Test the ApplicationService class"

    @pytest.fixture
    def app_config(self):
        "Return an ApplicationServiceConfig for testing"
        yield ApplicationServiceConfig(
            client_jwt_secret="test_secret",
            channel_jwt_secret="test_secret",
            max_clients_in_pairing=10,
            max_files_in_channel=10,
            client_expiration=60 * 60 * 24,  # 1 day
        )

    @pytest.fixture
    def app(self, app_config) -> ApplicationService:
        "Return the ApplicationService"
        return ApplicationService(app_config)

    def test_initialize(self, app):
        "Test initialization of the ApplicationService"
        assert app is not None

    def test_request_new_client_with_name(self, app):
        """When a new client is created,
        then the pairing code and client is returned.
        """
        client_id, code, token = app.new_client("Bob")  # pylint: disable=unused-variable
        assert isinstance(client_id, str)
        assert isinstance(code, str)
        assert isinstance(code, str)

    def test_pair_device_with_ereader(self, app):
        """Given two users,
        when the users are paired,
        then a channel is created.
        """
        client_id_a, code_a, token_a = app.new_client("Alice")  # pylint: disable=unused-variable
        client_id_b, code_b, token_b = app.new_client("Bob")  # pylint: disable=unused-variable

        channel_id, token = app.pair_with_ereader(
            client_id_a,
            token_a,
            code_b,
        )

        assert isinstance(channel_id, str)
        assert isinstance(token, str)

    def test_channels_for_client(self, app):
        """Given an app
        When two clients are paired
        Then the channel can be retrieved
        """
        client_id_a, code_a, token_a = app.new_client("Alice")  # pylint: disable=unused-variable
        client_id_b, code_b, token_b = app.new_client("Bob")  # pylint: disable=unused-variable

        channel_id, _ = app.pair_with_ereader(client_id_a, token_a, code_b)  # pylint: disable=unused-variable

        assert [c["id"] for c in app.channels_for_client(client_id_b, token_b)] == [channel_id]

    def test_store_file_for_channel(self, app):
        """Test storing a file for a channel"""
        client_id_a, code_a, token_a = app.new_client("Alice")  # pylint: disable=unused-variable
        client_id_b, code_b, token_b = app.new_client("Bob")  # pylint: disable=unused-variable

        channel_id, channel_token_a = app.pair_with_ereader(client_id_a, token_a, code_b)  # pylint: disable=unused-variable

        app.store_file_for_channel(
            channel_id, client_id_a, channel_token_a, "test_file_name", b"test_file_content"
        )

    def test_get_files_for_channel(self, app):
        """Test retrieving files for a channel"""
        client_id_a, code_a, token_a = app.new_client("Alice")  # pylint: disable=unused-variable
        client_id_b, code_b, token_b = app.new_client("Bob")  # pylint: disable=unused-variable

        channel_id, channel_token_a = app.pair_with_ereader(client_id_a, token_a, code_b)  # pylint: disable=unused-variable
        channel_token_b = app.channels_for_client(client_id_b, token_b)[0]["token"]

        for i in range(3):
            app.store_file_for_channel(
                channel_id,
                client_id_a,
                channel_token_a,
                f"test_file_name_{i}",
                b"test_file_content",
            )

        files = app.get_files_for_channel(channel_id, client_id_b, channel_token_b)
        assert len(files) == 3

    def test_get_file(self, app):
        """Test retrieving a file"""
        client_id_a, code_a, token_a = app.new_client("Alice")
        client_id_b, code_b, token_b = app.new_client("Bob")

        channel_id, channel_token_a = app.pair_with_ereader(client_id_a, token_a, code_b)
        channel_token_b = app.channels_for_client(client_id_b, token_b)[0]["token"]

        file_id = app.store_file_for_channel(
            channel_id, client_id_a, channel_token_a, "test_file_name", b"test_file_content"
        )

        file = app.get_file(channel_id, client_id_b, channel_token_b, file_id)
        assert file.name == "test_file_name"
        assert file.data.read() == b"test_file_content"
