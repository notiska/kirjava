#!/usr/bin/env python3

__all__ = (
    "pretty_repr",
    "print_trace", "print_jvm_graph",
)

"""
Pretty-ification of values and printing, mainly for debugging purposes.
"""

import logging
import operator
import typing

if typing.TYPE_CHECKING:
    from .jvm.analyse import Trace
    from .jvm.graph import Graph as JVMGraph


logger = logging.getLogger("ijd.pretty")


# Escaped special characters.
_SPECIAL = {
    "\a": "\\a",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\t": "\\t",
    "\v": "\\v",
}


def pretty_repr(name: str, max_len: int = 50) -> str:
    """
    Prettifies a string.

    When working with obfuscated classes with annoying names it's a lot easier if
    they're readable for debugging reasons.
    """

    for special in _SPECIAL:
        if special in name:
            name = name.replace(special, _SPECIAL[special])

    if len(name) >= max_len:
        name = name[:max_len - 3] + "..."

    name_ = ""
    for char in name:
        if 32 <= ord(char) < 127:
            name_ += char
        else:
            name_ += "-"

    return name_


def print_trace(trace: "Trace") -> None:
    """
    Prints trace information computed from a control flow graph.

    Parameters
    ----------
    trace: Trace
        The trace to print.
    """

    logger.info("")
    logger.info("------------------------------ trace information ------------------------------")

    active = set()
    for states in trace.states.values():
        active.update(states)
    logger.info("all states: %i, active states: %i", len(trace.all_states), len(active))

    for block in sorted(trace.states.keys(), key=operator.attrgetter("label")):
        states = trace.states[block]
        if not states:
            continue
        logger.info("%s:", block)

        for state in states:
            # logger.info(" state %i:", index + 1)
            if state.constraint.stack:
                logger.info(" stack:  [ %s ]", ", ".join(map(str, state.constraint.stack)))
            if trace.pre_live[block]:
                logger.info(" locals: { %s }", ", ".join(
                    "%i=%s" % (index, entry)
                    for index, entry in state.constraint.locals.items() if index in trace.pre_live[block]
                ))
            for step in state.steps:
                logger.info("   %s", step)
            if state.frame.thrown is not None:
                thrown = state.frame.thrown
                logger.info("  %s threw exception %s", thrown.source, thrown)

            for target in state.targets:
                if target.successor is None:
                    continue
                logger.info("  %s", target)

    logger.info("------------------------------ trace information ------------------------------")
    logger.info("")


def print_jvm_graph(graph: "JVMGraph") -> None:
    """
    Prints a control flow graph containing JVM instructions.

    Parameters
    ----------
    graph: JVMGraph
        The graph to print.
    """

    logger.info("")
    logger.info("------------------------------ JVM instructions graph ------------------------------")

    dont_print = {graph.return_, graph.rethrow, graph.opaque}

    for block in sorted(graph.blocks, key=operator.attrgetter("label")):
        if block in dont_print:
            continue
        logger.info("%s:", block)
        for instruction in block.insns:
            logger.info("   %s", instruction)
        for edge in sorted(graph.edges_out[block], key=operator.attrgetter("precedence")):
            logger.info("  %s", edge)

    logger.info("------------------------------ JVM instructions graph ------------------------------")
    logger.info("")
