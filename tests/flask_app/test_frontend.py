"""Smoke test for the frontend, checking if the templates can be rendered"""

import pytest

import booklink.flask_app


class TestClientHandling:
    """Test the handling of clients in pairing process"""

    @pytest.fixture
    def app(self):
        """Return the flask app"""
        app = booklink.flask_app.create_app()
        yield app

    def test_landing_page(self, app):
        """Test getting the landing page"""
        with app.test_client() as client:
            res = client.get("/")
            assert res.status_code == 200
            assert res.content_type == "text/html; charset=utf-8"
            assert b"Welcome" in res.data

    def test_pair(self, app):
        """Test getting the pairing page"""
        with app.test_client() as client:
            res = client.get("/pair")
            assert res.status_code == 200
            assert res.content_type == "text/html; charset=utf-8"
            assert b"Enter Pairing Code" in res.data

    def test_pair_ereader(self, app):
        """Test getting the pairing page for e-reader"""
        with app.test_client() as client:
            res = client.get("/pair_ereader")
            assert res.status_code == 200
            assert res.content_type == "text/html; charset=utf-8"
            assert b"Enter this code on your other device for pairing" in res.data

    def test_send(self, app):
        """Test send endpoint"""
        with app.test_client() as client:
            # Incorrect credentials make api queries fail, but frontend should render
            channel_id = "test_channel"
            client_id = "test_client"
            token = "test_token"
            res = client.get(f"/send/{channel_id}/{client_id}?token={token}")
            assert res.status_code == 200
            assert res.content_type == "text/html; charset=utf-8"
            assert b"Send to Device" in res.data

    def test_receive(self, app):
        """Test receive endpoint"""
        with app.test_client() as client:
            # Incorrect credentials make api queries fail, but frontend should render
            channel_id = "test_channel"
            client_id = "test_client"
            token = "test_token"
            res = client.get(f"/send/{channel_id}/{client_id}?token={token}")
            assert res.status_code == 200
            assert res.content_type == "text/html; charset=utf-8"
            # No specific text to check for, just that it renders
