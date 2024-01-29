#!/usr/bin/env python3

__all__ = (
    "JarFile",
    "CentralDirectoryFileHeader", "EndOfCentralDirectoryRecord", "LocalFileHeader",
)

"""
Proper Jar file parsing.
Sources:
 - https://en.wikipedia.org/wiki/ZIP_(file_format)
"""

import logging
from typing import IO, Optional

from .abc import ZipPart
from .cdfh import CentralDirectoryFileHeader
from .eocd import EndOfCentralDirectoryRecord
from .lfh import LocalFileHeader

logger = logging.getLogger("kirjava.jarfile")


class JarFile:
    """
    A Jar file.
    """

    @classmethod
    def read(self, buffer: IO[bytes]) -> "JarFile":
        ...

    @property
    def comment(self) -> bytes:
        """
        :return: This Jar file's zip comment.
        """

        if self._ecod is None:
            return b""
        return self._eocd.comment

    @comment.setter
    def comment(self, value: bytes) -> None:
        """
        Updates this Jar file's zip comment.

        :param value: The new comment.
        """

        if self._eocd is None:
            ...  # TODO: New EOCD

        self._eocd.comment = value
        self._ecod.comment_size = len(value)

    def __init__(self, zip64: bool = False, parts: Optional[list[ZipPart]] = None) -> None:
        """
        :param zip64: Is this a ZIP64 archive?
        :param parts: The zip parts present in this file.
        """

        self.zip64 = zip64

        self._parts: list[ZipPart] = []
        self._ecod: Optional[EndOfCentralDirectoryRecord] = None  # The EOCD that we're currently using

        if parts is not None:
            for part in parts:
                self._parts.append(part)
                if isinstance(part, EndOfCentralDirectoryRecord):
                    self._eocd = part  # Select the last EOCD record in the parts

    def __repr__(self) -> str:
        return "<JarFile(zip64=%s, parts=%i) at %x>" % (self.zip64, len(self._parts), id(self))
