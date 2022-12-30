#!/usr/bin/env python3

"""
Invocation instructions.
"""

from abc import ABC
from typing import Any, IO, List, Tuple, Union

from . import Instruction, MetaInstruction
from .. import descriptor, ClassFile
from ..constants import Class as Class_, InterfaceMethodRef, InvokeDynamic, MethodRef, NameAndType
from ... import _argument, types
from ...abc import Class, Error, Source, TypeChecker
from ...analysis.trace import Entry, State
from ...types import BaseType, ReferenceType
from ...types.reference import ClassOrInterfaceType
from ...types.verification import This, Uninitialized


class InvokeInstruction(Instruction, ABC):
    """
    An instruction that invokes a method.
    """

    __slots__ = ("class_", "name", "argument_types", "return_type")

    def __init__(
            self,
            class_: Union[ReferenceType, Class, Class_, str],
            name: str,
            *descriptor: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
    ) -> None:
        """
        :param class_: The class that the method belongs to.
        :param name: The name of the method.
        :param descriptor: The method descriptor.
        """

        self.class_ = _argument.get_reference_type(class_)
        self.name = name
        self.argument_types, self.return_type = _argument.get_method_descriptor(*descriptor)

    def __repr__(self) -> str:
        return "<InvokeInstruction(opcode=0x%x, mnemonic=%s, class=%s, name=%r, argument_types=(%s), return_type=%s) at %x>" % (
            self.opcode, self.mnemonic, self.class_, self.name, 
            ", ".join(map(str, self.argument_types)) + ("," if len(self.argument_types) == 1 else ""),
            self.return_type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s#%s %s(%s)" % (
            self.mnemonic, self.class_, self.return_type, self.name, ", ".join(map(str, self.argument_types)),
        )

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, MetaInstruction) and other == self.__class__) or (
            other.__class__ == self.__class__ and
            other.class_ == self.class_ and
            other.name == self.name and
            other.argument_types == self.argument_types and
            other.return_type == self.return_type
        )

    def copy(self) -> "InvokeInstruction":
        return self.__class__(self.class_, self.name, self.argument_types, self.return_type)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)

        method_ref = class_file.constant_pool[self._index]
        self.class_ = method_ref.class_.get_actual_type()
        self.name = method_ref.name_and_type.name
        self.argument_types, self.return_type = descriptor.parse_method_descriptor(method_ref.name_and_type.descriptor)

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if isinstance(self.class_, ClassOrInterfaceType):
            class_ = Class_(self.class_.name)
        else:
            class_ = Class_(descriptor.to_descriptor(self.class_))
        method_ref = MethodRef(
            class_, NameAndType(self.name, descriptor.to_descriptor(self.argument_types, self.return_type)),
        )
        self._index = class_file.constant_pool.add(method_ref)

        super().write(class_file, buffer, wide)

    def _trace_arguments(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> List[Entry]:
        """
        Partial tracing for the arguments this instruction should accept.
        """

        argument_entries = []

        for argument_type in reversed(self.argument_types):
            argument_type = argument_type.to_verification_type()

            entry, *_ = state.pop(source, argument_type.internal_size, tuple_=True)
            argument_entries.append(entry)

            if not checker.check_merge(argument_type, entry.type):
                errors.append(Error(
                    source, "expected type %s" % argument_type, "got %s (via %s)" % (entry.type, entry.source),
                ))

        return argument_entries


class InvokeVirtualInstruction(InvokeInstruction, ABC):
    """
    An instruction that invokes a virtual method.
    """

    throws = (  # FIXME
        types.abstractmethoderror_t,
        types.incompatibleclasschangeerror_t,
        types.nullpointerexception_t,
        types.unsatisfiedlinkerror_t,
    )

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        argument_entries = self._trace_arguments(source, state, errors, checker)
        entry = state.pop(source)

        if not checker.check_merge(self.class_, entry.type):
            errors.append(Error(
                source, "expected type %s" % self.class_, "got %s (via %s)" % (entry.type, entry.source),
            ))

        if self.return_type != types.void_t:
            state.push(source, self.return_type.to_verification_type(), parents=tuple(argument_entries) + (entry,))


class InvokeSpecialInstruction(InvokeVirtualInstruction, ABC):
    """
    An instruction that is similar to invokevirtual, except it has handling for special methods.
    """

    throws = (
        types.abstractmethoderror_t,
        types.incompatibleclasschangeerror_t,
        types.nullpointerexception_t,
        types.unsatisfiedlinkerror_t,
    )

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        argument_entries = self._trace_arguments(source, state, errors, checker)
        entry = state.pop(source)

        if self.name == "<init>" and self.return_type == types.void_t:
            if entry.type == types.uninit_this_t:
                state.replace(source, entry, This(entry.type.class_), merges=(entry,))
                return
            elif isinstance(entry.type, Uninitialized):  # Unverified code can cause this not to be an uninitialized type
                state.replace(source, entry, entry.type.class_, merges=(entry,))
                return

        if not checker.check_merge(self.class_, entry.type):
            errors.append(Error(
                source, "expected type %s" % self.class_, "got %s (via %s)" % (entry.type, entry.source),
            ))

        if self.return_type != types.void_t:
            state.push(source, self.return_type.to_verification_type(), parents=(*argument_entries, entry))


class InvokeStaticInstruction(InvokeInstruction, ABC):
    """
    An instruction that invokes a static method.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        argument_entries = self._trace_arguments(source, state, errors, checker)
        if self.return_type != types.void_t:
            state.push(source, self.return_type.to_verification_type(), parents=tuple(argument_entries))


class InvokeInterfaceInstruction(InvokeVirtualInstruction, ABC):
    """
    An instruction that invokes an interface method.
    """

    throws = (
        types.abstractmethoderror_t,
        types.illegalaccesserror_t,
        types.incompatibleclasschangeerror_t,
        types.nullpointerexception_t,
        types.unsatisfiedlinkerror_t,
    )

    def __init__(
            self,
            class_: Union[ReferenceType, Class, Class_, str],
            name: str,
            *descriptor: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
            count: int = 0,
    ) -> None:
        super().__init__(class_, name, *descriptor)

        self.count = count

    def copy(self) -> "InvokeInterfaceInstruction":
        return self.__class__(self.class_, self.name, self.argument_types, self.return_type, count=self.count)

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if isinstance(self.class_, ClassOrInterfaceType):
            class_ = Class_(self.class_.name)
        else:
            class_ = Class_(descriptor.to_descriptor(self.class_))
        method_ref = InterfaceMethodRef(
            class_, NameAndType(self.name, descriptor.to_descriptor(self.argument_types, self.return_type)),
        )
        self._index = class_file.constant_pool.add(method_ref)

        Instruction.write(self, class_file, buffer, wide)


class InvokeDynamicInstruction(InvokeStaticInstruction, ABC):
    """
    An instruction that invokes a dynamically computed callsite.
    """

    __slots__ = ("bootstrap_method_attr_index",)

    def __init__(
            self,
            bootstrap_method_attr_index: int,
            name: str,
            *descriptor: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
    ) -> None:
        """
        :param bootstrap_method_attr_index: The index in the bootstrap methods attribute this invokedynamic refers to.
        """

        self.bootstrap_method_attr_index = bootstrap_method_attr_index
        self.name = name
        self.argument_types, self.return_type = _argument.get_method_descriptor(*descriptor)

    def __repr__(self) -> str:
        # Ugly, but whatever
        return "<InvokeDynamicInstruction(opcode=0x%x, mnemonic=%s, bootstrap_method_attr_index=%i, name=%r, argument_types=(%s), return_type=%s) at %x>" % (
            self.opcode, self.mnemonic, self.bootstrap_method_attr_index, self.name, 
            ", ".join(map(str, self.argument_types)) + ("," if len(self.argument_types) == 1 else ""),
            self.return_type, id(self),
        )

    def __str__(self) -> str:
        return "%s index %i %s %s(%s)" % (
            self.mnemonic, self.bootstrap_method_attr_index, self.return_type, self.name, ", ".join(map(str, self.argument_types)),
        )

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, MetaInstruction) and other == self.__class__) or (
            other.__class__ == self.__class__ and
            other.bootstrap_method_attr_index == self.bootstrap_method_attr_index and
            other.name == self.name and
            other.argument_types == self.argument_types and
            other.return_type == self.return_type
        )

    def copy(self) -> "InvokeDynamicInstruction":
        return self.__class__(self.bootstrap_method_attr_index, self.name, self.argument_types, self.return_type)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        Instruction.read(self, class_file, buffer, wide)

        invoke_dynamic = class_file.constant_pool[self._index]

        self.bootstrap_method_attr_index = invoke_dynamic.bootstrap_method_attr_index
        self.name = invoke_dynamic.name_and_type.name
        self.argument_types, self.return_type = descriptor.parse_method_descriptor(invoke_dynamic.name_and_type.descriptor)

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        invoke_dynamic = InvokeDynamic(
            self.bootstrap_method_attr_index,
            NameAndType(self.name, descriptor.to_descriptor(self.argument_types, self.return_type)),
        )
        self._index = class_file.constant_pool.add(invoke_dynamic)

        Instruction.write(self, class_file, buffer, wide)
