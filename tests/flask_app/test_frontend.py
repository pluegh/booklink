"""Smoke test for the frontend."""

import pytest

import booklink.flask_app


class TestClientHandling:
    "Test the handling of clients in pairing process"

    @pytest.fixture
    def app(self):
        "Return the flask app"
        app = booklink.flask_app.create_app()
        yield app

    def test_landing_page(self, app):
        "Test new client generation"
        with app.test_client() as client:
            res = client.get("/")
            assert res.status_code == 200
            assert res.content_type == "text/html; charset=utf-8"
            assert b"Welcome to BookLink" in res.data
