"""Provides authentification for the service layer."""

from typing import Set

import jwt


class AuthenticationError(Exception):
    """Error raised when authentication fails"""


class Authenticator:
    """Handles client authentication for the service layer."""

    def __init__(self, jwt_secret: str, id_factors: Set[str]):
        """Inits the authenticator

        Parameters:
            jwt_secret: The secret for the JWT
            id_factors: The names of factors that make up the ID
        """
        self.jwt_secret = jwt_secret
        self.id_factors = id_factors

    def decode(self, token):
        """Decode token and return payload"""
        return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

    def token(self, timestamp_unixutc, **id_factors):
        """Create token from a payload"""
        if not self.id_factors.issubset(id_factors.keys()):
            raise ValueError("ID factors missing")
        payload = {
            "timestamp_unixutc": timestamp_unixutc,
        }
        payload.update(id_factors)

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def validate(self, token, **id_claim):
        """Raise exception if the claimed ID cannot be verified."""
        try:
            payload = self.decode(token)
        except jwt.DecodeError as exc:
            raise AuthenticationError("Invalid token") from exc

        if not id_claim == {key: payload[key] for key in self.id_factors}:
            raise AuthenticationError("Token does not match ID factors")
