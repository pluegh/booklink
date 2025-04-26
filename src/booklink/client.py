"""Client for pairing process"""

import dataclasses
from typing import Self

from booklink.utils import (
    now_unixutc,
    url_friendly_code,
)


@dataclasses.dataclass
class Client:
    """Represents a client for clients in pairing process.

    The client id must be uniquely generated without collisions.
    """

    id: str
    created_at_unixutc: float
    friendly_name: str

    @classmethod
    def make(
        cls,
        friendly_name: str,
    ) -> Self:
        """Generate a client with the given pairing code"""
        created_at_unixutc = now_unixutc()
        unique_client_id = f"{url_friendly_code(n_chars=5)}-{created_at_unixutc}"

        return cls(
            id=unique_client_id,
            created_at_unixutc=created_at_unixutc,
            friendly_name=friendly_name,
        )
