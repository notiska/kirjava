#!/usr/bin/env python3

__all__ = (
    "arithmetic", "array", "cast", "field", "flow", "invoke", "local", "misc", "stack",

    "INSTRUCTIONS",

    "nop",
    "aconst_null",
    "iconst_m1", "iconst_0", "iconst_1", "iconst_2", "iconst_3", "iconst_4", "iconst_5",
    "lconst_0", "lconst_1",
    "fconst_0", "fconst_1", "fconst_2",
    "dconst_0", "dconst_1",
    "bipush", "sipush", "ldc", "ldc_w", "ldc2_w",
    "iload", "lload", "fload", "dload", "aload",
    "iload_w", "lload_w", "fload_w", "dload_w", "aload_w",
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
    "iinc", "iinc_w",
    "arraylength",
    "athrow",
    "checkcast", "instanceof",
    "monitorenter", "monitorexit",
    "wide",
    "breakpoint_", "impdep1", "impdep2",

    "Instruction",
)

import typing
from functools import cache
from typing import IO

if typing.TYPE_CHECKING:
    from ..fmt import ConstPool
    from ..verify import Verifier


class Instruction:
    """
    A JVM instruction.

    Attributes
    ----------
    offset: int | None
        The offset of this instruction in the code.
        This only serves as extra information as to where the instruction came from,
        setting it to something else should not affect anything.
    opcode: int
        The numeric opcode of this instruction.
    mnemonic: str
        The mnemonic of this instruction.
    mutate_w: bool
        Used to denote mutated wide variants of instructions caused by a prefixed
        `wide` opcode.

    Methods
    -------
    read(stream: IO[bytes], pool: ConstPool) -> Instruction
        Reads an instruction from a binary stream.
    lookup(opcode: int) -> type[Instruction] | None
        Looks up an instruction given an opcode.
    write(self, stream: IO[bytes], pool: ConstPool) -> None
        Writes this instruction to the binary stream.
    verify(self, verifier: Verifier) -> None
        Verifies that this instruction is valid.
    """

    # trace(self, frame: Frame, state: State) -> None
    #     Traces how this instruction would execute in a given frame.

    __slots__ = ("offset",)

    opcode: int
    mnemonic: str
    can_throw: bool

    mutate_w = False

    @classmethod
    def read(cls, stream: IO[bytes], pool: "ConstPool") -> "Instruction":
        """
        Reads an instruction from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        pool: ConstPool
            The class file constant pool.
        """

        raise NotImplementedError("read() is not implemented for %r" % cls)

        # offset = stream.tell()
        # opcode, = stream.read(1)
        #
        # subclass = cls.lookup(opcode)
        # if subclass is None:
        #     raise ValueError("invalid opcode 0x%02x at offset %i" % (opcode, offset))
        #
        # self = subclass.parse(stream, pool)
        # self.offset = offset
        # return self

    @classmethod
    @cache
    def lookup(cls, opcode: int) -> type["Instruction"] | None:
        """
        Looks up an instruction given an opcode.

        Parameters
        ----------
        opcode: int
            The instruction opcode.

        Returns
        -------
        type[Instruction] | None
            The instruction subclass, or `None` if not found.
        """

        for subclass in cls.__subclasses__():
            if subclass.opcode == opcode:
                return subclass
        return None

    @classmethod
    def make(
            cls, opcode: int, mnemonic: str, base: type["Instruction"] | None = None, **kwargs: object,
    ) -> type["Instruction"]:
        namespace = {
            "opcode": opcode,
            "mnemonic": mnemonic,
            **kwargs,
        }
        return type(mnemonic, (base or cls,), namespace)

    def __repr__(self) -> str:
        return "<Instruction(offset=%s, opcode=0x%x, mnemonic=%r)>" % (self.offset, self.opcode, self.mnemonic)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: %s" % (self.offset, self.mnemonic)
        return self.mnemonic

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        """
        Writes this instruction to a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        pool: ConstPool
            The class file constant pool.
        """

        raise NotImplementedError("write() is not implemented for %r" % type(self))

    def verify(self, verifier: "Verifier") -> None:
        """
        Verifies that this instruction is valid.

        Parameters
        ----------
        verifier: Verifier
            The verifier to use and report to.
        """

        ...

    # def trace(self, frame: "Frame", state: "State") -> Optional["State.Step"]:
    #     """
    #     Traces how this instruction would execute in a given frame.
    #
    #     Parameters
    #     ----------
    #     frame: Frame
    #         The current frame.
    #     state: State
    #         The state to add trace information to.
    #
    #     Returns
    #     -------
    #     State.Step | None
    #         Optional information about the trace step.
    #     """
    #
    #     ...  # raise NotImplementedError("trace() is not implemented for %r" % self)


from .arithmetic import *
from .array import *
from .cast import *
from .field import *
from .flow import *
from .invoke import *
from .local import *
from .misc import *
from .stack import *

INSTRUCTIONS = (
    iaload, laload, faload, daload, aaload, baload, caload, saload,
    iastore, lastore, fastore, dastore, aastore, bastore, castore, sastore,
    newarray, anewarray, multianewarray, arraylength,

    i2l, i2f, i2d, l2i, l2f, l2d, f2i, f2l, f2d, d2i, d2l, d2f, i2b, i2c, i2s,
    checkcast, instanceof,

    getstatic, putstatic, getfield, putfield,

    goto, jsr, ret, goto_w, jsr_w,
    ifeq, ifne, iflt, ifge, ifgt, ifle,
    if_icmpeq, if_icmpne, if_icmplt, if_icmpge, if_icmpgt, if_icmple,
    if_acmpeq, if_acmpne,
    ifnull, ifnonnull,
    tableswitch, lookupswitch,

    invokevirtual, invokespecial, invokestatic, invokeinterface, invokedynamic,

    iload, lload, fload, dload, aload,
    iload_0, iload_1, iload_2, iload_3,
    lload_0, lload_1, lload_2, lload_3,
    fload_0, fload_1, fload_2, fload_3,
    dload_0, dload_1, dload_2, dload_3,
    aload_0, aload_1, aload_2, aload_3,
    istore, lstore, fstore, dstore, astore,
    istore_0, istore_1, istore_2, istore_3,
    lstore_0, lstore_1, lstore_2, lstore_3,
    fstore_0, fstore_1, fstore_2, fstore_3,
    dstore_0, dstore_1, dstore_2, dstore_3,
    astore_0, astore_1, astore_2, astore_3,
    iinc,

    nop,
    ireturn, lreturn, freturn, dreturn, areturn, return_,
    athrow,
    monitorenter, monitorexit,
    wide,
    breakpoint_, impdep1, impdep2,

    aconst_null,
    iconst_m1, iconst_0, iconst_1, iconst_2, iconst_3, iconst_4, iconst_5,
    lconst_0, lconst_1,
    fconst_0, fconst_1, fconst_2,
    dconst_0, dconst_1,
    bipush, sipush,
    ldc, ldc_w, ldc2_w,
    new,
    pop, pop2, dup, dup_x1, dup_x2, dup2, dup2_x1, dup2_x2, swap,
    iadd, ladd, fadd, dadd,
    isub, lsub, fsub, dsub,
    imul, lmul, fmul, dmul,
    idiv, ldiv, fdiv, ddiv,
    irem, lrem, frem, drem,
    ineg, lneg, fneg, dneg,
    ishl, lshl, ishr, lshr, iushr, lushr,
    iand, land, ior, lor, ixor, lxor,
    lcmp, fcmpl, fcmpg, dcmpl, dcmpg,
)
