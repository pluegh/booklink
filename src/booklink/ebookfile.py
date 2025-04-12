"Module for ebook files"

import dataclasses
import io
import zipfile
from typing import Optional

from lxml import etree

from booklink.storage import RegisteredFile
from booklink.utils import now_unixutc


@dataclasses.dataclass(frozen=True)
class BookMetadata:
    "Metadata for an ebook file"

    title: str
    author: str
    language: str
    date: str
    identifier: str

    @classmethod
    def empty(cls):
        "Create metadata with empty strings"
        return cls(
            title="",
            author="",
            language="",
            date="",
            identifier="",
        )


@dataclasses.dataclass
class InMemoryEbookFile(RegisteredFile):
    "Class for ebook files"

    name: str
    data: io.BytesIO
    metadata: Optional[BookMetadata] = None

    @classmethod
    def make(cls, name: str, data: io.BytesIO) -> "InMemoryEbookFile":
        "Create an EbookFile instance from bytes"

        valid_extensions = (".epub", ".mobi", ".pdf", ".kepub", ".azw", ".txt")
        for extension in valid_extensions:
            if name.lower().endswith(extension):
                # If the file name ends with a valid extension, skip the else clause
                break
        else:
            raise ValueError(f"File name must end with one of {valid_extensions}, got {name}")

        metadata = MetaDataFactory(name, data).get_metadata()

        return InMemoryEbookFile(
            name=name,
            data=data,
            metadata=metadata,
            created_at_unixutc=now_unixutc(),
        )

    def size_bytes(self) -> int:
        "Return the size of the file in bytes"
        return self.data.getbuffer().nbytes


class MetaDataFactory:
    "Factory for creating ebook files"

    def __init__(self, name: str, data: io.BytesIO):
        self.name = name
        self.data = data

    def get_metadata(self) -> Optional[BookMetadata]:
        "Check if the file is an epub file"
        if self.name.lower().endswith(".epub"):
            try:
                return self.extract_epub_metadata()
            except Exception:  # pylint: disable=broad-except
                return None
        else:
            return None

    def extract_epub_metadata(self) -> BookMetadata:
        "Return the metadata from the file"

        def first_path_match(element, path):
            "Return the first element matching the path"
            return element.xpath(
                path,
                namespaces={
                    "n": "urn:oasis:names:tc:opendocument:xmlns:container",
                    "pkg": "http://www.idpf.org/2007/opf",
                    "dc": "http://purl.org/dc/elements/1.1/",
                },
            )[0]

        try:
            zip_content = zipfile.ZipFile(self.data, mode="r")
            contents_path = first_path_match(
                etree.fromstring(zip_content.read("META-INF/container.xml")),
                "n:rootfiles/n:rootfile/@full-path",
            )
            metadata = first_path_match(
                etree.fromstring(zip_content.read(contents_path)), "/pkg:package/pkg:metadata"
            )
            scraped = {
                s: first_path_match(metadata, f"dc:{s}/text()")
                for s in ("title", "language", "creator", "date", "identifier")
            }
            self.data.seek(0)  # Reset file buffer after read
            return BookMetadata(
                title=scraped["title"],
                author=scraped["creator"],
                language=scraped["language"],
                date=scraped["date"],
                identifier=scraped["identifier"],
            )

        except Exception:
            # Need to reset the data stream for the next read
            self.data.seek(0)
            raise
