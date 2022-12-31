#!/usr/bin/env python3

"""
An example usage of Kirjava that creates a class named ControlFlow with some basic control flow constructs in it.
"""

import kirjava


def make_main(control_flow: kirjava.ClassFile) -> None:
    """
    Creates the main method in the class.
    """

    main = control_flow.add_method("main", "([Ljava/lang/String;)V", is_public=True, is_static=True)
    graph = kirjava.analysis.InsnGraph(main)

    # Set up the blocks that we'll need
    error_block  = kirjava.analysis.InsnBlock(graph)
    invoke_block = kirjava.analysis.InsnBlock(graph)

    graph.entry_block.add(kirjava.instructions.aload_0())
    graph.entry_block.add(kirjava.instructions.arraylength())
    graph.entry_block.add(kirjava.instructions.iconst_3())
    graph.entry_block.jump(invoke_block, kirjava.instructions.if_icmpge)
    graph.entry_block.fallthrough(error_block)

    error_block.add(kirjava.instructions.getstatic("java/lang/System", "out", "Ljava/io/PrintStream;"))
    error_block.add(kirjava.instructions.ldc(kirjava.constants.String("Please enter 3 or more arguments!")))
    error_block.add(kirjava.instructions.invokevirtual("java/io/PrintStream", "println", "(Ljava/lang/Object;)V"))
    error_block.return_()

    invoke_block.add(kirjava.instructions.aload_0())
    invoke_block.add(kirjava.instructions.dup())
    invoke_block.add(kirjava.instructions.dup())
    invoke_block.add(kirjava.instructions.iconst_0())
    invoke_block.add(kirjava.instructions.aaload())
    invoke_block.add(kirjava.instructions.invokestatic("ControlFlow", "testConditionals", "(Ljava/lang/String;)V"))
    invoke_block.add(kirjava.instructions.iconst_1())
    invoke_block.add(kirjava.instructions.aaload())
    invoke_block.add(kirjava.instructions.swap())
    invoke_block.add(kirjava.instructions.iconst_2())
    invoke_block.add(kirjava.instructions.aaload())
    invoke_block.add(kirjava.instructions.invokestatic("ControlFlow", "testLoop", "(Ljava/lang/String;Ljava/lang/String;)V"))
    invoke_block.return_()

    main.code = graph.assemble()


def make_conditionals(control_flow: kirjava.ClassFile) -> None:
    """
    Makes the testConditionals method.
    """

    test_conditionals = control_flow.add_method(
        "testConditionals", "(Ljava/lang/String;)V", is_private=True, is_static=True,
    )
    graph = kirjava.analysis.InsnGraph(test_conditionals)
 
    doesnt_contain_a = kirjava.analysis.InsnBlock(graph)
    length_check     = kirjava.analysis.InsnBlock(graph)
    longer_than_5    = kirjava.analysis.InsnBlock(graph)
    shorter_than_5   = kirjava.analysis.InsnBlock(graph)

    graph.entry_block.add(kirjava.instructions.aload_0())
    graph.entry_block.add(kirjava.instructions.ldc(kirjava.constants.String("a")))
    graph.entry_block.add(kirjava.instructions.invokevirtual("java/lang/String", "contains", "(Ljava/lang/CharSequence;)Z"))
    graph.entry_block.jump(length_check, kirjava.instructions.ifne)
    graph.entry_block.fallthrough(doesnt_contain_a)

    doesnt_contain_a.add(kirjava.instructions.getstatic("java/lang/System", "out", "Ljava/io/PrintStream;"))
    doesnt_contain_a.add(kirjava.instructions.ldc(kirjava.constants.String("First argument doesn't contain 'a' character.")))
    doesnt_contain_a.add(kirjava.instructions.invokevirtual("java/io/PrintStream", "println", "(Ljava/lang/Object;)V"))
    doesnt_contain_a.return_()

    length_check.add(kirjava.instructions.aload_0())
    length_check.add(kirjava.instructions.invokevirtual("java/lang/String", "length", "()I"))
    length_check.add(kirjava.instructions.iconst_5())
    length_check.jump(longer_than_5, kirjava.instructions.if_icmpge)
    length_check.fallthrough(shorter_than_5)

    longer_than_5.add(kirjava.instructions.getstatic("java/lang/System", "out", "Ljava/io/PrintStream;"))
    longer_than_5.add(kirjava.instructions.ldc(kirjava.constants.String("First argument is 5 characters or longer.")))
    longer_than_5.add(kirjava.instructions.invokevirtual("java/io/PrintStream", "println", "(Ljava/lang/Object;)V"))
    longer_than_5.return_()

    shorter_than_5.add(kirjava.instructions.getstatic("java/lang/System", "out", "Ljava/io/PrintStream;"))
    shorter_than_5.add(kirjava.instructions.ldc(kirjava.constants.String("First argument is shorter than 5 characters.")))
    shorter_than_5.add(kirjava.instructions.invokevirtual("java/io/PrintStream", "println", "(Ljava/lang/Object;)V"))
    shorter_than_5.return_()

    test_conditionals.code = graph.assemble()


