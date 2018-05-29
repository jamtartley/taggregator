import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tag_finder",
    version="0.0.1",
    author="Sam Hartley",
    author_email="sam@deadcentaur.com",
    description="Find lines of source code you have tagged with custom categories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jamtartley/tag_finder",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
