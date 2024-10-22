#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Block",
    "MutableBlock", "ImmutableBlock",
    "Return", "Rethrow", "Opaque",
)

import typing
from copy import deepcopy
from itertools import chain
from typing import Iterable

from ..insns import Instruction
from ..insns.flow import Jump, Switch

if typing.TYPE_CHECKING:
    from ...model.types import Class


class Block:
    """
    An extended basic block containing JVM instructions.

    Attributes
    ----------
    label: int
        A unique label for this block.
    insns: tuple[Instruction, ...]
        The instructions in this block, ordered correctly.
    lt_throws: frozenset[Class]
        A set of exceptions that could be thrown at link time.
    rt_throws: frozenset[Class]
        A set of exceptions that could be thrown at run time.

    Methods
    -------
    index(self, instruction: Instruction | type[Instruction], start: int = 0, stop: int = -1) -> int
        Returns the index of the first occurrence of an instruction in this block.
    count(self, instruction: Instruction | type[Instruction]) -> int
        Returns the number of occurrences of an instruction in this block.
    trace(frame: Frame) -> list[Trace.Step]
        Traces the execution of this block.
    """

    __slots__ = ("_label",)

    insns: tuple[Instruction, ...]
    lt_throws: frozenset["Class"]
    rt_throws: frozenset["Class"]

    @property
    def label(self) -> int:
        return self._label

    def __init__(self, label: int) -> None:
        self._label = label

    def __repr__(self) -> str:
        raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

    def __str__(self) -> str:
        return f"block_{self._label}"

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(f"== is not implemented for {type(self)!r}")

    def __hash__(self) -> int:
        raise NotImplementedError(f"hash() is not implemented for {type(self)!r}")

    def __getitem__(self, index: int) -> Instruction:
        return self.insns[index]

    def __len__(self) -> int:
        return len(self.insns)

    def index(self, instruction: Instruction | type[Instruction], start: int = 0, stop: int = -1) -> int:
        """
        Returns the index of the first occurrence of an instruction in this block.

        Parameters
        ----------
        instruction: Instruction | type[Instruction]
            The instruction to find.
        start: int
            The index to start searching from.
        stop: int
            The index to stop searching at.

        Returns
        -------
        int
            The index of the instruction, or `-1` if not found.
        """

        raise NotImplementedError(f"index() is not implemented for {type(self)!r}")

    def count(self, instruction: Instruction | type[Instruction]) -> int:
        """
        Returns the number of occurrences of an instruction in this block.

        Parameters
        ----------
        instruction: Instruction | type[Instruction]
            The instruction to count.

        Returns
        -------
        int
            The number of occurrences of the instruction.
        """

        raise NotImplementedError(f"count() is not implemented for {type(self)!r}")

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     """
    #     Traces the execution of this block.
    #
    #     Parameters
    #     ----------
    #     frame: Frame
    #         The current frame.
    #     state: State
    #         The state to add trace information to.
    #     """
    #
    #     steps = 0
    #     for instruction in self.insns:
    #         if instruction.trace(frame, state) is not None:
    #             steps += 1
    #         if frame.thrown is not None:
    #             break
    #
    #     logger.debug("Traced %s (%i insns) in %i step(s).", self, len(self.insns), steps)


