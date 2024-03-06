#!/usr/bin/env python3

__all__ = (
    "arithmetic", "array", "constant", "conversion", "field", "flow", "invoke", "local", "new", "other", "stack",
    "nop",
    "aconst_null",
    "iconst_m1", "iconst_0", "iconst_1", "iconst_2", "iconst_3", "iconst_4", "iconst_5",
    "lconst_0", "lconst_1",
    "fconst_0", "fconst_1", "fconst_2",
    "dconst_0", "dconst_1",
    "bipush", "sipush", "ldc", "ldc_w", "ldc2_w",
    "iload", "lload", "fload", "dload", "aload",
    "iload_0", "iload_1", "iload_2", "iload_3",
    "lload_0", "lload_1", "lload_2", "lload_3",
    "fload_0", "fload_1", "fload_2", "fload_3",
    "dload_0", "dload_1", "dload_2", "dload_3",
    "aload_0", "aload_1", "aload_2", "aload_3",
    "iaload", "laload", "faload", "daload", "aaload", "baload", "caload", "saload",
    "istore", "lstore", "fstore", "dstore", "astore",
    "istore_0", "istore_1", "istore_2", "istore_3",
    "lstore_0", "lstore_1", "lstore_2", "lstore_3",
    "fstore_0", "fstore_1", "fstore_2", "fstore_3",
    "dstore_0", "dstore_1", "dstore_2", "dstore_3",
    "astore_0", "astore_1", "astore_2", "astore_3",
    "iastore", "lastore", "fastore", "dastore", "aastore", "bastore", "castore", "sastore",
    "pop", "pop2", "dup", "dup_x1", "dup_x2", "dup2", "dup2_x1", "dup2_x2", "swap",
    "iadd", "ladd", "fadd", "dadd",
    "isub", "lsub", "fsub", "dsub",
    "imul", "lmul", "fmul", "dmul",
    "idiv", "ldiv", "fdiv", "ddiv",
    "irem", "lrem", "frem", "drem",
    "ineg", "lneg", "fneg", "dneg",
    "ishl", "lshl",
    "ishr", "lshr",
    "iushr", "lushr",
    "iand", "land",
    "ior", "lor",
    "ixor", "lxor",
    "i2l", "i2f", "i2d",
    "l2i", "l2f", "l2d",
    "f2i", "f2l", "f2d",
    "d2i", "d2l", "d2f",
    "i2b", "i2c", "i2s",
    "lcmp", "fcmpl", "fcmpg", "dcmpl", "dcmpg",
    "ifeq", "ifne", "iflt", "ifge", "ifgt", "ifle",
    "if_icmpeq", "if_icmpne", "if_icmplt", "if_icmpge", "if_icmpgt", "if_icmple",
    "if_acmpeq", "if_acmpne", "ifnull", "ifnonnull",
    "goto", "goto_w", "jsr", "jsr_w", "ret", "tableswitch", "lookupswitch",
    "ireturn", "lreturn", "freturn", "dreturn", "areturn", "return_",
    "getstatic", "putstatic", "getfield", "putfield",
    "invokevirtual", "invokespecial", "invokestatic", "invokeinterface", "invokedynamic",
    "new", "newarray", "anewarray", "multianewarray",
    "iinc",
    "arraylength",
    "athrow",
    "checkcast", "instanceof",
    "monitorenter", "monitorexit",
    "wide",
    "breakpoint_", "impdep1", "impdep2",

    "Instruction",

    "UnaryOperationInstruction", "BinaryOperationInstruction", "ComparisonInstruction",
    "AdditionInstruction", "SubtractionInstruction", "MultiplicationInstruction", "DivisionInstruction", "RemainderInstruction",
    "NegationInstruction",
    "ShiftLeftInstruction", "ShiftRightInstruction", "UnsignedShiftRightInstruction",
    "BitwiseAndInstruction", "BitwiseOrInstruction", "BitwiseXorInstruction",

    "ArrayLoadInstruction", "ArrayStoreInstruction", "ArrayLengthInstruction",

    "ConstantInstruction", "FixedConstantInstruction", "IntegerConstantInstruction", "LoadConstantInstruction",

    "ConversionInstruction", "TruncationInstruction", "CheckCastInstruction", "InstanceOfInstruction",

    "FieldInstruction", "GetFieldInstruction", "PutFieldInstruction",

    "JumpInstruction", "SwitchInstruction",
    "ConditionalJumpInstruction",
    "UnaryComparisonJumpInstruction", "BinaryComparisonJumpInstruction",
    "JsrInstruction", "RetInstruction",
    "TableSwitchInstruction", "LookupSwitchInstruction",

    "InvokeInstruction",
    "InvokeVirtualInstruction", "InvokeSpecialInstruction", "InvokeInterfaceInstruction",
    "InvokeStaticInstruction",
    "InvokeDynamicInstruction",

    "LoadLocalInstruction", "LoadLocalFixedInstruction",
    "StoreLocalInstruction", "StoreLocalFixedInstruction",
    "IncrementLocalInstruction",

    "NewInstruction", "NewArrayInstruction", "ANewArrayInstruction", "MultiANewArrayInstruction",

    "ReturnInstruction", "AThrowInstruction",
    "MonitorEnterInstruction", "MonitorExitInstruction",

    "PopInstruction", "Pop2Instruction",
    "DupInstruction", "DupX1Instruction", "DupX2Instruction",
    "Dup2Instruction", "Dup2X1Instruction", "Dup2X2Instruction",
    "SwapInstruction",
)

