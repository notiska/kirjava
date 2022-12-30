#!/usr/bin/env python3

"""
JVM instructions.
"""

import operator
import typing
from abc import ABCMeta
from typing import Any, Dict, IO, List, Tuple, Union

from .. import ClassFile
from ..constants import Double, Float, Long
from ...abc import Error, Source, TypeChecker
from ...types.reference import ClassOrInterfaceType

if typing.TYPE_CHECKING:
    from ...analysis.trace import State


class MetaInstruction(ABCMeta):
    """
    Instruction metaclass, I know, shame me.
    """

    @classmethod
    def new_instruction(
            cls,
            opcode: int,
            mnemonic: str,
            base: Union["MetaInstruction", None] = None,
            operands: Union[Dict[str, str], None] = None,
            operands_wide: Union[Dict[str, str], None] = None,
            throws: Union[Tuple[ClassOrInterfaceType, ...], None] = None,
            **namespace: Dict[str, object],
    ) -> "MetaInstruction":
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

        if base is None:
            base = Instruction
        if operands is None:
            operands = {}
        if operands_wide is None:
            operands_wide = {}

        # namespace["__qualname__"] = mnemonic
        namespace["opcode"] = opcode
        namespace["mnemonic"] = mnemonic
        namespace["operands"] = base.operands.copy()
        namespace["operands"].update(operands)
        namespace["operands_wide"] = base.operands_wide.copy()
        namespace["operands_wide"].update(operands_wide)
        if throws is not None:
            namespace["throws"] = throws

        if not "__slots__" in namespace:
            namespace["__slots__"] = ()
        namespace["__slots__"] = tuple(set(namespace["__slots__"]) | set(operands.keys()) | set(operands_wide.keys()))

        return cls.__new__(cls, mnemonic, (base,), namespace)


class Instruction(Source, metaclass=MetaInstruction):
    """
    A (somewhat abstracted) JVM instruction.
    """

    opcode: int = ...
    mnemonic: str = ...

    operands: Dict[str, str] = {}
    operands_wide: Dict[str, str] = {}

    throws: Tuple[ClassOrInterfaceType, ...] = ()

    def __repr__(self) -> str:
        return "<Instruction(opcode=0x%x, mnemonic=%s) at %x>" % (self.opcode, self.mnemonic, id(self))

    def __str__(self) -> str:
        return self.mnemonic

    def __eq__(self, other: Any) -> bool:
        return other == self.__class__ or other.__class__ == self.__class__

    def __hash__(self) -> int:
        return hash((self.opcode, self.mnemonic))

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

    # @abstractmethod
    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        """
        Reads the data from the buffer into this instruction's operands.

        :param class_file: The classfile that this instruction belongs to.
        :param buffer: The binary buffer to read from.
        :param wide: Should we be reading this instruction as if it were wide?
        """

        # if wide and not self.operands_wide:
        #     raise Exception("%r cannot be read wide." % self)

        for operand, format_ in (self.operands if not wide else self.operands_wide).items():
            value, = struct.unpack(format_, buffer.read(struct.calcsize(format_)))
            if operand != "_":
                setattr(self, operand, value)

    # @abstractmethod
    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        """
        Writes the operands from this instruction into the buffer.

        :param class_file: The classfile that this instruction belongs to.
        :param buffer: The binary buffer to write to.
        :param wide: Should we be writing this instruction as if it were wide?
        """

        # if wide and not self.operands_wide:
        #     raise Exception("%r cannot be written wide." % self)

        for operand, format_ in (self.operands if not wide else self.operands_wide).items():
            value = 0
            if operand != "_":
                value = getattr(self, operand)
            buffer.write(struct.pack(format_, value))

    def get_size(self, offset: int, wide: bool) -> None:
        """
        Gets the size of an instruction as if it were about to be written.

        :param offset: The offset that this instruction will be written at.
        :param wide: Will the instruction be written wide?
        :return: The size of the instruction.
        """

        return 1 + sum(map(struct.calcsize, (self.operands if not wide else self.operands_wide).values()))

    # @abstractmethod
    def trace(self, source: Source, state: "State", errors: List[Error], checker: TypeChecker) -> None:
        """
        Steps through this instruction (for stackmap frame generation and verification purposes).

        :param source: More specific information about where this instruction exactly is.
        :param state: The current stack state.
        :param errors: Cumulative errors to add to.
        :param checker: The type checker implementation to use.
        """

        ...


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


