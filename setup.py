"""
Emma - Emma Memory and Mapfile Analyser
Copyright (C) 2019 The Emma authors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

# Emma Memory and Mapfile Analyser - setup file


import setuptools
import Emma

with open("README.md", "r") as fp:
    long_description = fp.read()

setuptools.setup(
    name="pypiemma",
    version=Emma.EMMA_VERSION,
    license="GPLv3+",
    description="Emma Memory and Mapfile Analyser (Emma) | Conduct static (i.e. worst case) memory consumption \
    analyses based on arbitrary linker map files. It produces extensive .csv files which are easy to filter and \
    post-process. Optionally .html and markdown reports as well as neat figures help you visualising your results.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    maintainer="The Emma Authors",
    maintainer_email="emma-dev@googlegroups.com",
    url="https://github.com/bmwcarit/Emma",
    packages=setuptools.find_namespace_packages(),                  # Recursively find package files (i.e. sub-folders, ...)
    python_requires=Emma.PYTHON_REQ_VERSION,
    install_requires=["Pygments",
                      "Markdown",
                      "matplotlib",
                      "pandas",
                      "pypiscout>=2.0",
                      "graphviz"
                      ],
    extras_require={"dev":                                      # Install dev version via `pip3 install pypiemma[dev]`
                        ["gprof2dot",
                         "pylint",
                         "mkdocs",
                         "mkdocs-material"
                         ],
                    },
    entry_points={                                              # Make Emma available as independent scripts
        "console_scripts": [
            "emma=Emma.emma:runEmma",
            "emma_vis=Emma.emma_vis:runEmmaVis",
            "emma_deltas=Emma.emma_vis:runEmmaDeltas"
        ],
    },
    keywords=[
        "memory-analysis",
        "mapfile",
        "memory-analyzer",
        "embedded",
        "ghs",
        "gcc",
        "mcu",
        "linker",
        "visualization",
        "reports",
        "csv",
        "python",
        "categorisation",
        "memory-consumption",
        "mapfile-analyser"
        ],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Quality Assurance",
    ],
)
