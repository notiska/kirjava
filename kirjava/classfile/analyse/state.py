# #!/usr/bin/env python3

# __all__ = (
#     "State",
# )

# import logging
# import typing
# from typing import Optional

# if typing.TYPE_CHECKING:
#     from .entry import Entry
#     from .frame import Frame
#     from ...jvm.graph import Graph
#     from ...jvm.graph.block import Block
#     from ...jvm.graph.edge import Edge
#     from ...jvm.insns import Instruction

# logger = logging.getLogger("ijd.analysis.stack.state")


# class State:
#     """
#     A single state for a block.

#     Attributes
#     ----------
#     graph: Graph
#         The graph that is being/was traced.
#     block: Block
#         The block that this state represents.
#     constraint: Frame
#         The frame entry constraint.
#     frame: Frame
#         The current frame.
#     traversed: list[State]
#         The states that were traversed to reach this current state.
#     steps: list[State.Step]
#         The steps taken within this trace state.
#     targets: list[State.Target]
#         The targets that are jumped to at the end of this state.
#     dead: set[Edge]
#         A set of edges that won't be visited in this state and all previous states.
#     """

#     __slots__ = (
#         "graph", "block",
#         "constraint", "frame",
#         "traversed", "steps", "targets",
#         "dead",
#     )

#     def __init__(self, graph: "Graph", block: "Block", frame: "Frame") -> None:
#         self.graph = graph
#         self.block = block
#         self.constraint = frame.copy(False)
#         self.frame = frame

#         self.traversed: list["State"] = []

#         self.steps: list["State.Step"] = []
#         self.targets: list["State.Target"] = []

#         self.dead: set["Edge"] = set()

#     def __repr__(self) -> str:
#         return "<State(constraint=%r, steps=%r, targets=%r)>" % (self.constraint, self.steps, self.targets)

#     # ------------------------------ Trace methods ------------------------------ #

#     def branch(self, block: "Block", frame: "Frame") -> "State":
#         """
#         Branches this state and creates a new one with the given frame.

#         Parameters
#         ----------
#         block: Block
#             The block being branched to.
#         frame: Frame
#             The frame that will become the constraint of the next state.

#         Returns
#         -------
#         State
#             The created state.
#         """

#         state = State(self.graph, block, frame)
#         state.traversed.extend(self.traversed)
#         state.traversed.append(self)
#         state.dead.update(self.dead)
#         return state

#     def retrace(self, others: list["State"], live: set[int], *, pedantic: bool = False) -> bool:
#         """
#         Checks if a retrace is required given other entry states.

#         Parameters
#         ----------
#         others: list[State]
#             The other entry states to check against.
#         live: set[int]
#             The indices of the live locals.
#         pedantic: bool
#             Merges all constraints.

#         Returns
#         -------
#         bool
#             Whether a retrace is needed.
#         """

#         assert others, "state has not been visited?"

#         if pedantic:
#             retrace = False
#             for other in others:
#                 if not other.constraint.merge(self.constraint, live):
#                     retrace = True
#             return retrace

#         for other in others:
#             if other.constraint.merge(self.constraint, live):
#                 return False
#         return True

#     # ------------------------------ Step methods ------------------------------ #

#     def step(
#             self,
#             insn: "Instruction",
#             inputs: tuple["Entry", ...],
#             output: Optional["Entry"] = None,
#             metadata: Optional["Instruction.Metadata"] = None,
#     ) -> "State.Step":
#         """
#         Creates a single step within the state.

#         Parameters
#         ----------
#         insn: Instruction
#             The instruction that was traced.
#         inputs: tuple[Entry, ...]
#             The entries that were taken as an input.
#         output: Entry | None
#             An optional entry that was produced as output.
#         metadata: Instruction.Metadata | None
#             Optional trace metadata produced.

#         Returns
#         -------
#         State.Step
#             The step information.
#         """

#         step = State.Step(insn, inputs, output, metadata)
#         self.steps.append(step)
#         return step

#     def target(
#             self,
#             edge: "Edge",
#             block: Optional["Block"],
#             definite: bool = False,
#             step: Optional["State.Step"] = None,
#             frame: Optional["Frame"] = None,
#     ) -> "State.Target":
#         """
#         Creates an exit target within out of the state.

