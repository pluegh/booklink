import pytest

from dataclasses import dataclass

from booklink.storage import (
    RegisteredFile,
    FileRegister,
)
from booklink.utils import now_unixutc

DUMMY_FILE_SIZE_BYTES = 10


@dataclass
class DummyFile(RegisteredFile):
    "Dummy file class for testing"

    file_id: str

    def size_bytes(self) -> int:
        "Return the size of the file in bytes"
        return DUMMY_FILE_SIZE_BYTES


class TestFileRegister:
    "Test the FileRegister class"

    @pytest.fixture
    def register(self):
        "Return a FileRegister instance"
        yield FileRegister()

    def test_add_file(self, register):
        "Test adding a file"

        files = [DummyFile(file_id=f"id={i}", created_at_unixutc=now_unixutc()) for i in range(5)]
        for file in files:
            register.add_file("channel", file)

        res = register.get_files_for_channel("channel")
        assert res == files
        assert len(res) == len(files)

    def test_prune_expired_files(self, register):
        "Test pruning expired files"
        files = [DummyFile(file_id=f"id={i}", created_at_unixutc=0) for i in range(5)]
        for file in files:
            register.add_file("channel", file)

        # Set expiration to 0 to force pruning
        register.file_expiration_seconds = 0

        register.prune_expired_files()

        res = register.get_files_for_channel("channel")
        assert len(res) == 0
        assert res == []

        # Test that also channel did not become orphan (no content)
        assert "channel" not in register._files_per_channel

    def test_get_files_expired(self, register):
        "Expired files should not be returned"
        register.file_expiration_seconds = 100
        files_expired = [
            DummyFile(file_id=f"id={i}", created_at_unixutc=now_unixutc() - 100) for i in range(5)
        ]
        files_valid = [
            DummyFile(file_id=f"id={i}", created_at_unixutc=now_unixutc() + 100) for i in range(3)
        ]
        for file in files_expired + files_valid:
            register.add_file("channel", file)

        res = register.get_files_for_channel("channel")
        assert res == files_valid

    def test_total_size_bytes(self, register):
        "Test total size of files"
        n_files = 5
        files = [
            DummyFile(file_id=f"id={i}", created_at_unixutc=now_unixutc()) for i in range(n_files)
        ]
        for file in files:
            register.add_file("channel", file)

        res = register.total_size_bytes()
        assert res == n_files * DUMMY_FILE_SIZE_BYTES
