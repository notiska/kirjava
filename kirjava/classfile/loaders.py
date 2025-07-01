#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "ListLoader", "DirLoader", "ZipLoader",
)

"""
Basic class file loader implementations.
"""

import os
from os import PathLike
from types import TracebackType
from typing import Iterable
from zipfile import ZipFile

from .fmt import ClassFile, ClassInfo
from .._compat import Self
from ..backend import Result
from ..model import Class, Linker
from ..model.linker import Loader


class ListLoader(Loader):
    """
    Loads classes from a collection of already-parsed class files.

    Attributes
    ----------
    cfs: list[ClassFile]
        The collection of class files.
    """

    __slots__ = ("cfs",)

    def __init__(self, cfs: Iterable[ClassFile] | None = None) -> None:
        self.cfs: list[ClassFile] = []
        if cfs is not None:
            self.cfs.extend(cfs)

    def __repr__(self) -> str:
        return f"<ListLoader(cfs={self.cfs!r})>"

    def find_class(self, linker: Linker, name: str) -> Result[Class[ClassFile]]:
        with Result[Class]() as result:
            for cf in self.cfs:
                if not isinstance(cf.this, ClassInfo):
                    continue
                this = cf.this.lift().value
                if this is not None and this.name == name:
                    return result.ok(cf.lift(linker).unwrap_into(result))
        return result


class DirLoader(Loader):
    """
    Loads classes from a directory containing class files.

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

    def find_class(self, linker: Linker, name: str) -> Result[Class[ClassFile]]:
        with Result[Class]() as result:
            path = (name + ".class").split("/")
            with open(os.path.join(self._path, *path), "rb") as stream:
                cf = ClassFile.read(stream).unwrap_into(result)
            return result.ok(cf.lift(linker).unwrap_into(result))
        return result

    def find_resource(self, name: str) -> Result[bytes]:
        with Result[bytes]() as result:
            path = name.split("/")
            with open(os.path.join(self._path, *path), "rb") as stream:
                return result.ok(stream.read())
        return result


class ZipLoader(Loader):
    """
    Loads classes from a zip file containing class files.

    Attributes
    ----------
    archive: ZipFile
        The underlying `ZipFile` archive.
    """

    __slots__ = ("_archive",)

    @property
    def archive(self) -> ZipFile:
        return self._archive

    def __init__(self, path_or_archive: str | PathLike[str] | ZipFile) -> None:
        if isinstance(path_or_archive, (str, PathLike)):
            path_or_archive = ZipFile(os.fspath(path_or_archive), "r")
        self._archive = path_or_archive

    def __repr__(self) -> str:
        return f"<ZipLoader(archive={self._archive!r})>"

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def find_class(self, linker: "Linker", name: str) -> Result[Class[ClassInfo]]:
        with Result[Class]() as result:
            with self._archive.open(name + ".class", "r") as stream:
                cf = ClassFile.read(stream).unwrap_into(result)
            return result.ok(cf.lift(linker).unwrap_into(result))
        return result

    def find_resource(self, name: str) -> Result[bytes]:
        with Result[bytes]() as result:
            with self._archive.open(name, "r") as stream:
                return result.ok(stream.read())
        return result

    def close(self) -> None:
        """
        Closes the underlying archive.
        """

        self._archive.close()
