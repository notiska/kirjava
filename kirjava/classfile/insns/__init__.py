#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "arithmetic", "array", "cast", "field", "flow", "invoke", "local", "misc", "stack",

    "INSTRUCTIONS",

    "iadd", "ladd", "fadd", "dadd",
    "isub", "lsub", "fsub", "dsub",
    "imul", "lmul", "fmul", "dmul",
    "idiv", "ldiv", "fdiv", "ddiv",
    "irem", "lrem", "frem", "drem",
    "ineg", "lneg", "fneg", "dneg",
    "ishl", "lshl", "ishr", "lshr", "iushr", "lushr",
    "iand", "land", "ior", "lor", "ixor", "lxor",
    "lcmp", "fcmpl", "fcmpg", "dcmpl", "dcmpg",
    "iaload", "laload", "faload", "daload", "aaload", "baload", "caload", "saload",
    "iastore", "lastore", "fastore", "dastore", "aastore", "bastore", "castore", "sastore",
    "newarray", "anewarray", "multianewarray", "arraylength",
    "i2l", "i2f", "i2d", "l2i", "l2f", "l2d", "f2i", "f2l", "f2d", "d2i", "d2l", "d2f", "i2b", "i2c", "i2s",
    "checkcast", "instanceof",
    "getstatic", "putstatic", "getfield", "putfield",
    "goto", "jsr", "ret", "ret_w", "goto_w", "jsr_w",
    "ifeq", "ifne", "iflt", "ifge", "ifgt", "ifle",
    "if_icmpeq", "if_icmpne", "if_icmplt", "if_icmpge", "if_icmpgt", "if_icmple",
    "if_acmpeq", "if_acmpne",
    "ifnull", "ifnonnull",
    "tableswitch", "lookupswitch",
    "ireturn", "lreturn", "freturn", "dreturn", "areturn", "return_",
    "athrow",
    "invokevirtual", "invokespecial", "invokestatic", "invokeinterface", "invokedynamic",
    "iload", "lload", "fload", "dload", "aload",
    "iload_w", "lload_w", "fload_w", "dload_w", "aload_w",
    "iload_0", "iload_1", "iload_2", "iload_3",
    "lload_0", "lload_1", "lload_2", "lload_3",
    "fload_0", "fload_1", "fload_2", "fload_3",
    "dload_0", "dload_1", "dload_2", "dload_3",
    "aload_0", "aload_1", "aload_2", "aload_3",
    "istore", "lstore", "fstore", "dstore", "astore",
    "istore_w", "lstore_w", "fstore_w", "dstore_w", "astore_w",
    "istore_0", "istore_1", "istore_2", "istore_3",
    "lstore_0", "lstore_1", "lstore_2", "lstore_3",
    "fstore_0", "fstore_1", "fstore_2", "fstore_3",
    "dstore_0", "dstore_1", "dstore_2", "dstore_3",
    "astore_0", "astore_1", "astore_2", "astore_3",
    "iinc", "iinc_w",
    "nop", "wide",
    "monitorenter", "monitorexit",
    "breakpoint_", "impdep1", "impdep2",
    "aconst_null",
    "iconst_m1", "iconst_0", "iconst_1", "iconst_2", "iconst_3", "iconst_4", "iconst_5",
    "lconst_0", "lconst_1",
    "fconst_0", "fconst_1", "fconst_2",
    "dconst_0", "dconst_1",
    "bipush", "sipush",
    "ldc", "ldc_w", "ldc2_w",
    "new",
    "pop", "pop2", "dup", "dup_x1", "dup_x2", "dup2", "dup2_x1", "dup2_x2", "swap",

    "Instruction",
    "CodeIOWrapper",
)

import typing
from io import BytesIO
from os import SEEK_SET
from typing import IO  # , Self  # FIXME: Ditch support for 3.10 at some point.
from typing_extensions import Buffer

