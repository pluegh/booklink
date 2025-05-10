"""Utility functions"""

import datetime
import random
import secrets
import string


# Retire this later
def now_unixutc() -> float:
    """Return the current time in unix time for UTC"""
    return datetime.datetime.now(tz=datetime.timezone.utc).timestamp()


class Clock:
    """A clock that returns the current time in unix time for UTC"""

    def now_unixutc(self) -> float:
        """Return the current time in unix time for UTC"""
        return datetime.datetime.now(tz=datetime.timezone.utc).timestamp()


class MockClock:
    """A mock clock that returns a fixed time"""

    def __init__(self):
        """Initialize the mock clock with the current time"""
        self.time = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

    def now_unixutc(self) -> float:
        """Return the interal time"""
        return self.time

    def change_by(self, seconds: float):
        """Change the time by a given number of seconds"""
        self.time += seconds


def human_friendly_pairing_code(n_chars: int = 4) -> str:
    """Generate a human-friendly pairing code"""
    return "".join(random.choices(string.digits + string.ascii_lowercase, k=n_chars))


def url_friendly_code(n_chars: int = 16) -> str:
    """Generate a URL-friendly code"""
    return secrets.token_urlsafe(n_chars)


def file_size_string(byte_size: int) -> str:
    """Return a human-readable file size with byte suffix."""
    floating_size = float(byte_size)
    for unit in ("B", "kB", "MB", "GB"):
        if abs(floating_size) < 1000.0:
            return f"{floating_size:3.1f}{unit}"
        floating_size /= 1000.0
    return f"{floating_size:3.1f}TB"
