"Test Channel class"
import pytest

import jwt

from booklink.channel import Channel

class TestChannel:
    "Test the Channel class"

    def test_generate_channel(self):
        "Test instantiation of Channel"
        Channel.make(channel_id='xyz', establisher_name='A', accepter_name='B')

    @pytest.fixture
    def channel(self):
        "Return a Channel instance"
        return Channel.make(channel_id='xyz', establisher_name='A', accepter_name='B')
