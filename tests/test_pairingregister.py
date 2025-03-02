import pytest
import datetime

import jwt

from booklink.pairingregister import (
    Channel,
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

    def test_client_register(self, register):
        "Test client registration"
        client = register.new_client()

        assert register.client_is_in_pairing(client.pairing_code)
        assert isinstance(client, Client)

    def test_retrieve_client(self, register):
        "Test client retrieval from code"
        client = register.new_client()

        res = register.retrieve_client(client.pairing_code)
        assert res is not None
        assert isinstance(res, Client)

    def test_retrieve_client_invalid(self, register):
        "Test client retrieval from invalid code"
        client = register.new_client()

        with pytest.raises(ClientNotFoundError):
            register.retrieve_client(client.pairing_code + 'invalid')

    def test_client_expiration(self, register):
        "Test client expiration"
        for _ in range(3):
            register.new_client()
        assert len(register.all_clients_in_pairing) == 3

        register.client_expiration_seconds = 0
        register.new_client()  # prunes expired clients
        assert len(register.all_clients_in_pairing) == 0

    def test_new_channel(self, register):
        "Test client pairing"
        for _ in range(3):
            register.new_client()
        code_a, code_b, code_c = register.all_clients_in_pairing.keys()
        # Pair A, C and B, C
        channel_a = register.new_channel(code_a, code_c)
        channel_b = register.new_channel(code_b, code_c)

        res = register.channels_for(code_c)
        assert len(res) == 2
        assert res == [channel_a, channel_b]

    def test_channels_for_invalid(self, register):
        "Test getting channels invalid code"
        res = register.channels_for('invalid-code')
        assert res == []

    def test_channels_for_expired_client(self, register):
        "Ensure that expired clients are removed from channels"
        register.client_expiration_seconds = 300
        for _ in range(3):
            register.new_client()
        code_a, code_b, code_c = register.all_clients_in_pairing.keys()
        # Pair A, C and B, C
        channel_a = register.new_channel(code_a, code_c)
        channel_b = register.new_channel(code_b, code_c)

        # No expired clients
        res = register.channels_for(code_c)
        assert len(res) == 2
        assert res == [channel_a, channel_b]

        # Expire all clients
        register.client_expiration_seconds = 0
        register.prune_expired_clients()

        res = register.channels_for(code_c)
        assert len(res) == 0

    def test_client_is_in_pairing(self, register):
        "Test client is in pairing"
        client = register.new_client()

        assert register.client_is_in_pairing(client.pairing_code)
        assert not register.client_is_in_pairing(client.pairing_code + 'invalid')
