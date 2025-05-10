import pytest

from booklink.show_online import ClientsOnline
from booklink.utils import MockClock


class TestClientsOnline:
    """Test the ClientsOnline class"""

    TIMEOUT = 5

    @pytest.fixture
    def clock(self):
        """Return a MockClock instance for testing"""
        return MockClock()

    @pytest.fixture
    def clients_online(self, clock):
        """Return an Onlineclients instance for testing"""
        return ClientsOnline(clock=clock, timeout=self.TIMEOUT)

    def test_refresh_client(self, clients_online: ClientsOnline):
        """Test adding a client"""
        client_id = "client_0"
        clients_online.refresh_last_seen(client_id, channel_id="channel_0")
        assert clients_online.all() == {client_id}

    def test_removal_after_timeout(self, clients_online: ClientsOnline, clock: MockClock):
        """Test that a client is removed after timeout"""
        client_id = "client_0"
        clients_online.refresh_last_seen(client_id, channel_id="channel_0")
        clock.change_by(self.TIMEOUT + 1)

        assert clients_online.all() == set()

    def test_impl_with_ordererd_dict(self, clients_online: ClientsOnline, clock: MockClock):
        """Test that the list of online clients is complete and in the right order."""
        for i in range(10):
            client_id = f"client_{i}"
            clients_online.refresh_last_seen(client_id, channel_id="channel_0")

        clock.change_by(self.TIMEOUT - 1)
        clients_online.refresh_last_seen("client_0", channel_id="channel_0")  # Moved to the end?

        # pylint: disable=protected-access
        assert list(clients_online._last_seen) == [f"client_{i}" for i in range(1, 10)] + [
            "client_0"
        ]

        clock.change_by(2)
        clients_online.purge()
        assert list(clients_online._last_seen) == ["client_0"]

    def test_impl_automatic_purge(self, clients_online: ClientsOnline, clock: MockClock):
        """Test that a client list is purged after timeout"""
        for i in range(10):
            client_id = f"client_{i}"
            clients_online.refresh_last_seen(client_id, channel_id="channel_0")
            clock.change_by(0)

        clock.change_by(self.TIMEOUT + 1)
        assert clients_online.all() == set()

        # Assert that implementation leaves no orphan data
        # pylint: disable=protected-access
        assert clients_online._last_seen == {}
        assert clients_online._clients_per_channel == {}
        assert clients_online._channel == {}

    def test_all_for_channel(self, clients_online: ClientsOnline):
        """Test that the clients per channel are correct"""
        for i in range(10):
            client_id = f"client_{i}"
            clients_online.refresh_last_seen(client_id, channel_id=f"channel_{i % 2}")

        assert clients_online.all_for_channel("channel_0") == {
            f"client_{i}" for i in range(0, 10, 2)
        }
