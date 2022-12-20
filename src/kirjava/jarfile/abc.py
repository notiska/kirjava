#!/usr/bin/env python3

"""
Abstract base classes.
"""

from abc import abstractmethod, ABC
from typing import IO


class ZipPart(ABC):
    """
    Part of a zip file.
    """

    @classmethod
    @abstractmethod
    def read(cls, buffer: IO[bytes]) -> "ZipPart":
        """
        Reads this zip part from the given binary buffer.

        :param buffer: The buffer to read from.
        :return: The zip part that was read.
        """

        ...

    @abstractmethod
    def write(self, buffer: IO[bytes]) -> None:
        """
        Writes this zip part fo the given binary buffer.

        :param buffer: The buffer to write to.
        """

        ...
