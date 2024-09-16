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

    # Set up the blocks that we'll need. Using `graph.block()` and manually creating blocks both work.
    error_block  = graph.block()  # kirjava.analysis.InsnBlock(1)
    invoke_block = graph.block()  # kirjava.analysis.InsnBlock(2)

    graph.entry_block.append(kirjava.instructions.aload_0)
    graph.entry_block.append(kirjava.instructions.arraylength)
    graph.entry_block.append(kirjava.instructions.iconst_3)
    graph.jump(graph.entry_block, invoke_block, kirjava.instructions.if_icmpge)
    graph.fallthrough(graph.entry_block, error_block)

    error_block.append(kirjava.instructions.getstatic(kirjava.constants.FieldRef(
        "java/lang/System", "out", "Ljava/io/PrintStream;",
    )))
    error_block.append(kirjava.instructions.ldc(kirjava.constants.String("Please enter 3 or more arguments!")))
    error_block.append(kirjava.instructions.invokevirtual(kirjava.constants.MethodRef(
        "java/io/PrintStream", "println", "(Ljava/lang/Object;)V",
    )))
    graph.return_(error_block)

    invoke_block.append(kirjava.instructions.aload_0)
    invoke_block.append(kirjava.instructions.dup)
    invoke_block.append(kirjava.instructions.dup)
    invoke_block.append(kirjava.instructions.iconst_0)
    invoke_block.append(kirjava.instructions.aaload)
    invoke_block.append(kirjava.instructions.invokestatic(kirjava.constants.MethodRef(
        "ControlFlow", "testConditionals", "(Ljava/lang/String;)V",
    )))
    invoke_block.append(kirjava.instructions.iconst_1)
    invoke_block.append(kirjava.instructions.aaload)
    invoke_block.append(kirjava.instructions.swap)
    invoke_block.append(kirjava.instructions.iconst_2)
    invoke_block.append(kirjava.instructions.aaload)
    invoke_block.append(kirjava.instructions.invokestatic(kirjava.constants.MethodRef(
        "ControlFlow", "testLoop", "(Ljava/lang/String;Ljava/lang/String;)V",
    )))
    graph.return_(invoke_block)

    main.code = graph.assemble()


def make_conditionals(control_flow: kirjava.ClassFile) -> None:
    """
    Makes the testConditionals method.
    """

    test_conditionals = control_flow.add_method(
        "testConditionals", "(Ljava/lang/String;)V", is_private=True, is_static=True,
    )
    graph = kirjava.analysis.InsnGraph(test_conditionals)
 
    doesnt_contain_a = graph.block()  # kirjava.analysis.InsnBlock(1)
    length_check     = graph.block()  # kirjava.analysis.InsnBlock(2)
    longer_than_5    = graph.block()  # kirjava.analysis.InsnBlock(3)
    shorter_than_5   = graph.block()  # kirjava.analysis.InsnBlock(4)

    graph.entry_block.append(kirjava.instructions.aload_0)
    graph.entry_block.append(kirjava.instructions.ldc(kirjava.constants.String("a")))
    graph.entry_block.append(kirjava.instructions.invokevirtual(kirjava.constants.MethodRef(
        "java/lang/String", "contains", "(Ljava/lang/CharSequence;)Z",
    )))
    graph.jump(graph.entry_block, length_check, kirjava.instructions.ifne)
    graph.fallthrough(graph.entry_block, doesnt_contain_a)

    doesnt_contain_a.append(kirjava.instructions.getstatic(kirjava.constants.FieldRef(
        "java/lang/System", "out", "Ljava/io/PrintStream;",
    )))
    doesnt_contain_a.append(kirjava.instructions.ldc(kirjava.constants.String("First argument doesn't contain 'a' character.")))
    doesnt_contain_a.append(kirjava.instructions.invokevirtual(kirjava.constants.MethodRef(
        "java/io/PrintStream", "println", "(Ljava/lang/Object;)V",
    )))
    graph.return_(doesnt_contain_a)

    length_check.append(kirjava.instructions.aload_0)
    length_check.append(kirjava.instructions.invokevirtual(kirjava.constants.MethodRef("java/lang/String", "length", "()I")))
    length_check.append(kirjava.instructions.iconst_5)
    # You can actually notice that with this jump, it should really be flipped, as the fallthrough is actually to the
    # longer_than_5 block. Thankfully, the assembler handles this for us by generating the appropriate gotos.
    graph.jump(length_check, longer_than_5, kirjava.instructions.if_icmpge)
    graph.fallthrough(length_check, shorter_than_5)

    longer_than_5.append(kirjava.instructions.getstatic(kirjava.constants.FieldRef(
        "java/lang/System", "out", "Ljava/io/PrintStream;",
    )))
    longer_than_5.append(kirjava.instructions.ldc(kirjava.constants.String("First argument is 5 characters or longer.")))
    longer_than_5.append(kirjava.instructions.invokevirtual(kirjava.constants.MethodRef(
        "java/io/PrintStream", "println", "(Ljava/lang/Object;)V",
    )))
    graph.return_(longer_than_5)

    shorter_than_5.append(kirjava.instructions.getstatic(kirjava.constants.FieldRef(
        "java/lang/System", "out", "Ljava/io/PrintStream;",
    )))
    shorter_than_5.append(kirjava.instructions.ldc(kirjava.constants.String("First argument is shorter than 5 characters.")))
    shorter_than_5.append(kirjava.instructions.invokevirtual(kirjava.constants.MethodRef(
        "java/io/PrintStream", "println", "(Ljava/lang/Object;)V",
    )))
    graph.return_(shorter_than_5)

    test_conditionals.code = graph.assemble()


