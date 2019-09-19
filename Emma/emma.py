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
import timeit
import datetime
import argparse

from pypiscout.SCout_Logger import Logger as sc

import Emma
from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.shared_libs.emma_helper
import Emma.emma_libs.memoryManager


def main(arguments):
    """
    Emma application
    :param arguments: parsed arguments
    :return: None
    """
    # Setup SCout
    sc(invVerbosity=-1, actionWarning=(lambda: sys.exit(-10) if arguments.Werror is not None else None), actionError=lambda: sys.exit(-10))

    sc().header("Emma Memory and Mapfile Analyser", symbol="/")

    # Start and display time measurement
    TIME_START = timeit.default_timer()
    sc().info("Started processing at", datetime.datetime.now().strftime("%H:%M:%S"))

    memoryManager = Emma.emma_libs.memoryManager.MemoryManager(*processArguments(arguments))
    memoryManager.readConfiguration()
    memoryManager.processMapfiles()
    memoryManager.createReports()

    # Stop and display time measurement
    TIME_END = timeit.default_timer()
    sc().info("Finished job at:", datetime.datetime.now().strftime("%H:%M:%S"), "(duration: " "{0:.2f}".format(TIME_END - TIME_START) + "s)")


def initParser():
    """
    Prepare the parser for Emma
    We need this as a separate function for the top level sub commands (argparse).
    :return: Set-up parser
    """
    parser = argparse.ArgumentParser(
        prog="Emma Memory and Mapfile Analyser (Emma)",
        description="Analyser for map files from Greens Hills Linker (other files are supported via configuration options)."
                    "It creates a summary/overview about static memory usage in form of a csv file.",
        epilog=EPILOG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--version",
        help="Display the version number.",
        action="version",
        version="%(prog)s, Version: " + Emma.EMMA_VERSION
    )
    parser.add_argument(
        "--verbosity",
        "-v",
        action='count',
        default=0,
        help="Adjust verbosity of console output. DECREASE verbosity by adding more `v`s"
    )
    parser.add_argument(
        "--project",
        "-p",
        required=True,
        help="Path of directory holding the configuration."
             "The project name will be derived from the the name of this folder.",
    )
    parser.add_argument(
        "--mapfiles",
        required=True,
        help="The folder containing the map files that need to be analysed.",
    )
    parser.add_argument(
        "--dir",
        help="Output folder holding the statistics.",
        default=None
    )
    parser.add_argument(
        "--subdir",
        help="User defined subdirectory name in the --dir folder.",
        default=None
    )
    parser.add_argument(
        "--analyse_debug",
        help="Include DWARF debug sections in analysis",
        default=False,
        action="store_true"
    )
    parser.add_argument(        # TODO: Create Categories only (FM)
        "--create_categories",
        help="Create categories.json from keywords.",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "--remove_unmatched",
        help="Remove unmatched modules from categories.json.",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "--noprompt",
        help="Exit program with an error if a user prompt occurs; useful for CI systems",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--Werror",
        help="Treat all warnings as errors.",
        action="store_true",
        default=False
    )
    return parser


def parseArgs(arguments=""):
    """
    Parse command line arguments
    :param arguments: Optional arguments when nothing gets parsed
    :return: Parsed arguments
    """
    parser = initParser()
    parsedArguments = Emma.shared_libs.emma_helper.parseGivenArgStrOrStdIn(arguments, parser)
    return parsedArguments


def processArguments(arguments):
    """
    Function to extract the settings values from the command line arguments.
    :param arguments: The command line arguments, that is the result of the parser.parse_args().
    :return: The setting values.
    """
    projectName = Emma.shared_libs.emma_helper.projectNameFromPath(Emma.shared_libs.emma_helper.joinPath(arguments.project))
    configurationPath = Emma.shared_libs.emma_helper.joinPath(arguments.project)
    mapfilesPath = Emma.shared_libs.emma_helper.joinPath(arguments.mapfiles)

    # If an output directory was not specified then the result will be stored to the project folder
    if arguments.dir is None:
        directory = arguments.project
    else:
        # Get paths straight (only forward slashes)
        directory = Emma.shared_libs.emma_helper.joinPath(arguments.dir)
    # Get paths straight (only forward slashes) or set it to empty if it was empty
    subDir = Emma.shared_libs.emma_helper.joinPath(arguments.subdir) if arguments.subdir is not None else ""

    outputPath = Emma.shared_libs.emma_helper.joinPath(directory, subDir, OUTPUT_DIR)
    analyseDebug = arguments.analyse_debug
    createCategories = arguments.create_categories
    removeUnmatched = arguments.remove_unmatched
    noPrompt = arguments.noprompt

    return projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt


def runEmma():
    """
    Runs Emma application
    :return: None
    """
    # Parsing the command line arguments
    parsedArguments = parseArgs()

    # Execute Emma
    main(parsedArguments)


if __name__ == "__main__":
    runEmma()
