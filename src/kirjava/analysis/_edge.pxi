from typing import Any, Union

from .. import types
from ..abc.graph cimport Edge
from ..instructions import jvm as instructions
from ..instructions.jvm import (
    Instruction, JsrInstruction, LookupSwitchInstruction,
    RetInstruction, TableSwitchInstruction,
)
from ..types.reference import ClassOrInterfaceType


cdef class InsnEdge(Edge):
    """
    An edge that can contain an instruction. This instruction is added to the block that we're coming from.
    """

    def __init__(self, from_: InsnBlock, to: InsnBlock, instruction: Union[Instruction, None] = None) -> None:
        """
        :param instruction: The instruction that this edge contains.
        """

        super().__init__(from_, to)

        self.instruction = instruction

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            type(other) is self.__class__ and
            (<InsnEdge>other).from_ == self.from_ and
            (<InsnEdge>other).to == self.to and
            (<InsnEdge>other).instruction == self.instruction
        )

    def __hash__(self) -> int:
        return hash((self.from_, self.to, self.instruction.opcode if self.instruction is not None else None))

    def copy(self, from_: Union[InsnBlock, None] = None, to: Union[InsnBlock, None] = None) -> InsnEdge:
        return self.__class__(
            self.from_ if from_ is None else from_, self.to if to is None else to,
            self.instruction.copy() if self.instruction is not None else None,
        )


cdef class FallthroughEdge(InsnEdge):
    """
    A fallthrough edge (also called an immediate edge) between two blocks.
    This occurs when there are no jumps between blocks, so the flow just falls through to the next block.
    """

    limit = 1

    def __repr__(self) -> str:
        return "<FallthroughEdge(from=%s, to=%s) at %x>" % (self.from_, self.to, id(self))

    def __str__(self) -> str:
        if self.instruction is None:
            return "fallthrough %s -> %s" % (self.from_, self.to)
        return "%s %s -> %s" % (self.instruction, self.from_, self.to)


cdef class JumpEdge(InsnEdge):
    """
    An edge that occurs when an explicit jump instruction is used.
    This may be a conditional jump, if so, it must be matched with a fallthrough edge, this is enforced when the graph
    is assembled.
    """

    limit = 1

    def __init__(self, from_: InsnBlock, to: InsnBlock, instruction: Union[Instruction, None] = None) -> None:
        if instruction is None:
            instruction = instructions.goto()  # By default

        super().__init__(from_, to, instruction)

    def __repr__(self) -> str:
        return "<JumpEdge(from=%s, to=%s, instruction=%s) at %x>" % (self.from_, self.to, self.instruction, id(self))

    def __str__(self) -> str:
        return "%s %s -> %s" % (self.instruction, self.from_, self.to)


cdef class JsrJumpEdge(JumpEdge):
    """
    Specific edge for jsr instruction. This edge jumps to the subroutine.
    The corresponding JsrFallthroughEdge is used to return from the subroutine, if it returns at all.
    """

    def __init__(self, from_: InsnBlock, to: InsnBlock, instruction: JsrInstruction) -> None:
        super().__init__(from_, to, instruction)

    def __repr__(self) -> str:
        return "<JsrJumpEdge(from=%s, to=%s, jump=%s) at %x>" % (self.from_, self.to, self.instruction, id(self))

    def __str__(self) -> str:
        return "%s %s -> %s" % (self.instruction, self.from_, self.to)


cdef class JsrFallthroughEdge(JumpEdge):
    """
    Specific edge for jsr instruction. This edge is used to return from the subroutine.
    Should be matched with a JsrJumpEdge.
    """

    def __init__(self, from_: InsnBlock, to: InsnBlock, instruction: JsrInstruction) -> None:
        super().__init__(from_, to, instruction)

    def __repr__(self) -> str:
        return "<JsrFallthroughEdge(from=%r, to=%r, instruction=%s) at %x>" % (
            self.from_, self.to, self.instruction, id(self),
        )

    def __str__(self) -> str:
        return "fallthrough %s %s (-> %s)" % (self.instruction, self.from_, self.to)


