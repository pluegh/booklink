"Client for pairing process"

import dataclasses

from .utils import now_unixutc

@dataclasses.dataclass
class Client:
    "Represents a client for clients in pairing process."
    pairing_code: str
    friendly_name: str
    created_at_unixutc: float

    @classmethod
    def make(cls, pairing_code: str, friendly_name: str = None):
        "Generate a client with the given pairing code"
        return Client(pairing_code, friendly_name, now_unixutc())
