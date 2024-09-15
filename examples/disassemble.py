#!/usr/bin/env python3

"""
Basic Java class file disassembler example.
"""

import operator
import sys

import kirjava


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: disassemble.py <file> [methods]", file=sys.stderr)
        exit(1)

    cf = kirjava.load(sys.argv[1])

    if len(sys.argv) > 2:
        methods = []
        for name in sys.argv[2:]:
            if not cf.has_method(name):
                print("No method %r, cannot continue." % name, file=sys.stderr)
                exit(1)
            methods.append(cf.get_method(name))
    else:
        methods = list(cf.methods)

    for method in methods:
        print("Disassembly of method %s:" % method)
        try:
            graph = kirjava.disassemble(method)
        except Exception as error:
            print("Error while disassembling, continuing anyway.")
            print(repr(error))
            graph = kirjava.disassemble(method, do_raise=False)
        trace = kirjava.trace(graph)

        if trace.conflicts:
            print(" %i type conflict(s):" % len(trace.conflicts))
            for conflict in trace.conflicts:
                print("  %s" % conflict)

        # for subroutine in trace.subroutines:
        #     if type(subroutine) is kirjava.analysis.JsrJumpEdge:  # Older version compatibility.
        #         print(subroutine, trace.subroutines[subroutine])
        #     else:
        #         print(subroutine.jsr_edge, subroutine.ret_edge, subroutine.exit_block, subroutine.frame)

        # for block in graph:
        #     print(block, trace.pre_liveness.get(block), trace.post_liveness.get(block))

        frames = {}
        offset = -1
        frame = kirjava.analysis.frame.Frame.initial(method)

        if method.code.stackmap_table is not None:
            for sm_frame in method.code.stackmap_table:
                offset += sm_frame.offset_delta + 1
                frame = sm_frame.to_frame(frame, method.code)
                frames[offset] = frame

        printed = set()
        previous = None

        for offset, source in graph.source_map.items():
            if type(source) is kirjava.source.InstructionInBlock:
                block = source.block
            elif isinstance(source, kirjava.analysis.InsnEdge):
                block = source.from_
            else:
                continue
        
            if block == previous:
                continue

            printed.add(block)
            print(" %s (bci %i):" % (block, offset))

            frame = frames.get(offset)
            if frame is not None:
                print("  stack  (reported): [ %s ]" % ", ".join(map(str, frame.stack)))
                print("  locals (reported): { %s }" % (
                    ", ".join("%i=%s" % (index, value) for index, value in frame.locals.items()),
                ))
            if block in trace.entries:
                multiple = len(trace.entries[block]) > 1
                for index, constraint in enumerate(trace.entries[block]):
                    if multiple:
                        print("  stack  (computed, %i): [ " % (index + 1), end="")
                    else:
                        print("  stack  (computed): [ ", end="")
                    last = len(constraint.stack) - 1
                    for index_, entry in enumerate(constraint.stack):
                        end = ", " if index_ < last else " "
                        inference = entry.inference()
                        if len(inference) == 1:
                            for type_ in inference:
                                print(type_, end=end)
                            continue
                        print("{%s}" % ", ".join(map(str, entry.inference())), end=end)
                    print("]")

                    if multiple:
                        print("  locals (computed, %i): { " % (index + 1), end="")
                    else:
                        print("  locals (computed): { ", end="")
                    last = max(constraint.locals, default=0)
                    for index_, entry in sorted(constraint.locals.items(), key=operator.itemgetter(0)):
                        end = ", " if index_ < last else " "
                        inference = entry.inference()
                        if len(inference) == 1:
                            for type_ in inference:
                                print("%i=%s" % (index_, type_), end=end)
                            continue
                        print("%i={%s}" % (index_, ", ".join(map(str, entry.inference()))), end=end)
                    print("}")

            else:
                print(" block not traced (dead)")

            if not block:
                print("  (empty)")
            for instruction in block:
                print("   %s" % instruction)
            for edge in graph.out_edges(block):
                print("  %s" % edge)
            previous = block

        # There will still be some blocks in the graph that may not directly appear in the method code, but could still
        # be important to print.
        for block in graph:
            if block in printed:
                continue
            print(" %s:" % block)
            if not block:
                print(" (empty)")
            for instruction in block:
                print("   %s" % instruction)
            for edge in graph.out_edges(block):
                print("  %s" % edge)
