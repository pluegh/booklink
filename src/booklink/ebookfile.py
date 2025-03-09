"Class for ebook files"

import io
from dataclasses import dataclass

from booklink.transfer_files import RegisteredFile
from booklink.utils import now_unixutc


@dataclass
class InMemoryEbookFile(RegisteredFile):
    "Class for ebook files"

    name: str
    data: io.BytesIO

    @staticmethod
    def make(name: str, data: bytes):
        "Create an EbookFile instance from bytes"
        return InMemoryEbookFile(
            name=name,
            data=io.BytesIO(data),
            created_at_unixutc=now_unixutc(),
        )

    def size_bytes(self) -> int:
        "Return the size of the file in bytes"
        return self.data.getbuffer().nbytes
