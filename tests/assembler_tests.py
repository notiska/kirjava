#!/usr/bin/env python3

import unittest

import kirjava


# class TestNoErrors(unittest.TestCase):
#     """
#     Tests that no errors are thrown when assembling.
#     """

#     def setUp(self) -> None:
#         ...


class TestGeneralCases(unittest.TestCase):
    """
    Tests general assembler cases.
    """

    def setUp(self) -> None:
        self.test_class = kirjava.ClassFile("TestClass", is_public=True)

    def test_unordered_fallthrough(self) -> None:
        """
        Tests that the assembler can correctly handle unordered fallthroughs.
        I.e:
         - block 0 (fallthrough -> block 2)
         - block 1 (fallthrough -> return block)
         - block 2 (fallthrough -> block 1)
        The assembler shouldn't throw and should generate gotos where required.
        """

        method = self.test_class.add_method("testUnorderedFallthrough", "()V", is_private=True, is_static=True)
        graph = kirjava.InsnGraph(method)

        block_1 = kirjava.InsnBlock(1)
        block_2 = kirjava.InsnBlock(2)

        block_1.append(kirjava.instructions.iconst_0())
        block_1.append(kirjava.instructions.pop())

        block_2.append(kirjava.instructions.iconst_1())
        block_2.append(kirjava.instructions.pop())

        graph.fallthrough(graph.entry_block, block_2)
        graph.fallthrough(block_2, block_1)
        graph.return_(block_1)

        method.code = graph.assemble()

        graph = kirjava.disassemble(method)

        self.assertEqual(5, len(graph.blocks))
        self.assertEqual(graph[2], graph.out_edges(graph.entry_block)[0].to)
        self.assertEqual(graph[1], graph.out_edges(graph[2])[0].to)
        self.assertEqual(graph.return_block, graph.out_edges(graph[1])[0].to)