nop = MetaInstruction.new_instruction(0x00, "nop")

# ------------------------------ Constants ------------------------------ #

aconst_null = MetaInstruction.new_instruction(0x01, "aconst_null", FixedConstantInstruction, constant=types.null_t)
# Integer constants
iconst_m1 = MetaInstruction.new_instruction(0x02, "iconst_m1", FixedConstantInstruction, constant=Integer(-1))
iconst_0 = MetaInstruction.new_instruction(0x03, "iconst_0", FixedConstantInstruction, constant=Integer(0))
iconst_1 = MetaInstruction.new_instruction(0x04, "iconst_1", FixedConstantInstruction, constant=Integer(1))
iconst_2 = MetaInstruction.new_instruction(0x05, "iconst_2", FixedConstantInstruction, constant=Integer(2))
iconst_3 = MetaInstruction.new_instruction(0x06, "iconst_3", FixedConstantInstruction, constant=Integer(3))
iconst_4 = MetaInstruction.new_instruction(0x07, "iconst_4", FixedConstantInstruction, constant=Integer(4))
iconst_5 = MetaInstruction.new_instruction(0x08, "iconst_5", FixedConstantInstruction, constant=Integer(5))
# Long constants
lconst_0 = MetaInstruction.new_instruction(0x09, "lconst_0", FixedConstantInstruction, constant=Long(0))
lconst_1 = MetaInstruction.new_instruction(0x0a, "lconst_1", FixedConstantInstruction, constant=Long(1))
# Float constants
fconst_0 = MetaInstruction.new_instruction(0x0b, "fconst_0", FixedConstantInstruction, constant=Float(0))
fconst_1 = MetaInstruction.new_instruction(0x0c, "fconst_1", FixedConstantInstruction, constant=Float(1))
fconst_2 = MetaInstruction.new_instruction(0x0d, "fconst_2", FixedConstantInstruction, constant=Float(2))
# Double constants
dconst_0 = MetaInstruction.new_instruction(0x0e, "dconst_0", FixedConstantInstruction, constant=Double(0))
dconst_1 = MetaInstruction.new_instruction(0x0f, "dconst_1", FixedConstantInstruction, constant=Double(1))
# Other constants
bipush = MetaInstruction.new_instruction(0x10, "bipush", IntegerConstantInstruction, {"_value": ">B"})
sipush = MetaInstruction.new_instruction(0x11, "sipush", IntegerConstantInstruction, {"_value": ">H"})
ldc = MetaInstruction.new_instruction(0x12, "ldc", LoadConstantInstruction, {"_index": ">B"})
ldc_w = MetaInstruction.new_instruction(0x13, "ldc_w", ldc, {"_index": ">H"})
ldc2_w = MetaInstruction.new_instruction(0x14, "ldc2_w", ldc, {"_index": ">H"})

# ------------------------------ Local loads ------------------------------ #

