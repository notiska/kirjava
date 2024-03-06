#!/usr/bin/env python3

__all__ = (
    "InsnEdge", "FallthroughEdge", "JumpEdge", "JsrJumpEdge", "JsrFallthroughEdge", "RetEdge", "SwitchEdge", "ExceptionEdge",
)

import typing
from typing import Any, Optional

from ... import instructions, types
from ...abc import Edge
from ...error import NotAReturnAddressError, NotASubroutineError
from ...instructions import Instruction, JsrInstruction, RetInstruction, SwitchInstruction
from ...source import *
from ...types import Class, ReturnAddress

if typing.TYPE_CHECKING:
    from .block import InsnBlock
    from .. import Context, Frame


class InsnEdge(Edge):
    """
    An edge that can contain an instruction. This instruction is added to the block that we're coming from.
    """

    __slots__ = ("instruction",)

    from_: "InsnBlock"
    to: "InsnBlock"

    def __init__(self, from_: "InsnBlock", to: "InsnBlock", instruction: Instruction | None = None) -> None:
        """
        :param instruction: The instruction that this edge contains.
        """

        super().__init__(from_, to)

        self.instruction = instruction
        self._hash = hash((from_, to, instruction.opcode if instruction is not None else None))

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            type(other) is type(self) and
            # Faster check, though technically not necessary as dict code already performs this check to some extent.
            # other._hash == self._hash and
            other.from_ == self.from_ and
            other.to == self.to and
            other.instruction == self.instruction
        )

    def __hash__(self) -> int:
        return self._hash

    def copy(self, from_: Optional["InsnBlock"] = None, to: Optional["InsnBlock"] = None, deep: bool = True) -> "InsnEdge":
        instruction = self.instruction
        if instruction is not None and deep:
            instruction = instruction.copy()

        return type(self)(
            self.from_ if from_ is None else from_, self.to if to is None else to, instruction,
        )

    def trace(self, context: "Context") -> tuple[Optional["Frame"], Optional["InsnBlock"]]:
        """
        Traces any instructions in this edge.

        :param context: The context to use.
        :return: The new frame for the next block, and the next block itself (both are optional).
        """

        if self.instruction is not None:
            context.source = self
            self.instruction.trace(context)

        return context.frame, self.to


class FallthroughEdge(InsnEdge):
    """
    A fallthrough edge (also called an immediate edge) between two blocks.
    This occurs when there are no jumps between blocks, so the flow just falls through to the next block.
    """

    limit = 1

    def __repr__(self) -> str:
        return "<FallthroughEdge(from=%s, to=%s)>" % (self.from_, self.to)

    def __str__(self) -> str:
        if self.instruction is None:
            return "fallthrough %s -> %s" % (self.from_, self.to)
        return "%s %s -> %s" % (self.instruction, self.from_, self.to)

    def trace(self, context: "Context") -> tuple["Frame", "InsnBlock"]:
        # We can skip any extra computation as we know we shouldn't have executable instructions here.
        return context.frame, self.to


class JumpEdge(InsnEdge):
    """
    An edge that occurs when an explicit jump instruction is used.
    This may be a conditional jump, if so, it must be matched with a fallthrough edge, this is enforced when the graph
    is assembled.
    """

    limit = 1

    def __init__(self, from_: "InsnBlock", to: "InsnBlock", instruction: Optional["Instruction"] = None) -> None:
        if instruction is None:
            instruction = instructions.goto()  # By default

        super().__init__(from_, to, instruction)

    def __repr__(self) -> str:
        return "<JumpEdge(from=%s, to=%s, instruction=%s)>" % (self.from_, self.to, self.instruction)

    def __str__(self) -> str:
        return "%s %s -> %s" % (self.instruction, self.from_, self.to)


class JsrJumpEdge(JumpEdge):
    """
    Specific edge for jsr instruction. This edge jumps to the subroutine.
    The corresponding JsrFallthroughEdge is used to return from the subroutine, if it returns at all.
    """

    def __init__(self, from_: "InsnBlock", to: "InsnBlock", instruction: JsrInstruction) -> None:
        super().__init__(from_, to, instruction)

    def __repr__(self) -> str:
        return "<JsrJumpEdge(from=%s, to=%s, jump=%s)>" % (self.from_, self.to, self.instruction)

    def __str__(self) -> str:
        return "%s %s -> %s" % (self.instruction, self.from_, self.to)


