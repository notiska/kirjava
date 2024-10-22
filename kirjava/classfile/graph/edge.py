#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Edge", "Fallthrough", "Jump", "Ret", "Switch", "Catch",
)

import typing
from typing import Optional

from ..insns.flow import Jump as JumpInsn, Ret as RetInsn, Switch as SwitchInsn
from ...model.types import Class, ReturnAddress

if typing.TYPE_CHECKING:
    from .block import Block
    from ..fmt import ConstInfo


class Edge:
    """
    An edge between two blocks in a control flow graph.

    Attributes
    ----------
    precedence: int
        The precedence of this edge, determines the order they are evaluated.
    symbolic: bool
        Whether this edge is purely symbolic to maintain some structure in the graph.
        This indicates that it should not be pruned during tracing.
    source: Block
        The source block of this edge.
    target: Block
        The target block of this edge.
    """

    __slots__ = ("_source", "_target")

    precedence: int
    symbolic: bool

    @property
    def source(self) -> "Block":
        return self._source

    @property
    def target(self) -> "Block":
        return self._target

    def __init__(self, source: "Block", target: "Block") -> None:
        self._source = source
        self._target = target

    def __repr__(self) -> str:
        # return f"<Edge(source={self.source!s}, target={self.target!s})>"
        raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

    def __str__(self) -> str:
        return f"{self._source!s} -> {self._target!s}"

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(f"== is not implemented for {type(self)!r}")

    def __hash__(self) -> int:
        raise NotImplementedError(f"hash() is not implemented for {type(self)!r}")

    # def trace(self, frame: "Frame", state: "State") -> Optional["State.Target"]:
    #     """
    #     Traces the execution of this edge.
    #
    #     Parameters
    #     ----------
    #     frame: Frame
    #         The current frame.
    #     state: State
    #         The state to add trace information to.
    #
    #     Returns
    #     -------
    #     State.Target | None
    #         An optional target jump site.
    #     """
    #
    #     raise NotImplementedError("trace() not implemented for %r" % self)

    # def lift(self, target: "State.Target") -> "IREdge":
    #     """
    #     Lifts this edge into an IR edge.
    #
    #     Parameters
    #     ----------
    #     target: State.Target
    #         The target determined by the trace.
    #
    #     Returns
    #     -------
    #     IREdge
    #         The IR edge representation of this edge.
    #     """
    #
    #     raise NotImplementedError("lift() not implemented for %r" % self)


class Fallthrough(Edge):
    """
    A fallthrough edge with an optional JVM instruction.

    Some JVM instructions can generate fallthrough edges (i.e. conditionals) so it
    is important to note said instruction, for tracing.

    Attributes
    ----------
    insn: JumpInsn | None
        The instruction that caused this fallthrough.
    """

    __slots__ = ("_insn", "_symbolic", "_hash")

    precedence = 2

    @property  # type: ignore[override]
    def symbolic(self) -> bool:
        return self._symbolic

    @property
    def insn(self) -> Optional["JumpInsn"]:
        return self._insn

    def __init__(self, source: "Block", target: "Block", insn: Optional["JumpInsn"] = None) -> None:
        super().__init__(source, target)
        self._insn = insn
        # We'll say this fallthrough is symbolic if the jump is not conditional (meaning that this fallthrough will never
        # actually be taken).
        # Only really for jsrs.
        self._symbolic = insn is not None and not insn.conditional
        self._hash = hash((source, target, insn.opcode if insn is not None else None))

    def __repr__(self) -> str:
        return f"<Fallthrough(source={self._source!s}, target={self._target!s}, insn={self._insn!s})>"

    def __str__(self) -> str:
        if self._insn is not None:
            return f"{self._insn!s} : fallthrough {self._source!s} -> {self._target!s}"
        return f"fallthrough {self._source!s} -> {self._target!s}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Fallthrough) or self._source != other._source or self._target != other._target:
            return False
        elif self._insn is not None and other._insn is not None:
            return self._insn.opcode == other._insn.opcode
        return self._insn is None and other._insn is None

    def __hash__(self) -> int:
        return self._hash

    # def trace(self, frame: "Frame", state: "State") -> "State.Target":
    #     if frame.thrown is not None or self.symbolic:
    #         return state.target(self, None, True)
    #     elif self.insn is None:  # Direct fallthrough.
    #         return state.target(self, self.target, True)
    #
    #     for target in state.targets:
    #         if not isinstance(target.edge, Jump):
    #             continue
    #         assert target.edge.insn is self.insn, "jump instruction mismatch for edges %s and %s" % (self, target.edge)
    #         if not target.definite:
    #             return state.target(self, self.target, False, target.step)
    #         break
    #     else:
    #         assert False, "no matching jump edge for fallthrough %s" % self
    #
    #     jumps = target.successor is not None
    #     return state.target(self, self.target if not jumps else None, True, target.step)


