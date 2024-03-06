#!/usr/bin/env python

from pathlib import Path
from setuptools import setup


if __name__ == "__main__":
    setup(
        name="kirjava-jvm",
        version="0.1.5",
        description="A Java bytecode library for Python.",
        long_description=(Path(__file__).parent / "README.md").read_text(),
        long_description_content_type="text/markdown",
        # classifiers=[
        #     "Programming Language :: Python",
        # ],
        author="node3112 (Iska)",
        author_email="node3112@protonmail.com",
        license="GPL-3.0",
        url="https://github.com/notiska/kirjava",
        packages=[
            "kirjava",
            "kirjava.abc",
            "kirjava.analysis",
            "kirjava.analysis.graph",
            "kirjava.classfile",
            "kirjava.classfile.attributes",
            "kirjava.instructions",
            "kirjava.jarfile",
            "kirjava.types",
        ],
        package_dir={
            "": "src",
        },
        keywords=["java", "jvm", "bytecode", "assembler", "disassembler"],
    )