iload = MetaInstruction.new_instruction(0x15, "iload", LoadLocalInstruction, type_=types.int_t)
lload = MetaInstruction.new_instruction(0x16, "lload", LoadLocalInstruction, type_=types.long_t)
fload = MetaInstruction.new_instruction(0x17, "fload", LoadLocalInstruction, type_=types.float_t)
dload = MetaInstruction.new_instruction(0x18, "dload", LoadLocalInstruction, type_=types.double_t)
aload = MetaInstruction.new_instruction(0x19, "aload", LoadLocalInstruction, type_=None)
# Integer specifics
iload_0 = MetaInstruction.new_instruction(0x1a, "iload_0", LoadLocalFixedInstruction, type_=types.int_t, index=0) 
iload_1 = MetaInstruction.new_instruction(0x1b, "iload_1", LoadLocalFixedInstruction, type_=types.int_t, index=1)
iload_2 = MetaInstruction.new_instruction(0x1c, "iload_2", LoadLocalFixedInstruction, type_=types.int_t, index=2)
iload_3 = MetaInstruction.new_instruction(0x1d, "iload_3", LoadLocalFixedInstruction, type_=types.int_t, index=3)
# Long specifics
lload_0 = MetaInstruction.new_instruction(0x1e, "lload_0", LoadLocalFixedInstruction, type_=types.long_t, index=0)
lload_1 = MetaInstruction.new_instruction(0x1f, "lload_1", LoadLocalFixedInstruction, type_=types.long_t, index=1)
lload_2 = MetaInstruction.new_instruction(0x20, "lload_2", LoadLocalFixedInstruction, type_=types.long_t, index=2)
lload_3 = MetaInstruction.new_instruction(0x21, "lload_3", LoadLocalFixedInstruction, type_=types.long_t, index=3)
# Float specifics
fload_0 = MetaInstruction.new_instruction(0x22, "fload_0", LoadLocalFixedInstruction, type_=types.float_t, index=0)
fload_1 = MetaInstruction.new_instruction(0x23, "fload_1", LoadLocalFixedInstruction, type_=types.float_t, index=1)
fload_2 = MetaInstruction.new_instruction(0x24, "fload_2", LoadLocalFixedInstruction, type_=types.float_t, index=2)
fload_3 = MetaInstruction.new_instruction(0x25, "fload_3", LoadLocalFixedInstruction, type_=types.float_t, index=3)
# Double specifics
dload_0 = MetaInstruction.new_instruction(0x26, "dload_0", LoadLocalFixedInstruction, type_=types.double_t, index=0)
dload_1 = MetaInstruction.new_instruction(0x27, "dload_1", LoadLocalFixedInstruction, type_=types.double_t, index=1)
dload_2 = MetaInstruction.new_instruction(0x28, "dload_2", LoadLocalFixedInstruction, type_=types.double_t, index=2)
dload_3 = MetaInstruction.new_instruction(0x29, "dload_3", LoadLocalFixedInstruction, type_=types.double_t, index=3)
# Reference specifics
aload_0 = MetaInstruction.new_instruction(0x2a, "aload_0", LoadLocalFixedInstruction, type_=None, index=0)
aload_1 = MetaInstruction.new_instruction(0x2b, "aload_1", LoadLocalFixedInstruction, type_=None, index=1)
aload_2 = MetaInstruction.new_instruction(0x2c, "aload_2", LoadLocalFixedInstruction, type_=None, index=2)
aload_3 = MetaInstruction.new_instruction(0x2d, "aload_3", LoadLocalFixedInstruction, type_=None, index=3)

# ------------------------------ Array loads ------------------------------ #

iaload = MetaInstruction.new_instruction(0x2e, "iaload", ArrayLoadInstruction, type_=types.int_t)
laload = MetaInstruction.new_instruction(0x2f, "laload", ArrayLoadInstruction, type_=types.long_t)
faload = MetaInstruction.new_instruction(0x30, "faload", ArrayLoadInstruction, type_=types.float_t)
daload = MetaInstruction.new_instruction(0x31, "daload", ArrayLoadInstruction, type_=types.double_t)
aaload = MetaInstruction.new_instruction(0x32, "aaload", ArrayLoadInstruction, type_=None)
baload = MetaInstruction.new_instruction(0x33, "baload", iaload, type_=types.byte_t)
caload = MetaInstruction.new_instruction(0x34, "caload", iaload, type_=types.char_t)
saload = MetaInstruction.new_instruction(0x35, "saload", iaload, type_=types.short_t)

# ------------------------------ Local stores ------------------------------ #