class Jump(Edge):
    """
    An edge with a jump instruction.

    This may represent either an unconditional or conditional jump.

    Attributes
    ----------
    insn: JumpInsn
        The jump instruction.
    """

    __slots__ = ("_insn", "_hash")

    precedence = 1
    symbolic = False

    @property
    def insn(self) -> "JumpInsn":
        return self._insn

    def __init__(self, source: "Block", target: "Block", insn: "JumpInsn") -> None:
        super().__init__(source, target)
        self._insn = insn
        self._hash = hash((source, target, insn.opcode))

    def __repr__(self) -> str:
        return f"<Jump(source={self._source!s}, target={self._target!s}, insn={self._insn!s})>"

    def __str__(self) -> str:
        # if self.fallthrough is not None:
        #     return "%s : [%s] %s -> %s" % (self.insn, self.fallthrough, self.source, self.target)
        return f"{self._insn!s} : {self._source!s} -> {self._target!s}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Jump) and
            self._source == other._source and
            self._target == other._target and
            self._insn.opcode == other._insn.opcode
        )

    def __hash__(self) -> int:
        return self._hash

    # def trace(self, frame: "Frame", state: "State") -> Optional["State.Target"]:
    #     if frame.thrown is not None:
    #         return state.target(self, None, True)
    #
    #     step = self.insn.trace(frame, state)
    #
    #     definite = not self.insn.conditional
    #     if definite or step.metadata is None:
    #         return state.target(self, self.target, definite, step)
    #
    #     assert step is not None, "jump %s returned bad step data" % self.insn
    #     assert isinstance(step.metadata, JumpInsn.Metadata), "jump %s returned bad metadata" % self.insn
    #     jumps = step.metadata.jumps  # Mfw PyCharm can't see the assert directly above ^^^^^^^^^.
    #
    #     if jumps is None:
    #         return state.target(self, self.target, False, step)
    #     return state.target(self, self.target if jumps else None, True, step)


class Ret(Jump):
    """
    A jump edge with a ret instruction.

    These need special handling, so a separate ege is used.
    """

    __slots__ = ()

    def __init__(self, source: "Block", target: "Block", insn: "RetInsn") -> None:
        super().__init__(source, target, insn)

    def __repr__(self) -> str:
        return f"<Ret(source={self._source!s}, target={self._target!s}, insn={self._insn!s})>"

    # def trace(self, frame: "Frame", state: "State") -> "State.Target":
    #     if frame.thrown is not None:
    #         return state.target(self, None, True)
    #
    #     step = self.insn.trace(frame, state)
    #     assert step is not None, "ret %s returned bad step data" % self.insn
    #     assert isinstance(step.metadata, RetInsn.Metadata), "ret %s returned bad metadata" % self.insn
    #
    #     retaddr = step.metadata.retaddr
    #     # TODO: In the future it may be possible to support other types? Not sure, need to experiment.
    #     assert isinstance(retaddr.type, ReturnAddress), "ret %s returned bad return address"
    #     source = retaddr.type.source
    #
    #     for visited in reversed(state.traversed):
    #         for target in visited.targets:
    #             if isinstance(target.edge, Fallthrough) and target.edge.insn is source:
    #                 return state.target(self, target.edge.target, True, step)
    #
    #     assert False, "no matching jsr edge for ret %s" % self