class MutableBlock(Block):
    """
    A block that can be modified.

    Methods
    -------
    add(self, instruction: Instruction | type[Instruction], *, doraise: bool = True) -> None
        Adds an instruction to the end of this block.
    extend(self, instructions: Iterable[Instruction | type[Instruction]]) -> None
        Extends this block with a sequence of instructions.
    insert(self, index: int, instruction: Instruction | type[Instruction]) -> None
        Inserts an instruction at the given index.
    remove(self, instruction: Instruction | type[Instruction]) -> Instruction
        Removes and returns the first occurrence of an instruction from this block.
    pop(self, index: int = -1) -> Instruction | None
        Removes and returns the instruction at the given index.
    immutable(self) -> ImmutableBlock
        Creates an immutable block from this block.
    """

    __slots__ = ("_insns", "_hash")

    @property  # type: ignore[override]
    def insns(self) -> tuple[Instruction, ...]:
        return tuple(self._insns)

    @property  # type: ignore[override]
    def lt_throws(self) -> frozenset["Class"]:
        return frozenset(chain(*[instruction.lt_throws for instruction in self._insns]))

    @property  # type: ignore[override]
    def rt_throws(self) -> frozenset["Class"]:
        return frozenset(chain(*[instruction.rt_throws for instruction in self._insns]))

    def __init__(self, label: int, insns: Iterable[Instruction] | None = None) -> None:
        super().__init__(label)
        self._insns: list["Instruction"] = []
        if insns is not None:
            self._insns.extend(insns)
        self._hash = hash(label)

    def __copy__(self) -> "MutableBlock":
        return MutableBlock(self._label, self._insns)

    def __deepcopy__(self, memo: dict[int, object]) -> "MutableBlock":
        return MutableBlock(self._label, [deepcopy(instruction, memo) for instruction in self._insns])

    def __repr__(self) -> str:
        insns_str = ", ".join(map(str, self._insns))
        return f"<MutableBlock(label={self._label}, insns=({insns_str}))>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MutableBlock) and self._label == other._label and self._insns == other._insns

    def __hash__(self) -> int:
        return self._hash

    def __getitem__(self, index: int) -> Instruction:
        return self._insns[index]

    def __setitem__(self, index: int, value: Instruction | type[Instruction]) -> None:
        if not isinstance(value, Instruction):
            value = value()
        self._insns[index] = value

    def __delitem__(self, key: int | Instruction | type[Instruction]) -> None:
        if isinstance(key, int):
            del self._insns[key]
        else:
            self.remove(key)

    def __len__(self) -> int:
        return len(self._insns)

    def index(self, instruction: Instruction | type[Instruction], start: int = 0, stop: int = -1) -> int:
        if not isinstance(instruction, Instruction):
            instruction = instruction()
        try:
            return self._insns.index(instruction, start, stop)
        except ValueError:
            return -1

    def count(self, instruction: Instruction | type[Instruction]) -> int:
        if not isinstance(instruction, Instruction):
            instruction = instruction()
        return self._insns.count(instruction)

    def add(self, instruction: Instruction | type[Instruction], *, doraise: bool = True) -> None:
        """
        Adds an instruction to the end of this block.

        Parameters
        ----------
        instruction: Instruction | type[Instruction]
            The instruction to add.
        doraise: bool
            Raises an exception if the instruction cannot be added to this block.

        Raises
        -------
        TypeError
            If `doraise=True` and the instruction cannot be added to this block.
        """

        if not isinstance(instruction, Instruction):
            instruction = instruction()
        if doraise and isinstance(instruction, (Jump, Switch)):
            raise TypeError("cannot add jump instruction to block")

        self._insns.append(instruction)

    def extend(self, instructions: Iterable[Instruction | type[Instruction]], *, doraise: bool = True) -> None:
        """
        Extends this block with a sequence of instructions.

        Parameters
        ----------
        instructions: Iterable[Instruction | type[Instruction]]
            The instructions to add.
        doraise: bool
            Raises an exception if one or more instructions cannot be added to this
            block.

        Raises
        ------
        TypeError
            If `doraise=True` and one or more instructiosn cannot be added to this
            block.
        """

        for instruction in instructions:
            self.add(instruction, doraise=doraise)

    def insert(self, index: int, instruction: Instruction | type[Instruction]) -> None:
        """
        Inserts an instruction at the given index.

        Parameters
        ----------
        index: int
            The index to insert the instruction at.
        instruction: Instruction | type[Instruction]
            The instruction to insert.
        """

        if not isinstance(instruction, Instruction):
            instruction = instruction()
        self._insns.insert(index, instruction)

    def remove(self, instruction: Instruction | type[Instruction]) -> Instruction | None:
        """
        Removes and returns the first occurrence of an instruction from this block.

        Parameters
        ----------
        instruction: Instruction | type[Instruction]
            The instruction to remove.

        Returns
        -------
        Instruction | None
            The removed instruction, or `None` if not found.
        """

        if isinstance(instruction, Instruction):
            for index, instruction_ in enumerate(self._insns):
                if instruction == instruction_:
                    return self._insns.pop(index)
        else:
            for index, instruction_ in enumerate(self._insns):
                if isinstance(instruction_, instruction):
                    return self._insns.pop(index)

        return None

    def pop(self, index: int = -1) -> Instruction | None:
        """
        Removes and returns the instruction at the given index.

        Parameters
        ----------
        index: int
            The index of the instruction to remove.
        """

        try:
            return self._insns.pop(index)
        except IndexError:
            return None

    def clear(self) -> None:
        """
        Removes all instructions from this block.
        """

        self._insns.clear()

    def immutable(self) -> "ImmutableBlock":
        """
        Creates an immutable block from this block.
        """

        return ImmutableBlock(self._label, self._insns)