class JsrFallthroughEdge(FallthroughEdge):
    """
    Specific edge for jsr instruction. This edge is used to return from the subroutine.
    Should be matched with a JsrJumpEdge.
    """

    def __init__(self, from_: "InsnBlock", to: "InsnBlock", instruction: JsrInstruction) -> None:
        super().__init__(from_, to, instruction)

    def __repr__(self) -> str:
        return "<JsrFallthroughEdge(from=%r, to=%r, instruction=%s)>" % (self.from_, self.to, self.instruction)

    def __str__(self) -> str:
        return "fallthrough %s %s (-> %s)" % (self.instruction, self.from_, self.to)

    def trace(self, context: "Context") -> tuple[None, None]:
        return None, None  # Symbolic edge (merely for the assembler), do nothing.


class RetEdge(JumpEdge):
    """
    A specific edge for a ret instruction. Might be opaque, if the target is unknown.
    """

    def __init__(self, from_: "InsnBlock", to: Optional["InsnBlock"], instruction: RetInstruction) -> None:
        super().__init__(from_, to, instruction)

    def __repr__(self) -> str:
        return "<RetEdge(from=%s, to=%s, instruction=%s)>" % (self.from_, self.to, self.instruction)

    def __str__(self) -> str:
        if self.to is not None:
            return "%s %s -> %s" % (self.instruction, self.from_, self.to)
        return "%s %s -> unknown" % (self.instruction, self.from_)

    def trace(self, context: "Context") -> tuple[Optional["Frame"], Optional["InsnBlock"]]:
        # The deal with ret edges is that we need to resolve the origin of the subroutine, which is not as easy as you
        # may think, at times. In cases where it is actually impossible, we will either raise an exception or skip over
        # this edge.

        context.source = self
        entry = context.get(self.instruction.index)
        if not isinstance(entry.generic, ReturnAddress):
            # FIXME: JVM (hotspot in particular) can interpret any value as returnAddress and in some cases we may be
            #        able to work this out? Would be some weird edge cases though. Presumably any obfuscation using this
            #        would make the values opaque, but who knows.
            #        (https://discord.com/channels/443258489146572810/887649798918909972/1133022037674303499)
            if not context.do_raise:
                return None, None
            raise NotAReturnAddressError(self, entry.generic)

        # The following code is not the prettiest I've ever written, I'll admit :p.

        origin_block:     Optional["InsnBlock"] = None
        jump_edge:        JsrJumpEdge | None = None
        fallthrough_edge: JsrFallthroughEdge | None = None

        # Trying to find the source of the subroutine lol. It (might) have been messed with by the user?
        if type(entry.generic.source) is JsrJumpEdge:
            origin_block = entry.generic.source.from_
            jump_edge = entry.generic.source
        elif type(entry.generic.source) is JsrFallthroughEdge:
            origin_block = entry.generic.source.from_
            fallthrough_edge = entry.generic.source
        elif type(entry.generic.source) is InstructionInBlock:
            origin_block = entry.generic.source.block

        if origin_block is None:
            if not context.do_raise:
                return None, None
            raise NotASubroutineError(self, entry.generic.source)

        for origin_edge in context.graph.out_edges(origin_block):
            if jump_edge is None and type(origin_edge) is JsrJumpEdge:
                jump_edge = origin_edge
            elif fallthrough_edge is None and type(origin_edge) is JsrFallthroughEdge:
                fallthrough_edge = origin_edge

        if jump_edge is None or fallthrough_edge is None:
            if not context.do_raise:
                return None, None
            raise NotASubroutineError(self, origin_block)

        return context.frame, fallthrough_edge.to