istore = MetaInstruction.new_instruction(0x36, "istore", StoreLocalInstruction, type_=types.int_t)
lstore = MetaInstruction.new_instruction(0x37, "lstore", StoreLocalInstruction, type_=types.long_t)
fstore = MetaInstruction.new_instruction(0x38, "fstore", StoreLocalInstruction, type_=types.float_t)
dstore = MetaInstruction.new_instruction(0x39, "dstore", StoreLocalInstruction, type_=types.double_t)
astore = MetaInstruction.new_instruction(0x3a, "astore", StoreLocalInstruction, type_=None)
# Integer specifics
istore_0 = MetaInstruction.new_instruction(0x3b, "istore_0", StoreLocalFixedInstruction, type_=types.int_t, index=0)
istore_1 = MetaInstruction.new_instruction(0x3c, "istore_1", StoreLocalFixedInstruction, type_=types.int_t, index=1)
istore_2 = MetaInstruction.new_instruction(0x3d, "istore_2", StoreLocalFixedInstruction, type_=types.int_t, index=2)
istore_3 = MetaInstruction.new_instruction(0x3e, "istore_3", StoreLocalFixedInstruction, type_=types.int_t, index=3)
# Long specifics
lstore_0 = MetaInstruction.new_instruction(0x3f, "lstore_0", StoreLocalFixedInstruction, type_=types.long_t, index=0)
lstore_1 = MetaInstruction.new_instruction(0x40, "lstore_1", StoreLocalFixedInstruction, type_=types.long_t, index=1)
lstore_2 = MetaInstruction.new_instruction(0x41, "lstore_2", StoreLocalFixedInstruction, type_=types.long_t, index=2)
lstore_3 = MetaInstruction.new_instruction(0x42, "lstore_3", StoreLocalFixedInstruction, type_=types.long_t, index=3)
# Float specifics
fstore_0 = MetaInstruction.new_instruction(0x43, "fstore_0", StoreLocalFixedInstruction, type_=types.float_t, index=0)
fstore_1 = MetaInstruction.new_instruction(0x44, "fstore_1", StoreLocalFixedInstruction, type_=types.float_t, index=1)
fstore_2 = MetaInstruction.new_instruction(0x45, "fstore_2", StoreLocalFixedInstruction, type_=types.float_t, index=2)
fstore_3 = MetaInstruction.new_instruction(0x46, "fstore_3", StoreLocalFixedInstruction, type_=types.float_t, index=3)
# Double specifics
dstore_0 = MetaInstruction.new_instruction(0x47, "dstore_0", StoreLocalFixedInstruction, type_=types.double_t, index=0)
dstore_1 = MetaInstruction.new_instruction(0x48, "dstore_1", StoreLocalFixedInstruction, type_=types.double_t, index=1)
dstore_2 = MetaInstruction.new_instruction(0x49, "dstore_2", StoreLocalFixedInstruction, type_=types.double_t, index=2)
dstore_3 = MetaInstruction.new_instruction(0x4a, "dstore_3", StoreLocalFixedInstruction, type_=types.double_t, index=3)
# Reference specifics
astore_0 = MetaInstruction.new_instruction(0x4b, "astore_0", StoreLocalFixedInstruction, type_=None, index=0)
astore_1 = MetaInstruction.new_instruction(0x4c, "astore_1", StoreLocalFixedInstruction, type_=None, index=1)
astore_2 = MetaInstruction.new_instruction(0x4d, "astore_2", StoreLocalFixedInstruction, type_=None, index=2)
astore_3 = MetaInstruction.new_instruction(0x4e, "astore_3", StoreLocalFixedInstruction, type_=None, index=3)

# ------------------------------ Array stores ------------------------------ #

iastore = MetaInstruction.new_instruction(0x4f, "iastore", ArrayStoreInstruction, type_=types.int_t)
lastore = MetaInstruction.new_instruction(0x50, "lastore", ArrayStoreInstruction, type_=types.long_t)
fastore = MetaInstruction.new_instruction(0x51, "fastore", ArrayStoreInstruction, type_=types.float_t)
dastore = MetaInstruction.new_instruction(0x52, "dastore", ArrayStoreInstruction, type_=types.double_t)
aastore = MetaInstruction.new_instruction(0x53, "aastore", ArrayStoreInstruction, type_=None)
bastore = MetaInstruction.new_instruction(0x54, "bastore", iastore, type_=types.byte_t)  # Also bool_t but whatever
castore = MetaInstruction.new_instruction(0x55, "castore", iastore, type_=types.char_t)
sastore = MetaInstruction.new_instruction(0x56, "sastore", iastore, type_=types.short_t)

# ------------------------------ Stack manipulation ------------------------------ #

