import pytest

from dataclasses import dataclass

from BookLink.fileregister import (
    RegisteredFile,
    FileRegister,
)
from BookLink.utils import now_unixutc

@dataclass
class DummyFile(RegisteredFile):
    "Dummy file class for testing"
    file_id: str


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

        res = register.get_files("channel")
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

        res = register.get_files("channel")
        assert len(res) == 0
        assert res == []

    def test_get_files_expired(self, register):
        "Expired files should not be returned"
        register.file_expiration_seconds = 100
        files_expired = [DummyFile(file_id=f"id={i}",
                                   created_at_unixutc=now_unixutc() - 100) for i in range(5)]
        files_valid   = [DummyFile(file_id=f"id={i}",
                                   created_at_unixutc=now_unixutc() + 100) for i in range(3)]
        for file in files_expired + files_valid:
            register.add_file("channel", file)

        res = register.get_files("channel")
        assert res == files_valid