class SwitchEdge(JumpEdge):
    """
    An edge created by a switch instruction (tableswitch or lookupswitch).
    Contains the value and offset, as well as the switch instruction.
    """

    __slots__ = ("value", "_hash")

    limit = None

    def __init__(
            self,
            from_: "InsnBlock",
            to: "InsnBlock",
            instruction: SwitchInstruction,
            value: int | None = None,
    ) -> None:
        """
        :param instruction: The switch instruction that created this edge.
        :param value: The value (or index) in the switch instruction that created this edge, None for the default.
        """

        super().__init__(from_, to, instruction)

        self.value = value
        self._hash = hash((from_, to, instruction.opcode, value))

    def __repr__(self) -> str:
        return "<SwitchEdge(from=%s, to=%s, instruction=%s, value=%s)>" % (
            self.from_, self.to, self.instruction, self.value,
        )

    def __str__(self) -> str:
        if self.value is not None:
            return "switch %s value %i %s -> %s" % (self.instruction, self.value, self.from_, self.to)
        return "switch %s default %s -> %s" % (self.instruction, self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            type(other) is SwitchEdge and
            # other._hash == self._hash and
            other.from_ == self.from_ and
            other.to == self.to and
            other.instruction == self.instruction and
            other.value == self.value
        )

    def __hash__(self) -> int:
        return self._hash

    def copy(self, from_: Optional["InsnBlock"] = None, to: Optional["InsnBlock"] = None, deep: bool = True) -> "SwitchEdge":
        instruction = self.instruction
        if instruction is not None and deep:
            instruction = instruction.copy()

        return SwitchEdge(
            self.from_ if from_ is None else from_, self.to if to is None else to, instruction, self.value,
        )

    def trace(self, context: "Context") -> tuple[Optional["Frame"], Optional["InsnBlock"]]:
        # We'll only trace the instruction on the default edge to avoid tracing it for every case edge.
        if self.value is None:
            return super().trace(context)
        return context.frame, self.to


class ExceptionEdge(InsnEdge):
    """
    An edge for an exception handler.
    Contains the exception being caught and a priority (determined by the order of the handlers in the code).
    """

    __slots__ = ("priority", "throwable", "inline_coverage")

    def __init__(
            self,
            from_: "InsnBlock",
            to: "InsnBlock",
            priority: int,
            throwable: Class | None = None,
            inline_coverage: bool = False,
    ) -> None:
        """
        :param priority: The priority of this exception handler, lower values mean higher priority.
        :param throwable: The exception that this handler is catching, if None, it defaults to java/lang/Throwable.
        """

        super().__init__(from_, to, None)

        if throwable is None:
            throwable = types.throwable_t

        self.priority = priority
        self.throwable = throwable
        self.inline_coverage = inline_coverage

        self._hash = hash((from_, to, priority, throwable))

    def __repr__(self) -> str:
        return "<ExceptionEdge(from=%s, to=%s, priority=%i, throwable=%s, inline_coverage=%s)>" % (
            self.from_, self.to, self.priority, self.throwable, self.inline_coverage,
        )

    def __str__(self) -> str:
        if self.inline_coverage:
            return "catch %s priority %i %s (+inlined) -> %s" % (self.throwable, self.priority, self.from_, self.to)
        return "catch %s priority %i %s -> %s" % (self.throwable, self.priority, self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            type(other) is ExceptionEdge and
            # other._hash == self._hash and
            other.from_ == self.from_ and
            other.to == self.to and
            other.priority == self.priority and
            other.throwable == self.throwable
        )

    def __hash__(self) -> int:
        return self._hash

    def copy(self, from_: Optional["InsnBlock"] = None, to: Optional["InsnBlock"] = None, deep: bool = True) -> "ExceptionEdge":
        return ExceptionEdge(
            self.from_ if from_ is None else from_, self.to if to is None else to,
            self.priority, self.throwable, self.inline_coverage,
        )

    def trace(self, context: "Context") -> tuple["Frame", "InsnBlock"]:
        # Exception edges modify the state of the frame ONLY for the exception handler, if an exception is not thrown,
        # the frame will be the same as it was before and hence we need to create a copy of said frame and only operate
        # on the copy to avoid modifying the state of the non-exception jump.
        old_frame = context.frame
        context.frame = new_frame = old_frame.copy(deep=False)
        context.source = self

        context.pop(len(context.frame.stack))
        context.push(self.throwable)

        # And we'll just return everything back to normal here.
        context.frame = old_frame
        return new_frame, self.to
