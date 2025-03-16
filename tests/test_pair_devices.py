import pytest


from booklink.pair_devices import (
    Client,
    ClientNotFoundError,
    PairingRegister,
)


class TestPairingRegister:
    "Test the PairingClientRegister class"

    @pytest.fixture
    def register(self):
        "Return a PairingClientRegister instance"
        return PairingRegister()

    def test_new_client(self, register):
        "Test client registration"
        pairing_code, client = register.new_client()

        assert pairing_code is not None
        assert client is not None

    def test_get_client_by_pairing_code(self, register):
        "Test client retrieval from code"
        pairing_code, _ = register.new_client()

        res = register.get_client_by_pairing_code(pairing_code)
        assert res is not None
        assert isinstance(res, Client)

    def test_get_client_by_pairing_code_invalid(self, register):
        "Test client retrieval from invalid code"
        pairing_code, _ = register.new_client()

        with pytest.raises(ClientNotFoundError):
            register.get_client_by_pairing_code(pairing_code + "invalid")

    def test_client_expiration(self, register):
        "Test client expiration"
        for _ in range(3):
            register.new_client()
        assert len(register.all_clients_in_pairing) == 3

        register.client_expiration_seconds = 0
        register.new_client()  # prunes expired clients
        assert len(register.all_clients_in_pairing) == 0

    def test_new_channel(self, register):
        "Test new channel"
        for _ in range(2):
            register.new_client()
        code_a, code_b = register.all_clients_in_pairing.keys()
        id_a, id_b = [client.id for client in register.all_clients_in_pairing.values()]
        # Pair A, C and B, C
        channel = register.new_channel(id_a, code_b)

        assert channel is not None

    def test_channels_for(self, register):
        "Test getting channels after creation"
        for _ in range(3):
            register.new_client()
        code_a, code_b, code_c = register.all_clients_in_pairing.keys()
        id_a, id_b, id_c = [client.id for client in register.all_clients_in_pairing.values()]
        # Pair A, C and B, C
        channel_a = register.new_channel(id_a, code_c)
        channel_b = register.new_channel(id_b, code_c)

        res = register.channels_for(id_c)
        assert len(res) == 2
        assert res == [channel_a, channel_b]

    def test_channels_for_invalid(self, register):
        "Test getting channels invalid code"
        res = register.channels_for("invalid-code")
        assert res == []

    def test_channels_for_expired_client(self, register):
        "Ensure that expired clients are removed from channels"
        register.client_expiration_seconds = 300
        for _ in range(3):
            register.new_client()
        code_a, code_b, code_c = register.all_clients_in_pairing.keys()
        id_a, id_b, id_c = [client.id for client in register.all_clients_in_pairing.values()]
        # Pair A, C and B, C
        channel_a = register.new_channel(id_a, code_c)
        channel_b = register.new_channel(id_b, code_c)

        # No expired clients
        res = register.channels_for(id_c)
        assert len(res) == 2
        assert res == [channel_a, channel_b]

        # Expire all clients
        register.client_expiration_seconds = 0
        register.prune_data()

        res = register.channels_for(id_c)
        assert len(res) == 0

    def test_client_is_in_pairing(self, register):
        "Test client is in pairing"
        pairing_code, _ = register.new_client()

        assert register.client_is_in_pairing(pairing_code)
        assert not register.client_is_in_pairing(pairing_code + "invalid")
