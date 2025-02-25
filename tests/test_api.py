"Test routes of the api backend"

import pytest

from flask import current_app
import io
from werkzeug.datastructures import FileStorage

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

    def test_pair_response(self, app):
        "Test pairing of two clients"
        with app.test_client() as client:
            sender = client.get('/api/new_client').get_json()['client']
            ereader = client.get('/api/new_client').get_json()['client']

        with app.test_client() as client:
            res = client.get(f'/api/pair/{ereader["pairing_code"]}?token={sender["token"]}')
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
            pair_res = client.get(f'/api/pair/{ereader["pairing_code"]}?token={sender["token"]}')
            assert pair_res.status_code == 200
        pair_data = pair_res.get_json()['channel']
        
        with app.test_client() as client:
            channels_for_ereader_res = client.get(f'/api/channels_for_ereader?token={ereader["token"]}')
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

    def test_upload_file(self, app):
        "Test uploading a file"

        # Create users for pairing
        with app.test_client() as client:
            sender = client.get('/api/new_client').get_json()['client']
            ereader = client.get('/api/new_client').get_json()['client']

        # Create channel
        with app.test_client() as client:
            pair_res = client.get(f'/api/pair/{ereader["pairing_code"]}?token={sender["token"]}')
            assert pair_res.status_code == 200
        pair_response = pair_res.get_json()['channel']
        channel_id = pair_response['channel_id']
        channel_token = pair_response['token']

        with app.test_client() as client:
            upload_res = client.post(f'/api/upload?token={channel_token}',
            data={
                'file': (io.BytesIO(b'test_file_content'), 'test_file_name')
            },)
            assert upload_res.get_json() == {'message': 'File uploaded successfully'}

        files = app.file_register.get_files_for_channel(channel_id)
        assert len(files) == 1
        assert files[0].name == 'test_file_name'

    def test_get_files(self, app):
        "Test getting files for channel"

        # Create users for pairing
        with app.test_client() as client:
            sender = client.get('/api/new_client').get_json()['client']
            ereader = client.get('/api/new_client').get_json()['client']

        # Create channel
        with app.test_client() as client:
            pair_res = client.get(f'/api/pair/{ereader["pairing_code"]}?token={sender["token"]}')
            assert pair_res.status_code == 200
        pair_response = pair_res.get_json()['channel']
        channel_id = pair_response['channel_id']
        channel_token = pair_response['token']

        # Upload file
        with app.test_client() as client:
            upload_res = client.post(f'/api/upload?token={channel_token}',
            data={
                'file': (io.BytesIO(b'test_file_content'), 'test_file_name')
            },)
            assert upload_res.get_json() == {'message': 'File uploaded successfully'}

        # Get files
        with app.test_client() as client:
            get_files_res = client.get(f'/api/files?token={channel_token}')
            assert get_files_res.status_code == 200
            resp = get_files_res.get_json()
            assert len(resp['files']) == 1
            assert resp['files'][0]['name'] == 'test_file_name'
            assert resp['files'][0]['size'] == '17.0B'
            assert resp['files'][0]['id'] is not None
