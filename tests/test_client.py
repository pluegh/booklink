"Test Client class"

from booklink.client import Client


class TestClient:
    "Test the Client class"

    def test_generate_client(self):
        "Test instantiation of Client"
        Client.make(friendly_name="Philip's Macbook Pro")
