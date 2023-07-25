#!/usr/bin/env python3

__all__ = (
    "InvokeInstruction",
    "InvokeVirtualInstruction", "InvokeSpecialInstruction", "InvokeInterfaceInstruction",
    "InvokeStaticInstruction",
    "InvokeDynamicInstruction",
)

"""
Invocation instructions.
"""

import typing
from typing import Any, IO, List, Optional, Union

from . import Instruction
from .new import NewInstruction
from ..ir.invoke import *
from ..ir.variable import AssignStatement
from ... import types
from ...abc import Value
from ...constants import InterfaceMethodRef, InvokeDynamic, MethodRef
from ...source import *
from ...types import Class, Uninitialized

if typing.TYPE_CHECKING:
    from ...analysis import Context
    from ...classfile import ClassFile


class InvokeInstruction(Instruction):
    """
    An instruction that invokes a method.
    """

    __slots__ = ("_index", "reference")

    def __init__(self, reference: Union[MethodRef, InterfaceMethodRef, InvokeDynamic]) -> None:
        """
        :param reference: The reference to the method.
        """

        self.reference = reference

    def __repr__(self) -> str:
        return "<InvokeInstruction(opcode=0x%x, mnemonic=%s, reference=%r) at %x>" % (
            self.opcode, self.mnemonic, self.reference, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.reference)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.reference == self.reference) or other is type(self)

    def copy(self) -> "InvokeInstruction":
        return type(self)(self.reference)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.reference = class_file.constant_pool[self._index]

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(self.reference)
        super().write(class_file, buffer, wide)

    def _trace_arguments(self, context: "Context") -> None:  # List[Entry]:
        """
        Partial tracing for the arguments this instruction should accept.
        """

        for argument_type in reversed(self.reference.argument_types):
            *_, entry = context.pop(1 + argument_type.wide, as_tuple=True)
            context.constrain(entry, argument_type)


class InvokeVirtualInstruction(InvokeInstruction):
    """
    An instruction that invokes a virtual method.
    """

    __slots__ = ()

    throws = (  # FIXME
        Class("java/lang/AbstractMethodError"),
        Class("java/lang/IncompatibleClassChangeError"),
        Class("java/lang/NullPointerException"),
        Class("java/lang/UnsatisfiedLinkError"),
    )

    def trace(self, context: "Context") -> None:
        self._trace_arguments(context)
        context.constrain(context.pop(), self.reference.class_.class_type)
        if self.reference.return_type is not types.void_t:
            context.push(self.reference.return_type)

    # def lift(
    #         self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value],
    # ) -> Union[InvokeStatement, AssignStatement]:
    #     ...
    #
    #     # if self.reference.return_type == types.void_t:
    #     #     return InvokeStatement()


class InvokeSpecialInstruction(InvokeVirtualInstruction):
    """
    An instruction that is similar to invokevirtual, except it has handling for special methods.
    """

    __slots__ = ()

    throws = (
        Class("java/lang/AbstractMethodError"),
        Class("java/lang/IllegalAccessError"),
        Class("java/lang/IncompatibleClassChangeError"),
        Class("java/lang/NullPointerException"),
        Class("java/lang/UnsatisfiedLinkError"),
    )

    def trace(self, context: "Context") -> None:
        self._trace_arguments(context)
        entry = context.pop()

        if self.reference.name == "<init>" and self.reference.return_type is types.void_t:
            if entry.type == types.uninitialized_this_t:
                context.replace(entry, context.method.class_.get_type())
                return
            # Unverified code can cause this not to be an uninitialized type
            elif isinstance(entry.type, Uninitialized):
                class_type: Optional[Class] = None
                source = entry.type.source

                if isinstance(source, NewInstruction):
                    class_type = source.type
                elif type(source) in (InstructionInBlock, InstructionAtOffset) and isinstance(source.instruction, NewInstruction):
                    class_type = source.instruction.type

                if class_type is None:
                    class_type = self.reference.class_.class_type
                    # TODO: Report some kind of error here?

                context.replace(entry, class_type)
                return

        context.constrain(entry, self.reference.class_.class_type)
        if self.reference.return_type is not types.void_t:
            context.push(self.reference.return_type)

    # def lift(
    #         self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value],
    # ) -> Union[InvokeStatement, AssignStatement]:
    #     ...


class InvokeStaticInstruction(InvokeInstruction):
    """
    An instruction that invokes a static method.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        self._trace_arguments(context)
        if self.reference.return_type is not types.void_t:
            context.push(self.reference.return_type)

    # def lift(
    #         self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value],
    # ) -> Union[InvokeStaticStatement, AssignStatement]:
    #     ...


class InvokeInterfaceInstruction(InvokeVirtualInstruction):
    """
    An instruction that invokes an interface method.
    """

    __slots__ = ("_index", "count")

    throws = (
        Class("java/lang/AbstractMethodError"),
        Class("java/lang/IllegalAccessError"),
        Class("java/lang/IncompatibleClassChangeError"),
        Class("java/lang/NullPointerException"),
        Class("java/lang/UnsatisfiedLinkError"),
    )

    def __init__(self, reference: InterfaceMethodRef, count: int = 0) -> None:
        super().__init__(reference)
        self.count = count

    def copy(self) -> "InvokeInterfaceInstruction":
        return type(self)(self.reference, self.count)


class InvokeDynamicInstruction(InvokeStaticInstruction):
    """
    An instruction that invokes a dynamically computed callsite.
    """

    __slots__ = ()

    def __init__(self, reference: InvokeDynamic) -> None:
        super().__init__(reference)

    def __repr__(self) -> str:
        # Ugly, but whatever
        return "<InvokeDynamicInstruction(opcode=0x%x, mnemonic=%s, reference=%r) at %x>" % (
            self.opcode, self.mnemonic, self.reference, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.reference)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.reference == self.reference) or other is type(self)
