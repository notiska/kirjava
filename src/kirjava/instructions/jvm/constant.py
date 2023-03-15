#!/usr/bin/env python3

"""
Instructions that push constants to the stack.
"""

from typing import Any, Dict, IO

from . import Instruction
from ..ir.value import ConstantValue
from ... import types
from ...abc import Value
from ...analysis.ir.variable import Scope
from ...analysis.trace import Entry, Frame, FrameDelta
from ...classfile import ClassFile
from ...classfile.constants import ConstantInfo, Integer
from ...verifier import Error


class ConstantInstruction(Instruction):
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
        return (type(other) is self.__class__ and other.constant == self.constant) or other is self.__class__

    def copy(self) -> "ConstantInstruction":
        return self.__class__(self.constant)

    def trace(self, frame: Frame) -> None:
        try:
            frame.push(self.constant.get_type(), self.constant)
        except TypeError:
            frame.verifier.report(Error(
                Error.Type.INVALID_CONSTANT, frame.source, "can't convert constant %s to Java type" % self.constant,
            ))
            frame.push(types.top_t)  # Placeholder, doesn't account for wide types tho :(

    def lift(self, delta: FrameDelta, scope: "Scope", associations: Dict[Entry, Value]) -> None:
        associations[delta.pushes[0]] = ConstantValue(self.constant)


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
        return type(other) is self.__class__ or other is self.__class__

    def copy(self) -> "FixedConstantInstruction":
        return self  # Immutable type technically

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...


class IntegerConstantInstruction(ConstantInstruction):
    """
    Pushes one of the operands (as an integer) to the stack.
    """

    __slots__ = ("_value",)

    def __init__(self, constant: Integer) -> None:
        super().__init__(constant)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.constant = Integer(self._value)

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        self._value = self.constant.value
        super().write(class_file, buffer, wide)


class LoadConstantInstruction(ConstantInstruction):
    """
    Loads a constant from the constant pool.
    """

    __slots__ = ("_index",)

    category: int = ...

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.constant = class_file.constant_pool[self._index]

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(self.constant)
        super().write(class_file, buffer, wide)

    def trace(self, frame: Frame) -> None:
        try:
            type_ = self.constant.get_type()
            if not frame.verifier.checker.check_category(type_, self.category):
                frame.verifier.report_invalid_type_category(frame.source, self.category, type_, None)
            frame.push(type_, self.constant)
        except TypeError:
            frame.verifier.report(Error(
                Error.Type.INVALID_CONSTANT, frame.source, "can't convert constant %s to Java type" % self.constant,
            ))
            frame.push(types.top_t)  # Placeholder, doesn't account for wide types tho :(