if typing.TYPE_CHECKING:
    from ..fmt import ConstPool
    from ..version import Version
    from ...model.types import Class


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
    lt_throws: frozenset[Class]
        The types of exception that this instruction can throw at link time.
    rt_throws: frozenset[Class]
        The types of exception that this instruction can throw at run time.
    mutated: bool
        Used to denote mutated wide variants of instructions caused by a prefixed
        `wide` opcode.
    linked: bool
        Used to denote that this is a linked version of an instruction.

    Methods
    -------
    lookup(opcode: int, mutated: bool = False) -> type[Instruction] | None
        Looks up an instruction given an opcode.
    read(stream: IO[bytes], pool: ConstPool) -> Instruction
        Reads an instruction from a binary stream.

    write(self, stream: IO[bytes], pool: ConstPool) -> None
        Writes this instruction to the binary stream.
    link(self) -> Instruction
        Creates a linked version of this instruction.
    verify(self, verifier: Verifier) -> None
        Verifies that this instruction is valid.
    """

    # trace(self, frame: Frame, state: State) -> None
    #     Traces how this instruction would execute in a given frame.

    __slots__ = ("offset",)

    opcode: int
    mnemonic: str
    since: "Version"  # TODO: This (information is a little annoying to track down).

    lt_throws: frozenset["Class"]
    rt_throws: frozenset["Class"]

    mutated = False
    linked  = False

    _cache: dict[int, type["Instruction"] | None] = {}

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Instruction":
        """
        Instruction internal read.
        """

        raise NotImplementedError(f"_read() is not implemented for {cls!r}")

    @classmethod
    def lookup(cls, opcode: int, mutated: bool = False) -> type["Instruction"] | None:
        """
        Looks up an instruction given an opcode.

        Parameters
        ----------
        opcode: int
            The instruction opcode.
        mutated: bool
            Whether to look up a wide variant of the instruction.

        Returns
        -------
        type[Instruction] | None
            The instruction subclass, or `None` if not found.
        """

        subclasses = cls.__subclasses__().copy()

        if mutated:
            while subclasses:
                subclass = subclasses.pop()
                try:
                    if subclass.opcode == opcode and subclass.mutated:
                        return subclass
                except AttributeError:
                    ...  # Some instructions (abstract ones) don't explicitly define opcodes.
                subclasses.extend(subclass.__subclasses__())
        else:
            while subclasses:
                subclass = subclasses.pop()
                try:
                    if subclass.opcode == opcode and not subclass.mutated:
                        return subclass
                except AttributeError:
                    ...
                subclasses.extend(subclass.__subclasses__())
        return None

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

        offset = stream.tell()
        opcode, = stream.read(1)

        subclass: type[Instruction] | None = cls._cache.get(opcode)
        if subclass is None:
            subclass = cls.lookup(opcode)
            cls._cache[opcode] = subclass
        if subclass is None:
            # self = Unknown(opcode)
            raise ValueError(f"unknown opcode 0x{opcode:02x} at offset {offset}")
        self = subclass._read(stream, pool)
        self.offset = offset
        return self

        # if isinstance(self, wide):
        #     # We'll check if the next instruction has a wide mutation in order to essentially "merge" the `wide`
        #     # instruction that prefixes it with itself. If it does not have a wide mutation, we'll just continue
        #     # reading. This may simply be because the bytecode has `wide` instructions randomly in it.
        #     opcode, = stream.read(1)
        #     subclass = Instruction.lookup(opcode, True)
        #     if subclass is not None:
        #         instruction = subclass.read(stream, pool)
        #     else:
        #         stream.seek(-1, SEEK_CUR)  # Move back one byte as we attempted to read an opcode.

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

    def __init__(self) -> None:
        self.offset: int | None = None

    def __copy__(self) -> "Instruction":
        copy = type(self)()
        copy.offset = self.offset
        return copy

    def __repr__(self) -> str:
        # return "<Instruction(offset=%s, opcode=0x%x, mnemonic=%r)>" % (self.offset, self.opcode, self.mnemonic)
        raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:{self.mnemonic}"
        return self.mnemonic

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(f"== is not implemented for {type(self)!r}")

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

        raise NotImplementedError(f"write() is not implemented for {type(self)!r}")

    def link(self) -> "Instruction":  # TODO: This.
        """
        Creates a linked version of this instruction.

        Returns
        -------
        Instruction
            The linked instruction.
        """

        # if self.linked
        #     return self
        raise NotImplementedError(f"link() is not implemented for {type(self)!r}")

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


class CodeIOWrapper(BytesIO):  # Extended only for type hinting, BufferedIOBase doesn't seem to work.
    """
    A stream wrapper for code in a method, so that the offset is correct as per the
    base of the code, rather than the base of the class file.

    Attributes
    ----------
    delegate: IO[bytes]
        The underlying stream to read from.
    base: int
        The base offset of the code.
    """

    # __slots__ = ("delegate", "base")  # No slots on BytesIO, unfortunately.

    def __init__(self, delegate: IO[bytes], base: int | None) -> None:
        super().__init__()
        self.delegate = delegate
        self.base = base if base is not None else delegate.tell()  # base or delegate.tell()

    def read(self, size: int | None = -1) -> bytes:
        if size is None:
            size = -1
        return self.delegate.read(size)

    def tell(self) -> int:
        return self.delegate.tell() - self.base

    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        if whence == SEEK_SET:
            offset += self.base
        return self.delegate.seek(offset, whence)

    def write(self, data: Buffer) -> int:
        return self.delegate.write(data)


from .arithmetic import *  # noqa E402
from .array import *       # noqa E402
from .cast import *        # noqa E402
from .field import *       # noqa E402
from .flow import *        # noqa E402
from .invoke import *      # noqa E402
from .local import *       # noqa E402
from .misc import *        # noqa E402
from .stack import *       # noqa E402

INSTRUCTIONS = (
    iadd, ladd, fadd, dadd,
    isub, lsub, fsub, dsub,
    imul, lmul, fmul, dmul,
    idiv, ldiv, fdiv, ddiv,
    irem, lrem, frem, drem,
    ineg, lneg, fneg, dneg,
    ishl, lshl, ishr, lshr, iushr, lushr,
    iand, land, ior, lor, ixor, lxor,
    lcmp, fcmpl, fcmpg, dcmpl, dcmpg,

    iaload, laload, faload, daload, aaload, baload, caload, saload,
    iastore, lastore, fastore, dastore, aastore, bastore, castore, sastore,
    newarray, anewarray, multianewarray, arraylength,

    i2l, i2f, i2d, l2i, l2f, l2d, f2i, f2l, f2d, d2i, d2l, d2f, i2b, i2c, i2s,
    checkcast, instanceof,

    getstatic, putstatic, getfield, putfield,

    goto, jsr, ret, ret_w, goto_w, jsr_w,
    ifeq, ifne, iflt, ifge, ifgt, ifle,
    if_icmpeq, if_icmpne, if_icmplt, if_icmpge, if_icmpgt, if_icmple,
    if_acmpeq, if_acmpne,
    ifnull, ifnonnull,
    tableswitch, lookupswitch,
    ireturn, lreturn, freturn, dreturn, areturn, return_,
    athrow,

    invokevirtual, invokespecial, invokestatic, invokeinterface, invokedynamic,

    iload, lload, fload, dload, aload,
    iload_w, lload_w, fload_w, dload_w, aload_w,
    iload_0, iload_1, iload_2, iload_3,
    lload_0, lload_1, lload_2, lload_3,
    fload_0, fload_1, fload_2, fload_3,
    dload_0, dload_1, dload_2, dload_3,
    aload_0, aload_1, aload_2, aload_3,
    istore, lstore, fstore, dstore, astore,
    istore_w, lstore_w, fstore_w, dstore_w, astore_w,
    istore_0, istore_1, istore_2, istore_3,
    lstore_0, lstore_1, lstore_2, lstore_3,
    fstore_0, fstore_1, fstore_2, fstore_3,
    dstore_0, dstore_1, dstore_2, dstore_3,
    astore_0, astore_1, astore_2, astore_3,
    iinc, iinc_w,

    nop, wide,
    monitorenter, monitorexit,
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
)
