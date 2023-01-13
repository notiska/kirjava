#!/usr/bin/env python3

"""
Instructions that push constants to the stack.
"""

from abc import ABC
from typing import Any, Dict, IO, List

from . import Instruction
from .. import ClassFile
from ..constants import ConstantInfo, Integer
from ... import types
from ...abc import Source, TypeChecker, Value
from ...analysis.ir.value import ConstantValue
from ...analysis.trace import Entry, State
from ...verifier import Error


class ConstantInstruction(Instruction, ABC):
    """
    Pushes any constant to the stack.
    """

    __slots__ = ("constant",)

    def __init__(self, constant: ConstantInfo) -> None:
        """
        :param constant: The constant that this instruction holds.
        """

        self.constant = constant

    def __repr__(self) -> str:
        return "<ConstantInstruction(opcode=0x%x, mnemonic=%s, constant=%r) at %x>" % (
            self.opcode, self.mnemonic, self.constant, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.constant)

    def __eq__(self, other: Any) -> bool:
        return (other.__class__ is self.__class__ and other.constant == self.constant) or other is self.__class__

    def copy(self) -> "ConstantInstruction":
        return self.__class__(self.constant)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        try:
            state.push(source, self.constant.get_type(), self.constant)
        except TypeError:
            errors.append(Error(
                Error.Type.INVALID_CONSTANT, source, "can't convert constant %s to Java type" % self.constant,
            ))
            state.push(source, types.top_t)  # Placeholder, doesn't account for wide types tho :(

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = ConstantValue(self.constant)


class FixedConstantInstruction(ConstantInstruction, ABC):
    """
    Pushes the same constant to the stack every time.
    """

    constant: ConstantInfo = ...

    def __init__(self) -> None:
        super().__init__(self.__class__.constant)

    def __str__(self) -> str:
        return self.mnemonic

    def __eq__(self, other: Any) -> bool:
        return other.__class__ is self.__class__ or other is self.__class__

    def copy(self) -> "FixedConstantInstruction":
        return self  # Immutable type technically

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...


class IntegerConstantInstruction(ConstantInstruction, ABC):
    """
    Pushes one of the operands (as an integer) to the stack.
    """

    def __init__(self, constant: Integer) -> None:
        super().__init__(constant)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.constant = Integer(self._value)

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        self._value = self.constant.value
        super().write(class_file, buffer, wide)


class LoadConstantInstruction(ConstantInstruction, ABC):
    """
    Loads a constant from the constant pool.
    """

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.constant = class_file.constant_pool[self._index]

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(self.constant)
        super().write(class_file, buffer, wide)
