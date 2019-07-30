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


import sys
import os
import argparse

from pypiscout.SCout_Logger import Logger as sc
import gprof2dot    # pylint: disable=unused-import
                    # Rationale: Not directly used, but later we do a sys-call wich needs the library. This is needed to inform the user to install the package.

sys.path.append("../")
# pylint: disable=wrong-import-position
# Rationale: This module needs to access modules that are above them in the folder structure.

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import, wildcard-import
import shared_libs.emma_helper
import genDoc._genCallGraphs
import genDoc._genUmlDiagrams


def ParseArguments():
    """
    Argument parser
    :return: argparse object containing the parsed options
    """
    parser = argparse.ArgumentParser(
        prog="Emma - Call graph generator",
        description="Script to generate call graphs that can be used in the documentation or to examine the run of Emma and the Emma Visualiser.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--graphviz_bin_folder",
        help=r"The bin subfolder of the Graphviz software. Example: c:\Program Files (x86)\Graphviz2.38\bin",
        required=False
    )
    parser.add_argument(
        "--verbose",
        help="Prints out more info during run.",
        default=False
    )
    parser.add_argument(
        "--no_graphs",
        help="Do not update graphs (UML + call graph)",
        action="store_true",
        default=False
    )
    return parser.parse_args()


def main(arguments):
    """
    Main function.
    :param arguments: Processed command line arguments.
    :return: None
    """
    def exitProgram():
        sys.exit(-10)

    sc(-1, exitProgram, exitProgram)
    sc().header("Generating the Readme documents", symbol="/")

    # Give a hint on python sys-call
    sc().info("A `python` system call is going to happen. If any errors occur please check the following first:")
    if sys.platform == "win32":
        sc().info("Windows OS detected. Make sure `python` refers to the Python3 version targeted for this application (-> dependencies; e.g. WSL comes with its own Python).")
    else:
        sc().info("Make sure `python` refers to a Python 3 installation.")

    # Store original path variables
    pathOldValue = os.environ["PATH"]
    if not("Graphviz" in os.environ["PATH"] or "graphviz" in os.environ["PATH"]):
        if arguments.graphviz_bin_folder is not None:
            graphvizBinAbspath = os.path.abspath(arguments.graphviz_bin_folder)
            # Add to path
            os.environ["PATH"] += (graphvizBinAbspath + ";")
        else:
            sc().error("The \"graphviz_bin_folder\" was not found in PATH nor was given in the argument --graphviz_bin_folder")

    try:
        if not os.path.isdir(README_CALL_GRAPH_AND_UML_FOLDER_NAME):
            sc.info("The folder \"" + README_CALL_GRAPH_AND_UML_FOLDER_NAME + "\" was created because it did not exist...")
            os.makedirs(README_CALL_GRAPH_AND_UML_FOLDER_NAME)

        if not arguments.no_graphs:
            # pylint: disable=protected-access
            # Rationale: These modules are private so that the users will not use them directly. They are meant to be used trough this script.
            genDoc._genCallGraphs.main(arguments)
            genDoc._genUmlDiagrams.main()

        print("")
        sc().info("Storing Emma readme as a .html file...")
        markdownFilePath = r"../doc/readme.md"
        shared_libs.emma_helper.convertMarkdownFileToHtmlFile(markdownFilePath, (os.path.splitext(markdownFilePath)[0] + ".html"))
        sc().info("Done.")

        print("")
        sc().info("Storing Emma Visualiser readme as a .html file...")
        markdownFilePath = r"../doc/readme-vis.md"
        shared_libs.emma_helper.convertMarkdownFileToHtmlFile(markdownFilePath, (os.path.splitext(markdownFilePath)[0] + ".html"))
        sc().info("Done.")

        print("")
        sc().info("Storing the test_project readme as a .html file...")
        markdownFilePath = r"../doc/test_project/readme/readme.md"
        shared_libs.emma_helper.convertMarkdownFileToHtmlFile(markdownFilePath, (os.path.splitext(markdownFilePath)[0] + ".html"))
        sc().info("Done.")

        print("")
        sc().info("Storing the top level README as a .html file...")
        # Change the working directory; otherwise we get errors about the relative image import paths in emma_helper.changePictureLinksToEmbeddingInHtmlData()
        os.chdir("..")
        markdownFilePath = r"README.md"
        shared_libs.emma_helper.convertMarkdownFileToHtmlFile(markdownFilePath, (os.path.splitext(markdownFilePath)[0] + ".html"))
        sc().info("Done.")
        os.chdir("doc")     # Change working directory back

    except Exception as e:
        sc().error("An exception was caught:", e)

    # Get back initial path config
    os.environ["PATH"] = pathOldValue


if __name__ == "__main__":
    args = ParseArguments()
    main(args)
