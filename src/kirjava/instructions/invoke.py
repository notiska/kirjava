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
from typing import Any, IO

from . import Instruction
from .new import NewInstruction
from ..constants import InterfaceMethodRef, InvokeDynamic, MethodRef
from ..source import *
from ..types import null_t, uninitialized_this_t, void_t, Class, Reference, Uninitialized

if typing.TYPE_CHECKING:
    from ..analysis import Context
    from ..classfile import ClassFile


class InvokeInstruction(Instruction):
    """
    An instruction that invokes a method.
    """

    __slots__ = ("_index", "reference")

    def __init__(self, reference: MethodRef | InterfaceMethodRef | InvokeDynamic) -> None:
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

    def _trace_arguments(self, context: "Context") -> None:  # list[Entry]:
        """
        Partial tracing for the arguments this instruction should accept.
        """

        for argument_type in reversed(self.reference.argument_types):
            *_, entry = context.pop(1 + argument_type.wide, as_tuple=True)
            context.constrain(entry, argument_type)

    def _trace_return(self, context: "Context") -> None:
        """
        Partial tracing for the return type this instruction references.
        """

        return_type = self.reference.return_type
        if return_type is void_t:
            return

        entry = context.push(return_type.as_vtype())
        context.constrain(entry, return_type, original=True)
        if isinstance(return_type, Reference):
            # Just to be on the safe-side, we'll say that this is nullable.
            context.constrain(entry, null_t, original=True)


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
        self._trace_return(context)

    # def lift(
    #         self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value],
    # ) -> InvokeStatement | AssignStatement:
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

        # The requirements for the reference to be a constructor method.
        if self.reference.name != "<init>" or self.reference.return_type is not void_t:
            self._trace_return(context)
            return

        if entry.generic is uninitialized_this_t:
            context.replace(entry, context.method.class_.get_type())
            return

        # Unverified code can cause this not to be an uninitialized type
        elif isinstance(entry.generic, Uninitialized):
            class_type: Class | None = None
            source = entry.generic.source

            if isinstance(source, NewInstruction):
                class_type = source.type
            elif type(source) in (InstructionInBlock, InstructionAtOffset) and isinstance(source.instruction, NewInstruction):
                class_type = source.instruction.type

            if class_type is None:
                if context.do_raise:
                    ...  # TODO: Report some kind of error here?
                class_type = self.reference.class_.class_type

            context.replace(entry, class_type)
            return

        if context.do_raise:
            ...  # TODO: Raise error?
        self._trace_return(context)

    # def lift(
    #         self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value],
    # ) -> InvokeStatement | AssignStatement:
    #     ...


class InvokeStaticInstruction(InvokeInstruction):
    """
    An instruction that invokes a static method.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        self._trace_arguments(context)
        self._trace_return(context)

    # def lift(
    #         self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value],
    # ) -> InvokeStaticStatement | AssignStatement:
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

    def trace(self, context: "Context") -> None:
        self._trace_arguments(context)
        # Sidenote: it's not actually required that we check if it's an interface at verification time, but we'll add
        #           this "constraint" more as a hint that we're dealing with an interface.
        context.constrain(context.pop(), self.reference.class_.class_type.as_interface())
        self._trace_return(context)


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
        return (type(other) is type(self) and self.reference == other.reference) or other is type(self)
