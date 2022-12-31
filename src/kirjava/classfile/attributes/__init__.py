#!/usr/bin/env python3

import logging
import struct
import typing
from typing import Any, IO

from ...version import Version

if typing.TYPE_CHECKING:
    from .. import ClassFile

logger = logging.getLogger("kirjava.classfile.attributes")


class AttributeInfo:
    """
    Base attribute info class.
    """

    __slots__ = ("class_file", "parent", "name", "data")

    since = Version(45, 0)
    locations = ()

    def __init__(self, parent: Any, name: str) -> None:
        self.parent = parent

        self.name = name
        self.data = b""  # Fallback attribute data if we can't read it

    def __repr__(self) -> str:
        return "<%s()> at %x" % (self.__class__.__name__, id(self))

    def read(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Populates the attribute's data from the buffer.

        :param class_file: The class file that this attribute belongs to.
        :param buffer: The binary data buffer to read from.
        """

        ...

        # attribute_length, = struct.unpack(">I", buffer.read(4))
        # self.data = buffer.read(attribute_length)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes this attribute's data to the buffer.

        :param class_file: The class file that this attribute belongs to.
        :param buffer: The binary buffer to write to.
        """

        ...

        
from .class_ import *
from .code import *
from .field import *
from .method import *
from .shared import *

ATTRIBUTES = (
    ConstantValue,
    Code,
    StackMapTable,
    BootstrapMethods,
    NestHost,
    NestMembers,
    PermittedSubclasses,
    
    Exceptions,
    InnerClasses,
    EnclosingMethod,
    Synthetic,
    Signature,
    Record,
    SourceFile,
    LineNumberTable,
    LocalVariableTable,
    LocalVariableTypeTable,
    RuntimeVisibleAnnotations,
    RuntimeInvisibleAnnotations,
)

_attribute_map = {attribute.name_: attribute for attribute in ATTRIBUTES}


def read_attribute(parent: Any, class_file: "ClassFile", buffer: IO[bytes]) -> AttributeInfo:
    """
    Reads an attribute info from the buffer.
    
    :param parent: The parent (element in the class file, or the class file itself) that the attribute belongs to.
    :param class_file: The class file that the attribute belongs to.
    :param buffer: The buffer to read from.
    :return: The attribute.
    """

    # TODO: Option to "fail fast" so we don't read the entirety of an attribute if it's obvious that it's invalid

    name_index, attribute_length = struct.unpack(">HI", buffer.read(6))
    name = class_file.constant_pool.get_utf8(name_index, "<invalid>")  # FIXME: Yes or no?

    offset = buffer.tell()
    if name in _attribute_map:
        attribute = _attribute_map[name]
        version_valid = attribute.since <= class_file.version
        location_valid = (
            parent.__class__ in attribute.locations or
            parent.__class__.__name__ in attribute.locations  # To avoid circular import nightmares
        )
        if version_valid and location_valid:
            try:
                attribute_info = attribute(parent)
                attribute_info.read(class_file, buffer)
                # logger.debug("Found attribute %r." % attribute_info)

                difference = buffer.tell() - (offset + attribute_length)
                if difference > 0:
                    logger.debug("Attribute %r in class %r overread (%i bytes)." % (
                        name, class_file.name, difference,
                    ))
                    buffer.seek(offset + attribute_length)
                elif difference < 0:
                    logger.debug("Attribute %r in class %r underread (%i bytes)." % (
                        name, class_file.name, -difference,
                    ))
                    buffer.seek(offset + attribute_length)

                return attribute_info

            except Exception as error:
                # raise error
                # logger.error("Couldn't read attribute %r in class %r: %r" % (
                #     name, class_file.name, error,
                # ))
                logger.debug(error, exc_info=True)
    else:
        logger.debug("Unknown attribute %r in class %r." % (name, class_file.name))

    attribute_info = AttributeInfo(parent, name)
    buffer.seek(offset)
    attribute_info.data = buffer.read(attribute_length)

    return attribute_info


def write_attribute(attribute: AttributeInfo, class_file: "ClassFile", buffer: IO[bytes]) -> None:
    """
    Writes an attribute to the buffer.

    :param attribute: The attribute to write to the buffer.
    :param class_file: The class file that the attribute belongs to.
    :param buffer: The binary buffer to write to.
    """

    start = buffer.tell()
    buffer.write(b"\x00\x00\x00\x00\x00\x00")  # Placeholder for bytes for the name index and attribute length

    if attribute.data:
        buffer.write(attribute.data)
    else:
        attribute.write(class_file, buffer)

    current = buffer.tell()

    buffer.seek(start)
    buffer.write(struct.pack(">HI", class_file.constant_pool.add_utf8(attribute.name), current - start - 6))
    buffer.seek(current)