class ImmutableBlock(Block):
    """
    A block that cannot be modified once created.

    Methods
    -------
    mutable(self) -> MutableBlock
        Creates a mutable block from this block.
    """

    __slots__ = ("_insns", "_lt_throws", "_rt_throws", "_hash")

    @property  # type: ignore[override]
    def insns(self) -> tuple[Instruction, ...]:
        return self._insns

    @property  # type: ignore[override]
    def lt_throws(self) -> frozenset["Class"]:
        return self._lt_throws

    @property  # type: ignore[override]
    def rt_throws(self) -> frozenset["Class"]:
        return self._rt_throws

    def __init__(self, label: int, insns: Iterable[Instruction]) -> None:
        super().__init__(label)
        self._insns = tuple(insns)
        self._lt_throws = frozenset(chain(*[instruction.lt_throws for instruction in self._insns]))
        self._rt_throws = frozenset(chain(*[instruction.rt_throws for instruction in self._insns]))
        self._hash = hash((label, (instruction.opcode for instruction in self._insns)))

    def __repr__(self) -> str:
        insns_str = ", ".join(map(str, self._insns))
        return f"<ImmutableBlock(label={self._label}, insns=({insns_str}))>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ImmutableBlock) and self._label == other._label and self._insns == other._insns

    def __hash__(self) -> int:
        return self._hash

    def __getitem__(self, index: int) -> Instruction:
        return self._insns[index]

    def __len__(self) -> int:
        return len(self._insns)

    def index(self, instruction: Instruction | type[Instruction], start: int = 0, stop: int = -1) -> int:
        if not isinstance(instruction, Instruction):
            instruction = instruction()
        try:
            return self._insns.index(instruction, start, stop)
        except ValueError:
            return -1

    def count(self, instruction: Instruction | type[Instruction]) -> int:
        if not isinstance(instruction, Instruction):
            instruction = instruction()
        return self._insns.count(instruction)

    def mutable(self) -> MutableBlock:
        """
        Creates a mutable block from this block.
        """

        return MutableBlock(self._label, self._insns)


class Return(ImmutableBlock):
    """
    A return block.

    Represents the exit point of a graph via normal method return.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(-1, ())

    def __repr__(self) -> str:
        return "<Return>"

    def __str__(self) -> str:
        return "block_return"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Return)

    def __hash__(self) -> int:
        return self._hash


class Rethrow(ImmutableBlock):
    """
    A rethrow block.

    Represents the exit point of a graph via a rethrown exception.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(-2, ())

    def __repr__(self) -> str:
        return "<Rethrow>"

    def __str__(self) -> str:
        return "block_rethrow"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Rethrow)

    def __hash__(self) -> int:
        return self._hash


class Opaque(ImmutableBlock):
    """
    An opaque block.

    Represents the target of a jump whose real target is currently unknown.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(-3, ())

    def __repr__(self) -> str:
        return "<Opaque>"

    def __str__(self) -> str:
        return "block_opaque"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Opaque)

    def __hash__(self) -> int:
        return self._hash
