#!/usr/bin/env python3

__all__ = (
    "JAVA_1_0", "JAVA_1_0_1", "JAVA_1_0_2",
    "JAVA_1_1", "JAVA_1_2", "JAVA_1_3",
    "JAVA_1_4", "JAVA_5", "JAVA_6",
    "JAVA_7", "JAVA_8", "JAVA_9",
    "JAVA_10", "JAVA_11", "JAVA_12",
    "JAVA_13", "JAVA_14", "JAVA_15",
    "JAVA_16", "JAVA_17", "JAVA_18",
    "JAVA_19", "JAVA_20", "JAVA_21",
    "JAVA_22",
    "JAVA_MIN", "JAVA_MAX",
    "Version",
)

"""
Java versions (specifically for the Java Virtual Machine).
"""


class Version:  # FIXME: Class restructuring required.
    """
    Java Virtual Machine version.

    Attributes
    ----------
    previous: bool
        Whether the version is a preview version.
    name: str
        The name of the version.
    major: int
        The major version found in class files.
    minor: int
        The minor version found in class files.
    """

    __slots__ = ("name", "major", "minor")

    NAMES: dict[tuple[int, int] | int, str] = {  # A map of major and/or minor versions to names.
        # The 1.0 and 1.0.1 versions may not be true as I have not found any 45.0 or 45.1 classes anywhere.
        (45, 0): "1.0",
        (45, 1): "1.0.1",
        (45, 2): "1.0.2",
        (45, 3): "1.1",
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
        64: "20",
        65: "21",
        66: "22",
    }

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

    @classmethod
    def get(cls, version: str | float | tuple[int, int]) -> "Version":
        """
        Gets a version from a specifier.

        Parameters
        ----------
        version: str | float | tuple[int, int]
            The version specifier.

        Returns
        -------
        Version
            The version.

        Raises
        ------
        ValueError
            If the provided specifier cannot be converted into a version.
        TypeError
            If the provided type is not a valid specifier.
        """

        if type(version) is tuple:
            if len(version) != 2:
                raise ValueError("expected a 2-tuple specifying the major and minor version")
            return cls(*version)

        elif type(version) is str:
            for version_, name in cls.NAMES.items():
                if version != name:
                    continue
                if isinstance(version_, int):
                    return cls(version_, 0)
                return cls(*version_)
            raise ValueError("unknown Java version %r" % version)

        elif type(version) is float:
            return cls._normalise(version)

        raise TypeError("don't know how to convert %r into a version" % type(version))

    @property
    def preview(self) -> bool:
        return self.major >= 56 and self.minor == 65535

    def __init__(self, major: int, minor: int) -> None:
        name = Version.NAMES.get((major, minor))
        if name is None:
            name = Version.NAMES.get(major) or "unknown"

        self.name = name  # To please mypy.
        self.major = major
        self.minor = minor

    def __repr__(self) -> str:
        return "<Version(name=%r, major=%i, minor=%i)>" % (self.name, self.major, self.minor)

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if other is self:
            return True
        elif isinstance(other, Version):
            return other.major == self.major and (self.major > 45 or other.minor == self.minor)
        elif isinstance(other, int):
            return other == self.major
        elif isinstance(other, float):
            return self == Version._normalise(other)

        return False

    def __hash__(self) -> int:
        return hash((self.major, self.minor))

    def __gt__(self, other: object) -> bool:
        if isinstance(other, Version):
            return self.major > other.major or (self.major == other.major and self.minor > other.minor)
        elif isinstance(other, int):
            return self.major > other
        elif isinstance(other, float):
            return self > self._normalise(other)

        return False

    def __ge__(self, other: object) -> bool:
        return self == other or self > other

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Version):
            return self.major < other.major or (self.major == other.major and self.minor < other.minor)
        elif isinstance(other, int):
            return self.major < other
        elif isinstance(other, float):
            return self < Version._normalise(other)

        return False

    def __le__(self, other: object) -> bool:
        return self == other or self < other


JAVA_1_0   = Version(45, 0)
JAVA_1_0_1 = Version(45, 1)
JAVA_1_0_2 = Version(45, 2)
JAVA_1_1   = Version(45, 3)
JAVA_1_2   = Version(46, 0)
JAVA_1_3   = Version(47, 0)
JAVA_1_4   = Version(48, 0)
JAVA_5     = Version(49, 0)
JAVA_6     = Version(50, 0)
JAVA_7     = Version(51, 0)
JAVA_8     = Version(52, 0)
JAVA_9     = Version(53, 0)
JAVA_10    = Version(54, 0)
JAVA_11    = Version(55, 0)
JAVA_12    = Version(56, 0)
JAVA_13    = Version(57, 0)
JAVA_14    = Version(58, 0)
JAVA_15    = Version(59, 0)
JAVA_16    = Version(60, 0)
JAVA_17    = Version(61, 0)
JAVA_18    = Version(62, 0)
JAVA_19    = Version(63, 0)
JAVA_20    = Version(64, 0)
JAVA_21    = Version(65, 0)
JAVA_22    = Version(66, 0)

JAVA_MIN = JAVA_1_0
JAVA_MAX = JAVA_22
