"Utility functions for BookLink"

import datetime
import random
import secrets
import string

def now_unixutc():
    "Return the current time in unix time for UTC"
    return datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

def human_friendly_pairing_code(n_chars=4):
    "Generate a human-friendly pairing code"
    return ''.join(random.choices(string.digits + string.ascii_lowercase, k=n_chars))

def url_friendly_code(n_chars=16):
    "Generate a URL-friendly code"
    return secrets.token_urlsafe(n_chars)
