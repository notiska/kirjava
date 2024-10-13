#!/usr/bin/env python3

import unittest
from io import BytesIO
from os import SEEK_SET

from kirjava.backend import *
from kirjava.jvm.fmt import ConstPool
from kirjava.jvm.fmt.annotation import *
from kirjava.jvm.fmt.attribute import *
from kirjava.jvm.fmt.classfile import *
from kirjava.jvm.fmt.constants import *
from kirjava.jvm.fmt.field import *
from kirjava.jvm.fmt.method import *
from kirjava.jvm.fmt.stackmap import *
from kirjava.jvm.insns import *
from kirjava.jvm.version import JAVA_MAX, Version


class TestAttributes(unittest.TestCase):

    _DEFAULTS = {  # Attribute init default values.
        # Shared attributes.
        RawInfo:    (UTF8Info(b"test"), b"test"),
        Synthetic:  (),
        Signature:  (UTF8Info(b"LTest;"),),
        Deprecated: (),
        RuntimeVisibleAnnotations: ([
            Annotation(
                UTF8Info(b"LTestAnnotation1;"), [Annotation.NamedElement(
                    UTF8Info(b"testElement1"),ConstValue(ConstValue.KIND_BYTE, IntegerInfo(i32(1))),
                )],
            ),
            Annotation(
                UTF8Info(b"LTestAnnotation1;"), [Annotation.NamedElement(
                    UTF8Info(b"testElement2"), ConstValue(ConstValue.KIND_INT, IntegerInfo(i32(2))),
                )],
            ),
        ],),
        RuntimeInvisibleAnnotations: ([
            Annotation(
                UTF8Info(b"LTestAnnotation1;"),
                [
                    Annotation.NamedElement(
                        UTF8Info(b"testElement3"), ConstValue(ConstValue.KIND_STRING, StringInfo(UTF8Info(b"test"))),
                    ),
                ],
            ),
            Annotation(
                UTF8Info(b"LTestAnnotation1;"),
                [
                    Annotation.NamedElement(
                        UTF8Info(b"testElement4"),
                        EnumConstValue(UTF8Info(b"LTestEnum;"), UTF8Info(b"TEST_ENUM_FIELD_1")),
                    ),
                ],
            ),
        ],),
        RuntimeVisibleTypeAnnotations: ([  # Wtf am I even doing lol. I'm sure these aren't valid at this point.
            TypeAnnotation(
                UTF8Info(b"LTestAnnotation2;"),
                TypeParameterTarget(TargetInfo.GENERIC_CLASS_TYPE_PARAMETER, 0),
                TypePath(),
                [Annotation.NamedElement(UTF8Info(b"testElement1"), ClassValue(UTF8Info(b"LTest;")))],
            ),
            TypeAnnotation(
                UTF8Info(b"LTestAnnotation2;"), SuperTypeTarget(65535), TypePath(),
                [Annotation.NamedElement(UTF8Info(b"testElement1"), ClassValue(UTF8Info(b"LTest;")))],
            ),
            TypeAnnotation(
                UTF8Info(b"LTestAnnotation2;"),
                TypeParameterBoundTarget(TargetInfo.GENERIC_CLASS_TYPE_PARAMETER_BOUND, 0, 0),
                TypePath(),
                [Annotation.NamedElement(
                    UTF8Info(b"testElement2"), ConstValue(ConstValue.KIND_LONG, LongInfo(i64(1))),
                )],
            ),
            TypeAnnotation(
                UTF8Info(b"LTestAnnotation2;"),
                EmptyTarget(TargetInfo.METHOD_RETURN_TYPE_OR_NEW_OBJECT),
                TypePath([TypePath.Segment(TypePath.Segment.TYPE_ARGUMENT, 0)]),
                [Annotation.NamedElement(
                    UTF8Info(b"testElement2"), ConstValue(ConstValue.KIND_LONG, LongInfo(i64(1))),
                )],
            ),
            TypeAnnotation(
                UTF8Info(b"LTestAnnotaton3;"), FormalParameterTarget(2), TypePath(),
                [
                    Annotation.NamedElement(
                        UTF8Info(b"testElement1"), ConstValue(ConstValue.KIND_STRING, StringInfo(UTF8Info(b"test"))),
                    ),
                ],
            ),
            TypeAnnotation(
                UTF8Info(b"LTestAnnotaton2;"), ThrowsTarget(0), TypePath(),
                [Annotation.NamedElement(
                    UTF8Info(b"testElement2"), ConstValue(ConstValue.KIND_LONG, LongInfo(i64(1))),
                )],
            ),
        ],),
        RuntimeInvisibleTypeAnnotations: ([
            TypeAnnotation(
                UTF8Info(b"LTestAnnotation3;"),
                LocalVarTarget(TargetInfo.LOCAL_VARIABLE_TYPE, [LocalVarTarget.LocalVar(5, 23, 0)]),
                TypePath([
                    TypePath.Segment(TypePath.Segment.ARRAY_NESTED, 0),
                    TypePath.Segment(TypePath.Segment.ARRAY_NESTED, 0),
                ]),
                [
                    Annotation.NamedElement(
                        UTF8Info(b"testElement1"), ConstValue(ConstValue.KIND_CHAR, IntegerInfo(i32(ord("t")))),
                    ),
                ],
            ),
            TypeAnnotation(
                UTF8Info(b"LTestAnnotation2;"), CatchTarget(1), TypePath(),
                [Annotation.NamedElement(UTF8Info(b"testElement1"), ClassValue(UTF8Info(b"LTest;")))],
            ),
            TypeAnnotation(
                UTF8Info(b"LTestAnnotation3;"), OffsetTarget(TargetInfo.INSTANCEOF_TYPE, 12), TypePath(),
                [
                    Annotation.NamedElement(
                        UTF8Info(b"testElement1"), ConstValue(ConstValue.KIND_CHAR, IntegerInfo(i32(ord("t")))),
                    ),
                ],
            ),
            TypeAnnotation(
                UTF8Info(b"LTestAnnotation3;"),
                TypeArgumentTarget(TargetInfo.CAST_TYPE, 16, 2),
                TypePath(),
                [Annotation.NamedElement(UTF8Info(b"testElement2"), ClassValue(UTF8Info(b"LTest;")))],
            ),
        ],),

        # Class file attributes.
        BootstrapMethods: ([
            BootstrapMethods.BootstrapMethod(
                MethodHandleInfo(
                    MethodHandleInfo.INVOKE_STATIC,
                    MethodrefInfo(
                        ClassInfo(UTF8Info(b"Test")),
                        NameAndTypeInfo(
                            UTF8Info(b"test"),
                            # Yep, it's a long line, fun.
                            UTF8Info(b"(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;III)Ljava/lang/invoke/Callsite;"),
                        ),
                    ),
                ),
                [IntegerInfo(i32(5)), IntegerInfo(i32(6)), IntegerInfo(i32(7))],
            ),
        ],),
        NestHost: (ClassInfo(UTF8Info(b"Test")),),
        NestMembers: ([ClassInfo(UTF8Info(b"Test1")), ClassInfo(UTF8Info(b"Test2"))],),
        PermittedSubclasses: ([ClassInfo(UTF8Info(b"Test1")), ClassInfo(UTF8Info(b"Test2"))],),
        InnerClasses: ([
            InnerClasses.InnerClass(
                ClassInfo(UTF8Info(b"Test1")), ClassInfo(UTF8Info(b"Test")), None,
                InnerClasses.InnerClass.ACC_PUBLIC | InnerClasses.InnerClass.ACC_STATIC,
            ),
            InnerClasses.InnerClass(
                ClassInfo(UTF8Info(b"Test")), None, None,
                InnerClasses.InnerClass.ACC_PUBLIC | InnerClasses.InnerClass.ACC_STATIC,
            ),
        ],),
        EnclosingMethod: (ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"test"), UTF8Info(b"()V"))),
        Record: ([
            Record.ComponentInfo(UTF8Info(b"testComponent1"), UTF8Info(b"D")),
            Record.ComponentInfo(UTF8Info(b"testComponent2"), UTF8Info(b"Z")),
        ],),
        SourceFile: (UTF8Info(b"Test.java"),),
        SourceDebugExtension: (b"testing...",),
        Module: (  # My sanity at this point....
            # Also, I don't know how to name modules properly in Java, I've never used them.
            ModuleInfo(UTF8Info(b"test")), Module.ACC_OPEN | Module.ACC_MANDATED, UTF8Info(b"1.0"),
            [
                Module.Require(
                    ModuleInfo(UTF8Info(b"test2")),
                    Module.Require.ACC_TRANSITIVE | Module.Require.ACC_STATIC_PHASE | Module.Require.ACC_MANDATED,
                    UTF8Info(b"2.0"),
                ),
                Module.Require(
                    ModuleInfo(UTF8Info(b"test3")),
                    Module.Require.ACC_STATIC_PHASE | Module.Require.ACC_MANDATED,
                    None,
                ),
            ],
            [
                Module.Export(
                    PackageInfo(UTF8Info(b"tests1")),
                    Module.Export.ACC_MANDATED,
                    [ModuleInfo(UTF8Info(b"test2")), ModuleInfo(UTF8Info(b"test3"))],
                ),
                Module.Export(PackageInfo(UTF8Info(b"tests2")), 0, [ModuleInfo(UTF8Info(b"test2"))]),
            ],
            [
                Module.Open(
                    PackageInfo(UTF8Info(b"tests1")),
                    Module.Open.ACC_MANDATED,
                    [ModuleInfo(UTF8Info(b"test2")), ModuleInfo(UTF8Info(b"test3"))],
                ),
                Module.Open(PackageInfo(UTF8Info(b"tests2")), 0, [ModuleInfo(UTF8Info(b"test2"))]),
            ],
            [ClassInfo(UTF8Info(b"test1"))],
            [
                Module.Provide(
                    ClassInfo(UTF8Info(b"TestService1")),
                    [ClassInfo(UTF8Info(b"tests1/TestImpl1")), ClassInfo(UTF8Info(b"tests1/TestImpl2"))],
                ),
                Module.Provide(ClassInfo(UTF8Info(b"TestService2")), [ClassInfo(UTF8Info(b"tests1/TestImpl2"))]),
            ],
        ),
        ModulePackages: ([PackageInfo(UTF8Info(b"tests1")), PackageInfo(UTF8Info(b"test2"))],),
        ModuleMainClass: (ClassInfo(UTF8Info(b"Test")),),

        # Field info attributes.
        ConstantValue: (FloatInfo(f32(5.0)),),

        # Method info / code attributes.
        Code: (
            1, 5, 14, [iconst_0(), iconst_0(), iconst_0(), pop2(), dup(), pop2()],
            [Code.ExceptHandler(0, 30, 10, None), Code.ExceptHandler(5, 25, 10, ClassInfo(UTF8Info(b"TestException")))],
            [],
        ),
        StackMapTable: ([
            SameFrame(5),
            SameLocalsOneStackItemFrame(74, IntegerVarInfo()),
            SameLocalsOneStackItemFrameExtended(5, FloatVarInfo()),
            ChopFrame(250, 30),
            SameFrameExtended(2),
            AppendFrame(254, 10, (TopVarInfo(), DoubleVarInfo(), LongVarInfo())),
            FullFrame(
                10,
                (NullVarInfo(), UninitializedThisVarInfo()),
                (ObjectVarInfo(ClassInfo(UTF8Info(b"test"))), UninitializedVarInfo(4)),
            ),
        ],),
        Exceptions: ([ClassInfo(UTF8Info(b"TestException")), ClassInfo(UTF8Info(b"TestException2"))],),
        LineNumberTable: ([
            LineNumberTable.LineNumber(0, 30), LineNumberTable.LineNumber(2, 31), LineNumberTable.LineNumber(5, 32),
            LineNumberTable.LineNumber(10, 35), LineNumberTable.LineNumber(13, 36), LineNumberTable.LineNumber(16, 37),
        ],),
        LocalVariableTable: ([
            LocalVariableTable.LocalVariable(0, 30, UTF8Info(b"test"), UTF8Info(b"D"), 1),
            LocalVariableTable.LocalVariable(5, 25, UTF8Info(b"test2"), UTF8Info(b"Z"), 2),
        ],),
        LocalVariableTypeTable: ([  # Yep, I'm this lazy.
            LocalVariableTypeTable.LocalVariable(0, 30, UTF8Info(b"test"), UTF8Info(b"D"), 1),
            LocalVariableTypeTable.LocalVariable(5, 25, UTF8Info(b"test2"), UTF8Info(b"Z"), 2),
        ],),
        AnnotationDefault: (
            ArrayValue([
                ConstValue(ConstValue.KIND_BYTE, IntegerInfo(i32(1))),
                ConstValue(ConstValue.KIND_CHAR, IntegerInfo(i32(ord("t")))),
                ConstValue(ConstValue.KIND_DOUBLE, DoubleInfo(f64(2.0))),
                ConstValue(ConstValue.KIND_FLOAT, FloatInfo(f32(3.0))),
                ConstValue(ConstValue.KIND_INT, IntegerInfo(i32(4))),
                ConstValue(ConstValue.KIND_LONG, LongInfo(i64(5))),
                ConstValue(ConstValue.KIND_SHORT, IntegerInfo(i32(6))),
                ConstValue(ConstValue.KIND_BOOLEAN, IntegerInfo(i32(0))),
                ConstValue(ConstValue.KIND_STRING, StringInfo(UTF8Info(b"test"))),
                EnumConstValue(UTF8Info(b"LTestEnum;"), UTF8Info(b"TEST_ENUM_FIELD_1")),
                ClassValue(UTF8Info(b"LTest;")),
                AnnotationValue(
                    Annotation(
                        UTF8Info(b"LTestAnnotation1;"),
                        [
                            Annotation.NamedElement(
                                UTF8Info(b"testElement1"), ConstValue(ConstValue.KIND_BYTE, IntegerInfo(i32(1))),
                            ),
                            Annotation.NamedElement(
                                UTF8Info(b"testElement2"), ConstValue(ConstValue.KIND_INT, IntegerInfo(i32(2))),
                            ),
                            Annotation.NamedElement(
                                UTF8Info(b"testElement3"),
                                ConstValue(ConstValue.KIND_STRING, StringInfo(UTF8Info(b"test"))),
                            ),
                            Annotation.NamedElement(
                                UTF8Info(b"testElement4"),
                                EnumConstValue(UTF8Info(b"LTestEnum;"), UTF8Info(b"TEST_ENUM_FIELD_1")),
                            ),
                        ],
                    ),
                ),
            ],
        ),),
        MethodParameters: ([
            MethodParameters.Parameter(UTF8Info(b"test1"), MethodParameters.Parameter.ACC_FINAL),
            MethodParameters.Parameter(
                UTF8Info(b"test2"), MethodParameters.Parameter.ACC_FINAL | MethodParameters.Parameter.ACC_MANDATED,
            ),
        ],),
        RuntimeVisibleParameterAnnotations: ([
            ParameterAnnotations([
                Annotation(
                    UTF8Info(b"LTestAnnotation1;"),
                    [Annotation.NamedElement(
                        UTF8Info(b"testElement1"), ConstValue(ConstValue.KIND_BYTE, IntegerInfo(i32(1))),
                    )],
                ),
            ]),
            ParameterAnnotations([
                Annotation(
                    UTF8Info(b"LTestAnnotation1;"),
                    [Annotation.NamedElement(
                        UTF8Info(b"testElement2"), ConstValue(ConstValue.KIND_INT, IntegerInfo(i32(2))),
                    )],
                ),
            ]),
        ],),
        RuntimeInvisibleParameterAnnotations: ([
            ParameterAnnotations([
                Annotation(
                    UTF8Info(b"LTestAnnotation1;"),
                    [
                        Annotation.NamedElement(
                            UTF8Info(b"testElement3"), ConstValue(ConstValue.KIND_STRING, StringInfo(UTF8Info(b"test"))),
                        ),
                    ],
                ),
                Annotation(
                    UTF8Info(b"LTestAnnotation1;"),
                    [
                        Annotation.NamedElement(
                            UTF8Info(b"testElement4"),
                            EnumConstValue(UTF8Info(b"LTestEnum;"), UTF8Info(b"TEST_ENUM_FIELD_1")),
                        ),
                    ],
                ),
            ]),
        ],),
    }

    def setUp(self) -> None:
        self.pool = ConstPool()

    def test_abc_attrs(self) -> None:
        for subclass in AttributeInfo.__subclasses__():
            with self.subTest(subclass.__name__):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest("Missing default init values for %r." % subclass)
                attr = subclass(*init)  # type: ignore[arg-type]
                self.assertIsInstance(attr.tag, bytes)
                self.assertIsInstance(attr.since, Version)
                self.assertIsInstance(attr.locations, frozenset)
                self.assertIsInstance(attr.name, (ConstInfo, type(None)))
                self.assertIsInstance(attr.extra, bytes)

    def test_repr_str(self) -> None:
        for subclass in AttributeInfo.__subclasses__():
            with self.subTest(subclass.__name__):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest("Missing default init values for %r." % subclass)
                attr = subclass(*init)  # type: ignore[arg-type]
                print(repr(attr), str(attr))

    def test_symmetric_read_write(self) -> None:
        for subclass in AttributeInfo.__subclasses__():
            with self.subTest(subclass.__name__):  # , subclass=subclass):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest("Missing default init values for %r." % subclass)
                attr_init = subclass(*init)  # type: ignore[arg-type]

                data = BytesIO()
                attr_init.write(data, JAVA_MAX, self.pool)
                data_first = data.getvalue()
                data.seek(0, SEEK_SET)

                attr_read, _ = AttributeInfo.read(data, JAVA_MAX, self.pool, None)
                self.assertEqual(attr_init, attr_read)
                if data.read():
                    self.fail("Attribute underread.")

                data = BytesIO()
                attr_read.write(data, JAVA_MAX, self.pool)
                self.assertEqual(data_first, data.getvalue())
