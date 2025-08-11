#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "JImage",
)

"""
The JImage/JRT container file format.
"""

import os
from os import PathLike
from types import TracebackType
from typing import IO

from ._struct import *
from ..._compat import Self
from ...backend import Result


class JImage:
    """
    A JImage image file.

    Attributes
    ----------
    closed: bool
        Whether the image file is closed.
    file: str | None
        The path to the open file, or `None` if the image was opened directly via a
        stream.
    mode: str
        The file open mode for the image.
        Valid values are: "r" for reading, "w" for writing, "r+" for reading and
        writing.
    major: int
        The image file major version.
    minor: int
        The image file minor version.
    flags: int
        The image file flags.

    Methods
    -------
    open(self) -> Result[Self]
        Opens the image file.
    close(self) -> None
        Closes the image file.
    """

    __slots__ = (
        "file", "mode",
        "_stream", "_open",
        "major", "minor", "flags",
    )

    _MODES = {"r": "rb", "w": "wb", "r+": "r+b"}

    @property
    def closed(self) -> bool:
        return not self._open

    def __init__(self, file_or_stream: str | PathLike[str] | IO[bytes], mode: str = "r") -> None:
        self.file: str | None

        real_mode = JImage._MODES.get(mode)
        if real_mode is None:
            raise ValueError(f"invalid file mode {mode!r}")
        self.mode = mode

        if isinstance(file_or_stream, PathLike):
            file_or_stream = os.fspath(file_or_stream)

        if isinstance(file_or_stream, str):
            self.file = file_or_stream
            self._stream = None
        else:
            self.file = None
            self._stream = file_or_stream
            if self._stream.mode != real_mode:
                raise ValueError(f"provided stream has wrong mode {self._stream.mode!r}, expected {real_mode!r}")

        self._open = False

        self.major = 1  # Expected defaults. I believe there is only one version, currently.
        self.minor = 0
        self.flags = 0

    def __repr__(self) -> str:
        return f"<JImage(file={self.file!r}, mode={self.mode!r}, major={self.major}, minor={self.minor})>"

    def __enter__(self) -> Self:
        return self.open().unwrap()

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        self.close()

    def open(self) -> Result[Self]:
        """
        Opens the image file.
        """

        with Result[Self].meta(__name__, self) as result:
            if self._open:
                return result.err(ValueError(f"image {self!r} is already open"))

            if self._stream is None:
                assert self.file is not None, "no file"  # Shouldn't happen if internal state is maintained correctly.
                self._stream = open(self.file, JImage._MODES[self.mode])
            elif self._stream.closed:
                return result.err(ValueError(f"image {self!r} underlying stream is closed"))

            if not self._stream.seekable():
                return result.err(ValueError(f"image {self!r} underlying stream is not seekable"))

            magic = self._stream.read(4)
            if magic != b"\xda\xda\xfe\xca":
                result.err(ValueError(f"invalid jimage magic {magic!r}"))

            self.minor, self.major = unpack_HH(self._stream.read(4))
            self.flags, resources_count, table_size, locs_size, strings_size = unpack_IIIII(self._stream.read(20))
            print(self.flags, resources_count, table_size, locs_size, strings_size)

            self._open = True
            return result.ok(self)
        return result

    def close(self) -> None:
        """
        Closes the image file.
        """

        self._open = False
        if self._stream is not None:
            self._stream.close()