cdef class RetEdge(JumpEdge):
    """
    A specific edge for a ret instruction. Might be opaque, if the target is unknown.
    """

    def __init__(self, from_: InsnBlock, to: Union[InsnBlock, None], instruction: RetInstruction) -> None:
        super().__init__(from_, to, instruction)

    def __repr__(self) -> str:
        return "<RetEdge(from=%s, to=%s, instruction=%s) at %x>" % (self.from_, self.to, self.instruction, id(self))

    def __str__(self) -> str:
        if self.to is not None:
            return "%s %s -> %s" % (self.instruction, self.from_, self.to)
        return "%s %s -> unknown" % (self.instruction, self.from_)


cdef class SwitchEdge(JumpEdge):
    """
    An edge created by a switch instruction (tableswitch or lookupswitch).
    Contains the value and offset, as well as the switch instruction.
    """

    limit = None

    def __init__(
            self,
            from_: InsnBlock,
            to: InsnBlock,
            instruction: Union[LookupSwitchInstruction, TableSwitchInstruction],
            value: Union[int, None] = None,
    ) -> None:
        """
        :param instruction: The switch instruction that created this edge.
        :param value: The value (or index) in the switch instruction that created this edge, None for the default.
        """

        super().__init__(from_, to, instruction)

        self.value = value

    def __repr__(self) -> str:
        return "<SwitchEdge(from=%s, to=%s, instruction=%s, value=%s) at %x>" % (
            self.from_, self.to, self.instruction, self.value, id(self),
        )

    def __str__(self) -> str:
        if self.value is not None:
            return "switch %s value %i %s -> %s" % (self.instruction, self.value, self.from_, self.to)
        return "switch %s default %s -> %s" % (self.instruction, self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            isinstance(other, SwitchEdge) and
            (<SwitchEdge>other).from_ == self.from_ and
            (<SwitchEdge>other).to == self.to and
            (<SwitchEdge>other).instruction == self.instruction and
            (<SwitchEdge>other).value == self.value
        )

    def __hash__(self) -> int:
        return hash((self.from_, self.to, self.instruction.opcode, self.value))

    def copy(self, from_: Union[InsnBlock, None] = None, to: Union[InsnBlock, None] = None) -> SwitchEdge:
        return SwitchEdge(
            self.from_ if from_ is None else from_, self.to if to is None else to, self.instruction.copy(), self.value,
        )


cdef class ExceptionEdge(InsnEdge):
    """
    An edge for an exception handler.
    Contains the exception being caught and a priority (determined by the order of the handlers in the code).
    """

    def __init__(
            self,
            from_: InsnBlock,
            to: InsnBlock,
            priority: int,
            throwable: Union[ClassOrInterfaceType, None] = None,
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

    def __repr__(self) -> str:
        return "<ExceptionEdge(from=%s, to=%s, priority=%i, throwable=%s, inline_coverage=%s) at %x>" % (
            self.from_, self.to, self.priority, self.throwable, self.inline_coverage, id(self),
        )

    def __str__(self) -> str:
        if self.inline_coverage:
            return "catch %s priority %i %s (+inlined) -> %s" % (self.throwable, self.priority, self.from_, self.to)
        return "catch %s priority %i %s -> %s" % (self.throwable, self.priority, self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            isinstance(other, ExceptionEdge) and
            (<ExceptionEdge>other).from_ == self.from_ and
            (<ExceptionEdge>other).to == self.to and
            (<ExceptionEdge>other).priority == self.priority and
            (<ExceptionEdge>other).throwable == self.throwable
        )

    def __hash__(self) -> int:
        return hash((self.from_, self.to, self.priority, self.throwable))

    def copy(self, from_: Union[InsnBlock, None] = None, to: Union[InsnBlock, None] = None) -> ExceptionEdge:
        return ExceptionEdge(
            self.from_ if from_ is None else from_, self.to if to is None else to,
            self.priority, self.throwable, self.inline_coverage,
        )
