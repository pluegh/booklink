"Test routes of the api backend"

import pytest

from flask import current_app

import BookLink

class TestClientHandling():
    "Test the handling of clients in pairing process"

    @pytest.fixture
    def app(self):
        "Return the flask app"
        app = BookLink.create_app({
            'TESTING': True,
            'JWT_SECRET': 'secret',
            'MAX_CLIENTS_IN_PAIRING': 10,
        })
        yield app

    def test_new_client(self, app):
        "Test new client generation"
        with app.test_client() as client:
            res = client.get('/api/new_client')
            assert res.status_code == 200

            data = res.get_json()['client']
            assert 'pairing_code' in data
            assert 'token' in data
            assert isinstance(data['pairing_code'], str)
            assert isinstance(data['token'], str)

    def test_multiple_new_clients(self, app):
        "Test multiple new client generation"
        with app.test_client() as client:
            for _ in range(10):
                res = client.get('/api/new_client')
                assert res.status_code == 200

        with app.app_context():
            assert len(current_app.pairing_register.all_clients_in_pairing) == 10

    def test_too_many_new_clients(self, app):
        "Test handling of too many new clients"
        with app.test_client() as client:
            for _ in range(10):
                res = client.get('/api/new_client')
                assert res.status_code == 200

            # Get one more
            res = client.get('/api/new_client')
            assert res.status_code == 500


class TestChannelHandling():
    "Test the handling of channels"

    @pytest.fixture
    def app(self):
        "Return the flask app"
        app = BookLink.create_app({
            'TESTING': True,
            'JWT_SECRET': 'secret',
            'MAX_CLIENTS_IN_PAIRING': 10,
        })
        yield app

    def pair_response(self, app):
        "Test pairing of two clients"
        with app.test_client() as client:
            sender = client.get('/api/new_client').get_json()['client']
            ereader = client.get('/api/new_client').get_json()['client']

        with app.test_client() as client:
            res = client.get(f'/api/pair/{ereader['pairing_code']}?token={sender['token']}')
            assert res.status_code == 200
        
        data = res.get_json()
        assert isinstance(data['channel']['channel_id'], str)
        assert isinstance(data['channel']['token'], str)

    def test_channels_for_ereader(self, app):
        "Test retrieval of channels for e-reader"
        
        with app.test_client() as client:
            sender = client.get('/api/new_client').get_json()['client']
            ereader = client.get('/api/new_client').get_json()['client']

        with app.test_client() as client:
            pair_res = client.get(f'/api/pair/{ereader['pairing_code']}?token={sender['token']}')
            assert pair_res.status_code == 200
        pair_data = pair_res.get_json()['channel']
        
        with app.test_client() as client:
            channels_for_ereader_res = client.get(f'/api/channels_for_ereader?token={ereader['token']}')
            assert channels_for_ereader_res.status_code == 200
        channels_for_ereader_data = channels_for_ereader_res.get_json()['channels']

        assert channels_for_ereader_data == [pair_data]

    def test_channels_for_ereader_invalid_token(self, app):
        "Test failure of retrieval of channels for e-reader with invalid token"
    
        ereader_code = 'ereader-code'
        invalid_token = 'not-a-valid-token'
        with app.test_client() as client:
            pair_res = client.get(f'/api/pair/{ereader_code}?token={invalid_token}')
            assert pair_res.status_code == 401
