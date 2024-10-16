#!/usr/bin/env python3

import copy
import unittest
from io import BytesIO
from os import SEEK_SET

from kirjava.classfile.fmt import ConstPool
from kirjava.classfile.fmt.constants import *
from kirjava.classfile.insns import *
from kirjava.classfile.insns.array import NewArray
from kirjava.classfile.insns.flow import Jump


class TestInstructions(unittest.TestCase):

    _DEFAULTS = {
        iadd: (), ladd: (), fadd: (), dadd: (), isub: (), lsub: (), fsub: (), dsub: (),
        imul: (), lmul: (), fmul: (), dmul: (), idiv: (), ldiv: (), fdiv: (), ddiv: (),
        irem: (), lrem: (), frem: (), drem: (), ineg: (), lneg: (), fneg: (), dneg: (),
        ishl: (), lshl: (), ishr: (), lshr: (), iushr: (), lushr: (), iand: (), land: (),
        ior: (), lor: (), ixor: (), lxor: (),
        lcmp: (), fcmpl: (), fcmpg: (), dcmpl: (), dcmpg: (),

        iaload: (), laload: (), faload: (), daload: (), aaload: (), baload: (), caload: (), saload: (),
        iastore: (), lastore: (), fastore: (), dastore: (), aastore: (), bastore: (), castore: (), sastore: (),
        newarray: (newarray.INT,),
        anewarray: (ClassInfo(UTF8Info(b"Test")),),
        multianewarray: (ClassInfo(UTF8Info(b"[[LTest;")), 2),
        arraylength: (),

        i2l: (), i2f: (), i2d: (), l2i: (), l2f: (), l2d: (), f2i: (), f2l: (),
        f2d: (), d2i: (), d2l: (), d2f: (), i2b: (), i2c: (), i2s: (),
        checkcast:  (ClassInfo(UTF8Info(b"Test")),),
        instanceof: (ClassInfo(UTF8Info(b"Test")),),

        getstatic: (
            FieldrefInfo(ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"testField1"), UTF8Info(b"I"))),
        ),
        putstatic: (
            FieldrefInfo(ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"testField1"), UTF8Info(b"I"))),
        ),
        getfield: (
            FieldrefInfo(ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"testField2"), UTF8Info(b"Z"))),
        ),
        putfield: (
            FieldrefInfo(ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"testField2"), UTF8Info(b"Z"))),
        ),

        goto: (0x7fff,), jsr: (0x7fff,), ret: (1,), ret_w: (256,), goto_w: (0x7fffffff,), jsr_w: (0x7fffffff,),
        ifeq: (0x7fff,), ifne: (0x7fff,), iflt: (0x7fff,), ifge: (0x7fff,), ifgt: (0x7fff,), ifle: (0x7fff,),
        if_icmpeq: (0x7fff,), if_icmpne: (0x7fff,), if_icmplt: (0x7fff,),
        if_icmpge: (0x7fff,), if_icmpgt: (0x7fff,), if_icmple: (0x7fff,),
        if_acmpeq: (0x7fff,), if_acmpne: (0x7fff,),
        ifnull: (0x7fff,), ifnonnull: (0x7fff,),
        tableswitch: (32, 3, 10, {3: 6, 4: 8, 5: 10, 6: 16, 7: 14, 8: 16, 9: 18, 10: 20}),
        lookupswitch: (32, {5: 10, 6: 12, 8: 16, 10: 20}),
        ireturn: (), lreturn: (), freturn: (), dreturn: (), areturn: (), return_: (),
        athrow: (),

        invokevirtual: (
            MethodrefInfo(ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"testMethod1"), UTF8Info(b"()V"))),
        ),
        invokespecial: (
            MethodrefInfo(ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"<init>"), UTF8Info(b"()V"))),
        ),
        invokestatic: (
            MethodrefInfo(ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"testMethod2"), UTF8Info(b"()V"))),
        ),
        invokeinterface: (
            InterfaceMethodrefInfo(
                ClassInfo(UTF8Info(b"TestInterface")),
                NameAndTypeInfo(UTF8Info(b"testMethod3"), UTF8Info(b"()V")),
            ),
            0, 0,
        ),
        invokedynamic: (InvokeDynamicInfo(0, NameAndTypeInfo(UTF8Info(b"testMethod4"), UTF8Info(b"()V"))), 0),

        iload: (1,), lload: (1,), fload: (1,), dload: (1,), aload: (1,),
        iload_w: (256,), lload_w: (256,), fload_w: (256,), dload_w: (256,), aload_w: (256,),
        iload_0: (), iload_1: (), iload_2: (), iload_3: (),
        lload_0: (), lload_1: (), lload_2: (), lload_3: (),
        fload_0: (), fload_1: (), fload_2: (), fload_3: (),
        dload_0: (), dload_1: (), dload_2: (), dload_3: (),
        aload_0: (), aload_1: (), aload_2: (), aload_3: (),
        istore: (1,), lstore: (1,), fstore: (1,), dstore: (1,), astore: (1,),
        istore_w: (256,), lstore_w: (256,), fstore_w: (256,), dstore_w: (256,), astore_w: (256,),
        istore_0: (), istore_1: (), istore_2: (), istore_3: (),
        lstore_0: (), lstore_1: (), lstore_2: (), lstore_3: (),
        fstore_0: (), fstore_1: (), fstore_2: (), fstore_3: (),
        dstore_0: (), dstore_1: (), dstore_2: (), dstore_3: (),
        astore_0: (), astore_1: (), astore_2: (), astore_3: (),
        iinc: (1, 1), iinc_w: (256, 256),

        nop: (), wide: (),
        monitorenter: (), monitorexit: (),
        breakpoint_: (), impdep1: (), impdep2: (),

        aconst_null: (),
        iconst_m1: (), iconst_0: (), iconst_1: (), iconst_2: (), iconst_3: (), iconst_4: (), iconst_5: (),
        lconst_0: (), lconst_1: (),
        fconst_0: (), fconst_1: (), fconst_2: (),
        dconst_0: (), dconst_1: (),
        bipush: (0x7f,), sipush: (0x7fff,),
        ldc:    (StringInfo(UTF8Info(b"Test")),),
        ldc_w:  (StringInfo(UTF8Info(b"Test")),),
        ldc2_w: (StringInfo(UTF8Info(b"Test")),),
        new: (ClassInfo(UTF8Info(b"Test")),),
        pop: (), pop2: (), dup: (), dup_x1: (), dup_x2: (), dup2: (), dup2_x1: (), dup2_x2: (), swap: (),
    }

    def setUp(self) -> None:
        self.pool = ConstPool()

    def test_abc_attrs(self) -> None:
        for subclass in INSTRUCTIONS:
            with self.subTest(subclass.mnemonic):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest(f"Missing default init values for {subclass!r}.")
                insn = subclass(*init)
                self.assertIsInstance(insn.opcode, int)
                self.assertIsInstance(insn.mnemonic, str)
                # self.assertIsInstance(insn.since, Version)  # FIXME
                self.assertIsInstance(insn.lt_throws, frozenset)
                self.assertIsInstance(insn.rt_throws, frozenset)

    def test_repr_str_eq_copy(self) -> None:
        for subclass in INSTRUCTIONS:
            with self.subTest(subclass.mnemonic):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest(f"Missing default init values for {subclass!r}.")
                insn_no_offset = subclass(*init)

                print(str(insn_no_offset), repr(insn_no_offset), end=" ")
                insn_offset = copy.copy(insn_no_offset)
                insn_offset.offset = 30
                print(str(insn_offset), repr(insn_offset))

                self.assertEqual(insn_no_offset, insn_no_offset)
                self.assertEqual(insn_no_offset, insn_offset)
                self.assertIsNot(insn_no_offset, insn_offset)

                insn_deepcopy = copy.deepcopy(insn_offset)
                self.assertEqual(insn_deepcopy, insn_offset)
                self.assertEqual(insn_deepcopy, insn_no_offset)
                self.assertIsNot(insn_deepcopy, insn_offset)
                self.assertIsNot(insn_deepcopy, insn_no_offset)
                # TODO: More tests for individual attributes, to ensure that they have been deep copied.

                insn_offset_repr = repr(insn_offset)
                insn_offset_repr = insn_offset_repr.replace(f"(offset={insn_offset.offset})", "")
                insn_offset_repr = insn_offset_repr.replace(f"offset={insn_offset.offset}, ", "")
                self.assertEqual(repr(insn_no_offset), insn_offset_repr)

                # Jumps have a delta offset change in the str, so this doesn't work.
                if not isinstance(insn_no_offset, Jump):
                    self.assertEqual(str(insn_no_offset), str(insn_offset).replace(f"{insn_offset.offset}:", ""))

    def test_symmetric_read_write(self) -> None:
        for subclass in INSTRUCTIONS:
            with self.subTest(subclass.mnemonic):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest(f"Missing default init values for {subclass!r}.")
                insn_init = subclass(*init)

                data = BytesIO()
                insn_init.write(data, self.pool)
                data_first = data.getvalue()
                data.seek(0, SEEK_SET)

                insn_read = Instruction.read(data, self.pool)
                self.assertEqual(insn_init, insn_read)
                if data.read():
                    self.fail("Instruction underread.")

                data = BytesIO()
                insn_read.write(data, self.pool)
                self.assertEqual(data_first, data.getvalue())

    # TODO: Linkage tests.
