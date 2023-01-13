#!/usr/bin/env python3

"""
Example usage of Kirjava for creating an invalid goto jump.
"""

import kirjava


if __name__ == "__main__":
    kirjava.initialise()

    invalid_goto = kirjava.ClassFile("InvalidGoto", is_public=True)

    main = invalid_goto.add_method("main", "([Ljava/lang/String;)V", is_public=True, is_static=True)
    graph = kirjava.analysis.InsnGraph(main)

    # Jumps whose offsets are specified explicitly are not adjusted by the assembler.
    graph.entry_block.append(kirjava.instructions.goto(32767), do_raise=False)
    graph.return_(graph.entry_block)

    # Obviously, an invalid jump would raise an exception by default, but we can specify do_raise=False to mitigate
    # this.
    main.code = graph.assemble(do_raise=False)

    with open("InvalidGoto.class", "wb") as stream:
        invalid_goto.write(stream)
