#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "DirLoader", "ZipLoader",
)

"""
Basic class file loader implementations.
"""

import os
import typing
from os import PathLike

from .fmt import ClassFile
from ..backend import Result
from ..model.linker import Linker, Loader

if typing.TYPE_CHECKING:
    from ..model import Class


class DirLoader(Loader):
    """
    Loads classes from a directory containing classfiles.

    Attributes
    ----------
    path: str
        The path to the directory.
    """

    __slots__ = ("_path",)

    @property
    def path(self) -> str:
        return self._path

    def __init__(self, path: str | PathLike[str]) -> None:
        if isinstance(path, PathLike):
            path = os.fspath(path)
        self._path = path

    def __repr__(self) -> str:
        return f"<DirLoader(path={self._path!r})>"

    def find_class(self, name: str, linker: Linker) -> Result["Class"]:
        with Result["Class"]() as result:
            path = (name + ".class").split("/")
            with open(os.path.join(self._path, *path), "rb") as stream:
                cf = ClassFile.read(stream).unwrap_into(result, reraise=True)
            return result.ok(cf.link(linker).unwrap_into(result, reraise=True))
        return result

    def find_resource(self, name: str) -> Result[bytes]:
        with Result[bytes]() as result:
            path = name.split("/")
            with open(os.path.join(self._path, *path), "rb") as stream:
                return result.ok(stream.read())
        return result


class ZipLoader(Loader):
    ...
