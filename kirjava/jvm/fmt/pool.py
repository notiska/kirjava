#!/usr/bin/env python3

__all__ = (
    "ConstPool",
)

import typing
from os import SEEK_SET
from typing import IO, Iterable, Union

from .constants import ConstIndex, ConstInfo
from .._struct import *

if typing.TYPE_CHECKING:
    from .classfile import ClassFile
    from ..verify import Verifier


class ConstPool:
    """
    A class file constant pool.

    An abstraction over the constant pool allowing for easier management or entries
    and indices.

    Attributes
    ----------
    maximum: int
        The maximum valid index of this constant pool.
    entries: dict[int, ConstInfo]
        All the entries in this constant pool, mapped to their indices.
        Updating this collection will not update the underlying pool.

    Methods
    -------
    read(stream: IO[bytes]) -> ConstPool
        Reads a constant pool from a binary stream.
    write(self, stream: IO[bytes]) -> None
        Writes this constant pool to the binary stream.
    verify(self, verifier: Verifier, cf: ClassFile) -> None
        Verifies that this constant pool is valid.
    clear(self) -> None
        Clears all the entries from this constant pool.
    add(self, info: ConstInfo) -> int
        Adds a constant to the end of this constant pool.
    extend(self, constants: Iterable[ConstInfo] | ConstPool) -> None
        Adds multiple constants to the end of this constant pool.
    index(self, info: ConstInfo) -> int
        Gets the index of a constant in this constant pool.
    """

    # insert(self, index: int, info: ConstInfo) -> None
    #     Inserts a constant into this constant pool at the given index.
    # pop(self, index: int = -1) -> None
    #     Removes the constant in this constant pool, given an index and returns it.
    # remove(self, info: ConstInfo) -> None
    #     Removes a constant from this constant pool.

    __slots__ = ("_contiguous", "_non_contiguous", "_index")

    @classmethod
    def read(cls, stream: IO[bytes]) -> "ConstPool":
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
            tag, = stream.read(1)
            subclass = ConstInfo.lookup(tag)
            if subclass is None:
                raise ValueError("unknown constant pool tag %i at index %i" % (tag, self._index))
            info = subclass.read(stream, self)
            info.index = self._index
            self[self._index] = info

        for entry in self._contiguous[1:]:
            entry.populate(self)

        return self

    @property
    def maximum(self) -> int:
        return self._index

    @property
    def entries(self) -> dict[int, ConstInfo]:
        return {index: entry for index, entry in enumerate(self._contiguous) if not isinstance(entry, ConstIndex)}

    def __init__(self) -> None:
        self._contiguous: list[ConstInfo] = [ConstIndex(0)]
        self._non_contiguous: dict[int, ConstInfo] = {}

        self._index = 1  # The index of the last "valid" entry in this constant pool.

        # TODO: Some way of requesting low indices (<=255) when adding to the pool.

    def __repr__(self) -> str:
        return "<ConstPool(entries=%r)>" % (self.entries,)

    def __getitem__(self, index: int) -> ConstInfo:
        if index < 0 or index > 65535:
            raise IndexError("provided index %i is out of valid constant pool bounds" % index)
        elif index >= self._index:
            return self._non_contiguous.get(index) or ConstIndex(index)
        return self._contiguous[index]

    def __setitem__(self, index: int, info: ConstInfo | None) -> None:
        if index < 1 or index > self._index:
            raise IndexError("provided index %i is out of valid constant pool bounds" % index)
        elif index == self._index:
            if info is None:
                return
            self._contiguous.append(info)
            self._non_contiguous.pop(index, None)
            self._index += 1
            if info.wide:
                self._contiguous.append(ConstIndex(self._index))
                self._non_contiguous.pop(index + 1, None)
                self._index += 1
            return

        current = self._contiguous[index]
        if isinstance(current, ConstIndex):
            raise IndexError("provided index %i is reserved by a wide constant" % index)
        elif current.wide:
            self._contiguous.pop(index + 1)

        if info is None:
            self._contiguous.pop(index)
        else:
            self._contiguous[index] = info
            if info.wide:
                self._contiguous.insert(index + 1, ConstIndex(index + 1))

        # We may need to update any indices if we have shifted the contiguous entries at all.
        for index, entry in enumerate(self._contiguous):
            if isinstance(entry, ConstIndex):
                entry.index = index

    def __delitem__(self, index: int) -> None:
        if index < 1 or index >= self._index:
            raise IndexError("provided index %i is outside of the valid range of this constant pool" % index)
        self[index] = None

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
            stream.write(bytes((entry.tag,)))
            entry.write(stream, self)
            index += 1

        end = stream.tell()
        stream.seek(start, SEEK_SET)
        stream.write(pack_H(self._index))
        stream.seek(end, SEEK_SET)

    def verify(self, verifier: "Verifier", cf: "ClassFile") -> None:
        """
        Verifies that this constant pool is valid.

        Parameters
        ----------
        verifier: Verifier
            The verifier to use and report to.
        cf: ClassFile
            The class file that this pool belongs to.
        """

        if self._index > 65535:
            verifier.fatal(self, "too many constants")

        if verifier.check_const_vers:
            for entry in self._contiguous:
                if cf.version < entry.since:
                    verifier.fatal(entry, "constant not valid in current class file version")

        # TODO: Also check that this is actually contiguous.
        for entry in self._contiguous:
            entry.verify(verifier)

    def clear(self) -> None:
        """
        Clears all the entries from this constant pool.
        """

        self._contiguous.clear()
        self._non_contiguous.clear()
        self._index = 1
        self._contiguous.append(ConstIndex(0))

    def add(self, info: ConstInfo) -> int:
        """
        Adds a constant to the end of this constant pool.

        Parameters
        ----------
        info: ConstInfo
            The constant to add.

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

    def extend(self, constants: Union[Iterable[ConstInfo], "ConstPool"]) -> None:
        """
        Adds multiple constants to the end of this constant pool.

        Parameters
        ----------
        constants: Iterable[ConstInfo] | ConstPool
            The constants to add.
        """

        if isinstance(constants, ConstPool):
            constants = constants.entries.values()
        for constant in constants:
            self.add(constant)

    def index(self, info: ConstInfo) -> int:
        """
        Gets the index of a constant in this constant pool.

        Parameters
        ----------
        info: ConstInfo
            The constant to get the index of.

        Returns
        -------
        int
            The index of the constant in this constant pool.
            If the constant is not present in this constant pool, `-1` is returned.
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

    # def remove(self, info: ConstInfo) -> None:
    #     """
    #     Removes a constant from this constant pool.
    #
    #     Parameters
    #     ----------
    #     info: ConstInfo
    #         The constant to remove.
    #     """
