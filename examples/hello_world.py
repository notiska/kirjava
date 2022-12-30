#!/usr/bin/env python3

"""
An example usage of Kirjava that creates a class named HelloWorld which prints "Hello world." when run.
"""

import kirjava


if __name__ == "__main__":
    kirjava.initialise()

    hello_world = kirjava.ClassFile("HelloWorld", is_public=True)
    main = hello_world.add_method("main", "([Ljava/lang/String;)V", is_public=True, is_static=True)

    graph = kirjava.analysis.InsnGraph(main)
    graph.entry_block = kirjava.analysis.InsnBlock(graph)

    graph.entry_block.add(kirjava.instructions.getstatic("java/lang/System", "out", "Ljava/io/PrintStream;"))
    graph.entry_block.add(kirjava.instructions.ldc(kirjava.constants.String("Hello world.")))
    graph.entry_block.add(kirjava.instructions.invokevirtual("java/io/PrintStream", "println", "(Ljava/lang/Object;)V"))
    graph.entry_block.fallthrough(graph.return_block)

    main.code = graph.assemble()

    with open("HelloWorld.class", "wb") as stream:
        hello_world.write(stream)
