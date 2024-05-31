#!/usr/bin/env python

from pathlib import Path
from setuptools import setup


# This is my first PyPI package, just trying my best lol.
if __name__ == "__main__":
    setup(
        name="kirjava-jvm",
        version="0.1.6",
        description="A Java bytecode library for Python.",
        long_description=(Path(__file__).parent / "README.md").read_text(),
        long_description_content_type="text/markdown",
        classifiers=[  # Somewhat modelled after https://github.com/ninia/jep, thanks :).
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: File Formats",  # Maybe?
            "Topic :: Software Development",
            "Topic :: Software Development :: Assemblers",
            "Topic :: Software Development :: Code Generators",
            "Topic :: Software Development :: Disassemblers",
            "Topic :: Software Development :: Libraries :: Java Libraries",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.10",  # TODO: Would be nice to support eariler versions.
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
        ],
        # classifiers=[
        #     "Programming Language :: Python",
        # ],        author="node3112 (Iska)",
        author_email="node3113@gmail.com",
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
