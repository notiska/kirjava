#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "invokevirtual", "invokespecial", "invokestatic", "invokeinterface", "invokedynamic",
    "InvokeVirtual", "InvokeSpecial", "InvokeStatic", "InvokeInterface", "InvokeDynamic",
)

import typing
from copy import deepcopy
from typing import IO

from . import Instruction
# from .stack import New
# from .._desc import parse_method_descriptor
from .._struct import *
from ..._compat import Self
from ...model.types import error_t, throwable_t
# from ...model.types import *
# from ...model.values.constants import Null

if typing.TYPE_CHECKING:
    # from ..analyse.frame import Frame
    # from ..analyse.state import State
    from ..fmt import ConstInfo, ConstPool
    # from ..verify import Verifier


# TODO: Go easier on the assertions here. There's stuff that could be recorded in the metadata.

class InvokeVirtual(Instruction):
    """
    An `invokevirtual` instruction.

    Invokes a virtual method on an object.

    Attributes
    ----------
    methodref: ConstInfo
        A method reference constant, used as the method to invoke.
    """

    __slots__ = ("methodref",)

    lt_throws = frozenset({error_t})
    rt_throws = frozenset({throwable_t})

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, methodref: "ConstInfo") -> None:
        super().__init__()
        self.methodref = methodref

    def __copy__(self) -> "InvokeVirtual":
        copied = invokevirtual(self.methodref)
        copied.offset = self.offset
        return copied

    def __deepcopy__(self, memo: dict[int, object]) -> "InvokeVirtual":
        copied = invokevirtual(deepcopy(self.methodref, memo))
        copied.offset = self.offset
        return copied

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<InvokeVirtual(offset={self.offset}, methodref={self.methodref!s})>"
        return f"<InvokeVirtual(methodref={self.methodref!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:invokevirtual({self.methodref!s})"
        return f"invokevirtual({self.methodref!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, InvokeVirtual) and self.methodref == other.methodref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.methodref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.ref, MethodrefInfo):
    #         verifier.report("ref is not a method ref constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     assert isinstance(self.ref.class_index.info, ClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     assert isinstance(self.ref.name_and_type_index.info, NameAndTypeInfo), "invalid name and type info %r" % self.ref.name_and_type_index.info
    #     class_type = self.ref.class_index.info.unwrap().as_rtype()
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     arguments = []
    #     for argument_type in reversed(argument_types):
    #         argument = frame.pop(argument_type, self)
    #         arguments.append(argument)
    #         if isinstance(argument_type, Reference):
    #             argument.escapes.add(self)
    #
    #     instance = frame.pop(class_type, self)
    #     if isinstance(instance.value, Null) or instance.type is null_t:
    #         if frame.throw(Class("java/lang/NullPointerException"), self):
    #             return state.step(self, (instance, *arguments))
    #
    #     if return_type is void_t:
    #         return state.step(self, (instance, *arguments))
    #
    #     result = frame.push(return_type, self)
    #     if isinstance(return_type, Reference):
    #         result.constrain(null_t, self)
    #         result.escapes.add(self)
    #     return state.step(self, (instance, *arguments), result)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     class_ = self.ref.class_index.info.unwrap()
    #     name = self.ref.name_and_type_index.info.name_index
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     ref = Invoke.Ref(class_, name, argument_types, return_type)
    #
    #     variable = None
    #     if step.output:
    #         variable = codegen.variable(step.output.type)
    #         step.output.value = variable
    #     instance = codegen.value(step.inputs[0])
    #     arguments = tuple(map(codegen.value, reversed(step.inputs[1:])))
    #     codegen.emit(Invoke(step, variable, ref, instance, arguments))


