#!/usr/bin/env python3

# TODO


class Linker:
    """
    Links information about class, field and method references.

    This provides a higher level way to reference classes, fields and methods
    through an initial lookup by name.
    All of said references are singletons.
    """

    class ClassRef:
        ...

    class FieldRef:
        ...

    class MethodRef:
        ...