#         Parameters
#         ----------
#         edge: Edge
#             The edge that leads to the target.
#         block: Block | None
#             The target block to jump to.
#             If `None`, this edge does not evaluate.
#         definite: bool
#             Whether the target is definite.
#         step: State.Step | None
#             An optional step that was taken when evaluating the edge.
#         frame: Frame | None
#             The frame at the target or `None` the old frame is to be used.

#         Returns
#         -------
#         State.Target
#             The target.
#         """

#         target = State.Target(edge, block, definite, step, frame)
#         self.targets.append(target)
#         if target.successor is None:
#             self.dead.add(target.edge)
#         return target

#     # ------------------------------ Classes ------------------------------ #

#     class Step(Source):
#         """
#         Trace step information.

#         This is used to retrace instructions and emit IR instructions.
#         Interestingly enough, in a sense, this could act as pretty good initial IR as it
#         removes the use of the stack and contains minimal type information.

#         Attributes
#         ----------
#         insn: Instruction
#             The instruction that was traced.
#         inputs: tuple[Entry, ...]
#             The entries that were taken as an input.
#         output: Entry | None
#             An optional entry that was produced as output.
#         metadata: Instruction.Metadata | None
#             Optional trace metadata produced.
#         """

#         __slots__ = ("insn", "inputs", "output", "metadata")

#         def __init__(
#                 self,
#                 insn: "Instruction",
#                 inputs: tuple["Entry", ...],
#                 output: Optional["Entry"],
#                 metadata: Optional["Instruction.Metadata"],
#         ) -> None:
#             self.insn = insn
#             self.inputs = inputs
#             self.output = output
#             self.metadata = metadata

#         def __repr__(self) -> str:
#             # Super-duper necessary code.
#             inputs_str = ", ".join(map(str, self.inputs))
#             if len(self.inputs) == 1:
#                 inputs_str += ","
#             return "<State.Step(insn=%s, inputs=(%s), output=%s, metadata=%r)>" % (
#                 self.insn, inputs_str, self.output, self.metadata,
#             )

#         def __str__(self) -> str:
#             inner_str = []
#             if self.inputs:
#                 inner_str.append("<- (%s)" % ", ".join(map(str, self.inputs)))
#             if self.output is not None:
#                 inner_str.append("-> %s" % self.output)
#             if not inner_str:
#                 inner_str.append("...")

#             if self.metadata is not None and self.metadata.messages:
#                 return "%s [%s] // %s" % (self.insn, " ".join(inner_str), self.metadata)
#             return "%s [%s]" % (self.insn, " ".join(inner_str))

#     class Target(Source):
#         """
#         Represents a target jump site from an edge.

#         Attributes
#         ----------
#         edge: Edge
#             The edge that leads to the target.
#         successor: Block | None
#             The target block to jump to.
#             If `None`, the edge is not evaluated at runtime, in this state.
#         definite: bool
#             Whether the target is definite.
#         step: State.Step | None
#             An optional step that was taken when evaluating the edge.
#         frame: Frame | None
#             The frame at the target or `None` the old frame is to be used.
#         """

#         __slots__ = ("edge", "successor", "definite", "step", "frame")

#         def __init__(
#                 self,
#                 edge: "Edge",
#                 successor: Optional["Block"],
#                 definite: bool,
#                 step: Optional["State.Step"],
#                 frame: Optional["Frame"],
#         ) -> None:
#             self.edge = edge
#             self.successor = successor
#             self.definite = definite
#             self.step = step
#             self.frame = frame

#         def __repr__(self) -> str:
#             return "<State.Target(edge=%s, successor=%s, definite=%s, step=%r, frame=%r)>" % (
#                 self.edge, self.successor, self.definite, self.step, self.frame,
#             )

#         def __str__(self) -> str:
#             # Oh god I really hate this, at least it's just for debugging purposes.
#             if self.step is None:
#                 if self.successor is None:
#                     return "%s --> ?" % self.edge
#                 elif self.edge.target is not self.successor:
#                     return "%s --> %s" % (self.edge, self.successor)
#                 return str(self.edge)
#             elif not self.definite:
#                 if self.edge.target is not self.successor:
#                     return "%s --> MAYBE(%s)" % (self.edge, self.successor)
#                 return "%s --> MAYBE(%s)" % (self.edge, self.edge)
#             elif self.edge.target is not self.successor:
#                 return "%s --> ALWAYS(%s)" % (self.edge, self.successor)
#             return "%s --> ALWAYS(%s)" % (self.edge, self.edge)
