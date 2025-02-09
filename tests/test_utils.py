import pytest
import datetime

import urllib.parse

from BookLink.utils import (
    now_unixutc,
    human_friendly_pairing_code,
    url_friendly_code,
    file_size_string,
)

def test_now_unixutc():
    "Test now_unixutc function"
    timestamp = now_unixutc()

    assert isinstance(timestamp, float)

    dt = datetime.datetime.fromtimestamp(
        timestamp, tz=datetime.timezone.utc)
    assert isinstance(dt, datetime.datetime)
    assert dt.tzinfo == datetime.timezone.utc

def test_human_friendly_pairing_code():
    "Test human_friendly_pairing_code function"
    code = human_friendly_pairing_code()

    assert isinstance(code, str)
    assert len(code) == 4
    assert code.isalnum()

def test_url_friendly_code():
    "Test url_friendly_code function"
    code = url_friendly_code()

    assert isinstance(code, str)
    assert code == urllib.parse.quote(code)

def test_file_size_string():
    "Test file_size_string function"
    assert file_size_string(0) == "0.0B"
    assert file_size_string(1000) == "1.0kB"
    assert file_size_string(1e6) == "1.0MB"
    assert file_size_string(1e9) == "1.0GB"
    assert file_size_string(1e12) == "1.0TB"
    assert file_size_string(1e15) == "1000.0TB"  # Stop at TB
    assert file_size_string(-1e6) == "-1.0MB"  # Handle negative numbers
