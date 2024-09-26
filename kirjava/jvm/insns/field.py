#!/usr/bin/env python3

__all__ = (
    "getstatic", "putstatic", "getfield", "putfield",
    "GetStatic", "PutStatic", "GetField", "PutField",
)

import typing
from typing import IO

from . import Instruction
# from .._desc import parse_field_descriptor
from .._struct import *
from ..fmt.constants import ClassInfo, ConstInfo, FieldrefInfo, NameAndTypeInfo
# from ...model.types import *
# from ...model.values.constants import Null

if typing.TYPE_CHECKING:
    # from ..analyse.frame import Frame
    # from ..analyse.state import State
    from ..fmt import ConstPool
    # from ..verify import Verifier


class GetStatic(Instruction):
    """
    A `getstatic` instruction.

    Gets the value of a static field in a class.

    Attributes
    ----------
    ref: ConstInfo
        A field reference constant, used as the static field to get.
    """

    __slots__ = ("ref",)

    throws = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "GetStatic":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, ref: ConstInfo) -> None:
        super().__init__()
        self.ref = ref

    def __repr__(self) -> str:
        return "<GetStatic(offset=%s, ref=%s)>" % (self.offset, self.ref)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: getstatic %s" % (self.offset, self.ref)
        return "getstatic %s" % self.ref

    def __eq__(self, other: object) -> bool:
        return isinstance(other, GetStatic) and self.ref == other.ref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.ref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.ref, FieldrefInfo):
    #         verifier.report("ref is not a field ref constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     assert isinstance(self.ref.name_and_type_index.info, ConstantNameAndTypeInfo), "invalid name and type info %r" % self.ref.name_and_type_index.info
    #     field_type = parse_field_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     result = frame.push(field_type, self)
    #     if isinstance(field_type, Reference):
    #         result.constrain(null_t, self)
    #         result.escapes.add(self)
    #
    #     return state.step(self, (), result)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #
    #     class_ = self.ref.class_index.info.unwrap()
    #     name = str(self.ref.name_and_type_index.info.name_index.info)
    #     field_type = parse_field_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     variable = codegen.variable(field_type)
    #     step.output.value = variable
    #     codegen.emit(IRGetField(step, variable, IRGetField.Ref(class_, name, field_type), class_))


class PutStatic(Instruction):
    """
    A `putstatic` instruction.

    Sets the value of a static field in a class.

    Attributes
    ----------
    ref: ConstInfo
        A field reference constant, used as the static field to set.
    """

    __slots__ = ("ref",)

    throws = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "PutStatic":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, ref: ConstInfo) -> None:
        super().__init__()
        self.ref = ref

    def __repr__(self) -> str:
        return "<PutStatic(offset=%s, ref=%s)>" % (self.offset, self.ref)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: putstatic %s" % (self.offset, self.ref)
        return "putstatic %s" % self.ref

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PutStatic) and self.ref == other.ref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.ref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.ref, FieldrefInfo):
    #         verifier.report("ref is not a field ref constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     assert isinstance(self.ref.name_and_type_index.info, ConstantNameAndTypeInfo), "invalid name and type info %r" % self.ref.name_and_type_index.info
    #     field_type = parse_field_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     value = frame.pop(field_type, self)
    #     if isinstance(field_type, Reference):
    #         value.escapes.add(self)
    #
    #     return state.step(self, (value,))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #
    #     class_ = self.ref.class_index.info.unwrap()
    #     name = str(self.ref.name_and_type_index.info.name_index.info)
    #     field_type = parse_field_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     value = codegen.value(step.inputs[0])
    #     codegen.emit(SetField(step, SetField.Ref(class_, name, field_type), class_, value))


