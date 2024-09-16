#!/usr/bin/env python3

__all__ = (
    "Frame",
)

import logging
import typing

from .entry import Entry
from ...model.types import *
from ...model.values import Value

if typing.TYPE_CHECKING:
    from ...model.class_ import *

logger = logging.getLogger("ijd.analysis.stack.frame")


class Frame:
    """
    A stack frame used to store abstract trace data at program points.

    Attributes
    ----------
    method: Method
        The method that contains the frame.
    class_: Class
        The class that contains the method.
    stack: list[Entry]
        The operand stack of the frame.
    locals: dict[int, Entry]
        The local variables in the frame.
    thrown: Entry | None
        The latest exception thrown in the frame.
    returned: Entry | None
        The latest value returned in the frame.
    uses: set[int]
        The indices of the locals that are used.
    defs: set[int]
        The indices of the locals that are defined.

    Methods
    -------
    initial(method: Method, class_: Class, context: Context) -> Frame
        Creates the initial frame of a given method.
    copy(self, state: State | None = None, deep: bool = True) -> Frame
        Creates a copy of this frame.
    generify(self, state: State | None = None) -> Frame
        Creates a generified copy of this frame.
    merge(self, other: Frame, live: set[int]) -> bool
        Attempts to merge this frame with another frame.
    replace(self, entry: Entry, type_: Type, source: Source | None = None) -> Entry
        Replaces all occurrences of an entry in this frame with a new type.
    push(self, entry_type_or_value: Entry | Type | Value, source: Source | None = None) -> Entry
        Pushes an entry to the stack.
    pop(self, expect: Type | None = None, source: Source | None = None) -> Entry
        Pops an entry from the stack.
    store(self, index: int, entry_type_or_value: Entry | Type | Value, source: Source | None = None) -> Entry
        Stores an entry in the local variables.
    load(self, index: int, expect: Type | None = None, source: Source | None = None) -> Entry
        Loads an entry from the local variables.
    throw(self, entry_type_or_value: Entry | Type | Value, source: Source | None = None) -> bool
        Indicates that an exception would be thrown.
    return_(self, entry_type_or_value: Entry | Type | Value, source: Source | None = None) -> None
        Returns an entry from the method.
    """

    __slots__ = (
        "method", "class_", "context",
        "stack", "locals", "thrown", "returned",
        "uses", "defs",
    )

    @classmethod
    def initial(cls, method: "Method", class_: "Class", context: "Context") -> "Frame":
        """
        Creates the initial frame of a given method.

        The initial frame is the frame that would be present at the method entrypoint
        upon its invocation, containing a `this` reference if the method is virtual
        and any parameters that the method takes.

        Parameters
        ----------
        method: Method
            The method that contains the frame.
        class_: Class
            The class that contains the method.
        context: Context
            The decompiler context to use.

        Returns
        -------
        Frame
            The initial frame that was created.
        """

        frame = cls(method, class_, context)
        index = 0

        if not method.static:
            if method.name == "<init>" and method.return_ is void_t:
                entry = Entry(uninitialized_this_t)
            else:
                entry = Entry(class_.as_ctype())
            frame.locals[0] = entry
            index = 1

        for argument in method.arguments:
            frame.store(index, argument)
            if argument.wide:
                index += 1
            index += 1

        return frame

    def __init__(self, method: "Method", class_: "Class", context: "Context") -> None:
        self.method = method
        self.class_ = class_
        self.context = context

        self.stack: list[Entry] = []
        self.locals: dict[int, Entry] = {}
        self.thrown:   Entry | None = None
        self.returned: Entry | None = None

        self.uses: set[int] = set()
        self.defs: set[int] = set()

    def __repr__(self) -> str:
        return "<Frame(stack=%r, locals=%r, thrown=%r)>" % (self.stack, self.locals, self.thrown)

    def copy(self, deep: bool = True) -> "Frame":
        """
        Creates a copy of this frame.

        Parameters
        ----------
        deep: bool
            Whether to copy the entries inside the frame as well.

        Returns
        -------
        Frame
            The copy of this frame.
        """

        frame = Frame(self.method, self.class_, self.context)
        frame.thrown = self.thrown
        frame.returned = self.returned

        if not deep:
            frame.stack.extend(self.stack)
            frame.locals.update(self.locals)
            return frame

        copied: dict[Entry, Entry] = {}

        for entry in self.stack:
            copy = copied.get(entry)
            if copy is None:
                copied[entry] = copy = entry.copy()
            frame.stack.append(copy)

        for index, entry in self.locals.items():
            copy = copied.get(entry)
            if copy is None:
                copied[entry] = copy = entry.copy()
            frame.locals[index] = copy

        return frame

    def generify(self) -> "Frame":
        """
        Creates a generified copy of this frame.

        Returns
        -------
        Frame
            The generified copy of this frame.
        """

        frame = Frame(self.method, self.class_, self.context)

        copied: dict[Entry, Entry] = {}

        for entry in self.stack:
            copy = copied.get(entry)
            if copy is None:
                copied[entry] = copy = entry.generify()
            frame.stack.append(copy)

        for index, entry in self.locals.items():
            copy = copied.get(entry)
            if copy is None:
                copied[entry] = copy = entry.generify()
            frame.locals[index] = copy

        return frame

    def merge(self, other: "Frame", live: set[int]) -> bool:
        """
        Attempts to merge this frame with another frame.

        Parameters
        ----------
        other: Frame
            The other frame to merge with.
        live: set[int]
            The indices of the locals that are live at the merge.

        Returns
        -------
        bool
            Whether this frame can be merged with the other frame.
        """

        if len(self.stack) != len(other.stack):
            # raise NotImplementedError("cannot yet deal with varying stack depths")
            return False

        for entry_a, entry_b in zip(self.stack, other.stack):
            if not entry_a.type.assignable(entry_b.type):
                return False
            # elif entry_a.value != entry_b.value:
            #     return False
        for index in live:
            entry_a = self.locals[index]
            entry_b = other.locals.get(index)
            if entry_b is None:
                return False
            if not entry_a.type.assignable(entry_b.type):
                return False
            # elif entry_a.value != entry_b.value:
            #     return False

        for entry_a, entry_b in zip(self.stack, other.stack):
            if entry_a.generified:
                entry_a.adjacent.add(entry_b)
            # if entry_b.generified:
            #     entry_b.adjacent.add(entry_a)
        for index, entry_a in self.locals.items():
            entry_b = other.locals.get(index)
            if entry_b is None or not entry_a.type.assignable(entry_b.type):
                continue
            if entry_a.generified:
                entry_a.adjacent.add(entry_b)
            # if entry_b.generified:
            #     entry_b.adjacent.add(entry_a)

        return True

    def replace(self, entry: Entry, type_: Type, source: Source | None = None) -> Entry:
        """
        Replaces all occurrences of an entry in this frame with a new type.

        Parameters
        ----------
        entry: Entry
            The old entry to replace.
        type_: Type
            The type of the new entry.
        source: Source | None
            The source replacing the entry.

        Returns
        -------
        Entry
            The new entry.
        """

        new = entry.cast(type_, source)
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

    def push(self, entry_type_or_value: Entry | Type | Value, source: Source | None = None) -> Entry:
        """
        Pushes an entry to the stack.

        Wide types are handled automatically.

        Parameters
        ----------
        entry_type_or_value: Entry | Type | Value
            The entry, type of the entry or value of the entry to push to the stack.
        source: Source | None
            The source pushing the entry to the stack.

        Returns
        -------
        Entry
            The entry that was pushed to the stack.

        Raises
        ------
        TypeError
            If the `entry_type_or_value` argument cannot be handled properly.
        """

        if isinstance(entry_type_or_value, Type):
            entry = Entry(entry_type_or_value, source)
            type_ = entry_type_or_value
            value = None
        elif isinstance(entry_type_or_value, Value):
            entry = Entry(entry_type_or_value.type, source)
            type_ = entry_type_or_value.type
            value = entry_type_or_value
        elif isinstance(entry_type_or_value, Entry):
            entry = entry_type_or_value
            type_ = entry_type_or_value.type
            value = entry_type_or_value.value
        else:
            raise TypeError("push() given wrong type %r" % type(entry_type_or_value))

        if value is not None and self.context.stack_const_prop:
            entry.value = value
        self.stack.append(entry)

        if type_.wide:
            reserved = Entry(type_, source, hidword=False)
            if value is not None and self.context.stack_const_prop:
                reserved.value = value
            self.stack.append(reserved)

        return entry

    def pop(self, expect: Type | None = None, source: Source | None = None) -> Entry:
        """
        Pops an entry from the stack.

        Parameters
        ----------
        expect: Type | None
            The expected type of the entry.
            This will act as a constraint on the entry.
        source: Source | None
            The source pushing the entry to the stack.

        Returns
        -------
        Entry
            The entry that was popped from the stack.
        """

        if expect is not None and expect.wide:
            reserved = self.stack.pop()
            reserved.constrain(expect)

        entry = self.stack.pop()
        if entry.type.wide and (expect is None or not expect.wide):
            if not entry.split:
                entry = entry.copy()
                entry.split = True
                self.stack[-1] = self.stack[-1].copy()
                self.stack[-1].split = True

        if expect is not None:
            entry = entry.constrain(expect, source)

        return entry

    def store(self, index: int, entry_type_or_value: Entry | Type | Value, source: Source | None = None) -> Entry:
        """
        Stores an entry in the local variables.

        Wide types are handled automatically.

        Parameters
        ----------
        index: int
            The index of the local variable to store the entry.
        entry_type_or_value: Entry | Type | Value
            The entry, type of the entry or value of the entry to store.
        source: Source | None
            The source storing the entry in the local variables.

        Returns
        -------
        Entry
            The entry that was stored in the local variables.
        """

        if isinstance(entry_type_or_value, Type):
            entry = Entry(entry_type_or_value, source)
            type_ = entry_type_or_value
            value = None
        elif isinstance(entry_type_or_value, Value):
            entry = Entry(entry_type_or_value.type, source)
            type_ = entry_type_or_value.type
            value = entry_type_or_value
        elif isinstance(entry_type_or_value, Entry):
            entry = entry_type_or_value
            type_ = entry_type_or_value.type
            value = entry_type_or_value.value
        else:
            raise TypeError("store() given wrong type %r" % type(entry_type_or_value))

        if value is not None and self.context.stack_const_prop:
            entry.value = value
        self.locals[index] = entry
        self.defs.add(index)

        if type_.wide:
            reserved = Entry(type_, source, hidword=False)
            if value is not None and self.context.stack_const_prop:
                reserved.value = value
            self.locals[index + 1] = reserved
            self.defs.add(index + 1)

        return entry

    def load(self, index: int, expect: Type | None = None, source: Source | None = None) -> Entry:
        """
        Loads an entry from the local variables.

        Parameters
        ----------
        index: int
            The index of the local variable to load the entry.
        expect: Type | None
            The expected type of the entry.
            This will act as a constraint on the entry.
        source: Source | None
            The source loading the entry from the local variables.

        Returns
        -------
        Entry
            The entry that was loaded from the local variables.
        """

        entry = self.locals[index]
        assert not entry.type.wide or expect is None or expect.wide, "non-explicit wide local load from %i" % index

        if expect is not None:
            entry = entry.constrain(expect, source)
            if expect.wide:
                reserved = self.locals.get(index + 1)
                reserved.constrain(expect)

        # If we have overwritten the local before we later use it in the same block, then we needn't record the usage.
        # Although this does not result in a valid use-def chain, it emulates one well enough to compute liveness
        # information at block boundaries, which is all we really care about here.
        if not index in self.defs:
            self.uses.add(index)
            if expect is not None and expect.wide:
                self.uses.add(index + 1)

        return entry

    def throw(self, entry_type_or_value: Entry | Type | Value, source: Source | None = None) -> bool:
        """
        Indicates that an exception would be thrown.

        Parameters
        ----------
        entry_type_or_value: Entry | Type | Value
        source: Source | None

        Returns
        -------
        bool
            Whether the exception was "thrown" or not.

        Raises
        ------
        TypeError
            If the `entry_type_or_value` argument cannot be handled properly.
        """

        if not self.context.stack_exception_prop:
            return False

        if isinstance(entry_type_or_value, Type):
            entry = Entry(entry_type_or_value, source)
        elif isinstance(entry_type_or_value, Value):
            entry = Entry(entry_type_or_value.type, source)
        elif isinstance(entry_type_or_value, Entry):
            entry = entry_type_or_value
        else:
            raise TypeError("throw() given wrong type %r" % type(entry_type_or_value))

        # if self.thrown is not None:
        #     logger.debug("Skipping exception %r as %r is already thrown.", entry, self.thrown)
        #     return
        assert self.thrown is None, "multiple exceptions thrown at %r" % source
        self.thrown = entry

        return True

    def return_(self, entry_type_or_value: Entry | Type | Value, source: Source | None = None) -> None:
        """
        Returns an entry from the method.

        Parameters
        ----------
        entry_type_or_value: Entry | Type | Value
        source: Source | None

        Raises
        ------
        TypeError
            If the `entry_type_or_value` argument cannot be handled properly.
        """

        if isinstance(entry_type_or_value, Type):
            entry = Entry(entry_type_or_value, source)
        elif isinstance(entry_type_or_value, Value):
            entry = Entry(entry_type_or_value.type, source)
        elif isinstance(entry_type_or_value, Entry):
            entry = entry_type_or_value
        else:
            raise TypeError("throw() given wrong type %r" % type(entry_type_or_value))

        assert self.returned is None, "multiple return values at %r" % source
        self.returned = entry
        entry.escapes.add(source)
