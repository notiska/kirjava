#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Entry",
    "Step", "InOut", "Copy", "Cast", "Throw", "Target",
    "State",
)

"""
Execution state for bytecode analysis.
"""

import typing
from enum import Enum
from typing import Iterable, Optional

from ._entry import *
from ._step import *
from .frame import Frame
from ..desc import parse_method_descriptor
from ..fmt import ClassFile, ClassInfo, MethodInfo, UTF8Info
from ..._compat import Self
from ...backend import Result
from ...model.types import null_t, throwable_t, uninitialized_this_t, void_t, Class, Type
from ...model.values import Value
from ...model.values.constants import Null

if typing.TYPE_CHECKING:
    from ..graph import Block, Edge, Graph
    from ..insns import Instruction
    from ..version import Version


class State:
    """
    An execution state.

    Attributes
    ----------
    block: Block
        The block traced in this execution state.
    stack: list[Entry]
        The current operand stack state.
    locals: dict[int, Entry]
        The current local variable array state.
    thrown: Entry | None
        An entry that was thrown as exception, or `None` if no exception was thrown.
    returned: Entry | None
        The entry that was returned from th method, or `None` if there was no
        return.
    uses: set[int]
        The used local variable indices.
    defs: set[int]
        The defined local variable indices

    Methods
    -------
    substitute(self, entry: Entry, type: Type, insn: Instruction | None = None) -> Entry
        Substitutes all occurrences of an entry in this state with a new type.
    pop(self, insn: Instruction, expect: Type, steps: list[Step] | None = None) -> Result[tuple[Entry, list[Step]]]
        Pops an entry off the top of the stack.
    push(self, insn: Instruction, entry: Entry | Type | Value) -> Result[Entry]
        Pushes an entry to the stack.
    load(self, insn: Instruction index: int, expect: Type, steps: list[Step] | None = None) -> Result[tuple[Entry, list[Step]]]
        Loads an entry from the local variables.
    store(self, insn: Instruction, index: int, entry: Entry | Type | Value) -> Result[Entry]
        Stores an entry in the local variables.
    dup(self, insn: Instruction) -> Result[Step | None]
        Duplicates the entry on the top of the stack.
    dup_x1(self, insn: Instruction) -> Result[Step | None]
        Duplicates the entry on the top of the stack and inserts it one value down.
    dup_x2(self, insn: Instruction) -> Result[Step | None]
        Duplicates the entry on the top of the stack and inserts it two values down.
    dup2(self, insn: Instruction) -> Result[Step | None]
        Duplicates the two entries on the top of the stack.
    dup2_x1(self, insn: Instruction) -> Result[Step | None]
        Duplicates the two entries on the top of the stack and inserts them three
        values down.
    dup2_x2(self, insn: Instruction) -> Result[Step | None]
        Duplicates the two entries on the top of the stack and inserts them four
        values down.
    swap(self, insn: Instruction) -> Result[Step | None]
        Swaps the two entries on the top of the stack.
    throw(self, insn: "Instruction", inputs: Iterable[Entry], output: Entry | Type | Value) -> Result[Throw]
        
        Indicates that an exception would be thrown.
    return_(self, entry: Entry | Type | Value, insn: Instruction | None = None) -> Result[None]
        Returns an entry from the method.
    """

    __slots__ = (
        "_block", "_this", "_super", "_version",  # Similar data to what Frame stores.
        "stack", "locals", "_thrown", "_returned", "uses", "defs",
        "_traversed", "_steps", "_targets", "_dead",
    )

    @classmethod
    def initial(cls, graph: "Graph", method: MethodInfo, cf: ClassFile) -> Result[Self]:
        """
        Creates the initial entry state for the provided method.

        Parameters
        ----------
        graph: Graph
            The graph of the method.
        method: MethodInfo
            The method info.
        cf: ClassFile
            The classfile that the method belongs to.
        """

        with Result[Self]() as result:
            name = None
            if isinstance(method.name, UTF8Info):
                name = method.name.value.decode()
            else:
                result.err(TypeError(f"method name {method.name!s} is not a UTF8 constant"))

            if not isinstance(method.descriptor, UTF8Info):
                raise TypeError(f"method descriptor {method.descriptor!s} is not a UTF8 constant")
            arg_types, ret_type = parse_method_descriptor(
                method.descriptor.value.decode(), strict=True,
            ).unwrap_into(result)

            if not isinstance(cf.this, ClassInfo):
                raise TypeError(f"class file this class {cf.this!s} is not a class constant")
            if not isinstance(cf.super, ClassInfo):
                raise TypeError(f"class file super class {cf.super!s} is not a class constant")

            this_const = cf.this.lift().unwrap_into(result)
            super_const = None if cf.super is None else cf.super.lift().unwrap_into(result)
            if not isinstance(this_const.ref_type, Class):
                result.err(TypeError(f"class file this class {this_const.ref_type!s} is not a class type"))
            if super is not None and not isinstance(super_const.ref_type, Class):
                result.err(TypeError(f"class file super class {super_const.ref_type!s} is not a class type"))

            this_entry = Entry(this_const.ref_type)
            this_entry.value = this_const
            super_entry = None
            if super_const is not None:
                super_entry = Entry(super_const.ref_type)
                super_entry.value = super_const

            self = cls(graph.entry, this_entry, super_entry, cf.version)

            if not method.is_static:
                if name == "<init>" and ret_type is void_t:
                    self.locals[0] = Entry(uninitialized_this_t)
                else:
                    self.locals[0] = self.this

            index = max(self.locals, default=-1) + 1
            for arg_type in arg_types:
                self.locals[index] = Entry(arg_type.verification())
                index += 1 + arg_type.wide

            return result.ok(self)
        return result

    @property
    def block(self) -> "Block":
        return self._block

    @property
    def this(self) -> Entry:
        return self._this

    @property
    def super(self) -> Entry | None:
        return self._super

    @property
    def version(self) -> "Version":
        return self._version

    @property
    def thrown(self) -> Entry | None:
        return self._thrown

    @property
    def returned(self) -> Entry | None:
        return self._returned

    def __init__(self, block: "Block", this: Entry, super: Entry | None, version: "Version") -> None:
        self._block = block
        self._this = this
        self._super = super
        self._version = version

        self.stack: list[Entry] = []
        self.locals: dict[int, Entry] = {}

        self._thrown: Entry | None = None
        self._returned: Entry | None = None

        self.uses: set[int] = set()
        self.defs: set[int] = set()

        self._traversed: list[State] = []
        self._steps: list[Step] = []
        self._targets: list[Target] = []

        self._dead: set["Edge"] = set()

    # ------------------------------ Frame operations ------------------------------ #

    def substitute(self, entry: Entry, type: Type, insn: Optional["Instruction"] = None) -> Entry:
        """
        Substitutes all occurrences of an entry in this state with a new type.

        Parameters
        ----------
        entry: Entry
            The old entry to replace.
        type: Type
            The new type of the entry.
        insn: Instruction | None
            The instruction responsible for the substitution.

        Returns
        -------
        Entry
            The new entry.
        """

        new = entry.cast(type, insn)
        if new is entry:
            return entry
        old = entry

        for index, entry in enumerate(self.stack):
            if entry is old:
                self.stack[index] = new
        for index, entry in self.locals.items():
            if entry is old:
                self.locals[index] = new

        return new

    def pop(self, insn: "Instruction", expect: Type, steps: list[Step] | None = None) -> Result[tuple[Entry, list[Step]]]:
        """
        Pops an entry off the top of the stack.

        Parameters
        ----------
        insn: Instruction
            The instruction responsible for calling `pop()`.
        expect: Type
            The expected type of the entry.
            This will act as a constraint on the entry.
        steps: list[Step] | None = None
            The list of steps already taken, to append to.
            If `None`, a new list will be created.

        Returns
        -------
        Result[tuple[Entry, list[Step]]]
            The entry that was popped from the stack and any execution steps that
            were taken to get to that point.
        """

        with Result[tuple[Entry, list[Step]]]() as result:
            steps = steps or []
            if not self.stack:
                raise IndexError("pop from empty stack")

            if expect.wide:
                if len(self.stack) < 2:
                    raise IndexError("pop2 from stack of size 1")
                # There is no need to check that this is actually the lodword because it should never exist on the stack
                # without it being already split, since all splits should already be handled elsewhere. If this isn't
                # the case, then the implementation is incorrect.
                reserved = self.stack.pop()
                assert reserved.lodword or reserved.split, f"pop2 from stack yields non-lodword {reserved!r}"
                constrained = reserved.constrain(expect, insn).unwrap_into(result)
                if reserved is not constrained:
                    # Casts/subs are treated as separate steps in this case.
                    steps.append(self.step(insn, (reserved,), (constrained,)))

            entry = self.stack.pop()
            if entry.lodword and not entry.split and not expect.wide:
                assert entry.type.wide, f"lodword for non-wide entry {entry!r}"
                result.err(ValueError(f"pop splits wide entry {entry!r}"))
                step = self.step(insn, (entry, self.stack[-1]))
                entry = entry.copy()  # Copy so as to not mess with any earlier references.
                entry.split = True
                self.stack[-1] = self.stack[-1].copy()
                self.stack[-1].split = True
                step.outputs.extend((entry, self.stack[-1]))
                steps.append(step)

            constrained = entry.constrain(expect, insn).unwrap_into(result)
            if entry is not constrained:
                steps.append(self.step(insn, (entry,), (constrained,)))
            entry = constrained

            # As a side note, we won't add the entry to the inputs here and will instead leave that up to
            return result.ok((entry, steps))
        return result

    def push(self, insn: "Instruction", entry: Entry | Type | Value) -> Result[Entry]:
        """
        Pushes an entry to the stack.

        Wide types are handled automatically.

        Parameters
        ----------
        insn: Instruction
            The instruction responsible for calling `push()`.
        entry: Entry | Type | Value
            The entry, type of the entry, or value of the entry to push to the stack.

        Returns
        -------
        Result[Entry]
            The entry that was pushed to the stack.
        """

        with Result[Entry]() as result:
            if isinstance(entry, Type):
                type_ = entry
                entry = Entry(type_, insn)
                value = None
            elif isinstance(entry, Value):
                value = entry
                entry = Entry(value.type, insn)
                # entry.value = value
                type_ = value.type
            elif isinstance(entry, Entry):
                type_ = entry.type
                value = entry.value
            else:
                raise TypeError(f"push() given wrong type {type(entry)!r}")

            if value is not None:  # and self.context.stack_const_prop:
                entry.value = value
            self.stack.append(entry)

            if type_.wide:
                reserved = Entry(type_, insn, lodword=True)
                if value is not None:  # and self.context.stack_const_prop:
                    reserved.value = value
                self.stack.append(reserved)

            return result.ok(entry)
        return result

    def load(
        self, insn: "Instruction", index: int, expect: Type, steps: list[Step] | None = None,
    ) -> Result[tuple[Entry, list[Step]]]:
        """
        Loads an entry from the local variables.

        Parameters
        ----------
        insn: Instruction
            The instruction responsible for loading the entry from the local
            variable array.
        index: int
            The index of the local variable to load the entry.
        expect: Type
            The expected type of the entry.
            This will act as a constraint on the entry.
        steps: list[Step] | None = None
            The list of steps already taken, to append to.

        Returns
        -------
        Result[tuple[Entry, list[State.Step]]]
            The entry that was loaded from the local variable array and any execution
            steps that were taken to get to that point.
        """

        with Result[tuple[Entry, list[Step]]]() as result:
            steps = steps or []
            entry = self.locals.get(index)
            if entry is None:
                raise KeyError(f"local index {index} is empty")

            if not entry.split:
                needs_split = False

                if entry.lodword:  # Loading a lodword entry is always undefined behaviour.
                    assert entry.type.wide, f"lodword for non-wide entry {entry!r}"
                    result.err(ValueError(f"load from local {index} yields lodword"))
                    needs_split = True
                elif not expect.wide and entry.type.wide:
                    result.err(ValueError(f"non-explicit wide load from local {index}"))
                    needs_split = True

                if needs_split:
                    step = self.step(insn, (entry,))
                    entry = entry.copy()
                    entry.split = True
                    # Note: redef not needed as we're just copying from the locals to the stack.
                    step.outputs.append(entry)
                    steps.append(step)

            constrained = entry.constrain(expect, insn).unwrap_into(result)
            if entry is not constrained:
                steps.append(self.step(insn, (entry,), (constrained,)))
            entry = constrained

            # If we have overwritten the local before we later use it in the same block, then we needn't record the
            # usage. Although this does not result in a valid use-def chain, it emulates one well enough to compute
            # liveness information at block boundaries, which is all we really care about here.
            not_def = not index in self.defs
            if not_def:
                self.uses.add(index)
            if not expect.wide:
                return result.ok((entry, steps))
            if not_def:
                self.uses.add(index + 1)

            reserved = self.locals.get(index + 1)
            if (reserved is None or not reserved.lodword) and not entry.split:
                result.err(ValueError(f"missing lodword for wide entry {entry!r} (got {reserved!r})"))
                step = self.step(insn, (entry,))
                entry = entry.copy()
                entry.split = True
                step.outputs.append(entry)
                steps.append(step)

            if reserved is not None:
                constrained = reserved.constrain(expect, insn).unwrap_into(result)
                if constrained is not reserved:
                    steps.append(self.step(insn, (reserved,), (constrained,)))

            return result.ok((entry, steps))
        return result

    def store(self, insn: "Instruction", index: int, entry: Entry | Type | Value) -> Result[Entry]:
        """
        Stores an entry in the local variables.

        Wide types are handled automatically.

        Parameters
        ----------
        insn: Instruction
            The instruction responsible for storing the entry in the local variable
            array.
        index: int
            The index of the local variable to store the entry.
        entry: Entry | Type | Value
            The entry, type of the entry or value of the entry to store.

        Returns
        -------
        Result[Entry]
            The entry that was stored in the local variable array.
        """

        with Result[Entry]() as result:
            if isinstance(entry, Type):
                type_ = entry
                entry = Entry(type_, insn)
                value = None
            elif isinstance(entry, Value):
                value = entry
                entry = Entry(value.type, insn)
                type_ = value.type
            elif isinstance(entry, Entry):
                type_ = entry.type
                value = entry.value
            else:
                raise TypeError(f"store() given wrong type {type(entry)!r}")

            # previous = self.locals.get(index)
            # if previous is not None and previous.type.wide and not previous.split:  # Handling for previous non-split wides.
            #     if previous.lodword:
            #         result.err(ValueError(f"store splits wide type {previous!r}"))
            #         upper = self.locals.get(index - 1)
            #         assert upper is not None, f"missing hidword for wide entry {previous!r}"
            #         upper = upper.copy()
            #         upper.split = True
            #         self.locals[index - 1] = upper
            #     else:
            #         assert index + 1 in self.locals, f"missing lodword for wide entry {previous!r}"
            #         del self.locals[index + 1]

            if value is not None:  # and self.context.stack_const_prop:
                entry.value = value
            self.locals[index] = entry
            self.defs.add(index)

            if type_.wide:
                reserved = Entry(type_, insn, lodword=True)
                if value is not None:  # and self.context.stack_const_prop:
                    reserved.value = value
                self.locals[index + 1] = reserved
                self.defs.add(index + 1)

            return result.ok(entry)
        return result

    def dup(self, insn: "Instruction") -> Result[Step | None]:
        """
        Duplicates the entry on the top of on the stack.

        Parameters
        ----------
        insn: Instruction
            The instruction calling `dup()`.

        Returns
        -------
        Result[Step | None]
            The (optional) current execution step.
        """

        with Result[Optional[Step]]() as result:  # Result[Step | None]  # py3.8
            step = None
            if not self.stack:
                raise IndexError("dup on empty stack")
            entry = self.stack[-1]

            if entry.lodword and not entry.split:
                assert entry.type.wide, f"lodword for non-wide entry {entry!r}"
                result.err(ValueError(f"dup splits wide entry {entry!r}"))
                step = self.step(insn, (entry,))
                entry = entry.copy()
                entry.split = True
                step.outputs.append(entry)

            self.stack.append(entry)
            return result.ok(step)
        return result

    def dup_x1(self, insn: "Instruction") -> Result[Step | None]:
        """
        Duplicates the entry on the top of the stack and inserts it one value down.

        Parameters
        ----------
        insn: Instruction
            The instruction calling `dup_x1()`.

        Returns
        -------
        Result[Step | None]
            The (optional) current execution step.
        """

        with Result[Optional[Step]]() as result:  # Result[Step | None]  # py3.8
            step = None
            if len(self.stack) < 2:
                raise IndexError(f"dup_x1 on stack size {len(self.stack)}")
            middle, top = self.stack[-2:]

            if top.lodword and not top.split:
                assert top.type.wide, f"lodword for non-wide entry {top!r}"
                result.err(ValueError(f"dup_x1 splits wide entry {top!r}"))
                step = self.step(insn, (top,))
                top = top.copy()
                top.split = True
                step.outputs.append(top)

            if middle.lodword and not middle.split:
                assert middle.type.wide, f"lodword for non-wide entry {middle!r}"
                result.err(ValueError(f"dup_x1 splits wide entry {middle!r}"))
                step = step or self.step(insn)
                step.inputs.append(middle)
                middle = middle.copy()
                middle.split = True
                step.outputs.append(middle)
                self.stack[-2] = middle

            self.stack.insert(-2, top)
            return result.ok(step)
        return result

    def dup_x2(self, insn: "Instruction") -> Result[Optional["State.Step"]]:
        """
        Duplicates the entry on the top of the stack and inserts it two values down.

        Parameters
        ----------
        insn: Instruction
            The instruction responsible for calling `dup_x2()`.

        Returns
        -------
        Result[State.Step | None]
            The (optional) current execution step.
        """

        with Result[Optional[State.Step]]() as result:  # Result[State.Step | None]  # py3.8
            step = None
            if len(self.stack) < 3:
                raise IndexError(f"dup_x2 on stack size {len(self.stack)}")
            middle, _, top = self.stack[-3:]

            if top.lodword and not top.split:
                assert top.type.wide, f"lodword for non-wide entry {top!r}"
                result.err(ValueError(f"dup_x2 splits wide entry {top!r}"))
                step = self.step(insn, (top,))
                top = top.copy()
                top.split = True
                step.outputs.append(top)

            if middle.lodword and not middle.split:
                assert middle.type.wide, f"lodword for non-wide entry {middle!r}"
                result.err(ValueError(f"dup_x2 splits wide entry {middle!r}"))
                step = step or self.step(insn)
                step.inputs.append(middle)
                middle = middle.copy()
                middle.split = True
                step.outputs.append(middle)
                self.stack[-3] = middle

            self.stack.insert(-3, top)
            return result.ok(step)
        return result

    def dup2(self, insn: "Instruction") -> Result[Optional["State.Step"]]:
        """
        Duplicates the two entries on the top of the stack.

        Parameters
        ----------
        insn: Instruction
            The instruction responsible for calling `dup2()`.

        Returns
        -------
        Result[State.Step | None]
            The (optional) current execution step.
        """

        with Result[Optional[Step]]() as result:  # Result[State.Step | None]  # py3.8
            step = None
            if len(self.stack) < 2:
                raise IndexError(f"dup2 on stack size {len(self.stack)}")
            upper, lower = self.stack[-2:]

            if upper.lodword and not upper.split:
                assert upper.type.wide, f"lodword for non-wide entry {upper!r}"
                result.err(ValueError(f"dup2 splits wide entry {upper!r}"))
                step = self.step(insn, (upper,))
                upper = upper.copy()
                upper.split = True
                step.outputs.append(upper)

            # [a, b] -> [a, b, a]
            #  ^
            # [a, b, a] -> [a, b, a, b]
            #     ^
            self.stack.append(upper)
            self.stack.append(lower)
            return result.ok(step)
        return result

    def dup2_x1(self, insn: "Instruction") -> Result[Optional["State.Step"]]:
        """
        Duplicates the two entries on the top of the stack and inserts them three
        values down.

        Parameters
        ----------
        insn: Instruction
            The instruction responsible for calling `dup2_x1()`.

        Returns
        -------
        Result[State.Step | None]
            The (optional) current execution step.
        """

        with Result[Optional[State.Step]]() as result:  # Result[State.Step | None]  # py3.8
            step = None
            if len(self.stack) < 3:
                raise IndexError(f"dup2_x1 on stack size {len(self.stack)}")
            middle, upper, lower = self.stack[-3:]

            if upper.lodword and not upper.split:
                assert upper.type.wide, f"lodword for non-wide entry {upper!r}"
                result.err(ValueError(f"dup2_x1 splits wide entry {upper!r}"))
                step = self.step(insn, (upper,))
                upper = upper.copy()
                upper.split = True
                step.outputs.append(upper)

            if middle.lodword and not middle.split:
                assert middle.type.wide, f"lodword for non-wide entry {middle!r}"
                result.err(ValueError(f"dup2_x1 splits wide entry {middle!r}"))
                step = step or self.step(insn)
                step.inputs.append(middle)
                middle = middle.copy()
                middle.split = True
                step.outputs.append(middle)
                self.stack[-3] = middle

            self.stack.insert(-3, upper)
            self.stack.insert(-3, lower)
            return result.ok(step)
        return result

    def dup2_x2(self, insn: "Instruction", step: Step | None = None) -> Result[Step | None]:
        """
        Duplicates the two entries on the top of the stack and inserts them four
        values down.

        Parameters
        ----------
        insn: Instruction
            The instruction responsible for calling `dup2_x2()`.
        step: Step | None
            The current execution step, or `None` to create one if needed.

        Returns
        -------
        Result[Step | None]
            The (optional) current execution step.
        """

        with Result[Optional[Step]]() as result:  # Result[Step | None]  # py3.8
            step = None
            if len(self.stack) < 4:
                raise IndexError(f"dup2_x2 on stack size {len(self.stack)}")
            middle, _, upper, lower = self.stack[-4:]

            if upper.lodword and not upper.split:
                assert upper.type.wide, f"lodword for non-wide entry {upper!r}"
                result.err(ValueError(f"dup2_x2 splits wide entry {upper!r}"))
                step = step or self.step(insn, (upper,))
                upper = upper.copy()
                upper.split = True
                step.outputs.append(upper)

            if middle.lodword and not middle.split:
                assert middle.type.wide, f"lodword for non-wide entry {middle!r}"
                result.err(ValueError(f"dup2_x2 splits wide entry {middle!r}"))
                step = step or self.step(insn)
                step.inputs.append(middle)
                middle = middle.copy()
                middle.split = True
                step.outputs.append(middle)
                self.stack[-4] = middle

            self.stack.insert(-4, upper)
            self.stack.insert(-4, lower)
            return result.ok(step)
        return result

    def swap(self, insn: "Instruction") -> Result[Step | None]:
        """
        Swaps the two entries on the top of the stack.

        Parameters
        ----------
        insn: Instruction
            The instruction responsible for calling `swap()`.

        Returns
        -------
        Result[Step | None]
            The (optional) current execution step.
        """

        with Result[Optional[Step]]() as result:  # Result[Step | None]  # py3.8
            step = None
            if len(self.stack) < 2:
                raise IndexError(f"swap on stack size {len(self.stack)}")
            bottom, top = self.stack[-2:]

            if top.lodword and not top.split:
                assert top.type.wide, f"lodword for non-wide entry {top!r}"
                result.err(TypeError(f"swap splits wide entry {top!r}"))
                step = self.step(insn, (top,))
                top = top.copy()
                top.split = True
                step.outputs.append(top)

            if bottom.lodword and not bottom.split:
                assert bottom.type.wide, f"lodword for non-wide entry {bottom!r}"
                result.err(TypeError(f"swap splits wide type {bottom!r}"))
                step = step or self.step(insn)
                step.inputs.append(bottom)
                bottom = bottom.copy()
                bottom.split = True
                step.outputs.append(bottom)

            self.stack[-2:] = top, bottom
            return result.ok(step)
        return result

    def throw(
        self, insn: "Instruction", inputs: Iterable[Entry], output: Entry | Type | Value,
        steps: list[Step] | None = None,
    ) -> Result[list[Step]]:
        """
        Throws the provided exception.

        Parameters
        ----------
        insn: Instruction
            The instruction throwing the exception.
        inputs: Iterable[Entry]
            The entries that were taken as input for the exception to be thrown.
        output: Entry | Type | Value
            The exception to throw.
        steps: list[Step] | None
            The list of steps already taken, to append to.
        """

        with Result[list[Step]].meta(__name__) as result:
            steps = steps or []
            # if not self.context.stack_exception_prop:
            #     return False

            if isinstance(output, Type):
                output = Entry(output, insn)
            elif isinstance(output, Value):
                output = Entry(output.type, insn)
            elif not isinstance(output, Entry):
                raise TypeError(f"throw() given wrong type {type(output)!r}")

            if isinstance(output.value, Null) or output.type == null_t:
                result.debug("throw %s (null pointer)", output)
                inputs = (*inputs, output)  # FIXME: Drop old inputs?
                output = Entry(Class("java/lang/NullPointerException"))

            # if self.thrown is not None:
            #     logger.debug("Skipping exception %r as %r is already thrown.", entry, self.thrown)
            #     return
            if self._thrown is not None:
                # assert self._thrown is None, "multiple exceptions thrown at %r" % source
                result.err(ValueError(f"throwing multiple exceptions ({self._thrown!r} and {output!r})"))
            self._thrown = output

            constrained = output.constrain(throwable_t, insn).unwrap_into(result)
            output = constrained  # FIXME: Check cast.

            # output.escapes.add(insn)  # TODO: Narrower, may not hit rethrow.

            step = Throw(insn, inputs, output)
            steps.append(step)
            self._steps.append(step)
            return result.ok(steps)
        return result

    def return_(self, entry: Entry | Type | Value, insn: Optional["Instruction"] = None) -> Result[None]:
        """
        Returns an entry from the method.

        Parameters
        ----------
        entry: Entry | Type | Value
            The entry being returned.
        insn: Instruction | None
            The instruction returning the value.
        """

        with Result[None]() as result:
            if isinstance(entry, Type):
                entry = Entry(entry, insn)
            elif isinstance(entry, Value):
                entry = Entry(entry.type, insn)
            elif not isinstance(entry, Entry):
                raise TypeError(f"return_() given wrong type {type(entry)!r}")

            if self._returned is not None:
                # assert self._returned is None, "multiple return values at %r" % source
                result.err(ValueError(f"returning multiple return values ({self._returned!r} and {entry!r})"))
            self._returned = entry
            if insn is not None:  # FIXME: Really shouldn't be able to be `None`, no?
                entry.escapes.add(insn)

            return result.ok(None)
        return result

    # ------------------------------ Stepping operations ------------------------------ #

    def step(
        self, insn: "Instruction",
        inputs:  Iterable[Entry] | None = None,
        outputs: Iterable[Entry] | None = None,
    ) -> "State.Step":
        """
        Creates a single execution step in for this state.

        Parameters
        ----------
        insn: Instruction
            The instruction creating the step.
        inputs: Iterable[Entry] | None
            The entries that were taken as input.
        outputs: Iterable[Entry] | None
            The entries produced as output.
        """

        step = State.Step(insn, inputs, outputs)
        self._steps.append(step)
        return step

    def target(
        self, edge: "Edge", successor: Optional["Block"], definite: bool = False,
        steps: Iterable["State.Step"] | None = None,
    ) -> "State.Target":
        """
        Creates a target jump site for this state.

        Parameters
        ----------
        edge: Edge
            The edge to the target.
        successor: Block | None
            The successor (target) block.
            If `None`, the edge is not evaluated at runtime.
        definite: bool
            Whether the target is definitely always taken.
        steps: Iterable[State.Step] | None
            Any steps that were taken while evaluating the edge.
        """

        target = State.Target(edge, successor, definite, steps)
        self._targets.append(target)
        return target

    # ------------------------------ Tracing operations ------------------------------ #

    def branch(self, block: "Block", frame: "Frame") -> "State":
        """
        Branches this state and creates a new one with the given frame.

        Parameters
        ----------
        block: Block
            The block being branched to.
        frame: Frame
            The frame that will become the constraint of the next state.

        Returns
        -------
        State
            The created state.
        """

        # TODO: Copy anything else?
        state = State(block, self._this, self._super, self._version)

        state.stack.extend(self.stack)
        state.locals.update(self.locals)
        state._thrown = self._thrown
        state._returned = self._returned

        state._traversed.extend(self._traversed)
        state._traversed.append(self)
        state._dead.update(self._dead)

        return state

    def retrace(self, others: list["State"], live: set[int], *, pedantic: bool = False) -> bool:
        """
        Checks if a retrace is required given other entry states.

        Parameters
        ----------
        others: list[State]
            The other entry states to check against.
        live: set[int]
            The indices of the live locals.
        pedantic: bool
            Merges all constraints.

        Returns
        -------
        bool
            Whether a retrace is needed.
        """

        assert others, "state has not been visited?"

        if pedantic:
            retrace = False
            for other in others:
                if not other.constraint.merge(self.constraint, live):
                    retrace = True
            return retrace

        for other in others:
            if other.constraint.merge(self.constraint, live):
                return False
        return True
