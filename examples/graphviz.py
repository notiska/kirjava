#!/usr/bin/env python3

"""
A graphviz demo for the CFGs.
Usage: python3 graphviz.py <class file> <method name> > graph.dot && dot -Tsvg graph.dot > graph.svg
"""

import os
import sys

import kirjava

RESOLVE_SUBROUTINES = True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: %s <class file> <method>" % sys.argv[0])
        exit(1)

    if not os.path.exists(sys.argv[1]):
        print("File %s does not exist" % sys.argv[1])
        exit(1)

    cf = kirjava.load(sys.argv[1])
    graph = kirjava.disassemble(cf.get_method(sys.argv[2]))

    dot = "digraph G {\n"

    for block in graph.blocks:
        if not graph.in_edges(block) and not graph.out_edges(block):
            continue

        label = str(block).replace(" ", "_")
        instructions = ""
        for instruction in block:
            instructions += "%s\\l" % instruction

        dot += "    %s [label=\"%s\\n%s\", shape=%s];\n" % (label, block, instructions, "rect" if block else "oval")

    edges = list(graph.edges)

    if RESOLVE_SUBROUTINES:
        trace = kirjava.analysis.Trace.from_graph(graph)
        for edge in edges.copy():
            if type(edge) is kirjava.analysis.RetEdge or type(edge) is kirjava.analysis.JsrFallthroughEdge:
                edges.remove(edge)
        for subroutine in trace.subroutines:
            edges.append(subroutine.ret_edge.copy(to=subroutine.exit_block))

    for edge in edges:
        from_label = str(edge.from_).replace(" ", "_")
        to_label = str(edge.to).replace(" ", "_")

        dot += "    %s -> %s [label=\" %s\"];\n" % (from_label, to_label, edge)

    dot += "}"

    print(dot)