def make_loop(control_flow: kirjava.ClassFile) -> None:
    """
    Makes the testLoop method.
    """

    test_loop = control_flow.add_method(
        "testLoop", "(Ljava/lang/String;Ljava/lang/String;)V", is_private=True, is_static=True,
    )
    graph = kirjava.analysis.InsnGraph(test_loop)

    exponent_loop_body  = graph.block()  # kirjava.analysis.InsnBlock(1)
    result_check        = graph.block()  # kirjava.analysis.InsnBlock(2)
    infinite_loop_entry = graph.block()  # kirjava.analysis.InsnBlock(3)
    infinite_loop_body  = graph.block()  # kirjava.analysis.InsnBlock(4)
    return_block        = graph.block()  # kirjava.analysis.InsnBlock(5)

    # Decode the arguments into integers, if possible
    graph.entry_block.append(kirjava.instructions.aload_1)
    graph.entry_block.append(kirjava.instructions.invokestatic(kirjava.constants.MethodRef(
        "java/lang/Integer", "parseInt", "(Ljava/lang/String;)I",
    )))
    graph.entry_block.append(kirjava.instructions.aload_0)
    graph.entry_block.append(kirjava.instructions.invokestatic(kirjava.constants.MethodRef(
        "java/lang/Integer", "parseInt", "(Ljava/lang/String;)I",
    )))
    graph.entry_block.append(kirjava.instructions.dup)
    # Store the integers in locals, ready for the loop
    graph.entry_block.append(kirjava.instructions.istore_0)  # We'll store the original number in this local
    graph.entry_block.append(kirjava.instructions.istore_1)  # We'll store the exponentiation result in this local
    graph.entry_block.append(kirjava.instructions.istore_2)  # And we'll store the exponent in this local
    graph.entry_block.append(kirjava.instructions.iinc(2, -1))
    graph.entry_block.append(kirjava.instructions.iload_2)
    graph.jump(graph.entry_block, result_check, kirjava.instructions.ifle)  # If the exponent <= 0, jump straight to the result check
    graph.fallthrough(graph.entry_block, exponent_loop_body)

    exponent_loop_body.append(kirjava.instructions.iload_0)
    exponent_loop_body.append(kirjava.instructions.iload_1)
    exponent_loop_body.append(kirjava.instructions.imul)
    exponent_loop_body.append(kirjava.instructions.istore_1)
    exponent_loop_body.append(kirjava.instructions.iinc(2, -1))  # Decrement the exponent
    exponent_loop_body.append(kirjava.instructions.iload_2)
    graph.jump(exponent_loop_body, exponent_loop_body, kirjava.instructions.ifgt)  # If exponent > 0, jump back to start of loop
    graph.fallthrough(exponent_loop_body, result_check)

    result_check.append(kirjava.instructions.getstatic(kirjava.constants.FieldRef(
        "java/lang/System", "out", "Ljava/io/PrintStream;",
    )))
    result_check.append(kirjava.instructions.ldc(kirjava.constants.String("Result is: %d")))
    result_check.append(kirjava.instructions.iconst_1)
    result_check.append(kirjava.instructions.anewarray(kirjava.types.Array(kirjava.types.object_t)))
    result_check.append(kirjava.instructions.dup)
    result_check.append(kirjava.instructions.iconst_0)
    result_check.append(kirjava.instructions.iload_1)
    result_check.append(kirjava.instructions.invokestatic(kirjava.constants.MethodRef(
        "java/lang/Integer", "valueOf", "(I)Ljava/lang/Integer;",
    )))
    result_check.append(kirjava.instructions.aastore)
    result_check.append(kirjava.instructions.invokestatic(kirjava.constants.MethodRef(
        "java/lang/String", "format", "(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;",
    )))
    result_check.append(kirjava.instructions.invokevirtual(kirjava.constants.MethodRef(
        "java/io/PrintStream", "println", "(Ljava/lang/Object;)V",
    )))
    result_check.append(kirjava.instructions.iload_1)
    result_check.append(kirjava.instructions.sipush(kirjava.constants.Integer(1024)))
    graph.jump(result_check, infinite_loop_entry, kirjava.instructions.if_icmpgt)
    graph.fallthrough(result_check, return_block)

    infinite_loop_entry.append(kirjava.instructions.getstatic(kirjava.constants.FieldRef(
        "java/lang/System", "out", "Ljava/io/PrintStream;",
    )))
    infinite_loop_entry.append(kirjava.instructions.ldc(kirjava.constants.String("Result is greater than 1024, entering infinite loop...")))
    infinite_loop_entry.append(kirjava.instructions.invokevirtual(kirjava.constants.MethodRef(
        "java/io/PrintStream", "println", "(Ljava/lang/Object;)V",
    )))
    graph.fallthrough(infinite_loop_entry, infinite_loop_body)

    graph.jump(infinite_loop_body, infinite_loop_body)  # goto is used by default, so we don't need to specify anything

    graph.return_(return_block)

    test_loop.code = graph.assemble()


if __name__ == "__main__":
    control_flow = kirjava.ClassFile("ControlFlow", is_public=True)

    make_main(control_flow)
    make_conditionals(control_flow)
    make_loop(control_flow)

    with open("ControlFlow.class", "wb") as stream:
        control_flow.write(stream)
