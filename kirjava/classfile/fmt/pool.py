#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "ConstPool",
)

from copy import copy, deepcopy
from os import SEEK_SET
from typing import IO, Iterable, Iterator, Union

from .constants import ConstIndex, ConstInfo
from .._struct import *
from ..._compat import Self


class ConstPool:
    """
    A class file constant pool.

    An abstraction over the constant pool allowing for easier management or entries
    and indices.

    Attributes
    ----------
    entries: dict[int, ConstInfo]
        All the entries in this constant pool, mapped to their indices.
        Updating this collection will not update the underlying pool.

    Methods
    -------
    read(stream: IO[bytes]) -> Self
        Reads a constant pool from a binary stream.

    copy(self, deep: bool = False) -> ConstPool
        Creates a copy of this constant pool.
    write(self, stream: IO[bytes]) -> None
        Writes this constant pool to the binary stream.
    add(self, info: ConstInfo, low: bool = False) -> int
        Adds a constant to this constant pool.
    extend(self, infos: Iterable[ConstInfo] | ConstPool) -> None
        Extends this constant pool with a sequence of constants.
    index(self, info: ConstInfo) -> int
        Returns the index of the first occurrence of a constant in this constant pool.
    clear(self) -> None
        Clears all entries from this constant pool.
    """

    # insert(self, index: int, info: ConstInfo) -> None
    #     Inserts a constant into this constant pool at the given index.
    # pop(self, index: int = -1) -> None
    #     Removes the constant in this constant pool, given an index and returns it.
    # remove(self, info: ConstInfo) -> None
    #     Removes a constant from this constant pool.

    __slots__ = ("_contiguous", "_non_contiguous", "_low", "_index")

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads a constant pool from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        """

        count, = unpack_H(stream.read(2))
        self = cls()

        while self._index < count:
            info = ConstInfo.read(stream, self)
            self[self._index] = info
        for entry in self._contiguous[1:]:
            entry.deref(self)

        return self

    @property
    def entries(self) -> dict[int, ConstInfo]:
        return {index: entry for index, entry in enumerate(self._contiguous) if not isinstance(entry, ConstIndex)}

    def __init__(self, infos: Union[Iterable[ConstInfo], "ConstPool"] | None = None) -> None:
        self._contiguous: list[ConstInfo] = [ConstIndex(0)]
        self._non_contiguous: dict[int, ConstInfo] = {}
        self._low: list[ConstInfo] = []

        self._index = 1  # The index of the last "valid" entry in this constant pool.

        if infos is not None:
            self.extend(infos)

    def __copy__(self) -> "ConstPool":
        copied = ConstPool()
        copied._contiguous.extend(self._contiguous[1:])
        copied._non_contiguous.update(self._non_contiguous)
        copied._low.extend(self._low)
        copied._index = self._index
        return copied

    def __deepcopy__(self, memo: dict[int, object]) -> "ConstPool":
        copied = ConstPool()
        copied._contiguous.extend(deepcopy(entry, memo) for entry in self._contiguous[1:])
        copied._non_contiguous.update({index: deepcopy(entry, memo) for (index, entry) in self._non_contiguous.items()})
        copied._low.extend(deepcopy(entry, memo) for entry in self._low)
        copied._index = self._index
        return copied

    def __repr__(self) -> str:
        return f"<ConstPool(entries={self.entries!r})>"

    def __iter__(self) -> Iterator[ConstInfo]:
        return iter(self._contiguous)

    def __getitem__(self, index: int) -> ConstInfo:
        if index < 0 or index > 65535:
            raise IndexError(f"provided index {index} is out of valid constant pool bounds")
        elif index >= self._index:
            return self._non_contiguous.get(index) or ConstIndex(index)
        return self._contiguous[index]

    def __setitem__(self, index: int, value: ConstInfo | None) -> None:
        if index < 1 or index > self._index:
            raise IndexError(f"provided index {index} is out of valid constant pool bounds")
        elif index == self._index:
            if value is None:
                return
            self._contiguous.append(value)
            self._non_contiguous.pop(index, None)
            self._index += 1
            if value.wide:
                self._contiguous.append(ConstIndex(self._index))
                self._non_contiguous.pop(index + 1, None)
                self._index += 1
            return

        current = self._contiguous[index]
        if isinstance(current, ConstIndex):
            raise IndexError(f"provided index {index} is reserved by a wide constant")
        elif current.wide:
            self._contiguous.pop(index + 1)

        if value is None:
            self._contiguous.pop(index)
        else:
            self._contiguous[index] = value
            if value.wide:
                self._contiguous.insert(index + 1, ConstIndex(index + 1))

        # We may need to update any indices if we have shifted the contiguous entries at all.
        for index, entry in enumerate(self._contiguous):
            if isinstance(entry, ConstIndex):
                entry.index = index

    def __delitem__(self, index: int) -> None:
        if index < 1 or index >= self._index:
            raise IndexError(f"provided index {self.index} is outside of the valid range of this constant pool")
        self[index] = None

    def __len__(self) -> int:
        return self._index

    def copy(self, deep: bool = False) -> "ConstPool":
        """
        Creates a copy of this constant pool.

        Parameters
        ----------
        deep: bool
            Whether to copy the entries contained within this pool.
        """

        if not deep:
            return copy(self)
        return deepcopy(self)

    def write(self, stream: IO[bytes]) -> None:
        """
        Writes this constant pool to the binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        """

        start = stream.tell()
        stream.write(pack_H(self._index))

        index = 1
        while index < self._index:
            entry = self._contiguous[index]
            if isinstance(entry, ConstIndex):
                index += 1
                continue
            entry.write(stream, self)
            index += 1

        end = stream.tell()
        stream.seek(start, SEEK_SET)
        stream.write(pack_H(self._index))
        stream.seek(end, SEEK_SET)

    def add(self, info: ConstInfo, low: bool = False) -> int:
        """
        Adds a constant to this constant pool.

        The constant will usually be added at the end, but may be added at a lower
        index if requested.

        Parameters
        ----------
        info: ConstInfo
            The constant to add.
        low: bool
            Whether to request a low index (<=255) for this constant.

        Returns
        -------
        int
            The index of the added constant.
        """

        if isinstance(info, ConstIndex):
            return info.index

        index = self.index(info)
        if index >= 0:
            return index

        index = self._index
        self[self._index] = info
        return index

    def extend(self, infos: Union[Iterable[ConstInfo], "ConstPool"]) -> None:
        """
        Extends this constant pool with a sequence of constants.
        """

        if isinstance(infos, ConstPool):
            assert infos._contiguous, "invalid pool state"  # At least one entry is required.
            infos = infos._contiguous[1:]  # We need to skip the initial 0 index.
        for info in infos:
            self.add(info)

    # def insert(self, index: int, info: ConstInfo) -> None:
    #     """
    #     Inserts a constant into this constant pool at the given index.
    #
    #     Parameters
    #     ----------
    #     index: int
    #         The index to insert at.
    #     info: ConstInfo
    #         The constant to insert.
    #
    #     Raises
    #     ------
    #     IndexError
    #         If the provided index could not be inserted at.
    #     """
    #
    #     ...

    # def remove(self, info: ConstInfo) -> None:
    #     """
    #     Removes a constant from this constant pool.
    #
    #     Parameters
    #     ----------
    #     info: ConstInfo
    #         The constant to remove.
    #     """

    # def pop(self, index: int = -1) -> ConstInfo:
    #     """
    #     Removes the constant in this constant pool, given an index and returns it.
    #
    #     Parameters
    #     ----------
    #     index: int
    #         The index to pop.
    #         If this is negative, it is indexed from the back of the valid range of
    #         this constant pool (`ConstantPool.maximum`).
    #
    #     Returns
    #     -------
    #     ConstantPool.Ref
    #         The constant at the provided index.
    #         If the constant was wide, the first entry is returned.
    #
    #     Raises
    #     ------
    #     IndexError
    #         See `ConstantPool.__getitem__()` and `ConstantPool.__delitem__()`.
    #     ValueError
    #         See `ConstantPool.__delitem__()`.
    #     """
    #
    #     if index < 0:
    #         index += self._index + 1
    #
    #     # Any required validation is delegated to `__getitem__` and `__delitem__`.
    #     ref = self[index]
    #     del self[index]
    #
    #     return ref

    def index(self, info: ConstInfo) -> int:
        """
        Returns the index of the first occurrence of a constant in this constant pool.

        Returns
        -------
        int
            The index of the constant, `-1` if not present.
        """

        # First we'll search for an exact entry match, then fallback to default behaviour if this fails. This is to
        # attempt to preserve the original order of the constant pool.
        if info.index is not None:
            for index, entry in enumerate(self._contiguous):
                # if entry is info:  # May not be valid under certain circumstances.
                if entry.index == info.index and entry == info:
                    return index

        for index, entry in enumerate(self._contiguous):
            if entry == info:
                return index
        return -1

    def clear(self) -> None:
        """
        Clears all entries from this constant pool.
        """

        self._contiguous.clear()
        self._non_contiguous.clear()
        self._low.clear()
        self._index = 1
        self._contiguous.append(ConstIndex(0))
