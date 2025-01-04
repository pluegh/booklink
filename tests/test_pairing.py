import pytest
import datetime

import jwt

from BookLink.pairing import (
    Channel,
    Client,
    ClientError,
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

    def test_client_from_code(self, register):
        "Test client retrieval from code"
        client = register.new_client()

        res = register.client_from_code(client.pairing_code)    
        assert res is not None
        assert isinstance(res, Client)

    def test_client_from_code_invalid(self, register):
        "Test client retrieval from invalid code"
        client = register.new_client()

        with pytest.raises(ClientError):
            register.client_from_code(client.pairing_code + 'invalid')

    def test_register_channel_for_ereader(self, register):
        "Test channel registration for e-reader"
        client = register.new_client()
        channel = Channel.make('channel-id', 'sender name', 'ereader name')

        register.register_channel_for_ereader(client.pairing_code, channel)

        res = register.channels_for(client.pairing_code)
        assert res == [channel]

    def test_pair(self, register):
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