class Switch(Edge):
    """
    A switch edge with a JVM switch instruction.

    Attributes
    ----------
    insn: SwitchInsn
        The JVM switch instruction.
    value: int | None
        The lookup value of the switch, or `None` if it's the default.
    """

    __slots__ = ("_insn", "_value", "_hash")

    precedence = 1
    symbolic = False

    @property
    def insn(self) -> "SwitchInsn":
        return self._insn

    @property
    def value(self) -> int | None:
        return self._value

    def __init__(self, source: "Block", target: "Block", insn: "SwitchInsn", value: int | None) -> None:
        super().__init__(source, target)
        self._insn = insn
        self._value = value
        self._hash = hash((source, target, insn.opcode, value))

    def __repr__(self) -> str:
        return f"<Switch(source={self._source!s}, target={self._target!s}, insn={self._insn!s}, value={self._value})>"

    def __str__(self) -> str:
        if self._value is None:
            return f"{self._insn!s} [default] {self._source!s} -> {self._target!s}"
        return f"{self._insn!s} [{self._value}] {self._source!s} -> {self._target!s}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Switch) and
            self._source == other._source and
            self._target == other._target and
            self._insn.opcode == other._insn.opcode and
            self._value == other._value
        )

    def __hash__(self) -> int:
        return self._hash

    # def trace(self, frame: "Frame", state: "State") -> "State.Target":
    #     if frame.thrown is not None:
    #         return state.target(self, None, True)
    #
    #     for target in state.targets:
    #         if not isinstance(target.edge, Switch):
    #             continue
    #         assert target.edge.insn is self.insn, "switch instruction mismatch for edges %s and %s" % (self, target.edge)
    #
    #         if target.definite and target.successor is not None:  # The found switch target will definitely be jumped to.
    #             return state.target(self, None, True, target.step)
    #         step = target.step
    #         break
    #     else:  # We're the first switch edge to be traced, so we'll evaluate the instruction.
    #         step = self.insn.trace(frame, state)
    #         assert step is not None, "switch %s returned bad step data" % self.insn
    #         assert isinstance(step.metadata, SwitchInsn.Metadata), "switch %s returned bad metadata" % self.insn
    #     value = step.metadata.value
    #
    #     if not step.metadata.resolved:
    #         return state.target(self, self.target, False, step)
    #     return state.target(self, self.target if value == self.value else None, True, step)


class Catch(Edge):
    """
    A catch edge.

    This represents a transition from one block to another when an exception is
    thrown.
    Multiple catch edges can be present on a block, each specifying a different
    catch type and/or priority. These are used to determine which catch edge will
    handle the thrown exception.

    Attributes
    ----------
    class_: ConstInfo | None
        A class constant, used as the type of exception to catch.
        If `None`, all exceptions are caught.
    priority: int
        The priority of this catch edge, lower values are checked first.
    """

    __slots__ = ("_class", "_priority", "_hash")

    symbolic = False

    @property  # type: ignore[override]
    def precedence(self) -> int:
        return self._priority + 3

    @property
    def class_(self) -> Optional["ConstInfo"]:
        return self._class

    @property
    def priority(self) -> int:
        return self._priority

    def __init__(self, source: "Block", target: "Block", class_: Optional["ConstInfo"], priority: int) -> None:
        super().__init__(source, target)
        self._class = class_
        self._priority = priority
        self._hash = hash((source, target, id(class_) if class_ is not None else None, priority))

    def __repr__(self) -> str:
        return (
            f"<Catch(source={self._source!s}, target={self._target!s}, class_={self._class!s}, "
            f"priority={self._priority})>"
        )

    def __str__(self) -> str:
        return f"catch [{self._class!s} priority {self._priority}] {self._source!s} -> {self._target!s}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Catch) and
            self._source == other._source and
            self._target == other._target and
            self._class == other._class and
            self._priority == other._priority
        )

    def __hash__(self) -> int:
        return self._hash

    # def trace(self, frame: "Frame", state: "State") -> "State.Target":
    #     frame = frame.copy()
    #     frame.stack.clear()
    #     frame.push(frame.thrown or self.type)
    #
    #     # FIXME: Catch does not always evaluate, we could work this out.
    #     return state.target(self, self.target, True, None, frame)
