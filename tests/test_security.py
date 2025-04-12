"Test security authentication"

import pytest

from booklink.security import (
    AuthenticationError,
    Authenticator,
)


class TestAuthenticator:
    "Test the client authenticator"

    @pytest.fixture
    def id_authenticator(self) -> Authenticator:
        "Simple authenticator for testing with one ID factor"
        return Authenticator(jwt_secret="testing", id_factors={"id"})

    def test_encode_decode_sequence(self, id_authenticator):
        """Given client_id and creation time
        When token is created and decoded
        Then client_id and creation time are preserved
        """
        token = id_authenticator.token(0, id="Bob")
        assert token

        decoded = id_authenticator.decode(token)
        assert decoded["id"] == "Bob"
        assert decoded["timestamp_unixutc"] == 0

    def test_acccess_granted_when_token_valid(self, id_authenticator):
        """Given client_id and creation time
        When validating the token and ID claim
        Then no exception is raised
        """
        token = id_authenticator.token(0, id="Bob")
        id_authenticator.validate(token, id="Bob")

    def test_access_denied_when_client_id_mismatches(self, id_authenticator):
        """Given client_id and creation time
        When trying to validate a valid token with a wrong ID claim
        Then an exception is raised
        """
        token = id_authenticator.token(0, id="Bob")
        with pytest.raises(AuthenticationError):
            id_authenticator.validate(token, id="Alice")

    def test_access_denied_when_token_invalid(self, id_authenticator):
        """Given client_id and creation time
        When trying to validate an invalid token
        Then an exception is raised
        """
        with pytest.raises(AuthenticationError):
            id_authenticator.validate("invalid-token", id="Bob")

    @pytest.fixture
    def multi_id_authenticator(self) -> Authenticator:
        "Authenticator for testing with multiple ID factors"
        return Authenticator(jwt_secret="testing", id_factors={"id", "role"})

    def test_encode_decode_sequence_multi_id(self, multi_id_authenticator):
        """Given client_id, role, and creation time
        When token is created and decoded
        Then client_id, role, and creation time are preserved"
        """
        token = multi_id_authenticator.token(0, id="Bob", role="admin")
        assert token

        decoded = multi_id_authenticator.decode(token)
        assert decoded["id"] == "Bob"
        assert decoded["role"] == "admin"
        assert decoded["timestamp_unixutc"] == 0

    def test_access_granted_when_token_valid_multi_id(self, multi_id_authenticator):
        """Given client_id, role, and creation time
        When validating the token
        Then no exception is raised
        """
        token = multi_id_authenticator.token(0, id="Bob", role="admin")
        multi_id_authenticator.validate(token, id="Bob", role="admin")
