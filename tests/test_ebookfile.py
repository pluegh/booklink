import io

import pytest

from booklink.ebookfile import InMemoryEbookFile


class TestInMemoryEbookFile:
    "Test the EbookFile class"

    @pytest.fixture
    def epub(self):
        "Return a EbookFile with a test epub file"
        with open("tests/test_ebooks/frankenstein.epub", "rb") as f:
            data = io.BytesIO(f.read())
        yield InMemoryEbookFile.make(name="frankenstein.epub", data=data)

    def test_read_metadata(self, epub):
        "Test reading metadata from a file"

        assert epub.metadata.title.startswith("Frankenstein")
        assert epub.metadata.author == "Mary Wollstonecraft Shelley"
        assert epub.size_bytes() > 0
