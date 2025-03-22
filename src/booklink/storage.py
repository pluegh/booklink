"Defines resources for sending files"

import abc
from dataclasses import dataclass
import threading

from booklink.utils import now_unixutc
from booklink.utils import url_friendly_code


class FileRegisterError(Exception):
    "Base class for file register errors"


@dataclass
class RegisteredFile(abc.ABC):
    "Interface for registered files"

    created_at_unixutc: float

    @abc.abstractmethod
    def size_bytes(self) -> int:
        "Return the size of the file in bytes"


class FileRegister:
    """Manage files available in a channel.

    To make polling for files per channel fast, the files are stored in a dictionary instead of a
    flat list. This requires extra house keeping to ensure no empty channel storage is orphaned.
    """

    def __init__(
        self,
        max_files_in_channel: int = 100,
        file_expiration_seconds: int = 300,
        max_total_file_size_bytes: int = 100 * 1024 * 1024,  # 100 MB
        max_random_draws_file_id: int = 10,
    ):
        self.max_files_in_channel = max_files_in_channel
        self.file_expiration_seconds = file_expiration_seconds
        self.max_total_size_bytes = max_total_file_size_bytes
        self.max_random_draws_file_id = max_random_draws_file_id

        self._files_per_channel: dict[str, FilesPerChannel] = {}  # channel_id key
        self.__files_per_channel_lock = threading.Lock()

    def add_file(self, channel_id: str, file: RegisteredFile) -> str:
        "Add a file to the channel (slow method)."

        # Perform pruning when adding a new file
        self.prune_expired_files()

        if self.total_size_bytes() + file.size_bytes() > self.max_total_size_bytes:
            raise FileRegisterError("Total file size exceeds limit")

        with self.__files_per_channel_lock:
            if channel_id not in self._files_per_channel:
                self._files_per_channel[channel_id] = FilesPerChannel()

            if self._files_per_channel[channel_id].number_of_files() >= self.max_files_in_channel:
                raise FileRegisterError("Cannot add file to channel (max files reached)")

            file_id = self._generate_unique_file_id()
            self._files_per_channel[channel_id].add_file(file_id, file)

        return file_id

    def remove_file(self, file_id: str) -> None:
        "Remove a file from the channel"
        with self.__files_per_channel_lock:
            for channel in self._files_per_channel.values():
                if file_id in channel.file_ids():
                    channel.remove_file(file_id)
                    return

        raise FileRegisterError("File ID not found")

    def _generate_unique_file_id(self):
        "Generate a unique file ID"
        for _ in range(self.max_random_draws_file_id):
            file_id = url_friendly_code(n_chars=16)
            if file_id in self._all_file_ids():
                continue
            return file_id
        raise FileRegisterError("Failed to generate a unique file ID")

    def _all_file_ids(self):
        "Get all file IDs in the register"
        all_file_ids = []
        for file_list in self._files_per_channel.values():
            all_file_ids.extend(file_list.file_ids())
        return all_file_ids

    def prune_expired_files(self):
        "Check all files and remove expired ones. Leave no orphaned channels."
        with self.__files_per_channel_lock:
            for channel_id in self._files_per_channel:
                self._prune_expired_files_for_channel(channel_id)
            self._prune_orphan_channels()

    def _prune_orphan_channels(self):
        "Remove channels with no files"
        for channel_id in list(self._files_per_channel.keys()):
            if not self._files_per_channel[channel_id].get_files():
                self._files_per_channel.pop(channel_id)

    def _prune_expired_files_for_channel(self, channel_id):
        "Prune a list of files for a given channel"
        if channel_id not in self._files_per_channel:
            return
        for file_id in list(self._files_per_channel[channel_id].file_ids()):
            if self._is_expired(self._files_per_channel[channel_id].get_file(file_id)):
                self._files_per_channel[channel_id].remove_file(file_id)

    def _is_expired(self, file: RegisteredFile):
        "Check if a file is expired"
        return file.created_at_unixutc + self.file_expiration_seconds < now_unixutc()

    def get_files_for_channel(self, channel_id: str):
        "Get all files in the channel"
        with self.__files_per_channel_lock:
            self._prune_expired_files_for_channel(channel_id)
            files_per_channel = self._files_per_channel.get(channel_id, FilesPerChannel())
            return files_per_channel.get_files()

    def get_file_ids_for_channel(self, channel_id: str):
        "Get all file IDs in the channel"
        with self.__files_per_channel_lock:
            self._prune_expired_files_for_channel(channel_id)
            files_per_channel = self._files_per_channel.get(channel_id, FilesPerChannel())
            return files_per_channel.file_ids()

    def get_file_for_channel(self, channel_id: str, file_id: str):
        "Get a file from the channel"
        with self.__files_per_channel_lock:
            self._prune_expired_files_for_channel(channel_id)
            return self._files_per_channel[channel_id].get_file(file_id)

    def total_size_bytes(self):
        "Get the total size of all files in all channels"
        return sum(fpc.total_size_bytes() for fpc in self._files_per_channel.values())


class FilesPerChannel:
    "List of files per channel with access by file ID"

    def __init__(self) -> None:
        self._files: dict[str, RegisteredFile] = {}  # file_id key

    def number_of_files(self) -> int:
        "Get the number of files in the list"
        return len(self._files)

    def add_file(self, file_id: str, file: RegisteredFile):
        "Add a file to the list"
        if file_id in self._files:
            raise FileRegisterError("File ID already exists")
        self._files.update({file_id: file})

    def remove_file(self, file_id: str):
        "Remove a file from the list"
        if file_id not in self._files:
            raise FileRegisterError("File ID not found")
        self._files.pop(file_id)

    def get_file(self, file_id: str):
        "Get a file from the list"
        if file_id not in self._files:
            raise FileRegisterError("File ID not found")
        return self._files[file_id]

    def get_files(self):
        "Get all files in the list"
        return list(self._files.values())

    def file_ids(self):
        "Get all file IDs in the list"
        return self._files.keys()

    def total_size_bytes(self):
        "Get the total size of all files in the list"
        return sum(file.size_bytes() for file in self.get_files())