class InvokeSpecial(Instruction):
    """
    An `invokespecial` instruction.

    Invokes object constructors or directly invokes superclass methods of an object.

    Attributes
    ----------
    methodref: ConstInfo
        A method reference constant, used as the method to invoke.
    """

    __slots__ = ("methodref",)

    lt_throws = frozenset({error_t})
    rt_throws = frozenset({throwable_t})

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, methodref: "ConstInfo") -> None:
        super().__init__()
        self.methodref = methodref

    def __copy__(self) -> "InvokeSpecial":
        copied = invokespecial(self.methodref)
        copied.offset = self.offset
        return copied

    def __deepcopy__(self, memo: dict[int, object]) -> "InvokeSpecial":
        copied = invokespecial(deepcopy(self.methodref, memo))
        copied.offset = self.offset
        return copied

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<InvokeSpecial(offset={self.offset}, methodref={self.methodref!s})>"
        return f"<InvokeSpecial(methodref={self.methodref!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:invokespecial({self.methodref!s})"
        return f"invokespecial({self.methodref!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, InvokeSpecial) and self.methodref == other.methodref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.methodref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.ref, (MethodrefInfo, InterfaceMethodrefInfo)):
    #         verifier.report("ref is not a method ref or interface method ref constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     assert isinstance(self.ref.name_and_type_index.info, ConstantNameAndTypeInfo), "invalid name and type info %r" % self.ref.name_and_type_index.info
    #     class_type = self.ref.class_index.info.unwrap().as_rtype()
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     arguments = []
    #     for argument_type in reversed(argument_types):
    #         argument = frame.pop(argument_type, self)
    #         arguments.append(argument)
    #         if isinstance(argument_type, Reference):
    #             argument.escapes.add(self)
    #
    #     if str(self.ref.name_and_type_index.info.name_index) != "<init>" or return_type is not void_t:
    #         instance = frame.pop(class_type, self)
    #         if isinstance(instance.value, Null) or instance.type is null_t:
    #             if frame.throw(Class("java/lang/NullPointerException"), self):
    #                 return state.step(self, (instance, *arguments))
    #
    #         if return_type is void_t:
    #             return state.step(self, (instance, *arguments))
    #
    #         result = frame.push(return_type, self)
    #         if isinstance(return_type, Reference):
    #             result.constrain(null_t, self)
    #             result.escapes.add(self)
    #         return state.step(self, (instance, *arguments), result)
    #
    #     uninit = frame.pop(reference_t, self)
    #     if isinstance(uninit.value, Null) or uninit.type is null_t:
    #         if frame.throw(Class("java/lang/NullPointerException"), self):
    #             return state.step(self, (uninit, *arguments))
    #
    #     if uninit.type is uninitialized_this_t:
    #         instance = frame.replace(uninit, frame.class_.as_ctype())
    #     elif isinstance(uninit.type, Uninitialized):
    #         assert isinstance(uninit.type.source, New), "uninitialised type from unknown source %r" % uninit.type.source
    #         instance = frame.replace(uninit, uninit.type.source.class_.unwrap().as_rtype(), self)
    #     else:
    #         raise NotImplementedError("%r doesn't know how to handle %r" % (self, uninit))
    #
    #     return state.step(self, (uninit, *arguments), instance)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     class_ = self.ref.class_index.info.unwrap()
    #     name = self.ref.name_and_type_index.info.name_index
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     ref = Invoke.Ref(class_, name, argument_types, return_type)
    #
    #     variable = None
    #     if step.output:
    #         variable = codegen.variable(step.output.type)
    #         step.output.value = variable
    #     instance = codegen.value(step.inputs[0])
    #     arguments = tuple(map(codegen.value, reversed(step.inputs[1:])))
    #     codegen.emit(Invoke(step, variable, ref, instance, arguments))