def make_loop(control_flow: kirjava.ClassFile) -> None:
    """
    Makes the testLoop method.
    """

    test_loop = control_flow.add_method(
        "testLoop", "(Ljava/lang/String;Ljava/lang/String;)V", is_private=True, is_static=True,
    )
    graph = kirjava.analysis.InsnGraph(test_loop)

    exponent_loop_body  = kirjava.analysis.InsnBlock(graph)
    result_check        = kirjava.analysis.InsnBlock(graph)
    infinite_loop_entry = kirjava.analysis.InsnBlock(graph)
    infinite_loop_body  = kirjava.analysis.InsnBlock(graph)
    return_block        = kirjava.analysis.InsnBlock(graph)

    # Decode the arguments into integers, if possible
    graph.entry_block.add(kirjava.instructions.aload_1())
    graph.entry_block.add(kirjava.instructions.invokestatic("java/lang/Integer", "parseInt", "(Ljava/lang/String;)I"))
    graph.entry_block.add(kirjava.instructions.aload_0())
    graph.entry_block.add(kirjava.instructions.invokestatic("java/lang/Integer", "parseInt", "(Ljava/lang/String;)I"))
    graph.entry_block.add(kirjava.instructions.dup())
    # Store the integers in locals, ready for the loop
    graph.entry_block.add(kirjava.instructions.istore_0())  # We'll store the original number in this local
    graph.entry_block.add(kirjava.instructions.istore_1())  # We'll store the exponentiation result in this local
    graph.entry_block.add(kirjava.instructions.istore_2())  # And we'll store the exponent in this local
    graph.entry_block.add(kirjava.instructions.iinc(2, -1))
    graph.entry_block.add(kirjava.instructions.iload_2())
    graph.entry_block.jump(result_check, kirjava.instructions.ifle)  # If the exponent <= 0, jump straight to the result check
    graph.entry_block.fallthrough(exponent_loop_body)

    exponent_loop_body.add(kirjava.instructions.iload_0())
    exponent_loop_body.add(kirjava.instructions.iload_1())
    exponent_loop_body.add(kirjava.instructions.imul())
    exponent_loop_body.add(kirjava.instructions.istore_1())
    exponent_loop_body.add(kirjava.instructions.iinc(2, -1))  # Decrement the exponent
    exponent_loop_body.add(kirjava.instructions.iload_2())
    exponent_loop_body.jump(exponent_loop_body, kirjava.instructions.ifgt)  # If exponent > 0, jump back to start of loop
    exponent_loop_body.fallthrough(result_check)

    result_check.add(kirjava.instructions.getstatic("java/lang/System", "out", "Ljava/io/PrintStream;"))
    result_check.add(kirjava.instructions.ldc(kirjava.constants.String("Result is: %d")))
    result_check.add(kirjava.instructions.iconst_1())
    result_check.add(kirjava.instructions.anewarray(kirjava.types.object_array_t))
    result_check.add(kirjava.instructions.dup())
    result_check.add(kirjava.instructions.iconst_0())
    result_check.add(kirjava.instructions.iload_1())
    result_check.add(kirjava.instructions.invokestatic("java/lang/Integer", "valueOf", "(I)Ljava/lang/Integer;"))
    result_check.add(kirjava.instructions.aastore())
    result_check.add(kirjava.instructions.invokestatic("java/lang/String", "format", "(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;"))
    result_check.add(kirjava.instructions.invokevirtual("java/io/PrintStream", "println", "(Ljava/lang/Object;)V"))
    result_check.add(kirjava.instructions.iload_1())
    result_check.add(kirjava.instructions.sipush(kirjava.constants.Integer(1024)))
    result_check.jump(infinite_loop_entry, kirjava.instructions.if_icmpgt)
    result_check.fallthrough(return_block)

    infinite_loop_entry.add(kirjava.instructions.getstatic("java/lang/System", "out", "Ljava/io/PrintStream;"))
    infinite_loop_entry.add(kirjava.instructions.ldc(kirjava.constants.String("Result is greater than 1024, entering infinite loop...")))
    infinite_loop_entry.add(kirjava.instructions.invokevirtual("java/io/PrintStream", "println", "(Ljava/lang/Object;)V"))
    infinite_loop_entry.fallthrough(infinite_loop_body)

    infinite_loop_body.jump(infinite_loop_body)  # goto is used by default, so we don't need to specify anything

    return_block.return_()

    test_loop.code = graph.assemble()


if __name__ == "__main__":
    kirjava.initialise()

    control_flow = kirjava.ClassFile("ControlFlow", is_public=True)

    make_main(control_flow)
    make_conditionals(control_flow)
    make_loop(control_flow)

    with open("ControlFlow.class", "wb") as stream:
        control_flow.write(stream)
