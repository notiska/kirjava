#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Step",
    "General", "Copy", "Cast", "Throw",
    "Target",
)

import typing
from typing import Iterable, Optional

if typing.TYPE_CHECKING:
    from ._entry import Entry
    from ..graph import Block, Edge
    from ..insns import Instruction


class Step:
    """
    A single execution step.

    Attributes
    ----------
    insn: Instruction
        The instruction responsible for this step.
    type: Step.Type
        The type of execution step taken.
    inputs: tuple[Entry, ...]
        The entries that were taken as input.
    outputs: tuple[Entry, ...]
        The entries produced as output.
    """

    __slots__ = ("_insn",)

    inputs: tuple["Entry", ...]
    outputs: tuple["Entry", ...]

    @property
    def insn(self) -> "Instruction":
        return self._insn

    def __init__(self, insn: "Instruction") -> None:
        self._insn = insn

    def __repr__(self) -> str:
        raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

    def __str__(self) -> str:
        # raise NotImplementedError(f"str() is not implemented for {type(self)!r}")
        inner = []
        if self.inputs:
            inputs_str = ",".join(map(str, self.inputs))
            inner.append(f"<-({inputs_str})")
        if self.outputs:
            outputs_str = ",".join(map(str, self.outputs))
            inner.append(f"->({outputs_str!s})")
        if not inner:
            inner.append("...")
        inner_str = " ".join(inner)
        return f"{self._insn!s}[{inner_str}]"

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(f"== is not implemented for {type(self)!r}")


class General(Step):
    """
    A general input-output step, takes in inputs and produces different outputs.

    Attributes
    ----------
    inputs: tuple[Entry, ...]
        The entries that were taken as input.
    outpus: tuple[Entry, ...]
        The entries that were produced as output.
    """

    __slots__ = ("_inputs", "_outputs")

    @property  # type: ignore[override]
    def inputs(self) -> tuple["Entry", ...]:
        return self._inputs

    @property  # type: ignore[override]
    def outputs(self) -> tuple["Entry", ...]:
        return self._outputs

    def __init__(self, insn: "Instruction", inputs: Iterable["Entry"], outputs: Iterable["Entry"]) -> None:
        super().__init__(insn)
        # TODO: Assert all inputs != outputs?
        self._inputs = tuple(inputs)
        self._outputs = tuple(outputs)

    def __repr__(self) -> str:
        inputs_str = ", ".join(map(str, self.inputs))
        if len(inputs_str) == 1:
            inputs_str += ","
        outputs_str = ", ".join(map(str, self.outputs))
        if len(outputs_str) == 1:
            outputs_str += ","
        return f"<General(insn={self._insn!s}, inputs=({inputs_str}), outputs=({outputs_str!s}))>"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, General) and
            self._insn == other._insn and
            self._inputs == other._inputs and
            self._outputs == other._outputs
        )


class Copy(Step):
    """
    A step where a single entry is copied.

    Attributes
    ----------
    input: Entry
        The input entry.
    output: Entry
        The output, copied entry.
    """

    __slots__ = ("_input", "_output")

    @property  # type: ignore[override]
    def inputs(self) -> tuple["Entry", ...]:
        return self._input,

    @property  # type: ignore[override]
    def outputs(self) -> tuple["Entry", ...]:
        return self._output,

    @property
    def input(self) -> "Entry":
        return self._input

    @property
    def output(self) -> "Entry":
        return self._output

    def __init__(self, insn: "Instruction", input: "Entry", output: "Entry") -> None:
        super().__init__(insn)
        assert input != output, f"input {input!r} is the same as output {output!r}"
        self._input = input
        self._output = output

    def __repr__(self) -> str:
        return f"<Copy(insn={self._insn!s}, input={self._input!s}, output={self._output!s})>"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Copy) and
            self._insn == other._insn and
            self._input == other._input and
            self._output == other._output
        )