pop = MetaInstruction.new_instruction(0x57, "pop", PopInstruction)
pop2 = MetaInstruction.new_instruction(0x58, "pop2", Pop2Instruction)
dup = MetaInstruction.new_instruction(0x59, "dup", DupInstruction)
dup_x1 = MetaInstruction.new_instruction(0x5a, "dup_x1", DupX1Instruction)
dup_x2 = MetaInstruction.new_instruction(0x5b, "dup_x2", DupX2Instruction)
dup2 = MetaInstruction.new_instruction(0x5c, "dup2", Dup2Instruction)
dup2_x1 = MetaInstruction.new_instruction(0x5d, "dup2_x1", Dup2X1Instruction)
dup2_x2 = MetaInstruction.new_instruction(0x5e, "dup2_x2", Dup2X2Instruction)
swap = MetaInstruction.new_instruction(0x5f, "swap", SwapInstruction)

# ------------------------------ Arithmetic ------------------------------ #

# Addition
iadd = MetaInstruction.new_instruction(0x60, "iadd", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
ladd = MetaInstruction.new_instruction(0x61, "ladd", BinaryOperationInstruction, type_a=types.long_t, type_b=types.long_t)
fadd = MetaInstruction.new_instruction(0x62, "fadd", BinaryOperationInstruction, type_a=types.float_t, type_b=types.float_t)
dadd = MetaInstruction.new_instruction(0x63, "dadd", BinaryOperationInstruction, type_a=types.double_t, type_b=types.double_t)
# Subtraction
isub = MetaInstruction.new_instruction(0x64, "isub", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
lsub = MetaInstruction.new_instruction(0x65, "lsub", BinaryOperationInstruction, type_a=types.long_t, type_b=types.long_t)
fsub = MetaInstruction.new_instruction(0x66, "fsub", BinaryOperationInstruction, type_a=types.float_t, type_b=types.float_t)
dsub = MetaInstruction.new_instruction(0x67, "dsub", BinaryOperationInstruction, type_a=types.double_t, type_b=types.double_t)
# Multiplication
imul = MetaInstruction.new_instruction(0x68, "imul", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
lmul = MetaInstruction.new_instruction(0x69, "lmul", BinaryOperationInstruction, type_a=types.long_t, type_b=types.long_t)
fmul = MetaInstruction.new_instruction(0x6a, "fmul", BinaryOperationInstruction, type_a=types.float_t, type_b=types.float_t)
dmul = MetaInstruction.new_instruction(0x6b, "dmul", BinaryOperationInstruction, type_a=types.double_t, type_b=types.double_t)
# Division
idiv = MetaInstruction.new_instruction(0x6c, "idiv", BinaryOperationInstruction, throws=(types.arithmeticexception_t,), type_a=types.int_t, type_b=types.int_t)
ldiv = MetaInstruction.new_instruction(0x6d, "ldiv", BinaryOperationInstruction, type_a=types.long_t, type_b=types.long_t)
fdiv = MetaInstruction.new_instruction(0x6e, "fdiv", BinaryOperationInstruction, type_a=types.float_t, type_b=types.float_t)
ddiv = MetaInstruction.new_instruction(0x6f, "ddiv", BinaryOperationInstruction, type_a=types.double_t, type_b=types.double_t)
# Modulo
irem = MetaInstruction.new_instruction(0x70, "irem", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
lrem = MetaInstruction.new_instruction(0x71, "lrem", BinaryOperationInstruction, type_a=types.long_t, type_b=types.long_t)
frem = MetaInstruction.new_instruction(0x72, "frem", BinaryOperationInstruction, type_a=types.float_t, type_b=types.float_t)
drem = MetaInstruction.new_instruction(0x73, "drem", BinaryOperationInstruction, type_a=types.double_t, type_b=types.double_t)
# Negation
ineg = MetaInstruction.new_instruction(0x74, "ineg", UnaryOperationInstruction, type_=types.int_t)
lneg = MetaInstruction.new_instruction(0x75, "lneg", UnaryOperationInstruction, type_=types.long_t)
fneg = MetaInstruction.new_instruction(0x76, "fneg", UnaryOperationInstruction, type_=types.float_t)
dneg = MetaInstruction.new_instruction(0x77, "dneg", UnaryOperationInstruction, type_=types.double_t)
# Left shift
ishl = MetaInstruction.new_instruction(0x78, "ishl", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
lshl = MetaInstruction.new_instruction(0x79, "lshl", BinaryOperationInstruction, type_a=types.int_t, type_b=types.long_t)
# Right shift
ishr = MetaInstruction.new_instruction(0x7a, "ishr", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
lshr = MetaInstruction.new_instruction(0x7b, "lshr", BinaryOperationInstruction, type_a=types.int_t, type_b=types.long_t)
# Unsigned right shift
iushr = MetaInstruction.new_instruction(0x7c, "iushr", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
lushr = MetaInstruction.new_instruction(0x7d, "lushr", BinaryOperationInstruction, type_a=types.int_t, type_b=types.long_t)
# Logical and
iand = MetaInstruction.new_instruction(0x7e, "iand", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
land = MetaInstruction.new_instruction(0x7f, "land", BinaryOperationInstruction, type_a=types.long_t, type_b=types.long_t)
# Logical or
ior = MetaInstruction.new_instruction(0x80, "ior", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
lor = MetaInstruction.new_instruction(0x81, "lor", BinaryOperationInstruction, type_a=types.long_t, type_b=types.long_t)
# Logical xor
ixor = MetaInstruction.new_instruction(0x82, "ixor", BinaryOperationInstruction, type_a=types.int_t, type_b=types.int_t)
lxor = MetaInstruction.new_instruction(0x83, "lxor", BinaryOperationInstruction, type_a=types.long_t, type_b=types.long_t)

# ------------------------------ Conversions ------------------------------ #

# Integer to ...
i2l = MetaInstruction.new_instruction(0x85, "i2l", ConversionInstruction, type_in=types.int_t, type_out=types.long_t)
i2f = MetaInstruction.new_instruction(0x86, "i2f", ConversionInstruction, type_in=types.int_t, type_out=types.float_t)
i2d = MetaInstruction.new_instruction(0x87, "i2d", ConversionInstruction, type_in=types.int_t, type_out=types.double_t)
# Long to ...
l2i = MetaInstruction.new_instruction(0x88, "l2i", ConversionInstruction, type_in=types.long_t, type_out=types.int_t)
l2f = MetaInstruction.new_instruction(0x89, "l2f", ConversionInstruction, type_in=types.long_t, type_out=types.float_t)
l2d = MetaInstruction.new_instruction(0x8a, "l2d", ConversionInstruction, type_in=types.long_t, type_out=types.double_t)
# Float to ...
f2i = MetaInstruction.new_instruction(0x8b, "f2i", ConversionInstruction, type_in=types.float_t, type_out=types.int_t)
f2l = MetaInstruction.new_instruction(0x8c, "f2l", ConversionInstruction, type_in=types.float_t, type_out=types.long_t)
f2d = MetaInstruction.new_instruction(0x8d, "f2d", ConversionInstruction, type_in=types.float_t, type_out=types.double_t)
# Double to ...
d2i = MetaInstruction.new_instruction(0x8e, "d2i", ConversionInstruction, type_in=types.double_t, type_out=types.int_t)
d2l = MetaInstruction.new_instruction(0x8f, "d2l", ConversionInstruction, type_in=types.double_t, type_out=types.long_t)
d2f = MetaInstruction.new_instruction(0x90, "d2f", ConversionInstruction, type_in=types.double_t, type_out=types.float_t)
# Integer truncation
i2b = MetaInstruction.new_instruction(0x91, "i2b", TruncationInstruction, type_out=types.byte_t)
i2c = MetaInstruction.new_instruction(0x92, "i2c", TruncationInstruction, type_out=types.char_t)
i2s = MetaInstruction.new_instruction(0x93, "i2s", TruncationInstruction, type_out=types.short_t)

checkcast = MetaInstruction.new_instruction(0xc0, "checkcast", CheckCastInstruction)
instanceof = MetaInstruction.new_instruction(0xc1, "instanceof", InstanceOfInstruction)

# ------------------------------ Comparisons ------------------------------ #

lcmp = MetaInstruction.new_instruction(0x94, "lcmp", ComparisonInstruction, type_=types.long_t)
fcmpl = MetaInstruction.new_instruction(0x95, "fcmpl", ComparisonInstruction, type_=types.float_t)
fcmpg = MetaInstruction.new_instruction(0x96, "fcmpg", ComparisonInstruction, type_=types.float_t)
dcmpl = MetaInstruction.new_instruction(0x97, "dcmpl", ComparisonInstruction, type_=types.double_t)
dcmpg = MetaInstruction.new_instruction(0x98, "dcmpg", ComparisonInstruction, type_=types.double_t)

# ------------------------------ Jumps ------------------------------ #

# Compare to 0
ifeq = MetaInstruction.new_instruction(0x99, "ifeq", UnaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
ifne = MetaInstruction.new_instruction(0x9a, "ifne", UnaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
iflt = MetaInstruction.new_instruction(0x9b, "iflt", UnaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
ifge = MetaInstruction.new_instruction(0x9c, "ifge", UnaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
ifgt = MetaInstruction.new_instruction(0x9d, "ifgt", UnaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
ifle = MetaInstruction.new_instruction(0x9e, "ifle", UnaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
# Integer comparison
if_icmpeq = MetaInstruction.new_instruction(0x9f, "if_icmpeq", BinaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
if_icmpne = MetaInstruction.new_instruction(0xa0, "if_icmpne", BinaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
if_icmplt = MetaInstruction.new_instruction(0xa1, "if_icmplt", BinaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
if_icmpge = MetaInstruction.new_instruction(0xa2, "if_icmpge", BinaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
if_icmpgt = MetaInstruction.new_instruction(0xa3, "if_icmpgt", BinaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
if_icmple = MetaInstruction.new_instruction(0xa4, "if_icmple", BinaryComparisonJumpInstruction, {"offset": ">h"}, type_=types.int_t)
# Reference comparison
if_acmpeq = MetaInstruction.new_instruction(0xa5, "if_acmpeq", BinaryComparisonJumpInstruction, {"offset": ">h"}, type_=None)
if_acmpne = MetaInstruction.new_instruction(0xa6, "if_acmpne", BinaryComparisonJumpInstruction, {"offset": ">h"}, type_=None)
ifnull = MetaInstruction.new_instruction(0xc6, "ifnull", UnaryComparisonJumpInstruction, {"offset": ">h"}, type_=None)
ifnonnull = MetaInstruction.new_instruction(0xc7, "ifnonnull", UnaryComparisonJumpInstruction, {"offset": ">h"}, type_=None)
# Other jumps
goto = MetaInstruction.new_instruction(0xa7, "goto", JumpInstruction, {"offset": ">h"})
goto_w = MetaInstruction.new_instruction(0xc8, "goto_w", JumpInstruction, {"offset": ">i"})
jsr = MetaInstruction.new_instruction(0xa8, "jsr", JsrInstruction, {"offset": ">h"})
jsr_w = MetaInstruction.new_instruction(0xc9, "jsr_w", JsrInstruction, {"offset": ">i"})
ret = MetaInstruction.new_instruction(0xa9, "ret", RetInstruction)
tableswitch = MetaInstruction.new_instruction(0xaa, "tableswitch", TableSwitchInstruction)
lookupswitch = MetaInstruction.new_instruction(0xab, "lookupswitch", LookupSwitchInstruction)

# ------------------------------ Returns ------------------------------ #

ireturn = MetaInstruction.new_instruction(0xac, "ireturn", ReturnInstruction, type_=types.int_t)
lreturn = MetaInstruction.new_instruction(0xad, "lreturn", ReturnInstruction, type_=types.long_t)
freturn = MetaInstruction.new_instruction(0xae, "freturn", ReturnInstruction, type_=types.float_t)
dreturn = MetaInstruction.new_instruction(0xaf, "dreturn", ReturnInstruction, type_=types.double_t)
areturn = MetaInstruction.new_instruction(0xb0, "areturn", ReturnInstruction, type_=None)
return_ = MetaInstruction.new_instruction(0xb1, "return", ReturnInstruction, type_=types.void_t)

# ------------------------------ Fields ------------------------------ #

getstatic = MetaInstruction.new_instruction(0xb2, "getstatic", FieldInstruction, {"_index": ">H"}, get=True, static=True)
putstatic = MetaInstruction.new_instruction(0xb3, "putstatic", FieldInstruction, {"_index": ">H"}, get=False, static=True)
getfield = MetaInstruction.new_instruction(0xb4, "getfield", FieldInstruction, {"_index": ">H"}, get=True, static=False)
putfield = MetaInstruction.new_instruction(0xb5, "putfield", FieldInstruction, {"_index": ">H"}, get=False, static=False)

# ------------------------------ Invokes ------------------------------ #

invokevirtual = MetaInstruction.new_instruction(0xb6, "invokevirtual", InvokeVirtualInstruction, {"_index": ">H"})
invokespecial = MetaInstruction.new_instruction(0xb7, "invokespecial", InvokeSpecialInstruction, {"_index": ">H"})
invokestatic = MetaInstruction.new_instruction(0xb8, "invokestatic", InvokeStaticInstruction, {"_index": ">H"})
invokeinterface = MetaInstruction.new_instruction(
    0xb9, "invokeinterface", InvokeInterfaceInstruction, {"_index": ">H", "count": ">B", "_": ">B"},
)
invokedynamic = MetaInstruction.new_instruction(0xba, "invokedynamic", InvokeDynamicInstruction, {"_index": ">H", "_": ">H"})

# ------------------------------ New ------------------------------ #

new = MetaInstruction.new_instruction(0xbb, "new", NewInstruction)
newarray = MetaInstruction.new_instruction(0xbc, "newarray", NewArrayInstruction)
anewarray = MetaInstruction.new_instruction(0xbd, "anewarray", ANewArrayInstruction)
multianewarray = MetaInstruction.new_instruction(0xc5, "multianewarray", MultiANewArrayInstruction)

# ------------------------------ Other ------------------------------ #

iinc = MetaInstruction.new_instruction(0x84, "iinc", IncrementLocalInstruction)

arraylength = MetaInstruction.new_instruction(0xbe, "arraylength", ArrayLengthInstruction)

athrow = MetaInstruction.new_instruction(0xbf, "athrow", AThrowInstruction)

monitorenter = MetaInstruction.new_instruction(0xc2, "monitorenter", MonitorEnterInstruction)
monitorexit = MetaInstruction.new_instruction(0xc3, "monitorexit", MonitorExitInstruction)

wide = MetaInstruction.new_instruction(0xc4, "wide")

# ------------------------------ Internal ------------------------------ #

breakpoint_ = MetaInstruction.new_instruction(0xca, "breakpoint")
impdep1 = MetaInstruction.new_instruction(0xfe, "impdep1")
impdep2 = MetaInstruction.new_instruction(0xff, "impdep2")


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
_opcode_map = {instruction.opcode: instruction for instruction in INSTRUCTIONS}


def read_instructions(class_file: ClassFile, buffer: IO[bytes], length: int) -> Dict[int, Instruction]:
    """
    Reads a list of instructions from the provided buffer.

    :param class_file: The classfile that the instructions belong to.
    :param buffer: The binary buffer to read from.
    :param length: The number of bytes to read.
    :return: The list of instructions (and their offsets) that were read.
    """

    instructions = {}

    offset = buffer.tell()
    wide_ = False

    while offset < length:
        opcode, = buffer.read(1)
        if not opcode in _opcode_map:
            raise ValueError("Unknown opcode: 0x%x." % opcode)
        instruction = _opcode_map[opcode]
        instruction = instruction.__new__(instruction)
        instruction.read(class_file, buffer, wide_)

        instructions[offset] = instruction
        # print(offset, "\t", instruction)

        offset = buffer.tell()
        wide_ = instruction == wide

    return instructions


def write_instructions(instructions: Dict[int, Instruction], class_file: ClassFile, buffer: IO[bytes]) -> None:
    """
    Writes a list of instructions to the buffer.

    :param instructions: The instructions to write.
    :param class_file: The classfile that the instructions belong to.
    :param buffer: The binary buffer to write to.
    """

    wide_ = False
    for offset, instruction in sorted(instructions.items(), key=operator.itemgetter(0)):
        buffer.write(bytes((instruction.opcode,)))
        instruction.write(class_file, buffer, wide_)

        wide_ = instruction == wide
