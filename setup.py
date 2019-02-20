#! /usr/bin/env python3
#! -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="taggregator",
    version="0.0.44",
    author="Sam Hartley",
    author_email="sam@jamtartley.com",
    description="Find lines of source code you have tagged with custom categories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jamtartley/taggregator",
    python_requires=">=3",
    include_package_data=True,
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "tagg = taggregator.__main__:main"
        ]
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
