"""
Test routes of the api backend
"""

import io
from dataclasses import dataclass
from typing import Generator

import flask
import pytest

import booklink.flask_app


class TestConfig(booklink.flask_app.BaseConfig):
    "FlaskConfig for testing"

    SECRET_KEY = "test_secret"
    MAX_CLIENTS_IN_PAIRING = 10


class TestClientHandling:
    "Test the handling of clients in pairing process"

    @pytest.fixture
    def app(self) -> Generator[flask.Flask, None, None]:
        "Return the flask app"
        app = booklink.flask_app.create_app(TestConfig=TestConfig)
        yield app

    def test_new_client(self, app: flask.Flask):
        "Test new client generation"
        with app.test_client() as client:
            res = client.get("/api/new_client")
            assert res.status_code == 200

            data = res.get_json()
            assert "pairing_code" in data
            assert "token" in data
            assert isinstance(data["pairing_code"], str)
            assert isinstance(data["token"], str)

    def test_multiple_new_clients(self, app: flask.Flask):
        "Test multiple new client generation"
        with app.test_client() as client:
            for _ in range(10):
                res = client.get("/api/new_client")
                assert res.status_code == 200

    def test_too_many_new_clients(self, app: flask.Flask):
        "Test handling of too many new clients"
        with app.test_client() as client:
            for _ in range(10):
                res = client.get("/api/new_client")
                assert res.status_code == 200

            # Get one more
            res = client.get("/api/new_client")
            assert res.status_code == 500


class TestChannelHandling:
    "Test the handling of channels"

    @dataclass(frozen=True)
    class AppWithPairedUsersFixture:
        "Fixture for app with paired users"

        app: booklink.flask_app.Flask
        client_id_a: str
        client_token_a: str
        client_id_b: str
        client_token_b: str
        channel_id: str
        channel_token_a: str
        channel_token_b: str

    @pytest.fixture
    def app_with_paired_users(self) -> Generator[AppWithPairedUsersFixture, None, None]:
        "Return app with paired users and associated data"
        app = booklink.flask_app.create_app(TestConfig=TestConfig)

        with app.test_client() as client:
            user_a = client.get("/api/new_client").get_json()
            user_b = client.get("/api/new_client").get_json()

        with app.test_client() as client:
            res = client.get(
                f"/api/pair/{user_a['client_id']}/{user_b['pairing_code']}?token={user_a['token']}"
            )
            assert res.status_code == 200
            channel_res_a = res.get_json()

        with app.test_client() as client:
            res = client.get(f"/api/channels_for/{user_b['client_id']}?token={user_b['token']}")
            channel_res_b = res.get_json()[0]

        channel_id = channel_res_a["channel_id"]

        return self.AppWithPairedUsersFixture(
            app,
            user_a["client_id"],
            user_a["token"],
            user_b["client_id"],
            user_b["token"],
            channel_id,
            channel_res_a["token"],
            channel_res_b["token"],
        )

    def test_pair_response(self, app_with_paired_users: AppWithPairedUsersFixture):
        "Test pairing of two clients"
        fixture = app_with_paired_users  # pylint: disable=unused-variable

        assert isinstance(fixture.channel_id, str)
        assert isinstance(fixture.channel_token_a, str)
        assert isinstance(fixture.channel_token_b, str)

    def test_channels_for_ereader(self, app_with_paired_users: AppWithPairedUsersFixture):
        "Test retrieval of channels for e-reader"
        fixture = app_with_paired_users  # pylint: disable=unused-variable

        with fixture.app.test_client() as client:
            res = client.get(
                f"/api/channels_for/{fixture.client_id_b}?token={fixture.client_token_b}"
            )
            assert res.status_code == 200

        channels_for_ereader_data = res.get_json()

        assert len(channels_for_ereader_data) == 1

    def test_upload_file(self, app_with_paired_users: AppWithPairedUsersFixture):
        "Test uploading a file"
        fixture = app_with_paired_users  # pylint: disable=unused-variable

        with fixture.app.test_client() as client:
            upload_res = client.post(
                f"/api/upload/{fixture.channel_id}/{fixture.client_id_a}"
                f"?token={fixture.channel_token_a}",
                data={"file": (io.BytesIO(b"test_file_content"), "test.epub")},
            )
            assert upload_res.get_json() == {"message": "File uploaded successfully"}

    def test_get_files(self, app_with_paired_users: AppWithPairedUsersFixture):
        "Test getting files for channel"
        fixture = app_with_paired_users

        # Upload file
        with fixture.app.test_client() as client:
            upload_res = client.post(
                f"/api/upload/{fixture.channel_id}"
                f"/{fixture.client_id_a}?token={fixture.channel_token_a}",
                data={"file": (io.BytesIO(b"test_file_content"), "test.epub")},
            )
            assert upload_res.get_json() == {"message": "File uploaded successfully"}

        # Get list of files
        with fixture.app.test_client() as client:
            get_files_res = client.get(
                f"/api/files/{fixture.channel_id}/"
                f"{fixture.client_id_b}?token={fixture.channel_token_b}"
            )
            assert get_files_res.status_code == 200
            data = get_files_res.get_json()
            assert len(data) == 1
            assert data[0]["name"] == "test.epub"
            assert data[0]["size"] == 17
            assert data[0]["id"] is not None