class TestHasErrors(unittest.TestCase):
    """
    Tests that the correct errors are thrown when attempting to assemble invalid methods.
    """

    def setUp(self) -> None:
        self.test_class = kirjava.ClassFile("TestClass", is_public=True)

        self.stack_types = {
            kirjava.types.int_t:          kirjava.instructions.iconst_0(),
            kirjava.types.long_t:         kirjava.instructions.lconst_0(),
            kirjava.types.float_t:        kirjava.instructions.fconst_0(),
            kirjava.types.double_t:       kirjava.instructions.dconst_0(),
            kirjava.types.string_t:       kirjava.instructions.ldc(kirjava.constants.Class("java/lang/String")),
            kirjava.types.string_array_t: kirjava.instructions.ldc(kirjava.constants.Class("[Ljava/lang/String;"))
        }
        self.local_types = {
            kirjava.types.int_t:          kirjava.instructions.istore,
            kirjava.types.long_t:         kirjava.instructions.lstore,
            kirjava.types.float_t:        kirjava.instructions.fstore,
            kirjava.types.double_t:       kirjava.instructions.dstore,
            kirjava.types.string_t:       kirjava.instructions.astore,
            kirjava.types.string_array_t: kirjava.instructions.astore,
        }

    def test_unbound_jump(self) -> None:
        """
        Tests that the assembler gives the correct errors when unbound jumps are present.
        """

        method = self.test_class.add_method("testUnboundJump", "()V", is_private=True, is_static=True)
        graph = kirjava.InsnGraph(method)

        graph.entry_block.append(kirjava.instructions.goto(0), do_raise=False)
        graph.return_(graph.entry_block)

        with self.assertRaises(kirjava.verifier.VerifyError) as context:
            method.code = graph.assemble()

        self.assertEqual(kirjava.verifier.Error.Type.INVALID_BLOCK, context.exception.errors[0].type)
        self.assertIn("block has unbound jumps", str(context.exception.errors[0]))

    def test_unbound_return(self) -> None:
        """
        Tests that the assembler gives the correct errors when encountering unbound returns.
        """

        method = self.test_class.add_method("testUnboundReturn", "()V", is_private=True, is_static=True)
        graph = kirjava.InsnGraph(method)

        graph.entry_block.append(kirjava.instructions.return_(), do_raise=False)

        with self.assertRaises(kirjava.verifier.VerifyError) as context:
            method.code = graph.assemble()

        self.assertEqual(kirjava.verifier.Error.Type.INVALID_BLOCK, context.exception.errors[0].type)
        self.assertIn("block has unbound returns", str(context.exception.errors[0]))

    def test_unbound_return_with_value(self) -> None:
        """
        Tests that the assembler gives the correct errors when encountering unbound returns with a value.
        """

        method = self.test_class.add_method("testUnboundReturnWithValue", "()V", is_private=True, is_static=True)
        graph = kirjava.InsnGraph(method)

        graph.entry_block.append(kirjava.instructions.iconst_0())
        graph.entry_block.append(kirjava.instructions.ireturn(), do_raise=False)

        with self.assertRaises(kirjava.verifier.VerifyError) as context:
            method.code = graph.assemble()

        self.assertEqual(kirjava.verifier.Error.Type.INVALID_BLOCK, context.exception.errors[0].type)
        self.assertIn("block has unbound returns", str(context.exception.errors[0]))

    def test_unbound_athrow(self) -> None:
        """
        Tests that the assembler gives the correct errors when encountering an unbound athrow.
        """

        method = self.test_class.add_method("testUnboundAthrow", "()V", is_private=True, is_static=True)
        graph = kirjava.InsnGraph(method)
        graph.return_(graph.entry_block)

        graph.entry_block.append(kirjava.instructions.aconst_null())
        graph.entry_block.append(kirjava.instructions.athrow(), do_raise=False)

        with self.assertRaises(kirjava.verifier.VerifyError) as context:
            method.code = graph.assemble()

        self.assertEqual(kirjava.verifier.Error.Type.INVALID_BLOCK, context.exception.errors[0].type)
        self.assertIn("block has unbound athrows", str(context.exception.errors[0]))

    def test_stack_underflows(self) -> None:
        """
        Tests that the assembler gives the correct errors when encountering certain stack underflows.
        """

        method = self.test_class.add_method("testStackUnderflows", "()V", is_private=True, is_static=True)
        graph = kirjava.InsnGraph(method)
        graph.return_(graph.entry_block)

        for instruction in (kirjava.instructions.pop(), kirjava.instructions.dup()):
            graph.entry_block.clear()

            graph.entry_block.append(instruction)

            with self.assertRaises(kirjava.verifier.VerifyError) as context:
                method.code = graph.assemble()

            self.assertIn("-1 entries", str(context.exception.errors[0]))

        for instruction in (kirjava.instructions.pop2(), kirjava.instructions.dup2()):
            graph.entry_block.clear()

            graph.entry_block.append(instruction)

            with self.assertRaises(kirjava.verifier.VerifyError) as context:
                method.code = graph.assemble()

            self.assertIn("-2 entries", str(context.exception.errors[0]))

        graph.entry_block.clear()

        graph.entry_block.append(kirjava.instructions.swap())

        with self.assertRaises(kirjava.verifier.VerifyError) as context:
            method.code = graph.assemble()

        self.assertEqual(kirjava.verifier.Error.Type.STACK_UNDERFLOW, context.exception.errors[0].type)
        self.assertEqual(kirjava.verifier.Error.Type.STACK_UNDERFLOW, context.exception.errors[1].type)
        self.assertIn("-1 entries", str(context.exception.errors[0]))
        self.assertIn("-2 entries", str(context.exception.errors[1]))

    def test_local_types(self) -> None:
        """
        Test that local types do not accept incorrect values.
        """

        method = self.test_class.add_method("testLocals", "()V", is_private=True, is_static=True)
        graph = kirjava.InsnGraph(method)

        error_insns = []

        for stack_type, push_insn in self.stack_types.items():
            for local_type, store_insn in self.local_types.items():
                if stack_type == local_type:  # No point testing this, we're looking for errors
                    continue

                for index in range(5, 8):
                    error_insn = store_insn(index)
                    error_insns.append((len(graph.entry_block) + 1, error_insn))

                    graph.entry_block.append(push_insn)
                    graph.entry_block.append(error_insn)

        graph.return_(graph.entry_block)

        with self.assertRaises(kirjava.verifier.VerifyError) as context:
            method.code = graph.assemble()

        for error in context.exception.errors:
            if error.type != kirjava.verifier.Error.Type.INVALID_TYPE:
                continue
            source = (error.source.index, error.source.instruction)
            self.assertIn(source, error_insns)
