"Channel for communication between sender device and e-reader"

import dataclasses

from booklink.utils import now_unixutc


@dataclasses.dataclass
class Channel:
    "Represents a channel for communication between sender device and e-reader"

    channel_id: str
    sender_name: str
    ereader_name: str
    created_at_unixutc: float

    @staticmethod
    def make(channel_id: str, establisher_name: str, accepter_name: str):
        "Generate a channel with the given channel id"
        return Channel(channel_id, establisher_name, accepter_name, now_unixutc())
