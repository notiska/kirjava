#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "dump", "dumps", "load", "loads",
    "disassemble",
)

"""
Nicer Python API functions.
"""

import os
from io import BytesIO
from os import PathLike
from typing import IO

from .fmt import ClassFile, MethodInfo
from .graph import Graph


def dump(cf: ClassFile, file_or_stream: str | PathLike[str] | IO[bytes]) -> None:
    """
    Dumps a class file to a file or binary stream.
    """

    if isinstance(file_or_stream, PathLike):
        file_or_stream = os.fspath(file_or_stream)
    if isinstance(file_or_stream, str):
        with open(file_or_stream, "rb") as stream:
            cf.write(stream)
    else:
        cf.write(file_or_stream)


def dumps(cf: ClassFile) -> bytes:
    """
    Dumps a class file to binary data.
    """

    stream = BytesIO()
    cf.write(stream)
    return stream.getvalue()


def load(file_or_stream: str | PathLike[str] | IO[bytes]) -> ClassFile:
    """
    Loads a class file from a file or binary stream.
    """

    if isinstance(file_or_stream, PathLike):
        file_or_stream = os.fspath(file_or_stream)
    if isinstance(file_or_stream, str):
        with open(file_or_stream, "rb") as stream:
            return ClassFile.read(stream).unwrap()
    return ClassFile.read(file_or_stream).unwrap()


def loads(data: bytes) -> ClassFile:
    """
    Loads a class file from binary data.
    """

    return ClassFile.read(BytesIO(data)).unwrap()


def disassemble(method: MethodInfo, cf: ClassFile | None = None) -> Graph:
    """
    Disassembles the provided method.
    """

    return Graph.disassemble(method, cf).unwrap()
