#!/usr/bin/env python

from setuptools import setup


if __name__ == "__main__":
    setup(
        name="kirjava",
        version="0.1.5",
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
        package_data={
            "kirjava.skeleton.skeletons": ["*.json"],
        },
        include_package_data=True,
        # data_files=[  # FIXME
        #     ("kirjava/skeleton/skeletons", [
        #         "src/kirjava/skeleton/skeletons/skeletons_j8.json",
        #         "src/kirjava/skeleton/skeletons/skeletons_j11.json",
        #         "src/kirjava/skeleton/skeletons/skeletons_j17.json",
        #         "src/kirjava/skeleton/skeletons/skeletons_j19.json",
        #     ]),
        # ],
    )
