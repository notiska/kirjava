#!/usr/bin/env python3

__all__ = (
    "CodeIOWrapper",
)

"""
The JVM bytecode disassembler.
"""

from io import BytesIO
from os import SEEK_SET
from typing import IO


class CodeIOWrapper(BytesIO):  # Extended only for type hinting, BufferedIOBase doesn't seem to work.
    """
    A stream wrapper for code in a method, so that the offset is correct as per the
    base of the code, rather than the base of the class file.

    Attributes
    ----------
    delegate: IO[bytes]
        The underlying stream to read from.
    base: int
        The base offset of the code.
    """

    # __slots__ = ("delegate", "base")  # No slots on BytesIO, unfortunately.

    def __init__(self, delegate: IO[bytes], base: int | None) -> None:
        super().__init__()
        self.delegate = delegate
        self.base = base if base is not None else delegate.tell()  # base or delegate.tell()

    def read(self, size: int | None = ...) -> bytes:
        return self.delegate.read(size)

    def tell(self) -> int:
        return self.delegate.tell() - self.base

    def seek(self, offset: int, whence: int = ...) -> int:
        if whence == SEEK_SET:
            offset += self.base
        return self.delegate.seek(offset, whence)

    def write(self, data: bytes) -> int:
        return self.delegate.write(data)