class InvokeStatic(Instruction):
    """
    An `invokestatic` instruction.

    Invokes a static method.

    Attributes
    ----------
    methodref: ConstInfo
        A method reference constant, used as the method to invoke.
    """

    __slots__ = ("methodref",)

    lt_throws = frozenset({error_t})
    rt_throws = frozenset({throwable_t})

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, methodref: "ConstInfo") -> None:
        super().__init__()
        self.methodref = methodref

    def __copy__(self) -> "InvokeStatic":
        copied = invokestatic(self.methodref)
        copied.offset = self.offset
        return copied

    def __deepcopy__(self, memo: dict[int, object]) -> "InvokeStatic":
        copied = invokestatic(deepcopy(self.methodref, memo))
        copied.offset = self.offset
        return copied

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<InvokeStatic(offset={self.offset}, methodref={self.methodref!s})>"
        return f"<InvokeStatic(methodref={self.methodref!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:invokestatic({self.methodref!s})"
        return f"invokestatic({self.methodref!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, InvokeStatic) and self.methodref == other.methodref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.methodref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.ref, MethodrefInfo):
    #         verifier.report("ref is not a method ref constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     assert isinstance(self.ref.name_and_type_index.info, ConstantNameAndTypeInfo), "invalid name and type info %r" % self.ref.name_and_type_index.info
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     arguments = []
    #     for argument_type in reversed(argument_types):
    #         argument = frame.pop(argument_type, self)
    #         arguments.append(argument)
    #         if isinstance(argument_type, Reference):
    #             argument.escapes.add(self)
    #
    #     if return_type is void_t:
    #         return state.step(self, tuple(arguments))
    #
    #     result = frame.push(return_type, self)
    #     if isinstance(return_type, Reference):
    #         result.constrain(null_t, self)
    #         result.escapes.add(self)
    #     return state.step(self, tuple(arguments), result)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     class_ = self.ref.class_index.info.unwrap()
    #     name = self.ref.name_and_type_index.info.name_index
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     ref = Invoke.Ref(class_, name, argument_types, return_type)
    #
    #     variable = None
    #     if step.output:
    #         variable = codegen.variable(step.output.type)
    #         step.output.value = variable
    #     codegen.emit(Invoke(step, variable, ref, class_, tuple(map(codegen.value, reversed(step.inputs)))))


class InvokeInterface(Instruction):
    """
    An `invokeinterface` instruction.

    Invokes an interface method.

    Attributes
    ----------
    methodref: ConstInfo
        An interface method reference constant, used as the method to invoke.
    count: int
        The number of arguments to the method.
    reserved: int
        A reserved byte, should be 0.
    """

    __slots__ = ("methodref", "count", "reserved")

    lt_throws = frozenset({error_t})
    rt_throws = frozenset({throwable_t})

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, count, reserved = unpack_HBB(stream.read(4))
        return cls(pool[index], count, reserved)

    def __init__(self, methodref: "ConstInfo", count: int, reserved: int) -> None:
        super().__init__()
        self.methodref = methodref
        self.count = count
        self.reserved = reserved

    def __copy__(self) -> "InvokeInterface":
        copied = invokeinterface(self.methodref, self.count, self.reserved)
        copied.offset = self.offset
        return copied

    def __deepcopy__(self, memo: dict[int, object]) -> "InvokeInterface":
        copied = invokeinterface(deepcopy(self.methodref, memo), self.count, self.reserved)
        copied.offset = self.offset
        return copied

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<InvokeInterface(offset={self.offset}, methodref={self.methodref!s}, count={self.count})>"
        return f"<InvokeInterface(methodref={self.methodref!s}, count={self.count})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:invokeinterface({self.methodref!s},{self.count})"
        return f"invokeinterface({self.methodref!s},{self.count})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, InvokeInterface) and
            self.methodref == other.methodref and
            self.count == other.count and
            self.reserved == other.reserved
        )

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHBB(self.opcode, pool.add(self.methodref), self.count, self.reserved))

    # def verify(self, verifier: "Verifier") -> None:
    #     # TODO: Verify count is equal to argument size.
    #     if verifier.check_const_types and not isinstance(self.ref, InterfaceMethodrefInfo):
    #         verifier.report("ref is not an interface method ref", instruction=self)
    #     if not (0 <= self.count <= 255):
    #         verifier.report("invalid count", instruction=self)
    #     if not (0 <= self.reserved <= 255):
    #         verifier.report("invalid reserved field", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     assert isinstance(self.ref.name_and_type_index.info, ConstantNameAndTypeInfo), "invalid name and type info %r" % self.ref.name_and_type_index.info
    #     class_type = self.ref.class_index.info.unwrap().as_rtype()
    #     assert isinstance(class_type, Class), "invalid class type %r" % class_type
    #     class_type = class_type.as_interface()
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     arguments = []
    #     for argument_type in reversed(argument_types):
    #         argument = frame.pop(argument_type, self)
    #         arguments.append(argument)
    #         if isinstance(argument_type, Reference):
    #             argument.escapes.add(self)
    #
    #     # We don't need to specifically check if this entry actually has the correct superinterface here. Instead, we'll
    #     # add it as a type hint. This can be refined later on.
    #     instance = frame.pop(reference_t, self)
    #     instance.hint(class_type, self)
    #     if isinstance(instance.value, Null) or instance.type is null_t:
    #         if frame.throw(Class("java/lang/NullPointerException"), self):
    #             return state.step(self, (instance, *arguments))
    #
    #     if return_type is void_t:
    #         return state.step(self, (instance, *arguments))
    #
    #     result = frame.push(return_type, self)
    #     if isinstance(return_type, Reference):
    #         result.constrain(null_t)
    #         result.escapes.add(self)
    #     return state.step(self, (instance, *arguments), result)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     class_ = self.ref.class_index.info.unwrap()
    #     name = self.ref.name_and_type_index.info.name_index
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     ref = Invoke.Ref(class_, name, argument_types, return_type)
    #
    #     variable = None
    #     if step.output:
    #         variable = codegen.variable(step.output.type)
    #         step.output.value = variable
    #     instance = codegen.value(step.inputs[0])
    #     arguments = tuple(map(codegen.value, reversed(step.inputs[1:])))
    #     codegen.emit(Invoke(step, variable, ref, instance, arguments))


