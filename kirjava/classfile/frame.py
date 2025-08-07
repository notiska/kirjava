#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Frame",
)

from copy import copy
from operator import itemgetter
from typing import Iterable, Mapping, Optional

from .desc import parse_method_descriptor
from .fmt import ClassFile, ClassInfo, MethodInfo, UTF8Info
from .version import JAVA_MAX, Version
from .._compat import Self
from ..backend import Result
from ..model.types import object_t, reserved_t, uninitialized_this_t, void_t, Class, Verification


class Frame:
    """
    Basic frame information.

    Attributes
    ----------
    stack: list[Verification]
        All verification types on the stack.
    locals: dict[int, Verification]
        All verification types in the local variable array.
    this: Class
        The class that the method belongs to.
    super: Class | None
        The super class of the class that the method belongs to.
    version: Version
        The class file / JVM version being verified.

    Methods
    -------
    initial(method: MethodInfo, cf: ClassFile | None = None) -> Result[Self]
        Creates an initial frame that would be created on entry to the method.

    copy(self) -> Frame
        Creates a copy of this frame.
    substitute(self, old: Verification, new: Verification) -> None
        Substitutes all occurrences of a type with another type.
    pop(self, expect: Verification) -> Result[Verification]
        Pops the item off the top of the stack.
    push(self, value: Verification) -> None
        Pushes an item on to the top of the stack.
    load(self, local: int, expect: Verification) -> Result[Verification]
        Loads an item from the local variable array.
    store(self, local: int, item: Verification) -> None
        Stores an item in the local variable array.
    rload(self, local: int, expect: Verification) -> None
        "Reverse loads" an item from the local variable array.
    rstore(self, local: int, expect: Verification) -> None
        "Reverse stores" an item in the local variable array.
    dup(self) -> Result[Verification]
        Duplicates the item on the top of the stack.
    dup_x1(self) -> Result[Verification]
        Duplicates the item on the top of the stack and inserts it one value down.
    dup_x2(self) -> Result[Verification]
        Duplicates the item on the top of the stack and inserts it two values down.
    dup2(self) -> Result[tuple[Verification, Verification]]
        Duplicates the two items on the top of the stack.
    dup2_x1(self) -> Result[tuple[Verification, Verification]]
        Duplicates the two items on the top of the stack and inserts them three
        values down.
    dup2_x2(self) -> Result[tuple[Verification, Verification]]
        Duplicates the two items on the top of the stack and inserts them four
        values down.
    swap(self) -> Result[tuple[Verification, Verification]]
        Swaps the two items on the top of the stack.
    rdup(self) -> Result[Self]
    rdup_x1(self) -> Result[Self]
    rdup_x2(self) -> Result[Self]
    rdup2(self) -> Result[Self]
    rdup2_x1(self) -> Result[Self]
    rdup2_x2(self) -> Result[Self]
    rswap(self) -> Result[Self]
    """

    __slots__ = ("stack", "locals", "this", "super", "version")

    @classmethod
    def initial(cls, method: MethodInfo, cf: ClassFile | None = None) -> Result[Self]:
        """
        Creates an initial frame that would be created on entry to the method.

        Parameters
        ----------
        method: MethodInfo
            The method to create the initial frame for.
        cf: ClassFile | None
            The class file that the method belongs to.
        """

        with Result[Self].meta(__name__) as result:
            self = cls()
            name = None

            if isinstance(method.name, UTF8Info):
                name = method.name.value.decode()
            else:
                # Not the end of the world, really, but it's still an error.
                result.err(TypeError(f"method name {method.name!s} is not a UTF8 constant"))
            if not isinstance(method.descriptor, UTF8Info):
                raise TypeError(f"method descriptor {method.descriptor!s} is not a UTF8 constant")
            arg_types, ret_type = parse_method_descriptor(
                method.descriptor.value.decode(), strict=True,
            ).unwrap_into(result)

            if cf is not None:
                if isinstance(cf.this, ClassInfo):
                    this = cf.this.lift().into(result).value
                    # FIXME: This is all so ugly.
                    if this is not None:
                        if isinstance(this.ref_type, Class):
                            self.this = this.ref_type
                        else:
                            result.err(TypeError(f"class file this class {this.ref_type!s} is not a class type"))
                else:
                    result.err(TypeError(f"class file this class {cf.this!s} is not a class constant"))

                if isinstance(cf.super, ClassInfo):
                    super = cf.super.lift().into(result).value
                    if super is not None:
                        if isinstance(super.ref_type, Class):
                            self.super = super.ref_type
                        else:
                            result.err(TypeError(f"class file super class {super.ref_type!s} is not a class type"))
                elif cf.super is None:
                    self.super = None
                else:
                    result.err(TypeError(f"class file super class {cf.super!s} is not a class constant"))

                self.version = cf.version

            else:
                result.warn("No class file provided, frame info may not be accurate.")

            if not method.is_static:
                if name == "<init>" and ret_type is void_t:
                    self.locals[0] = uninitialized_this_t
                else:
                    self.locals[0] = self.this

            index = max(self.locals, default=-1) + 1
            for arg_type in arg_types:
                self.locals[index] = arg_type.verification()
                index += 1 + arg_type.wide

            return result.ok(self)
        return result

    def __init__(
        self, stack: Iterable[Verification] | None = None,
        locals:  Mapping[int, Verification] | None = None,
        this: Class = object_t, super: Class | None = object_t, version: Version = JAVA_MAX,
    ) -> None:
        self.stack: list[Verification] = []
        self.locals: dict[int, Verification] = {}
        # self.uses: set[int] = set()
        # self.defs: set[int] = set()
        self.this = this
        self.super = super
        self.version = version

        if stack is not None:
            self.stack.extend(stack)
        if locals is not None:
            self.locals.update(locals)

    def __copy__(self) -> "Frame":
        copied = Frame(self.stack, self.locals, self.this, self.super, self.version)
        # copied.uses.update(self.uses)
        # copied.defs.update(self.defs)
        return copied

    def __repr__(self) -> str:
        stack_str = ", ".join(map(str, self.stack))
        locals_str = ", ".join(f"{index}: {type!s}" for index, type in sorted(self.locals.items(), key=itemgetter(0)))
        return (
            f"<Frame(stack=[{stack_str}], locals={{{locals_str}}}, " +  # uses={self.uses!r}, defs={self.defs!r}, " +
            f"this={self.this!s}, super={self.super!s}, version={self.version!r})>"
        )

    def __str__(self) -> str:
        stack_str = ",".join(map(str, self.stack))
        locals_str = ",".join(f"{index}={type!s}" for index, type in sorted(self.locals.items(), key=itemgetter(0)))
        return f"frame([{stack_str}],{{{locals_str}}})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Frame) and
            self.stack == other.stack and
            self.locals == other.locals and
            self.version == other.version
        )

    def copy(self) -> "Frame":
        """
        Creates a copy of this frame.
        """

        return copy(self)

    def substitute(self, old: Verification, new: Verification) -> None:
        """
        Substitutes all occurrences of a type with another type.
        """

        for index, item in enumerate(self.stack):
            if item == old:
                self.stack[index] = new
        for index, item in self.locals.items():
            if item == old:
                self.locals[index] = new

    def pop(self, expect: Verification) -> Result[Verification]:
        """
        Pops an item off the top of the stack.

        Parameters
        ----------
        expect: Verification
            The type that is expected to be on the top of the stack.
        """

        with Result[Verification]() as result:
            if not self.stack:
                raise IndexError("pop from empty stack")
            item = self.stack.pop()
            if expect.wide:
                self.pop(reserved_t).unwrap_into(result)
            # FIXME: This is a hack in all honesty. We could still pop a primitive_t and it wouldn't raise an exception.
            #        Needs some thought into how this could be done properly.
            # elif item.wide and not expect.abstract:
            #     raise TypeError(f"pop splits wide type {item!s}")
            if not expect.assignable(item):
                raise TypeError(f"{item!s} is not assignable to {expect!s}")
            return result.ok(item)
        return result

    def push(self, item: Verification) -> None:
        """
        Pushes an item on to the top of the stack.
        """

        if item.wide:
            self.stack.append(reserved_t)
        self.stack.append(item)

    def load(self, index: int, expect: Verification) -> Result[Verification]:
        """
        Loads an item from the local variable array.

        Parameters
        ----------
        index: int
            The local variable array index to get.
        expect: Verification
            The type that is expected to be in the local variable slot.
        """

        with Result[Verification]() as result:
            item = self.locals.get(index)
            if expect.wide:
                self.load(index + 1, reserved_t).unwrap_into(result)
            if item is None:
                raise IndexError(f"local index {index} is empty")
            if not expect.assignable(item):
                raise TypeError(f"{item!s} is not assignable to {expect!s}")
            # if not index in self.defs:
            #     self.uses.add(index)
            #     if expect is not None and expect.wide:
            #         self.uses.add(index + 1)
            return result.ok(item)
        return result

    def store(self, index: int, item: Verification) -> Result[Verification | None]:
        """
        Stores an item in the local variable array.

        Returns
        -------
        Result[Verification | None]
            A result containing the previous item in the local slot, or `None` if it
            was empty.
        """

        with Result[Optional[Verification]]() as result:  # Result[Verification | None]  # py3.8
            previous = self.locals.get(index)
            # self.defs.add(index)
            if previous is not None and previous.wide:
                del self.locals[index + 1]
            elif previous == reserved_t:
                # raise TypeError(f"setting local {index} splits wide type {self.locals[index - 1]}")
                del self.locals[index - 1]
            self.locals[index] = item
            if item.wide:
                self.locals[index + 1] = reserved_t
                # self.defs.add(index + 1)
            return result.ok(previous)
        return result

    def rload(self, index: int, expect: Verification) -> None:
        """
        "Reverse loads" an item from the local variable array.

        Sets the item in the provided local slot if, and only if, it is not
        assignable to the expected type, or empty.

        Parameters
        ----------
        index: int
            The local variable array index to "reverse load".
        expect: Verification
            The type that is expected to be in the local variable slot.
            If the item is not assignable to this type, this type becomes the item.
        """

        item = self.locals.get(index)
        if item is None or not expect.assignable(item):
            self.locals[index] = expect

    def rstore(self, index: int, expect: Verification) -> None:
        """
        "Reverse stores" an item in the local variable array.

        Removes the item in the provided local index slot, if it matches the
        expected type.
        Naturally, it is lossy to reverse the `store()` operation.

        Parameters
        ----------
        index: int
            The local variable array index to "reverse store".
        expect: Verification
            The type that is expected to be in the local variable slot.
        """

        item = self.locals.get(index)
        if item is not None and expect.assignable(item):
            del self.locals[index]

    def dup(self) -> Result[Verification]:
        """
        Duplicates the item on the top of on the stack.

        Returns
        -------
        Result[Verification]
            A result containing the item that was duplicated.
        """

        with Result[Verification]() as result:
            if not self.stack:
                raise IndexError("dup on empty stack")
            item = self.stack[-1]
            if item.wide:
                raise TypeError(f"dup wide type {item!s}")
            self.stack.append(item)
            return result.ok(item)
        return result

    def dup_x1(self) -> Result[Verification]:
        """
        Duplicates the item on the top of the stack and inserts it one value down.

        Returns
        -------
        Result[Verification]
            A result containing the item that was duplicated.
        """

        with Result[Verification]() as result:
            if len(self.stack) < 2:
                raise IndexError(f"dup_x1 on stack size {len(self.stack)}")
            middle, top = self.stack[-2:]
            if top.wide:
                raise TypeError(f"dup_x1 wide type {top!s}")
            elif middle.wide:
                raise TypeError(f"dup_x1 splits wide type {middle!s}")
            self.stack.insert(-2, top)
            return result.ok(top)
        return result

    def dup_x2(self) -> Result[Verification]:
        """
        Duplicates the item on the top of the stack and inserts it two values down.

        Returns
        -------
        Result[Verification]
            A result containing the item that was duplicated.
        """

        with Result[Verification]() as result:
            if len(self.stack) < 3:
                raise IndexError(f"dup_x2 on stack size {len(self.stack)}")
            middle, _, top = self.stack[-3:]
            if top.wide:
                raise TypeError(f"dup_x2 wide type {top!s}")
            elif middle.wide:
                raise TypeError(f"dup_x2 splits wide type {middle!s}")
            self.stack.insert(-3, top)
            return result.ok(top)
        return result

    def dup2(self) -> Result[tuple[Verification, Verification]]:
        """
        Duplicates the two items on the top of the stack.

        Returns
        -------
        Result[tuple[Verification, Verification]]
            A result containing the two items that were duplicated.
        """

        with Result[tuple[Verification, Verification]]() as result:
            if len(self.stack) < 2:
                raise IndexError(f"dup2 on stack size {len(self.stack)}")
            lower, upper = self.stack[-2:]
            if lower.wide:
                raise TypeError(f"dup2 splits wide type {lower!s}")
            self.stack.append(lower)
            self.stack.append(upper)
            return result.ok((lower, upper))
        return result

    def dup2_x1(self) -> Result[tuple[Verification, Verification]]:
        """
        Duplicates the two items on the top of the stack and inserts them three
        values down.

        Returns
        -------
        Result[tuple[Verification, Verification]]
            A result containing the two items that were duplicated.
        """

        with Result[tuple[Verification, Verification]]() as result:
            if len(self.stack) < 3:
                raise IndexError(f"dup2_x1 on stack size {len(self.stack)}")
            middle, lower, upper = self.stack[-3:]
            if middle.wide:
                raise TypeError(f"dup2_x1 splits wide type {middle!s}")
            elif lower.wide:
                raise TypeError(f"dup2_x1 splits wide type {lower!s}")
            self.stack.insert(-3, lower)
            self.stack.insert(-3, upper)
            return result.ok((lower, upper))
        return result

    def dup2_x2(self) -> Result[tuple[Verification, Verification]]:
        """
        Duplicates the two items on the top of the stack and inserts them four
        values down.

        Returns
        -------
        Result[tuple[Verification, Verification]]
            A result containing the two items that were duplicated.
        """

        with Result[tuple[Verification, Verification]]() as result:
            if len(self.stack) < 4:
                raise IndexError(f"dup2_x2 on stack size {len(self.stack)}")
            middle, _, lower, upper = self.stack[-4:]
            if middle.wide:
                raise TypeError(f"dup2_x2 splits wide type {middle!s}")
            elif lower.wide:
                raise TypeError(f"dup2_x2 splits wide type {lower!s}")
            self.stack.insert(-4, lower)
            self.stack.insert(-4, upper)
            return result.ok((lower, upper))
        return result

    def swap(self) -> Result[tuple[Verification, Verification]]:
        """
        Swaps the two items on the top of the stack.

        Returns
        -------
        Result[tuple[Verification, Verification]]
            A result containing the two items that were swapped.
        """

        with Result[tuple[Verification, Verification]]() as result:
            if len(self.stack) < 2:
                raise IndexError(f"swap on stack size {len(self.stack)}")
            lower, upper = self.stack[-2:]
            if lower.wide:
                raise TypeError(f"swap splits wide type {lower!s}")
            elif upper.wide:
                raise TypeError(f"swap splits wide type {upper!s}")
            self.stack[-2:] = upper, lower
            return result.ok((lower, upper))
        return result

    def rdup(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup_x1(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup_x2(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup2(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup2_x1(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup2_x2(self) -> Result[Self]:
        raise NotImplementedError()

    def rswap(self) -> Result[Self]:
        raise NotImplementedError()
