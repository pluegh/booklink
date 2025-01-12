"""
Defines resources for sending files.
"""

import abc
from dataclasses import dataclass
import threading

from BookLink.channel import Channel
from BookLink.utils import now_unixutc

@dataclass
class RegisteredFile(abc.ABC):
    "Interface for registered files"
    created_at_unixutc: float

class FileRegister:
    "Manage files available in a channel"

    def __init__(
            self,
            max_files_in_channel: int = 100,
            file_expiration_seconds: int = 300,
        ):
        self.max_files_in_channel = max_files_in_channel
        self.file_expiration_seconds = file_expiration_seconds

        self._files = {}  # channel_id -> list of files
        self.__files_lock = threading.Lock()

    def add_file(self, channel_id: str, file: RegisteredFile):
        "Add a file to the channel"
        with self.__files_lock:
            if channel_id not in self._files:
                self._files[channel_id] = []
            self._files[channel_id].append(file)
        # Also perform pruning when adding a new file
        self.prune_expired_files()

    def prune_expired_files(self):
        "Check all files and remove expired ones"
        for channel_id in self._files:
            self.prune_expired_files_for_channel(channel_id)

    def prune_expired_files_for_channel(self, channel_id):
        "Prune a list of files for a given channel"
        with self.__files_lock:
            if not channel_id in self._files:
                return
            files = self._files[channel_id]
            self._files[channel_id] = [file for file in files if not self.is_expired(file)]

    def is_expired(self, file: RegisteredFile):
        "Check if a file is expired"
        return file.created_at_unixutc + self.file_expiration_seconds < now_unixutc()

    def get_files(self, channel_id: str):
        "Get all files in the channel"
        self.prune_expired_files_for_channel(channel_id)
        with self.__files_lock:
            files = self._files.get(channel_id, [])
        return files
