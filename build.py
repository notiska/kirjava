#!/usr/bin/env python3

from pybuilder.core import init, use_plugin, Author, Project

use_plugin("python.core")
use_plugin("python.distutils")


name = "kirjava"
version = "0.1.1"
summary = "A Java bytecode manipulation library for Python."
authors = (
    Author("node3112 (Iska)", "node3112@protonmail.com"),
)
default_task = "publish"


@init
def set_properties(project: Project) -> None:
    project.depends_on("frozendict")

    project.set_property("dir_source_main_python", "src/")
    project.set_property("dir_source_unittest_python", "tests/")

    project.include_directory("kirjava/skeleton", ["*.json"], "src/")

