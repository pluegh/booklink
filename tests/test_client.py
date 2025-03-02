"Test Client class"
import pytest

import jwt

from booklink.client import Client

class TestClient:
    "Test the Client class"

    def test_generate_client(self):
        "Test instantiation of Client"
        Client.make(pairing_code='xyz')
