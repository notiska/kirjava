#!/usr/bin/env python3

__all__ = (
    "StackMapTable", "LineNumberTable", "LocalVariableTable", "LocalVariableTypeTable",
)

"""
Attributes found exclusively in the Code attribute.
"""

import logging
import typing
from typing import Any, IO, Iterable, Optional

from . import AttributeInfo
from ... import types
from ..._struct import *
from ...abc import Offset, Source
from ...analysis import Entry, Frame
from ...constants import Class as ClassConstant, UTF8
from ...source import InstructionAtOffset
from ...types import (
    descriptor,
    double_t, float_t, int_t, long_t, null_t, reserved_t, top_t, uninitialized_this_t,
    Array, Class as ClassType, Uninitialized, Verification,
)
from ...version import Version

if typing.TYPE_CHECKING:
    from .method import Code
    from .. import ClassFile

logger = logging.getLogger("kirjava.classfile.attributes.code")

# TODO: https://github.com/jacoco/jacoco/wiki/CharacterRangeTable, https://bugs.openjdk.org/browse/CODETOOLS-7900337


class StackMapTable(AttributeInfo):
    """
    Contains information about stack frames, used for inference verification.
    """

    __slots__ = ("frames",)

    name_ = "StackMapTable"
    since = Version(50, 0)
    locations = ("Code",)

    @classmethod
    def _read_verification_type(cls, class_file: "ClassFile", buffer: IO[bytes]) -> Verification:
        """
        Reads a verification type info from a buffer.
        """

        tag, = buffer.read(1)

        # The tags are somewhat sorted by their occurrence frequency. Some of the less common types are harder to
        # distinguish in terms of usage, but the most common types tend to be class, int and top, in that order.
        if tag == 7:
            class_index, = unpack_H(buffer.read(2))
            # constant = class_file.constant_pool[class_index]
            # if type(constant) is ClassConstant:
            #     return constant.type
            return class_file.constant_pool[class_index].class_type  # FIXME: Support invalid CP indices.
        elif tag == 1:
            return int_t
        elif tag == 0:
            return top_t
        elif tag == 2:
            return float_t
        elif tag == 3:
            return double_t
        elif tag == 4:
            return long_t
        elif tag == 8:
            offset, = unpack_H(buffer.read(2))
            return Uninitialized(Offset(offset))
        elif tag == 5:
            return null_t
        elif tag == 6:
            return uninitialized_this_t

        raise ValueError("Invalid tag %i for verification type." % tag)

    @classmethod
    def _write_verification_type(cls, type_: Verification, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes a verification type to a buffer.
        """

        if isinstance(type_, ClassType):
            buffer.write(bytes((7,)))
            buffer.write(pack_H(class_file.constant_pool.add(ClassConstant(type_.name))))
        elif type_ is int_t:
            buffer.write(bytes((1,)))
        elif type_ is top_t:
            buffer.write(bytes((0,)))
        elif type(type_) is Array:
            buffer.write(bytes((7,)))
            buffer.write(pack_H(class_file.constant_pool.add(ClassConstant(descriptor.to_descriptor(type_)))))
        elif type_ is float_t:
            buffer.write(bytes((2,)))
        elif type_ is double_t:
            buffer.write(bytes((3,)))
        elif type_ is long_t:
            buffer.write(bytes((4,)))
        elif type(type_) is Uninitialized:
            if not isinstance(type_.source, Offset):
                raise TypeError("Invalid source %r for Uninitialized." % type(type_.source))
            buffer.write(bytes((8,)))
            buffer.write(pack_H(type_.source.offset))
        elif type_ is null_t:
            buffer.write(bytes((5,)))
        elif type_ == uninitialized_this_t:
            buffer.write(bytes((6,)))
        else:
            raise TypeError("Invalid verification type %r." % type_)

    def __init__(self, parent: "Code", frames: Iterable["StackMapTable.StackMapFrame"] | None = None) -> None:
        """
        :param frames: The stackmap frames in this table.
        """

        super().__init__(parent, StackMapTable.name_)

        self.frames: list[StackMapTable.StackMapFrame] = []
        if frames is not None:
            self.frames.extend(frames)

    def __repr__(self) -> str:
        return "<StackMapTable(%r) at %x>" % (self.frames, id(self))

    def __iter__(self) -> Iterable["StackMapTable.StackMapFrame"]:
        return iter(self.frames)

    def __getitem__(self, index: int) -> "StackMapTable.StackMapFrame":
        return self.frames[index]

    def __setitem__(self, index: int, value: "StackMapTable.StackMapFrame") -> None:
        self.frames[index] = value

    def __contains__(self, item: Any) -> bool:
        return item in self.frames

    def __len__(self) -> int:
        return len(self.frames)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.frames.clear()
        frames_count, = unpack_H(buffer.read(2))
        for index in range(frames_count):
            frame_type, = buffer.read(1)
            for stack_frame in self.STACK_MAP_FRAMES:
                if frame_type in stack_frame.frame_type:
                    self.frames.append(stack_frame.read(frame_type, class_file, buffer))
                    break
            else:
                raise ValueError("Unknown stackmap frame type %i." % frame_type)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.frames)))
        for stack_frame in self.frames:
            stack_frame.write(class_file, buffer)

    # ------------------------------ Stack frame types ------------------------------ #

    class StackMapFrame:
        """
        A stack map frame info structure.
        """

        __slots__ = ("offset_delta",)

        frame_type = range(-1, -1)

        @classmethod
        # @abstractmethod
        def read(cls, frame_type: int, class_file: "ClassFile", buffer: IO[bytes]) -> "StackMapTable.StackMapFrame":
            """
            Reads a stack map frame from a buffer.

            :param frame_type: The frame type that has already been read.
            :param class_file: The classfile that the frame belongs to.
            :param buffer: The binary buffer to read from.
            :return: The stack map frame that was read.
            """

            ...

        def __init__(self, offset_delta: int) -> None:
            """
            :param offset_delta: The starting bytecode offset for this frame, as a delta from the previous frame.
            """

            self.offset_delta = offset_delta

        def __repr__(self) -> str:
            return "<%s(offset_delta=%i) at %x>" % (type(self).__name__, self.offset_delta, id(self))

        def _make_entry(self, type_: Verification, code: Optional["Code"]) -> Entry:
            if type_ is top_t:
                return Frame.TOP

            if code is not None and type(type_) is Uninitialized and type(type_.source) is Offset:
                # We need to convert the Offsets to InstructionAtOffsets as those are used in the analyser.
                type_ = Uninitialized(InstructionAtOffset(
                    type_.source.offset, code.instructions.get(type_.source.offset),
                ))

            return Entry(type_)

        # @abstractmethod
        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            """
            Writes this stack map frame to a buffer.

            :param class_file: The classfile that this stack map frame belongs to.
            :param buffer: The binary buffer to write to.
            """

            ...

        def to_frame(self, previous: Frame, code: Optional["Code"] = None) -> Frame:
            """
            Converts this stack map frame to a frame.

            :param code: The code attribute the frame belongs to.
            :param previous: The previous frame.
            :return: The frame that was created.
            """

            ...

    class SameFrame(StackMapFrame):
        """
        Indicates that this frame has the exact same locals as the previous frame and that the operand stack is empty.
        """

        __slots__ = ()

        frame_type = range(0, 64)

        @classmethod
        def read(cls, frame_type: int, class_file: "ClassFile", buffer: IO[bytes]) -> "StackMapTable.SameFrame":
            return cls(frame_type)

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            buffer.write(bytes((self.offset_delta,)))

        def to_frame(self, previous: Frame, code: Optional["Code"] = None) -> Frame:
            frame = previous.copy()
            frame.pop(len(frame.stack))
            return frame

    class SameLocals1StackItemFrame(StackMapFrame):
        """
        Indicates that this frame has the exact same locals as the previous frame and that the operand stack has one entry.
        """

        __slots__ = ("stack_item",)

        frame_type = range(64, 128)

        @classmethod
        def read(
                cls, frame_type: int, class_file: "ClassFile", buffer: IO[bytes],
        ) -> "StackMapTable.SameLocals1StackItemFrame":
            stack_item = StackMapTable._read_verification_type(class_file, buffer)
            return cls(frame_type - 64, stack_item)

        def __init__(self, offset_delta: int, stack_item: Verification) -> None:
            """
            :param stack_item: The extra stack item.
            """

            super().__init__(offset_delta)

            self.stack_item = stack_item

        def __repr__(self) -> str:
            return "<SameLocals1StackItemFrame(offset_delta=%i, stack_item=%s) at %x>" % (
                self.offset_delta, self.stack_item, id(self),
            )

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            buffer.write(bytes((self.offset_delta + 64,)))
            StackMapTable._write_verification_type(self.stack_item, class_file, buffer)

        def to_frame(self, previous: Frame, code: Optional["Code"] = None) -> Frame:
            frame = previous.copy()
            frame.pop(len(frame.stack))
            frame.push(self._make_entry(self.stack_item, code))
            if self.stack_item.wide:
                frame.push(self._make_entry(reserved_t, code))
            return frame

    class SameLocals1StackItemFrameExtended(StackMapFrame):  # Uh, yeah lmao
        """
        Indicates that this frame has the exact same locals as the previous frame and that the operand stack has one entry.
        The delta offset is given explicitly, however.
        """

        __slots__ = ("stack_item",)

        frame_type = range(247, 248)

        @classmethod
        def read(
                cls, frame_type: int, class_file: "ClassFile", buffer: IO[bytes],
        ) -> "StackMapTable.SameLocals1StackItemFrameExtended":
            offset_delta, = unpack_H(buffer.read(2))
            stack_item = StackMapTable._read_verification_type(class_file, buffer)
            return cls(offset_delta, stack_item)

        def __init__(self, offset_delta: int, stack_item: Verification) -> None:
            """
            :param stack_item: The extra stack item.
            """

            super().__init__(offset_delta)
            
            self.stack_item = stack_item

        def __repr__(self) -> str:
            return "<SameLocals1StackItemFrameExtended(offset_delta=%i, stack_item=%s) at %x>" % (
                self.offset_delta, self.stack_item, id(self),
            )

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            buffer.write(bytes((247,)))
            buffer.write(pack_H(self.offset_delta))
            StackMapTable._write_verification_type(self.stack_item, class_file, buffer)

        def to_frame(self, previous: Frame, code: Optional["Code"] = None) -> Frame:
            frame = previous.copy()
            frame.pop(len(frame.stack))
            frame.push(self._make_entry(self.stack_item, code))
            if self.stack_item.wide:
                frame.push(self._make_entry(reserved_t, code))
            return frame

    class ChopFrame(StackMapFrame):
        """
        Indicates that the frame has the same locals as the previous frame except that the last <k> locals are absent and
        that the operand stack is empty.
        """

        __slots__ = ("chopped",)

        frame_type = range(248, 251)

        @classmethod
        def read(cls, frame_type: int, class_file: "ClassFile", buffer: IO[bytes]) -> "StackMapTable.ChopFrame":
            offset_delta, = unpack_H(buffer.read(2))
            return cls(offset_delta, 251 - frame_type)

        def __init__(self, offset_delta: int, chopped: int) -> None:
            """
            :param chopped: The number of locals that were chopped.
            """

            super().__init__(offset_delta)

            self.chopped = chopped

        def __repr__(self) -> str:
            return "<ChopFrame(offset_delta=%i, chopped=%i) at %x>" % (self.offset_delta, self.chopped, id(self))

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            buffer.write(bytes((251 - self.chopped,)))
            buffer.write(pack_H(self.offset_delta))

        def to_frame(self, previous: Frame, code: Optional["Code"] = None) -> Frame:
            frame = previous.copy()
            frame.pop(len(frame.stack))

            max_local = max(frame.locals)

            for index in range(self.chopped):
                entry = frame.locals.pop(max_local)
                max_local -= 1
                if entry.generic is reserved_t:  # Category 2 type
                    max_local -= 1

            return frame

    class SameFrameExtended(StackMapFrame):
        """
        Indicates that the frame has the exact same locals as the previous frame and that the operand stack is empty. The
        delta offset is explicitly given.
        """

        __slots__ = ()

        frame_type = range(251, 252)

        @classmethod
        def read(cls, frame_type: int, class_file: "ClassFile", buffer: IO[bytes]) -> "StackMapTable.SameFrameExtended":
            offset_delta, = unpack_H(buffer.read(2))
            return cls(offset_delta)

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            buffer.write(bytes((251,)))
            buffer.write(pack_H(self.offset_delta))

        def to_frame(self, previous: Frame, code: Optional["Code"] = None) -> Frame:
            frame = previous.copy()
            frame.pop(len(frame.stack))
            return frame

    class AppendFrame(StackMapFrame):
        """
        Indicates that the frame has the exact same locals as the previous frame except that <k> additional locals are
        defined and that the operand stack is empty.
        """

        __slots__ = ("locals",)

        frame_type = range(252, 255)

        @classmethod
        def read(cls, frame_type: int, class_file: "ClassFile", buffer: IO[bytes]) -> "StackMapTable.AppendFrame":
            offset_delta, = unpack_H(buffer.read(2))
            locals_ = tuple(
                StackMapTable._read_verification_type(class_file, buffer) for index in range(frame_type - 251)
            )
            return cls(offset_delta, locals_)

        def __init__(self, offset_delta: int, locals_: tuple[Verification, ...]) -> None:
            """
            :param locals_: The locals to append.
            """

            super().__init__(offset_delta)

            self.locals = locals_

        def __repr__(self) -> str:
            return "<AppendFrame(offset_delta=%i, locals=[%s]) at %x>" % (
                self.offset_delta, ", ".join(map(str, self.locals)), id(self),
            )

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            buffer.write(bytes((251 + len(self.locals),)))
            buffer.write(pack_H(self.offset_delta))
            for local in self.locals:
                StackMapTable._write_verification_type(local, class_file, buffer)

        def to_frame(self, previous: Frame, code: Optional["Code"] = None) -> Frame:
            frame = previous.copy()
            frame.pop(len(frame.stack))

            index = max(frame.locals, default=-1) + 1
            for type_ in self.locals:
                frame.set(index, self._make_entry(type_, code))
                index += 1
                if type_.wide:
                    frame.set(index, self._make_entry(reserved_t, code))
                    index += 1

            return frame

    class FullFrame(StackMapFrame):
        """
        A full stack frame.
        """

        __slots__ = ("locals", "stack")

        frame_type = range(255, 256)

        @classmethod
        def read(cls, frame_type: int, class_file: "ClassFile", buffer: IO[bytes]) -> "StackMapTable.FullFrame":
            offset_delta, = unpack_H(buffer.read(2))
            locals_ = tuple(
                StackMapTable._read_verification_type(class_file, buffer)
                for index in range(unpack_H(buffer.read(2))[0])
            )
            stack = tuple(
                StackMapTable._read_verification_type(class_file, buffer)
                for index in range(unpack_H(buffer.read(2))[0])
            )

            return cls(offset_delta, locals_, stack)

        def __init__(
                self, offset_delta: int, locals_: tuple[Verification, ...], stack: tuple[Verification, ...],
        ) -> None:
            """
            :param locals_: The locals in this frame.
            :param stack: The stack in this frame.
            """

            super().__init__(offset_delta)

            self.locals = locals_
            self.stack = stack

        def __repr__(self) -> str:
            return "<FullFrame(offset_delta=%i, locals=[%s], stack=[%s]) at %x>" % (
                self.offset_delta, ", ".join(map(str, self.locals)), ", ".join(map(str, self.stack)), id(self),
            )

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            buffer.write(bytes((255,)))
            buffer.write(pack_H(self.offset_delta))

            buffer.write(pack_H(len(self.locals)))
            for local in self.locals:
                StackMapTable._write_verification_type(local, class_file, buffer)

            buffer.write(pack_H(len(self.stack)))
            for state in self.stack:
                StackMapTable._write_verification_type(state, class_file, buffer)

        def to_frame(self, previous: Frame, code: Optional["Code"] = None) -> Frame:
            frame = previous.copy()
            frame.pop(len(frame.stack))
            frame.locals.clear()

            index = 0
            for type_ in self.locals:
                frame.set(index, self._make_entry(type_, code))
                index += 1
                if type_.wide:
                    frame.set(index, self._make_entry(reserved_t, code))
                    index += 1

            for type_ in self.stack:
                frame.push(self._make_entry(type_, code))
                if type_.wide:
                    frame.push(self._make_entry(reserved_t, code))

            return frame

    STACK_MAP_FRAMES = (
        SameFrame,
        AppendFrame,
        SameLocals1StackItemFrame,
        ChopFrame,
        FullFrame,
        SameFrameExtended,
        SameLocals1StackItemFrameExtended,
    )


class LineNumberTable(AttributeInfo):
    """
    Records a mapping of line numbers to bytecode offsets.
    """

    __slots__ = ("entries",)

    name_ = "LineNumberTable"
    since = Version(45, 3)
    locations = ("Code",)

    def __init__(self, parent: "Code", entries: Iterable["LineNumberTable.LineNumberEntry"] | None = None) -> None:
        """
        :param entries: The line number entries.
        """

        super().__init__(parent, LineNumberTable.name_)

        self.entries: list[LineNumberTable.LineNumberEntry] = []
        if entries is not None:
            self.entries.extend(entries)

    def __repr__(self) -> str:
        return "<LineNumberTable(%r) at %x>" % (self.entries, id(self))

    def __iter__(self) -> Iterable["LineNumberTable.LineNumberEntry"]:
        return iter(self.entries)

    def __getitem__(self, index: int) -> "LineNumberTable.LineNumberEntry":
        return self.entries[index]

    def __setitem__(self, index: int, value: "LineNumberTable.LineNumberEntry") -> None:
        self.entries[index] = value

    def __contains__(self, item: Any) -> bool:
        return item in self.entries

    def __len__(self) -> int:
        return len(self.entries)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.entries.clear()
        entry_count, = unpack_H(buffer.read(2))
        for index in range(entry_count):
            self.entries.append(LineNumberTable.LineNumberEntry.read(buffer))

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.entries)))
        for entry in self.entries:
            entry.write(buffer)

    class LineNumberEntry:
        """
        An entry in the line number table.
        """

        __slots__ = ("class_file", "start_pc", "line_number",)

        @classmethod
        def read(cls, buffer: IO[bytes]) -> "LineNumberTable.LineNumberEntry":
            """
            Reads a line number entry from the buffer.

            :param buffer: The binary buffer to read from.
            :return: The read line number entry.
            """

            start_pc, line_number = unpack_HH(buffer.read(4))
            return cls(start_pc, line_number)

        def __init__(self, start_pc: int, line_number: int) -> None:
            """
            :param start_pc: The starting bytecode offset of the line.
            :param line_number: The source code line number.
            """

            self.start_pc = start_pc
            self.line_number = line_number

        def __repr__(self) -> str:
            return "<LineNumberEntry(start_pc=%i, line_number=%i) at %x>" % (self.start_pc, self.line_number, id(self))

        def write(self, buffer: IO[bytes]) -> None:
            """
            Writes this line number entry to the buffer.

            :param buffer: The binary buffer to write to.
            """

            buffer.write(pack_HH(self.start_pc, self.line_number))


class LocalVariableTable(AttributeInfo):
    """
    Contains the names of the local variables used in the code.
    """

    __slots__ = ("entries",)

    name_ = "LocalVariableTable"
    since = Version(45, 3)
    locations = ("Code",)

    def __init__(
            self, parent: "Code", entries: Iterable["LocalVariableTable.LocalVariableEntry"] | None = None,
    ) -> None:
        """
        :param entries: The local variable entries.
        """

        super().__init__(parent, LocalVariableTable.name_)

        self.entries: list[LocalVariableTable.LocalVariableEntry] = []
        if entries is not None:
            self.entries.extend(entries)

    def __repr__(self) -> str:
        return "<LocalVariableTable(%r) at %x>" % (self.entries, id(self))

    def __iter__(self) -> Iterable["LocalVariableTable.LocalVariableEntry"]:
        return iter(self.entries)

    def __getitem__(self, index: int) -> "LocalVariableTable.LocalVariableEntry":
        return self.entries[index]

    def __setitem__(self, index: int, value: "LocalVariableTable.LocalVariableEntry") -> None:
        self.entries[index] = value

    def __contains__(self, item: Any) -> bool:
        return item in self.entries

    def __len__(self) -> int:
        return len(self.entries)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.entries.clear()
        entries_count, = unpack_H(buffer.read(2))
        for index in range(entries_count):
            self.entries.append(LocalVariableTable.LocalVariableEntry.read(class_file, buffer, fail_fast))

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.entries)))
        for entry in self.entries:
            entry.write(class_file, buffer)

    class LocalVariableEntry:
        """
        An entry in the local variable table.
        """

        __slots__ = ("start_pc", "length", "name", "descriptor", "index")

        @classmethod
        def read(cls, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool) -> "LocalVariableTable.LocalVariableEntry":
            """
            Reads a local variable entry from the buffer.

            :param class_file: The class file that the entry belongs to.
            :param buffer: The binary buffer to read from.
            :param fail_fast: Throws an exception if it's obvious this local variable entry is invalid.
            :return: The read local variable entry.
            """

            entry = cls.__new__(cls)

            (
                entry.start_pc,
                entry.length,
                name_index,
                descriptor_index,
                entry.index,
            ) = unpack_HHHHH(buffer.read(10))

            entry.name = class_file.constant_pool.get(name_index, do_raise=fail_fast)
            entry.descriptor = class_file.constant_pool.get(descriptor_index, do_raise=fail_fast)

            # try:
            #     self.type_ = descriptor.parse_field_descriptor(
            #         self.descriptor,
            #         force_read=self.class_file.context.force_read_descriptors,
            #         dont_throw=False,
            #     )
            # except Exception as error:
            #     self.type_ = descriptor.parse_field_descriptor(self.descriptor, force_read=False, dont_throw=True)

            #     logger.warning("Invalid descriptor %r in class %r: %r" % (
            #         self.descriptor, self.class_file.name, error.args[0],
            #     ))
            #     logger.debug("Invalid descriptor on local %r." % self, exc_info=True)

            return entry

        def __init__(self, start_pc: int, length: int, name: UTF8, descriptor_: UTF8, index: int) -> None:
            """
            :param start_pc: The starting bytecode offset that the local variable appears at.
            :param length: How many bytecodes the local variable persists for.
            :param name: The name of the local variable.
            :param descriptor_: The type descriptor of the local variable.
            :param index: The local variable index.
            """

            self.start_pc = start_pc
            self.length = length
            self.name = name
            self.descriptor = descriptor_
            self.index = index

        def __repr__(self) -> str:
            return "<LocalVariableEntry(start_pc=%i, length=%i, index=%i, name=%r, descriptor=%r) at %x>" % (
                self.start_pc, self.length, self.index, self.name, self.descriptor, id(self),
            )

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            """
            Writes this local variable entry to the buffer.

            :param class_file: The class file that the entry belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(pack_HHHHH(
                self.start_pc,
                self.length,
                class_file.constant_pool.add(self.name),
                class_file.constant_pool.add(self.descriptor),
                self.index,
            ))


class LocalVariableTypeTable(AttributeInfo):
    """
    Information about local variables with signatures.
    """

    __slots__ = ("entries",)

    name_ = "LocalVariableTypeTable"
    since = Version(49, 0)
    locations = ("Code",)

    def __init__(
            self, parent: "Code", entries: Iterable["LocalVariableTypeTable.LocalVariableTypeEntry"] | None = None,
    ) -> None:
        """
        :param entries: The local variable type entries.
        """

        super().__init__(parent, LocalVariableTypeTable.name_)

        self.entries: list[LocalVariableTypeTable.LocalVariableTypeEntry] = []
        if entries is not None:
            self.entries.extend(entries)

    def __repr__(self) -> str:
        return "<LocalVariableTypeTable(%r) at %x>" % (self.entries, id(self))

    def __len__(self) -> int:
        return len(self.entries)

    def __bool__(self) -> bool:
        return bool(self.entries)

    def __iter__(self) -> Iterable["LocalVariableTypeTable.LocalVariableTypeEntry"]:
        return iter(self.entries)

    def __contains__(self, item: Any) -> bool:
        return item in self.entries

    def __getitem__(self, index: int) -> "LocalVariableTypeTable.LocalVariableTypeEntry":
        return self.entries[index]

    def __setitem__(self, index: int, value: "LocalVariableTypeTable.LocalVariableTypeEntry") -> None:
        self.entries[index] = value

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.entries.clear()
        entries_count, = unpack_H(buffer.read(2))
        for index in range(entries_count):
            self.entries.append(LocalVariableTypeTable.LocalVariableTypeEntry.read(class_file, buffer, fail_fast))

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.entries)))
        for entry in self.entries:
            entry.write(class_file, buffer)

    class LocalVariableTypeEntry:
        """
        An entry in the local variable type table.
        """

        __slots__ = ("start_pc", "length", "name", "signature", "index")

        @classmethod
        def read(cls, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool) -> "LocalVariableTypeTable.LocalVariableTypeEntry":
            """
            Reads a local variable type entry from the buffer.

            :param class_file: The class file that the entry belongs to.
            :param buffer: The binary buffer to read from.
            :param fail_fast: Throws an exception if it's obvious that this local variable type entry is invalid.
            :return: The entry that was read.
            """

            entry = cls.__new__(cls)

            (
                entry.start_pc,
                entry.length,
                name_index,
                signature_index,
                entry.index,
            ) = unpack_HHHHH(buffer.read(10))

            entry.name = class_file.constant_pool.get(name_index, do_raise=fail_fast)
            entry.signature = class_file.constant_pool.get(signature_index, do_raise=fail_fast)

            # try:
            #     self.type_ = signature.parse_field_signature(
            #         self.signature,
            #         force_read=self.class_file.context.force_read_signatures,
            #         dont_throw=False,
            #     )
            # except Exception as error:
            #     self.type_ = signature.parse_field_signature(self.signature, force_read=False, dont_throw=True)

            #     logger.warning("Invalid signature %r in class %r: %r" % (
            #         self.signature, self.class_file.name, error.args[0],
            #     ))
            #     logger.debug("Invalid signature on local %r." % self, exc_info=True)

            return entry

        def __init__(self, start_pc: int, length: int, name: UTF8, signature: UTF8, index: int) -> None:
            """
            :param start_pc: The starting bytecode offset that the local variable appears.
            :param length: How many bytecodes the local variable appears for.
            :param name: The name of the local variable.
            :param signature: The signature of the local variable.
            :param index: The index of the local variable.
            """

            self.start_pc = start_pc
            self.length = length
            self.name = name
            self.signature = signature
            self.index = index

        def __repr__(self) -> str:
            return "<LocalVariableTypeEntry(start_pc=%i, length=%i, index=%i, name=%r, signature=%r) at %x>" % (
                self.start_pc, self.length, self.index, self.name, self.signature, id(self),
            )

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            """
            Writes this local variable type entry to the buffer.

            :param class_file: The class file that this entry belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(pack_HHHHH(
                self.start_pc,
                self.length,
                class_file.constant_pool.add(self.name),
                class_file.constant_pool.add(self.signature),
                self.index,
            ))
