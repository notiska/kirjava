#!/usr/bin/env python

from Cython.Build import cythonize
from setuptools import setup


if __name__ == "__main__":
    setup(
        name="kirjava",
        version="0.1.3",
        description="A Java bytecode library for Python.",
        # classifiers=[
        #     "Programming Language :: Python",
        # ],
        author="node3112 (Iska)",
        author_email="node3112@protonmail.com",
        license="GPL-3.0",
        url="https://github.com/node3112/kirjava",
        packages=[
            "kirjava",
            "kirjava.abc",
            "kirjava.analysis",
            "kirjava.analysis.ir",
            "kirjava.classfile",
            "kirjava.classfile.attributes",
            "kirjava.classfile.instructions",
            "kirjava.jarfile",
            "kirjava.skeleton",
            "kirjava.skeleton.reconstruct",
            "kirjava.types",
            "kirjava.verifier",
        ],
        ext_modules=cythonize([
            "src/kirjava/abc/*.pyx",
            "src/kirjava/analysis/*.pyx",
            # "src/kirjava/analysis/ir/*.pyx",
            "src/kirjava/classfile/*.pyx",
            # "src/kirjava/classfile/attributes/*.pyx",
            # "src/kirjava/classfile/instructions/*.pyx",
            # "src/kirjava/jarfile/*.pyx",
            # "src/kirjava/skeleton/*.pyx",
            # "src/kirjava/skeleton/reconstruct/*.pyx",
            # "src/kirjava/types/*.pyx",
            # "src/kirjava/verifier/*.pyx",
        ], build_dir="build/"),
        package_dir={
            "": "src/",
        },
        data_files=[
            ("kirjava/skeleton/skeletons", [
                "src/kirjava/skeleton/skeletons/skeletons_j8.json",
                "src/kirjava/skeleton/skeletons/skeletons_j11.json",
                "src/kirjava/skeleton/skeletons/skeletons_j17.json",
                "src/kirjava/skeleton/skeletons/skeletons_j19.json",
            ]),
        ],
        requires=[
            "Cython",
        ],
        install_requires=[
            "frozendict",
        ],
    )

