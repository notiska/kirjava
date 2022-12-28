#!/usr/bin/env python3

"""
An example usage of Kirjava that creates a class named HelloWorld which prints "Hello world." when run.
"""

import kirjava


if __name__ == "__main__":
    kirjava.initialise()

    hello_world = kirjava.ClassFile("HelloWorld", is_public=True)
    # A note on array types, if the array type does not exist in kirjava.types, you can just wrap it with
    # kirjava.types.ArrayType. With this, you can specify dimensions too.
    main = kirjava.MethodInfo(
        "main", (kirjava.types.string_array_t,), kirjava.types.void_t, hello_world, is_public=True, is_static=True,
    )

    graph = kirjava.analysis.InsnGraph(main)
    graph.entry_block = kirjava.analysis.InsnBlock(graph)  # Block with label 0, that belongs to the given graph

    # Types can be specified as descriptors to be parsed, when instantiating certain instructions. You can also use the
    # kirjava.types package to specify them, as with the main method above.
    graph.entry_block.add(kirjava.instructions.getstatic("java/lang/System", "out", "Ljava/io/PrintStream;"))
    graph.entry_block.add(kirjava.instructions.ldc(kirjava.constants.String("Hello world.")))
    graph.entry_block.add(kirjava.instructions.invokevirtual("java/io/PrintStream", "println", "(Ljava/lang/Object;)V"))
    graph.entry_block.fallthrough(graph.return_block)

    main.code = graph.assemble()

    with open("HelloWorld.class", "wb") as stream:
        hello_world.write(stream)
