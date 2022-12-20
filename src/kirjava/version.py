#!/usr/bin/env python3

from typing import Any, Tuple, Union


class Version:
    """
    A Java version.
    """

    __slots__ = ("name", "major", "minor")

    NAMES = {  # A map of major versions to names
        45: "1.1",  # Note: 1.0.2 is also 45, but we'll discount it
        46: "1.2",
        47: "1.3",
        48: "1.4",
        49: "5.0",
        50: "6",
        51: "7",
        52: "8",
        53: "9",
        54: "10",
        55: "11",
        56: "12",
        57: "13",
        58: "14",
        59: "15",
        60: "16",
        61: "17",
        62: "18",
        63: "19",
    }

    @classmethod
    def get(cls, version: Union[Tuple[int, int], str, float]) -> "Version":
        """
        Gets a version from some form of specifier.

        :param version: The specifier.
        :return: The version.
        """

        if isinstance(version, tuple):
            if len(version) != 2:
                raise ValueError("Expected a 2-tuple for specifying major and minor version numbers.")
            return cls(*version)

        elif isinstance(version, str):
            for major, name in cls.NAMES.items():
                if version == name:
                    return cls(major, 0)
            raise ValueError("Unknown Java version %r." % version)

        elif isinstance(version, float):
            return cls._normalise(version)

        raise TypeError("Don't know how to convert %r into a version." % version.__class__)

    @staticmethod
    def _normalise(version: float) -> "Version":
        """
        Normalises a float into a usable version.
        """

        major = int(version)
        minor = version % 1
        while minor % 1:  # Keep increasing until it's no longer a float
            minor *= 10

        return Version(major, int(minor))
    
    @property
    def preview(self) -> bool:
        """
        :return: Is this a preview version?
        """

        return self.major >= 56 and self.minor == 65535

    def __init__(self, major: int, minor: int) -> None:
        self.name = self.NAMES[major]
        self.major = major
        self.minor = minor

    def __repr__(self) -> str:
        return "<Version(name=%r, major=%i) at %x>" % (self.name, self.major, id(self))

    def __eq__(self, other: Any) -> bool:
        if other.__class__ == Version:
            return other.major == self.major and (self.major > 45 or other.minor == self.minor)
        elif isinstance(other, int):
            return other == self.major
        elif isinstance(other, float):
            return self == self._normalise(other)

        return False

    def __hash__(self) -> int:
        return hash((self.major, self.minor))

    def __gt__(self, other: Any) -> bool:
        if other.__class__ == Version:
            return self.major > other.major or (self.major == other.major and self.minor > other.minor)
        elif isinstance(other, int):
            return self.major > other
        elif isinstance(other, float):
            return self > self._normalise(other)

        return False

    def __ge__(self, other: Any) -> bool:
        return self == other or self > other

    def __lt__(self, other: Any) -> bool:
        if other.__class__ == Version:
            return self.major < other.major or (self.major == other.major and self.minor < other.minor)
        elif isinstance(other, int):
            return self.major < other
        elif isinstance(other, float):
            return self < self._normalise(other)

        return False

    def __le__(self, other: Any) -> bool:
        return self == other or self < other
