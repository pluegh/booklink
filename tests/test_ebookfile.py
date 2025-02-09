import pytest

from BookLink.ebookfile import InMemoryEbookFile

class TestInMemoryEbookFile:
    "Test the EbookFile class"

    @pytest.fixture
    def file(self):
        "Return a EbookFile instance"
        yield InMemoryEbookFile.make(name="test", data=b"test")

    def test_create_file(self, file):
        "Test creating a file"
        assert file.name == "test"
        assert file.data.read() == b"test"
        assert file.created_at_unixutc > 0
        assert file.size_bytes() == 4
