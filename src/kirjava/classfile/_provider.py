#!/usr/bin/env python3

__all__ = (
    "DirectoryProvider", "ZipProvider",
)

import os
import zipfile
from os import PathLike

from . import ClassFile
from ..environment import Provider
from ..error import ClassNotFoundError


class DirectoryProvider(Provider):
    """
    Provides classfiles from a directory.
    """

    __slots__ = ("directory",)

    def __init__(self, directory: PathLike | str) -> None:
        self.directory = os.fspath(directory)
        if not os.path.isdir(self.directory):
            raise ValueError("Not a directory: %s" % self.directory)

    def __repr__(self) -> str:
        return "<DirectoryProvider(directory=%r) at %x>" % (self.directory, id(self))

    def provide_class(self, name: str) -> ClassFile:
        path = os.path.join(self.directory, name + ".class")
        if not os.path.isfile(path):
            raise ClassNotFoundError(name)
        try:
            with open(path, "rb") as stream:
                return ClassFile.read(stream)
        except Exception as error:
            raise ClassNotFoundError(name) from error


class ZipProvider(Provider):
    """
    Provides classfiles from a zip file.
    """

    __slots__ = ("zip_file",)

    def __init__(self, zip_file: PathLike | str | zipfile.ZipFile) -> None:
        if not isinstance(zip_file, zipfile.ZipFile):
            zip_file = zipfile.ZipFile(zip_file, "r")
        elif zip_file.mode != "r":
            raise ValueError("%r is not open in read mode." % zip_file)
        self.zip_file = zip_file

    def __repr__(self) -> str:
        return "<ZipProvider(zip_file=%r) at %x>" % (self.zip_file, id(self))

    def provide_class(self, name: str) -> ClassFile:
        path = name + ".class"
        if not path in self.zip_file.namelist():
            raise ClassNotFoundError(name)
        try:
            with self.zip_file.open(path, "r") as stream:
                return ClassFile.read(stream)
        except Exception as error:
            raise ClassNotFoundError(name) from error
