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

from shared_libs.stringConstants import *
import shared_libs.emma_helper
import emma_libs.memoryManager


def main(args):
    memoryManager = emma_libs.memoryManager.MemoryManager(*processArguments(args))
    memoryManager.readConfiguration()
    memoryManager.processMapfiles()
    memoryManager.createReports()


def parseArgs(arguments=""):
    """
    Parse command line arguments
    :param arguments: Optional arguments when nothing gets parsed
    :return: Parsed arguments
    """

    parser = argparse.ArgumentParser(
        prog="Emma Memory and Mapfile Analyser (Emma)",
        description="Analyser for mapfiles from Greens Hills Linker (other files are supported via configuration options)."
                    "It creates a summary/overview about static memory usage in form of a comma separated values file.",
        epilog=EPILOG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--version",
        help="Display the version number.",
        action="version",
        version="%(prog)s, Version: " + EMMA_VERSION
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
        help="The folder containing the mapfiles that needs to be analyzed.",
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
    # parser.add_argument(      # TODO: Currently not implemented (useful?) (MSc)
    #     "--verbose",
    #     "-v",
    #     help="Generate verbose output",
    #     action="count"        # See: https://docs.python.org/3/library/argparse.html#action
    # )
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
        "-Werror",
        help="Treat all warnings as errors.",
        action="store_true",
        default=False
    )

    # We will either parse the arguments string if it is not empty,
    # or in the default case the data from sys.argv
    if "" == arguments:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arguments)

    return args


def processArguments(args):
    projectName = shared_libs.emma_helper.projectNameFromPath(shared_libs.emma_helper.joinPath(args.project))
    configurationPath = shared_libs.emma_helper.joinPath(args.project)
    mapfilesPath = shared_libs.emma_helper.joinPath(args.mapfiles)

    # If an output directory was not specified then the result will be stored to the project folder
    if args.dir is None:
        directory = args.project
    else:
        # Get paths straight (only forward slashes)
        directory = shared_libs.emma_helper.joinPath(args.dir)
    # Get paths straight (only forward slashes) or set it to empty if it was empty
    subDir = shared_libs.emma_helper.joinPath(args.subdir) if args.subdir is not None else ""

    outputPath = shared_libs.emma_helper.joinPath(directory, subDir, OUTPUT_DIR)
    analyseDebug = args.analyse_debug
    create_categories = args.create_categories
    remove_unmatched = args.remove_unmatched
    noprompt = args.noprompt

    return projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, create_categories, remove_unmatched, noprompt


if __name__ == "__main__":
    # Parsing the arguments
    args = parseArgs()

    def exitProgram():
        sys.exit(-10)

    actionWarning = exitProgram if args.Werror is not None else None
    actionError = exitProgram
    sc(-1, actionWarning=actionWarning, actionError=actionError)

    sc().header("Emma Memory and Mapfile Analyser", symbol="/")

    # Starting the time measurement of Emma
    timeStart = timeit.default_timer()
    sc().info("Started processing at", datetime.datetime.now().strftime("%H:%M:%S"))

    # Executing Emma
    main(args)

    # Stopping the time measurement of Emma
    timeEnd = timeit.default_timer()
    sc().info("Finished job at:", datetime.datetime.now().strftime("%H:%M:%S"), "(duration: " "{0:.2f}".format(timeEnd - timeStart) + "s)")
