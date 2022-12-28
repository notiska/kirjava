#!/usr/bin/env python3

"""
The end of central directory structure.
"""

import struct
from typing import IO

from .abc import ZipPart


class EndOfCentralDirectoryRecord(ZipPart):
    """
    The zip EOCD record structure.
    """

    __slots__ = (
        "disk_number",
        "central_directory_start_disk",
        "central_directory_start_offset",
        "central_directory_records_count",
        "central_directory_size",
        "central_directory_offset",
        "comment_size",
        "comment",
    )

    HEADER = b"PK\x05\x06"

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "EndOfCentralDirectoryRecord":
        eocd_record = cls()

        (
            eocd_record.disk_number,
            eocd_record.central_directory_start_disk,
            eocd_record.central_driectory_start_offset,
            eocd_record.central_directory_record_count,
            eocd_record.central_directory_size,
            eocd_record.central_directory_offset,
            eocd_record.comment_size,
        ) = struct.unpack("<HHHHIIH", buffer.read(18))

        eocd_record.comment = buffer.read(eocd_record.comment_size)

        return eocd_record

    def write(self, buffer: IO[bytes]) -> None:
        struct.pack(
            "<HHHHIIH", 
            (
                self.disk_number,
                self.central_directory_start_disk,
                self.central_driectory_start_offset,
                self.central_directory_record_count,
                self.central_directory_size,
                self.central_directory_offset,
                self.comment_size,
            ),
        )
        buffer.write(self.comment)