class Cast(Step):
    """
    A step where a single entry is cast to a different type.

    Attributes
    ----------
    input: Entry
        The input entry.
    output: Entry
        The output entry.
    """

    __slots__ = ("_input", "_output")

    @property  # type: ignore[override]
    def inputs(self) -> tuple["Entry", ...]:
        return self._input,

    @property  # type: ignore[override]
    def outputs(self) -> tuple["Entry", ...]:
        return self._output,

    @property
    def input(self) -> "Entry":
        return self._input

    @property
    def output(self) -> "Entry":
        return self._output

    def __init__(self, insn: "Instruction", input: "Entry", output: "Entry") -> None:
        super().__init__(insn)
        self._input = input
        self._output = output

    def __repr__(self) -> str:
        return f"<Cast(insn={self._insn!s}, input={self._input!s}, output={self._output!s})>"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Cast) and
            self._insn == other._insn and
            self._input == other._input and
            self._output == other._output
        )


class Throw(Step):
    """
    A step where an exception is thrown from certain inputs.

    Attributes
    ----------
    inputs: tuple[Entry, ...]
        The input entries.
    output: Entry
        The output exception entry.
    """

    __slots__ = ("_inputs", "_output")

    @property  # type: ignore[override]
    def inputs(self) -> tuple["Entry", ...]:
        return self._inputs

    @property  # type: ignore[override]
    def outputs(self) -> tuple["Entry", ...]:
        return self._output,

    @property
    def output(self) -> "Entry":
        return self._output

    def __init__(self, insn: "Instruction", inputs: Iterable["Entry"], output: "Entry") -> None:
        super().__init__(insn)
        self._inputs = tuple(inputs)
        self._output = output

    def __repr__(self) -> str:
        inputs_str = ", ".join(map(str, self._inputs))
        if len(self._inputs) == 1:
            inputs_str += ","
        return f"<Throw(insn={self._insn!s}, inputs=({inputs_str}), output={self._output!s})>"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Throw) and
            self._insn == other._insn and
            self._inputs == other._inputs and
            self._output == other._output
        )


class Target:
    """
    A target jump site.

    Attributes
    ----------
    edge: Edge
        The edge to the target.
    successor: Block | None
        The successor (target) block.
        If `None`, the edge is not evaluated at runtime.
    definite: bool
        Whether the target is definitely always taken.
    steps: tuple[Step, ...]
        Any steps that were taken while evaluating the edge.
    """

    __slots__ = ("_edge", "_successor", "_definite", "_steps")

    @property
    def edge(self) -> "Edge":
        return self._edge

    @property
    def successor(self) -> Optional["Block"]:
        return self._successor

    @property
    def definite(self) -> bool:
        return self._definite

    @property
    def steps(self) -> tuple[Step, ...]:
        return self._steps

    def __init__(self, edge: "Edge", successor: Optional["Block"], definite: bool, steps: Iterable[Step]) -> None:
        self._edge = edge
        self._successor = successor
        self._definite = definite
        self._steps = tuple(steps)

    def __repr__(self) -> str:
        steps_str = ", ".join(map(str, self._steps))
        if len(self._steps) == 1:
            steps_str += ","
        return (
            f"<Target(edge={self._edge!s}, successor={self._successor!s}, definite={self._definite!s}, steps=({steps_str}))>"
        )

    def __str__(self) -> str:
        # TODO: Include the step info too?
        # if self._step is not None:
        #     if self._successor is None:
        #         return f"{self._edge!s}[--> ?]"
        #     elif self._edge.target != self._successor:
        #         return f"{self._edge!s}[--> {self._successor!s}]"
        #     return f"{self._edge!s}[...]"

        if not self._definite:
            if self._edge.target != self._successor:
                return f"{self._edge}[-->maybe({self._successor!s})]"
            return f"{self._edge}[-->maybe]"
        elif self._edge.target != self._successor:
            return f"{self._edge}[-->always({self._successor!s})]"
        return f"{self._edge}[-->always]"
