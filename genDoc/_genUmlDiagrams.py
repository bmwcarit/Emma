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


import os
import argparse
import subprocess

import pypiscout as sc
import gprof2dot           # Not directly used; later we do a sys-call wich needs the library

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import


list_of_source_file_paths = [           # "../../*" instead of "../*" since we change the working directory within the system call
    "../../emma_libs/mapfileRegexes.py",
    "../../emma_libs/memoryEntry.py",
    "../../emma_libs/memoryManager.py",
    "../../emma_libs/memoryMap.py",
    "../../emma_delta_libs/Delta.py",
    "../../emma_delta_libs/FilePresenter.py",
    "../../emma_delta_libs/FileSelector.py",
    "../../emma_delta_libs/RootSelector.py",
    "../../emma_vis_libs/dataReports.py",
    "../../emma_vis_libs/dataVisualiser.py",
    "../../emma_vis_libs/dataVisualiserCategorisedSections.py",
    "../../emma_vis_libs/dataVisualiserMemoryMap.py",
    "../../emma_vis_libs/dataVisualiserObjects.py",
    "../../emma_vis_libs/dataVisualiserSections.py",
    "../../shared_libs/emma_helper.py",
    "../../emma.py",
    "../../emma_deltas.py",
    "../../emma_vis.py"
]


def ParseArguments():
    """
    Argument parser
    :return: argparse object containing the parsed options
    """
    parser = argparse.ArgumentParser(
        prog="Emma - Call graph generator",
        description="Script to generate call graphs that can be used in the documentation or to examine the run of Emma and the Emma visualiser.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--graphviz_bin_folder",
        help=r"The bin subfolder of the Graphviz software. Example: c:\Program Files (x86)\Graphviz2.38\bin",
        required=True
    )
    parser.add_argument(
        "--verbose",
        help="Prints out more info during run.",
        default=False
    )
    return parser.parse_args()


def main(arguments):
    sc.info("Generating UML Class diagrams from the source files...")
    for source_file_path in list_of_source_file_paths:
        source_file_name = os.path.splitext(os.path.basename(source_file_path))[0]
        subprocess.run("pyreverse -AS -o " + README_PICTURE_FORMAT + " " + source_file_path + " -p " + source_file_name, cwd=README_CALL_GRAPH_AND_UML_FOLDER_NAME, shell=True)
        # Note that pyreverse must be called via subprocess (do NOT import it as a module)
        # The main reason are licencing issues (GPLv2 is incompatible with GPLv3) (https://softwareengineering.stackexchange.com/questions/110380/call-gpl-software-from-non-gpl-software)
        # See also: https://github.com/TeamFlowerPower/kb/wiki/callGraphsUMLdiagrams


if __name__ == "__main__":
    commandLineArguments = ParseArguments()
    if not os.path.isdir(README_CALL_GRAPH_AND_UML_FOLDER_NAME):
        sc.info("The folder \"" + README_CALL_GRAPH_AND_UML_FOLDER_NAME + "\" was created because it did not exist...")
        os.makedirs(README_CALL_GRAPH_AND_UML_FOLDER_NAME)
    main(commandLineArguments)