class GetField(Instruction):
    """
    A `getfield` instruction.

    Gets the value of a field in an object.

    Attributes
    ----------
    ref: ConstInfo
        A field reference constant, used as the field to get.
    """

    __slots__ = ("ref",)

    throws = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "GetField":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, ref: ConstInfo) -> None:
        super().__init__()
        self.ref = ref

    def __repr__(self) -> str:
        return "<GetField(offset=%s, ref=%s)>" % (self.offset, self.ref)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: getfield %s" % (self.offset, self.ref)
        return "getfield %s" % self.ref

    def __eq__(self, other: object) -> bool:
        return isinstance(other, GetField) and self.ref == other.ref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.ref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.ref, FieldrefInfo):
    #         verifier.report("ref is not a field ref constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     assert isinstance(self.ref.name_and_type_index.info, ConstantNameAndTypeInfo), "invalid name and type info %r" % self.ref.name_and_type_index.info
    #     class_type = self.ref.class_index.info.unwrap().as_rtype()
    #     field_type = parse_field_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     instance = frame.pop(class_type, self)
    #     if isinstance(instance.value, Null) or instance.type is null_t:
    #         if frame.throw(Class("java/lang/NullPointerException"), self):
    #             return state.step(self, (instance,))
    #
    #     result = frame.push(field_type, self)
    #     if isinstance(field_type, Reference):
    #         result.constrain(null_t, self)
    #         result.escapes.add(self)
    #
    #     return state.step(self, (instance,), result)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #
    #     class_ = self.ref.class_index.info.unwrap()
    #     name = str(self.ref.name_and_type_index.info.name_index.info)
    #     field_type = parse_field_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     variable = codegen.variable(field_type)
    #     step.output.value = variable
    #     instance = codegen.value(step.inputs[0])
    #     codegen.emit(IRGetField(step, variable, IRGetField.Ref(class_, name, field_type), instance))


class PutField(Instruction):
    """
    A `putfield` instruction.

    Sets the value of a field in an object.

    Attributes
    ----------
    ref: ConstInfo
        A field reference constant, used as the field to set.
    """

    __slots__ = ("ref",)

    throws = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "PutField":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, ref: ConstInfo) -> None:
        super().__init__()
        self.ref = ref

    def __repr__(self) -> str:
        return "<PutField(offset=%s, ref=%s)>" % (self.offset, self.ref)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: putfield %s" % (self.offset, self.ref)
        return "putfield %s" % self.ref

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PutField) and self.ref == other.ref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.ref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.ref, FieldrefInfo):
    #         verifier.report("ref is not a field ref constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #     assert isinstance(self.ref.name_and_type_index.info, ConstantNameAndTypeInfo), "invalid name and type info %r" % self.ref.name_and_type_index.info
    #     class_type = self.ref.class_index.info.unwrap().as_rtype()
    #     field_type = parse_field_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     value = frame.pop(field_type, self)
    #     if isinstance(field_type, Reference):
    #         value.escapes.add(self)
    #
    #     instance = frame.pop(reference_t, self)
    #     if isinstance(instance.value, Null) or instance.type is null_t:
    #         if frame.throw(Class("java/lang/NullPointerException"), self):
    #             return frame.step(self, (instance, value))
    #     # JVM allows you to set field on an uninitializedThis type so long as they are not fields on the supertype, so
    #     # we need to account for this here.
    #     elif instance.type is not uninitialized_this_t:
    #         instance.constrain(class_type, self)
    #
    #     return state.step(self, (instance, value))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     assert isinstance(self.ref.class_index.info, ConstantClassInfo), "invalid class info %r" % self.ref.class_index.info
    #
    #     class_ = self.ref.class_index.info.unwrap()
    #     name = str(self.ref.name_and_type_index.info.name_index.info)
    #     field_type = parse_field_descriptor(str(self.ref.name_and_type_index.info.descriptor_index))
    #
    #     instance = codegen.value(step.inputs[0])
    #     value = codegen.value(step.inputs[1])
    #     codegen.emit(SetField(step, SetField.Ref(class_, name, field_type), instance, value))


getstatic = GetStatic.make(0xb2, "getstatic")
putstatic = PutStatic.make(0xb3, "putstatic")
getfield   = GetField.make(0xb4, "getfield")
putfield   = PutField.make(0xb5, "putfield")
