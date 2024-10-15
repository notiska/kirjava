# #!/usr/bin/env python3

# __all__ = (
#     "entry", "frame", "state",
#     "Trace",
# )

# """
# Stack state tracing.
# """

# import typing
# from collections import defaultdict

# from ._trace import *

# if typing.TYPE_CHECKING:
#     from .state import State
#     from ...jvm.graph import Graph
#     from ...jvm.graph.block import Block
#     from ...model.class_ import Class
#     from ...model.class_.method import Method


# class Trace:

#     __slots__ = ("graph", "states", "all_states", "pre_live", "post_live")

#     @classmethod
#     def trace(cls, graph: "Graph", method: "Method", class_: "Class") -> "Trace":
#         """
#         Computes the trace of a JVM control flow graph.

#         Parameters
#         ----------
#         graph: Graph
#             The graph to trace.
#         method: Method
#             The method containing the code represented in this graph.
#         class_: Class
#             The class containing the method.
#         context: Context
#             The decompiler context to use.

#         Returns
#         -------
#         Trace
#             The computed trace.
#         """

#         self = cls(graph)
#         trace(self, graph, method, class_)
#         return self

#     def __init__(self, graph: "Graph") -> None:
#         self.graph = graph

#         self.states: dict["Block", list["State"]] = defaultdict(list)
#         self.all_states: list["State"] = []

#         self.pre_live:  dict["Block", set[int]] = defaultdict(set)
#         self.post_live: dict["Block", set[int]] = defaultdict(set)

#     def __repr__(self) -> str:
#         return "<Trace(graph=%r)>" % self.graph