"""
JVM instructions.
"""

import struct
import typing
from typing import Any, Callable, IO

from .. import types
from ..abc import Source
from ..constants import Double, Float, Integer, Long, Null
from ..types import Array, Class

if typing.TYPE_CHECKING:
    from ..analysis import Context, Delta
    from ..classfile import ClassFile


class Instruction(Source):
    """
    A (somewhat abstracted) JVM instruction.
    """

    __slots__ = ()

    opcode: int = ...
    mnemonic: str = ...

    operands:      dict[str, str] = {}
    operands_wide: dict[str, str] = {}

    throws: tuple[Class, ...] = ()

    # Hidden attributes, so PyCharm doesn't complain.
    _operands: tuple[list[tuple[str, int, Callable, Callable]], ...]
    _hash: int
    _size: tuple[int, int]

    _cache: dict[type["Instruction"], "Instruction"] = {}

    def __new__(cls, *args: Any, **kwargs: Any) -> "Instruction":
        if args or kwargs:
            return super().__new__(cls)
        return cls._cache.get(cls) or super().__new__(cls)

    def __repr__(self) -> str:
        return "<Instruction(opcode=0x%x, mnemonic=%s) at %x>" % (self.opcode, self.mnemonic, id(self))

    def __str__(self) -> str:
        return self.mnemonic

    def __eq__(self, other: Any) -> bool:
        return other is self or type(other) is type(self) or other is type(self)

    def __hash__(self) -> int:
        return self._hash  # hash((self.opcode, self.mnemonic))

    def copy(self) -> "Instruction":
        """
        Creates a copy of this instruction.

        :return: The copied instruction.
        """

        # instruction = self.__class__.__new__(self.__class__)
        # for operand in self.operands:
        #     if hasattr(self, operand):
        #         setattr(instruction, operand, getattr(self, operand))
        # return instruction

        return self  # Assume immutable if not overriden

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        """
        Reads the data from the buffer into this instruction's operands.

        :param class_file: The classfile that this instruction belongs to.
        :param buffer: The binary buffer to read from.
        :param wide: Should we be reading this instruction as if it were wide?
        """

        # if wide and not self.operands_wide:
        #     raise Exception("%r cannot be read wide." % self)

        for name, size, unpack, _ in self._operands[wide]:
            value, = unpack(buffer.read(size))
            setattr(self, name, value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        """
        Writes the operands from this instruction into the buffer.

        :param class_file: The classfile that this instruction belongs to.
        :param buffer: The binary buffer to write to.
        :param wide: Should we be writing this instruction as if it were wide?
        """

        # if wide and not self.operands_wide:
        #     raise Exception("%r cannot be written wide." % self)

        for name, _, _, pack in self._operands[wide]:
            buffer.write(pack(getattr(self, name, 0)))  # Assume default as 0

    def get_size(self, offset: int, wide: bool) -> int:
        """
        Gets the size of an instruction as if it were about to be written.

        :param offset: The offset that this instruction will be written at.
        :param wide: Will the instruction be written wide?
        :return: The size of the instruction.
        """

        return self._size[wide]

    # @abstractmethod
    def trace(self, context: "Context") -> "Delta":
        """
        Steps through this instruction (for stackmap frame generation and verification purposes).

        :param context: Trace context.
        :return: The frame delta this instruction produced.
        """

        ...

    # @abstractmethod
    # def lift(self, delta: "FrameDelta", scope: "Scope", associations: dict["Entry", Value]) -> Statement | None:
    #     """
    #     Generates IR code from this instruction.
    #
    #     :param delta: The frame delta this instruction produced when traced.
    #     :param scope: The current scope to declare variables in.
    #     :param associations: The associations between stack entries and IR values.
    #     :return: The generated IR statement, or None if there was no effect.
    #     """
    #
    #     ...


class _ReservedInstruction(Instruction):
    """
    An instruction used for use inside the library, in order to indicate certain things.
    """

    opcode = -1
    mnemonic = "__reserved"

    __slots__ = ()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise Exception("Cannot create an instance of a reserved instruction.")

    def __repr__(self) -> str:
        return "<ReservedInstruction(opcode=0x%x, mnemonic=%s) at %x>" % (self.opcode, self.mnemonic, id(self))

    def __str__(self) -> str:
        return self.mnemonic

    def __eq__(self, other: Any) -> bool:
        return other is self or type(other) is type(self) or other is type(self)

    def __hash__(self) -> int:
        return self._hash

    # def copy(self) -> "Instruction":
    #     return self

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        ...

    def get_size(self, offset: int, wide: bool) -> int:
        return 0


def new_instruction(
        opcode: int,
        mnemonic: str,
        base: type[Instruction] | None = None,
        operands: dict[str, str] | None = None,
        operands_wide: dict[str, str] | None = None,
        throws: tuple[Class, ...] | None = None,
        **namespace: object,
) -> type[Instruction]:
    """
    Creates a new instruction with the given information.

    :param opcode: The opcode value.
    :param mnemonic: The opcode mnemonic.
    :param base: The base instruction that this one extends.
    :param operands: Operands and their struct format.
    :param operands_wide: Wide variants of the operands.
    :param throws: Exceptions that this instruction can throw.
    :param namespace: Any extra variables to include in the class' namespace.
    :return: The created instruction class.
    """

    base = base or Instruction

    # namespace["__qualname__"] = mnemonic
    namespace["opcode"]   = opcode
    namespace["mnemonic"] = mnemonic

    namespace["operands"]      = operands or base.operands.copy()
    namespace["operands_wide"] = operands_wide or base.operands_wide.copy()

    namespace["throws"] = throws or base.throws

    if operands is not None:
        namespace["__slots__"] = tuple(operands.keys())

    # Pre-compile the structs for the operands for faster reading/writing

    operand_structs = []
    size = 1  # Starts at 1 to account for the size of the opcode

    for name, format_ in namespace["operands"].items():
        struct_ = struct.Struct(format_)
        operand_structs.append((name, struct_.size, struct_.unpack, struct_.pack))
        size += struct_.size

    if namespace["operands_wide"]:
        operand_structs_wide = []
        size_wide = 1

        for name, format_ in namespace["operands_wide"].items():
            struct_ = struct.Struct(format_)
            operand_structs_wide.append((name, struct_.size, struct_.unpack, struct_.pack))
            size_wide += struct_.size

    else:
        operand_structs_wide = operand_structs
        size_wide = size

    namespace["_operands"] = (operand_structs, operand_structs_wide)
    namespace["_size"] = (size, size_wide)
    namespace["_hash"] = hash((opcode, mnemonic))

    class_ = type(mnemonic, (base,), namespace)
    # If the instruction is immutable, we cache an instance of it to save memory and performance.
    if not class_.operands:
        class_._cache[class_] = class_()
    return class_


# ------------------------------ Instructions ------------------------------ #

from .arithmetic import *
from .array import *
from .constant import *
from .conversion import *
from .field import *
from .flow import *
from .invoke import *
from .local import *
from .new import *
from .other import *
from .stack import *


nop = new_instruction(0x00, "nop")

# ------------------------------ Constants ------------------------------ #

aconst_null = new_instruction(0x01, "aconst_null", FixedConstantInstruction, constant=Null())
# Integer constants
iconst_m1 = new_instruction(0x02, "iconst_m1", FixedConstantInstruction, constant=Integer(-1))
iconst_0 = new_instruction(0x03, "iconst_0", FixedConstantInstruction, constant=Integer(0))
iconst_1 = new_instruction(0x04, "iconst_1", FixedConstantInstruction, constant=Integer(1))
iconst_2 = new_instruction(0x05, "iconst_2", FixedConstantInstruction, constant=Integer(2))
iconst_3 = new_instruction(0x06, "iconst_3", FixedConstantInstruction, constant=Integer(3))
iconst_4 = new_instruction(0x07, "iconst_4", FixedConstantInstruction, constant=Integer(4))
iconst_5 = new_instruction(0x08, "iconst_5", FixedConstantInstruction, constant=Integer(5))
# Long constants
lconst_0 = new_instruction(0x09, "lconst_0", FixedConstantInstruction, constant=Long(0))
lconst_1 = new_instruction(0x0a, "lconst_1", FixedConstantInstruction, constant=Long(1))
# Float constants
fconst_0 = new_instruction(0x0b, "fconst_0", FixedConstantInstruction, constant=Float(0))
fconst_1 = new_instruction(0x0c, "fconst_1", FixedConstantInstruction, constant=Float(1))
fconst_2 = new_instruction(0x0d, "fconst_2", FixedConstantInstruction, constant=Float(2))
# Double constants
dconst_0 = new_instruction(0x0e, "dconst_0", FixedConstantInstruction, constant=Double(0))
dconst_1 = new_instruction(0x0f, "dconst_1", FixedConstantInstruction, constant=Double(1))
# Other constants
bipush = new_instruction(0x10, "bipush", IntegerConstantInstruction, {"_value": ">B"})
sipush = new_instruction(0x11, "sipush", IntegerConstantInstruction, {"_value": ">H"})
ldc = new_instruction(0x12, "ldc", LoadConstantInstruction, {"_index": ">B"})
ldc_w = new_instruction(0x13, "ldc_w", ldc, {"_index": ">H"})
ldc2_w = new_instruction(0x14, "ldc2_w", ldc, {"_index": ">H"}, wide=True)

# ------------------------------ Local loads ------------------------------ #

iload = new_instruction(0x15, "iload", LoadLocalInstruction, type=types.int_t)
lload = new_instruction(0x16, "lload", LoadLocalInstruction, type=types.long_t)
fload = new_instruction(0x17, "fload", LoadLocalInstruction, type=types.float_t)
dload = new_instruction(0x18, "dload", LoadLocalInstruction, type=types.double_t)
aload = new_instruction(0x19, "aload", LoadLocalInstruction, type=types.reference_t)
# Integer specifics
iload_0 = new_instruction(0x1a, "iload_0", LoadLocalFixedInstruction, type=types.int_t, index=0)
iload_1 = new_instruction(0x1b, "iload_1", LoadLocalFixedInstruction, type=types.int_t, index=1)
iload_2 = new_instruction(0x1c, "iload_2", LoadLocalFixedInstruction, type=types.int_t, index=2)
iload_3 = new_instruction(0x1d, "iload_3", LoadLocalFixedInstruction, type=types.int_t, index=3)
# Long specifics
lload_0 = new_instruction(0x1e, "lload_0", LoadLocalFixedInstruction, type=types.long_t, index=0)
lload_1 = new_instruction(0x1f, "lload_1", LoadLocalFixedInstruction, type=types.long_t, index=1)
lload_2 = new_instruction(0x20, "lload_2", LoadLocalFixedInstruction, type=types.long_t, index=2)
lload_3 = new_instruction(0x21, "lload_3", LoadLocalFixedInstruction, type=types.long_t, index=3)
# Float specifics
fload_0 = new_instruction(0x22, "fload_0", LoadLocalFixedInstruction, type=types.float_t, index=0)
fload_1 = new_instruction(0x23, "fload_1", LoadLocalFixedInstruction, type=types.float_t, index=1)
fload_2 = new_instruction(0x24, "fload_2", LoadLocalFixedInstruction, type=types.float_t, index=2)
fload_3 = new_instruction(0x25, "fload_3", LoadLocalFixedInstruction, type=types.float_t, index=3)
# Double specifics
dload_0 = new_instruction(0x26, "dload_0", LoadLocalFixedInstruction, type=types.double_t, index=0)
dload_1 = new_instruction(0x27, "dload_1", LoadLocalFixedInstruction, type=types.double_t, index=1)
dload_2 = new_instruction(0x28, "dload_2", LoadLocalFixedInstruction, type=types.double_t, index=2)
dload_3 = new_instruction(0x29, "dload_3", LoadLocalFixedInstruction, type=types.double_t, index=3)
# Reference specifics
aload_0 = new_instruction(0x2a, "aload_0", LoadLocalFixedInstruction, type=types.reference_t, index=0)
aload_1 = new_instruction(0x2b, "aload_1", LoadLocalFixedInstruction, type=types.reference_t, index=1)
aload_2 = new_instruction(0x2c, "aload_2", LoadLocalFixedInstruction, type=types.reference_t, index=2)
aload_3 = new_instruction(0x2d, "aload_3", LoadLocalFixedInstruction, type=types.reference_t, index=3)

# ------------------------------ Array loads ------------------------------ #

iaload = new_instruction(0x2e, "iaload", ArrayLoadInstruction, type=Array(types.int_t))
laload = new_instruction(0x2f, "laload", ArrayLoadInstruction, type=Array(types.long_t))
faload = new_instruction(0x30, "faload", ArrayLoadInstruction, type=Array(types.float_t))
daload = new_instruction(0x31, "daload", ArrayLoadInstruction, type=Array(types.double_t))
aaload = new_instruction(0x32, "aaload", ArrayLoadInstruction, type=Array(types.object_t))
baload = new_instruction(0x33, "baload", iaload, type=Array(types.byte_t))
caload = new_instruction(0x34, "caload", iaload, type=Array(types.char_t))
saload = new_instruction(0x35, "saload", iaload, type=Array(types.short_t))

# ------------------------------ Local stores ------------------------------ #

istore = new_instruction(0x36, "istore", StoreLocalInstruction, type=types.int_t)
lstore = new_instruction(0x37, "lstore", StoreLocalInstruction, type=types.long_t)
fstore = new_instruction(0x38, "fstore", StoreLocalInstruction, type=types.float_t)
dstore = new_instruction(0x39, "dstore", StoreLocalInstruction, type=types.double_t)
astore = new_instruction(0x3a, "astore", StoreLocalInstruction, type=types.reference_t)
# Integer specifics
istore_0 = new_instruction(0x3b, "istore_0", StoreLocalFixedInstruction, type=types.int_t, index=0)
istore_1 = new_instruction(0x3c, "istore_1", StoreLocalFixedInstruction, type=types.int_t, index=1)
istore_2 = new_instruction(0x3d, "istore_2", StoreLocalFixedInstruction, type=types.int_t, index=2)
istore_3 = new_instruction(0x3e, "istore_3", StoreLocalFixedInstruction, type=types.int_t, index=3)
# Long specifics
lstore_0 = new_instruction(0x3f, "lstore_0", StoreLocalFixedInstruction, type=types.long_t, index=0)
lstore_1 = new_instruction(0x40, "lstore_1", StoreLocalFixedInstruction, type=types.long_t, index=1)
lstore_2 = new_instruction(0x41, "lstore_2", StoreLocalFixedInstruction, type=types.long_t, index=2)
lstore_3 = new_instruction(0x42, "lstore_3", StoreLocalFixedInstruction, type=types.long_t, index=3)
# Float specifics
fstore_0 = new_instruction(0x43, "fstore_0", StoreLocalFixedInstruction, type=types.float_t, index=0)
fstore_1 = new_instruction(0x44, "fstore_1", StoreLocalFixedInstruction, type=types.float_t, index=1)
fstore_2 = new_instruction(0x45, "fstore_2", StoreLocalFixedInstruction, type=types.float_t, index=2)
fstore_3 = new_instruction(0x46, "fstore_3", StoreLocalFixedInstruction, type=types.float_t, index=3)
# Double specifics
dstore_0 = new_instruction(0x47, "dstore_0", StoreLocalFixedInstruction, type=types.double_t, index=0)
dstore_1 = new_instruction(0x48, "dstore_1", StoreLocalFixedInstruction, type=types.double_t, index=1)
dstore_2 = new_instruction(0x49, "dstore_2", StoreLocalFixedInstruction, type=types.double_t, index=2)
dstore_3 = new_instruction(0x4a, "dstore_3", StoreLocalFixedInstruction, type=types.double_t, index=3)
# Reference specifics
astore_0 = new_instruction(0x4b, "astore_0", StoreLocalFixedInstruction, type=types.reference_t, index=0)
astore_1 = new_instruction(0x4c, "astore_1", StoreLocalFixedInstruction, type=types.reference_t, index=1)
astore_2 = new_instruction(0x4d, "astore_2", StoreLocalFixedInstruction, type=types.reference_t, index=2)
astore_3 = new_instruction(0x4e, "astore_3", StoreLocalFixedInstruction, type=types.reference_t, index=3)

# ------------------------------ Array stores ------------------------------ #

iastore = new_instruction(0x4f, "iastore", ArrayStoreInstruction, type=Array(types.int_t))
lastore = new_instruction(0x50, "lastore", ArrayStoreInstruction, type=Array(types.long_t))
fastore = new_instruction(0x51, "fastore", ArrayStoreInstruction, type=Array(types.float_t))
dastore = new_instruction(0x52, "dastore", ArrayStoreInstruction, type=Array(types.double_t))
aastore = new_instruction(0x53, "aastore", ArrayStoreInstruction, type=Array(types.object_t))
bastore = new_instruction(0x54, "bastore", iastore, type=Array(types.byte_t))  # Also bool_t but whatever
castore = new_instruction(0x55, "castore", iastore, type=Array(types.char_t))
sastore = new_instruction(0x56, "sastore", iastore, type=Array(types.short_t))

# ------------------------------ Stack manipulation ------------------------------ #

pop = new_instruction(0x57, "pop", PopInstruction)
pop2 = new_instruction(0x58, "pop2", Pop2Instruction)
dup = new_instruction(0x59, "dup", DupInstruction)
dup_x1 = new_instruction(0x5a, "dup_x1", DupX1Instruction)
dup_x2 = new_instruction(0x5b, "dup_x2", DupX2Instruction)
dup2 = new_instruction(0x5c, "dup2", Dup2Instruction)
dup2_x1 = new_instruction(0x5d, "dup2_x1", Dup2X1Instruction)
dup2_x2 = new_instruction(0x5e, "dup2_x2", Dup2X2Instruction)
swap = new_instruction(0x5f, "swap", SwapInstruction)

# ------------------------------ Arithmetic ------------------------------ #

# Addition
iadd = new_instruction(0x60, "iadd", AdditionInstruction, type_a=types.int_t, type_b=types.int_t)
ladd = new_instruction(0x61, "ladd", AdditionInstruction, type_a=types.long_t, type_b=types.long_t)
fadd = new_instruction(0x62, "fadd", AdditionInstruction, type_a=types.float_t, type_b=types.float_t)
dadd = new_instruction(0x63, "dadd", AdditionInstruction, type_a=types.double_t, type_b=types.double_t)
# Subtraction
isub = new_instruction(0x64, "isub", SubtractionInstruction, type_a=types.int_t, type_b=types.int_t)
lsub = new_instruction(0x65, "lsub", SubtractionInstruction, type_a=types.long_t, type_b=types.long_t)
fsub = new_instruction(0x66, "fsub", SubtractionInstruction, type_a=types.float_t, type_b=types.float_t)
dsub = new_instruction(0x67, "dsub", SubtractionInstruction, type_a=types.double_t, type_b=types.double_t)
# Multiplication
imul = new_instruction(0x68, "imul", MultiplicationInstruction, type_a=types.int_t, type_b=types.int_t)
lmul = new_instruction(0x69, "lmul", MultiplicationInstruction, type_a=types.long_t, type_b=types.long_t)
fmul = new_instruction(0x6a, "fmul", MultiplicationInstruction, type_a=types.float_t, type_b=types.float_t)
dmul = new_instruction(0x6b, "dmul", MultiplicationInstruction, type_a=types.double_t, type_b=types.double_t)
# Division
idiv = new_instruction(0x6c, "idiv", DivisionInstruction, throws=(Class("java/lang/ArithmeticException"),), type_a=types.int_t, type_b=types.int_t)
ldiv = new_instruction(0x6d, "ldiv", DivisionInstruction, type_a=types.long_t, type_b=types.long_t)
fdiv = new_instruction(0x6e, "fdiv", DivisionInstruction, type_a=types.float_t, type_b=types.float_t)
ddiv = new_instruction(0x6f, "ddiv", DivisionInstruction, type_a=types.double_t, type_b=types.double_t)
# Modulo
irem = new_instruction(0x70, "irem", RemainderInstruction, type_a=types.int_t, type_b=types.int_t)
lrem = new_instruction(0x71, "lrem", RemainderInstruction, type_a=types.long_t, type_b=types.long_t)
frem = new_instruction(0x72, "frem", RemainderInstruction, type_a=types.float_t, type_b=types.float_t)
drem = new_instruction(0x73, "drem", RemainderInstruction, type_a=types.double_t, type_b=types.double_t)
# Negation
ineg = new_instruction(0x74, "ineg", NegationInstruction, type=types.int_t)
lneg = new_instruction(0x75, "lneg", NegationInstruction, type=types.long_t)
fneg = new_instruction(0x76, "fneg", NegationInstruction, type=types.float_t)
dneg = new_instruction(0x77, "dneg", NegationInstruction, type=types.double_t)
# Left shift
ishl = new_instruction(0x78, "ishl", ShiftLeftInstruction, type_a=types.int_t, type_b=types.int_t)
lshl = new_instruction(0x79, "lshl", ShiftLeftInstruction, type_a=types.int_t, type_b=types.long_t)
# Right shift
ishr = new_instruction(0x7a, "ishr", ShiftRightInstruction, type_a=types.int_t, type_b=types.int_t)
lshr = new_instruction(0x7b, "lshr", ShiftRightInstruction, type_a=types.int_t, type_b=types.long_t)
# Unsigned right shift
iushr = new_instruction(0x7c, "iushr", UnsignedShiftRightInstruction, type_a=types.int_t, type_b=types.int_t)
lushr = new_instruction(0x7d, "lushr", UnsignedShiftRightInstruction, type_a=types.int_t, type_b=types.long_t)
# Bitwise and
iand = new_instruction(0x7e, "iand", BitwiseAndInstruction, type_a=types.int_t, type_b=types.int_t)
land = new_instruction(0x7f, "land", BitwiseAndInstruction, type_a=types.long_t, type_b=types.long_t)
# Bitwise or
ior = new_instruction(0x80, "ior", BitwiseOrInstruction, type_a=types.int_t, type_b=types.int_t)
lor = new_instruction(0x81, "lor", BitwiseOrInstruction, type_a=types.long_t, type_b=types.long_t)
# Bitwise xor
ixor = new_instruction(0x82, "ixor", BitwiseXorInstruction, type_a=types.int_t, type_b=types.int_t)
lxor = new_instruction(0x83, "lxor", BitwiseXorInstruction, type_a=types.long_t, type_b=types.long_t)

# ------------------------------ Conversions ------------------------------ #

# Integer to ...
i2l = new_instruction(0x85, "i2l", ConversionInstruction, type_in=types.int_t, type_out=types.long_t)
i2f = new_instruction(0x86, "i2f", ConversionInstruction, type_in=types.int_t, type_out=types.float_t)
i2d = new_instruction(0x87, "i2d", ConversionInstruction, type_in=types.int_t, type_out=types.double_t)
# Long to ...
l2i = new_instruction(0x88, "l2i", ConversionInstruction, type_in=types.long_t, type_out=types.int_t)
l2f = new_instruction(0x89, "l2f", ConversionInstruction, type_in=types.long_t, type_out=types.float_t)
l2d = new_instruction(0x8a, "l2d", ConversionInstruction, type_in=types.long_t, type_out=types.double_t)
# Float to ...
f2i = new_instruction(0x8b, "f2i", ConversionInstruction, type_in=types.float_t, type_out=types.int_t)
f2l = new_instruction(0x8c, "f2l", ConversionInstruction, type_in=types.float_t, type_out=types.long_t)
f2d = new_instruction(0x8d, "f2d", ConversionInstruction, type_in=types.float_t, type_out=types.double_t)
# Double to ...
d2i = new_instruction(0x8e, "d2i", ConversionInstruction, type_in=types.double_t, type_out=types.int_t)
d2l = new_instruction(0x8f, "d2l", ConversionInstruction, type_in=types.double_t, type_out=types.long_t)
d2f = new_instruction(0x90, "d2f", ConversionInstruction, type_in=types.double_t, type_out=types.float_t)
# Integer truncation
i2b = new_instruction(0x91, "i2b", TruncationInstruction, type_out=types.byte_t)
i2c = new_instruction(0x92, "i2c", TruncationInstruction, type_out=types.char_t)
i2s = new_instruction(0x93, "i2s", TruncationInstruction, type_out=types.short_t)

checkcast = new_instruction(0xc0, "checkcast", CheckCastInstruction)
instanceof = new_instruction(0xc1, "instanceof", InstanceOfInstruction)

# ------------------------------ Comparisons ------------------------------ #

lcmp = new_instruction(0x94, "lcmp", ComparisonInstruction, type=types.long_t)
fcmpl = new_instruction(0x95, "fcmpl", ComparisonInstruction, type=types.float_t)
fcmpg = new_instruction(0x96, "fcmpg", ComparisonInstruction, type=types.float_t)
dcmpl = new_instruction(0x97, "dcmpl", ComparisonInstruction, type=types.double_t)
dcmpg = new_instruction(0x98, "dcmpg", ComparisonInstruction, type=types.double_t)

# ------------------------------ Jumps ------------------------------ #

# Compare to 0
ifeq = new_instruction(0x99, "ifeq", UnaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.EQ)
ifne = new_instruction(0x9a, "ifne", UnaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.NE)
iflt = new_instruction(0x9b, "iflt", UnaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.LT)
ifge = new_instruction(0x9c, "ifge", UnaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.GE)
ifgt = new_instruction(0x9d, "ifgt", UnaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.GT)
ifle = new_instruction(0x9e, "ifle", UnaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.LE)
# Integer comparison
if_icmpeq = new_instruction(0x9f, "if_icmpeq", BinaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.EQ)
if_icmpne = new_instruction(0xa0, "if_icmpne", BinaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.NE)
if_icmplt = new_instruction(0xa1, "if_icmplt", BinaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.LT)
if_icmpge = new_instruction(0xa2, "if_icmpge", BinaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.GE)
if_icmpgt = new_instruction(0xa3, "if_icmpgt", BinaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.GT)
if_icmple = new_instruction(0xa4, "if_icmple", BinaryComparisonJumpInstruction, {"offset": ">h"}, type=types.int_t, comparison=ConditionalJumpInstruction.LE)
# Reference comparison
if_acmpeq = new_instruction(0xa5, "if_acmpeq", BinaryComparisonJumpInstruction, {"offset": ">h"}, type=types.reference_t, comparison=ConditionalJumpInstruction.EQ)
if_acmpne = new_instruction(0xa6, "if_acmpne", BinaryComparisonJumpInstruction, {"offset": ">h"}, type=types.reference_t, comparison=ConditionalJumpInstruction.NE)
ifnull = new_instruction(0xc6, "ifnull", UnaryComparisonJumpInstruction, {"offset": ">h"}, type=types.reference_t, comparison=ConditionalJumpInstruction.EQ)
ifnonnull = new_instruction(0xc7, "ifnonnull", UnaryComparisonJumpInstruction, {"offset": ">h"}, type=types.reference_t, comparison=ConditionalJumpInstruction.NE)
# Other jumps
goto = new_instruction(0xa7, "goto", JumpInstruction, {"offset": ">h"})
goto_w = new_instruction(0xc8, "goto_w", JumpInstruction, {"offset": ">i"})
jsr = new_instruction(0xa8, "jsr", JsrInstruction, {"offset": ">h"})
jsr_w = new_instruction(0xc9, "jsr_w", JsrInstruction, {"offset": ">i"})
ret = new_instruction(0xa9, "ret", RetInstruction)
tableswitch = new_instruction(0xaa, "tableswitch", TableSwitchInstruction)
lookupswitch = new_instruction(0xab, "lookupswitch", LookupSwitchInstruction)

# ------------------------------ Returns ------------------------------ #

ireturn = new_instruction(0xac, "ireturn", ReturnInstruction, type=types.int_t)
lreturn = new_instruction(0xad, "lreturn", ReturnInstruction, type=types.long_t)
freturn = new_instruction(0xae, "freturn", ReturnInstruction, type=types.float_t)
dreturn = new_instruction(0xaf, "dreturn", ReturnInstruction, type=types.double_t)
areturn = new_instruction(0xb0, "areturn", ReturnInstruction, type=types.object_t)
return_ = new_instruction(0xb1, "return", ReturnInstruction, type=types.void_t)

# ------------------------------ Fields ------------------------------ #

getstatic = new_instruction(0xb2, "getstatic", GetFieldInstruction, {"_index": ">H"}, static=True)
putstatic = new_instruction(0xb3, "putstatic", PutFieldInstruction, {"_index": ">H"}, static=True)
getfield = new_instruction(0xb4, "getfield", GetFieldInstruction, {"_index": ">H"}, static=False)
putfield = new_instruction(0xb5, "putfield", PutFieldInstruction, {"_index": ">H"}, static=False)

# ------------------------------ Invokes ------------------------------ #

invokevirtual = new_instruction(0xb6, "invokevirtual", InvokeVirtualInstruction, {"_index": ">H"})
invokespecial = new_instruction(0xb7, "invokespecial", InvokeSpecialInstruction, {"_index": ">H"})
invokestatic = new_instruction(0xb8, "invokestatic", InvokeStaticInstruction, {"_index": ">H"})
invokeinterface = new_instruction(
    0xb9, "invokeinterface", InvokeInterfaceInstruction, {"_index": ">H", "count": ">B", "_": ">B"},
)
invokedynamic = new_instruction(0xba, "invokedynamic", InvokeDynamicInstruction, {"_index": ">H", "_": ">H"})

# ------------------------------ New ------------------------------ #

new = new_instruction(0xbb, "new", NewInstruction)
newarray = new_instruction(0xbc, "newarray", NewArrayInstruction)
anewarray = new_instruction(0xbd, "anewarray", ANewArrayInstruction)
multianewarray = new_instruction(0xc5, "multianewarray", MultiANewArrayInstruction)

# ------------------------------ Other ------------------------------ #

iinc = new_instruction(0x84, "iinc", IncrementLocalInstruction)

arraylength = new_instruction(0xbe, "arraylength", ArrayLengthInstruction)

athrow = new_instruction(0xbf, "athrow", AThrowInstruction)

monitorenter = new_instruction(0xc2, "monitorenter", MonitorEnterInstruction)
monitorexit = new_instruction(0xc3, "monitorexit", MonitorExitInstruction)

wide = new_instruction(0xc4, "wide")

# ------------------------------ Internal ------------------------------ #

breakpoint_ = new_instruction(0xca, "breakpoint")
impdep1 = new_instruction(0xfe, "impdep1")
impdep2 = new_instruction(0xff, "impdep2")


INSTRUCTIONS = (
    nop,

    aconst_null,
    iconst_m1, iconst_0, iconst_1, iconst_2, iconst_3, iconst_4, iconst_5,
    lconst_0, lconst_1,
    fconst_0, fconst_1, fconst_2,
    dconst_0, dconst_1,
    bipush, sipush, ldc, ldc_w, ldc2_w,

    iload, lload, fload, dload, aload,
    iload_0, iload_1, iload_2, iload_3,
    lload_0, lload_1, lload_2, lload_3,
    fload_0, fload_1, fload_2, fload_3,
    dload_0, dload_1, dload_2, dload_3,
    aload_0, aload_1, aload_2, aload_3,

    iaload, laload, faload, daload, aaload, baload, caload, saload,

    istore, lstore, fstore, dstore, astore,
    istore_0, istore_1, istore_2, istore_3,
    lstore_0, lstore_1, lstore_2, lstore_3,
    fstore_0, fstore_1, fstore_2, fstore_3,
    dstore_0, dstore_1, dstore_2, dstore_3,
    astore_0, astore_1, astore_2, astore_3,

    iastore, lastore, fastore, dastore, aastore, bastore, castore, sastore,

    pop, pop2, dup, dup_x1, dup_x2, dup2, dup2_x1, dup2_x2, swap,

    iadd, ladd, fadd, dadd,
    isub, lsub, fsub, dsub,
    imul, lmul, fmul, dmul,
    idiv, ldiv, fdiv, ddiv,
    irem, lrem, frem, drem,
    ineg, lneg, fneg, dneg,
    ishl, lshl,
    ishr, lshr,
    iushr, lushr,
    iand, land,
    ior, lor,
    ixor, lxor,

    i2l, i2f, i2d,
    l2i, l2f, l2d,
    f2i, f2l, f2d,
    d2i, d2l, d2f,
    i2b, i2c, i2s,

    lcmp, fcmpl, fcmpg, dcmpl, dcmpg,

    ifeq, ifne, iflt, ifge, ifgt, ifle,
    if_icmpeq, if_icmpne, if_icmplt, if_icmpge, if_icmpgt, if_icmple,
    if_acmpeq, if_acmpne, ifnull, ifnonnull,
    goto, goto_w, jsr, jsr_w, ret, tableswitch, lookupswitch,

    ireturn, lreturn, freturn, dreturn, areturn, return_,

    getstatic, putstatic, getfield, putfield,

    invokevirtual, invokespecial, invokestatic, invokeinterface, invokedynamic,

    new, newarray, anewarray, multianewarray,

    iinc,
    arraylength,
    athrow,

    checkcast, instanceof,

    monitorenter, monitorexit,

    wide,

    breakpoint_, impdep1, impdep2,
)
