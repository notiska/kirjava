#!/usr/bin/env python3

__all__ = (
    "ConstantInstruction", "FixedConstantInstruction", "IntegerConstantInstruction", "LoadConstantInstruction",
)

"""
Instructions that push constants to the stack.
"""

import typing
from typing import Any, Dict, IO, Union

from . import Instruction
from ..ir.value import ConstantValue
from ... import types
from ...abc import Value
from ...constants import ConstantInfo, Integer
from ...error import ConstantWidthError, InvalidConstantError

if typing.TYPE_CHECKING:
    from ...analysis import Context
    from ...classfile import ClassFile


class ConstantInstruction(Instruction):
    """
    Pushes any constant to the stack.
    """

    __slots__ = ("constant",)

    def __init__(self, constant: ConstantInfo) -> None:
        """
        :param constant: The constant that this instruction holds.
        """

        # TODO: Might be nice to have it automatically work out constant types from the value passed?
        self.constant = constant

    def __repr__(self) -> str:
        return "<ConstantInstruction(opcode=0x%x, mnemonic=%s, constant=%r) at %x>" % (
            self.opcode, self.mnemonic, self.constant, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.constant)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.constant == self.constant) or other is type(self)

    def copy(self) -> "ConstantInstruction":
        return type(self)(self.constant)

    def trace(self, context: "Context") -> None:
        context.push(self.constant.type or context.frame.TOP)
        # TODO: Report error if not valid type

    # def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
    #     associations[delta.pushes[0]] = ConstantValue(self.constant)


class FixedConstantInstruction(ConstantInstruction):
    """
    Pushes the same constant to the stack every time.
    """

    __slots__ = ()

    constant: ConstantInfo = ...

    def __init__(self) -> None:
        ...  # super().__init__(self.__class__.constant)

    def __str__(self) -> str:
        return self.mnemonic

    def __eq__(self, other: Any) -> bool:
        return type(other) is type(self) or other is type(self)

    def copy(self) -> "FixedConstantInstruction":
        return self  # Immutable type technically

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        ...


class IntegerConstantInstruction(ConstantInstruction):
    """
    Pushes one of the operands (as an integer) to the stack.
    """

    __slots__ = ("_value",)

    def __init__(self, constant: Union[int, Integer]) -> None:
        if type(constant) is int:
            constant = Integer(constant)
        super().__init__(constant)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.constant = Integer(self._value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._value = self.constant.value
        super().write(class_file, buffer, wide)


class LoadConstantInstruction(ConstantInstruction):
    """
    Loads a constant from the constant pool.
    """

    __slots__ = ("_index",)

    wide: bool = False

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.constant = class_file.constant_pool[self._index]

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(self.constant)
        super().write(class_file, buffer, wide)

    def trace(self, context: "Context") -> None:
        type_ = self.constant.type
        if type_ is None:
            if context.do_raise:
                raise InvalidConstantError(self.constant)
            context.push(context.frame.TOP)  # Best we can do.
            if self.wide:
                context.push(context.frame.TOP)
            return

        if type_.wide != self.wide and context.do_raise:
            raise ConstantWidthError(self.constant, self.wide)
        context.push(type_)