class InvokeDynamic(Instruction):
    """
    An `invokedynamic` instruction.

    Invokes a dynamically computed callsite.

    Attributes
    ----------
    indyref: ConstInfo
        An invoke dynamic constant, used as the method to invoke in order to compute
        the callsite.
    reserved: int
        Two reserved bytes, should be 0.
    """

    __slots__ = ("indyref", "reserved")

    lt_throws = frozenset({error_t})
    rt_throws = frozenset({throwable_t})

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, reserved = unpack_HH(stream.read(4))
        return cls(pool[index], reserved)

    def __init__(self, indyref: "ConstInfo", reserved: int) -> None:
        super().__init__()
        self.indyref = indyref
        self.reserved = reserved

    def __copy__(self) -> "InvokeDynamic":
        copied = invokedynamic(self.indyref, self.reserved)
        copied.offset = self.offset
        return copied

    def __deepcopy__(self, memo: dict[int, object]) -> "InvokeDynamic":
        copied = invokedynamic(deepcopy(self.indyref, memo), self.reserved)
        copied.offset = self.offset
        return copied

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<InvokeDynamic(offset={self.offset}, indyref={self.indyref!s})>"
        return f"<InvokeDynamic(indyref={self.indyref!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:invokedynamic({self.indyref!s})"
        return f"invokedynamic({self.indyref!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, InvokeDynamic) and self.indyref == other.indyref and self.reserved == other.reserved

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(self.opcode, pool.add(self.indyref), self.reserved))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.ref, InvokeDynamicInfo):
    #         verifier.report("ref is not an invoke dynamic constant", instruction=self)
    #     if not (0 <= self.reserved <= 65535):
    #         verifier.report("invalid reserved field", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     assert isinstance(self.ref.name_and_type_index.info, ConstantNameAndTypeInfo), "invalid name and type info %r" % self.ref.name_and_type_index.info
    #     # FIXME: May need to do more on this later in the future?
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     arguments = []
    #     for argument_type in reversed(argument_types):
    #         argument = frame.pop(argument_type, self)
    #         arguments.append(argument)
    #         if isinstance(argument_type, Reference):
    #             argument.escapes.add(self)
    #
    #     if return_type is void_t:
    #         return state.step(self, tuple(arguments))
    #
    #     result = frame.push(return_type, self)
    #     if isinstance(return_type, Reference):
    #         result.constrain(null_t, self)
    #         result.escapes.add(self)
    #     return state.step(self, tuple(arguments), result)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     class_ = self.ref.class_index.info.unwrap()
    #     name = self.ref.name_and_type_index.info.name_index
    #     argument_types, return_type = parse_method_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     ref = Invoke.Ref(class_, name, argument_types, return_type)
    #
    #     variable = None
    #     if step.output:
    #         variable = codegen.variable(step.output.type)
    #         step.output.value = variable
    #     codegen.emit(Invoke(step, variable, ref, class_, tuple(map(codegen.value, reversed(step.inputs)))))


invokevirtual     = InvokeVirtual.make(0xb6, "invokevirtual")
invokespecial     = InvokeSpecial.make(0xb7, "invokespecial")
invokestatic       = InvokeStatic.make(0xb8, "invokestatic")
invokeinterface = InvokeInterface.make(0xb9, "invokeinterface")
invokedynamic     = InvokeDynamic.make(0xba, "invokedynamic")
