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
from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper
import emma_delta_libs.Delta
import emma_delta_libs.FilePresenter
import emma_delta_libs.FileSelector
import emma_delta_libs.RootSelector


def initParser():
    """
    Prepare the parser for Emma
    We need this as a separate function for the top level sub commands (argparse).
    :return: Set-up parser
    """
    # Argument parser
    parser = argparse.ArgumentParser(
        prog="Emma Delta Analyser",
        description="Analyses differences between analyses",
        epilog=EPILOG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--version",
        help="Display the version number.",
        action="version",
        version="%(prog)s, Version: " + EMMA_DELTAS_VERSION
    )
    parser.add_argument(
        "--infiles",
        "-i",
        nargs=2,
        help="Files to compare",
        default=None
    )
    parser.add_argument(
        "--project",
        "-p",
        help="Project root folder for deltas.",
        default=None
    )
    parser.add_argument(
        "--outfile",
        "-o",
        help="Outfile.",
        default="",
    )
    parser.add_argument(
        "-r",
        help="Skips the prompt for root path of the analyses.",
        action="store_true"
    )
    return parser


def parseArgs(arguments=""):
    """
    Argument parser
    :param arguments: List of strings specifying the arguments to be parsed (default: "" (-> meaning that arguments from the command line should be parsed)
    :return: Argparse object
    """
    parser = initParser()
    parsedArguments = shared_libs.emma_helper.parseGivenArgStrOrStdIn(arguments, parser)
    return parsedArguments


def main(arguments):
    """
    Emma deltas application
    :param arguments: parsed arguments
    :return: None
    """
    # Setup SCout
    sc(invVerbosity=-1, actionWarning=(lambda : sys.exit(-10) if arguments.Werror is not None else None), actionError=lambda : sys.exit(-10))

    sc().header("Emma Memory and Mapfile Analyser - Deltas", symbol="/")

    # Start and display time measurement
    TIME_START = timeit.default_timer()
    sc().info("Started processing at", datetime.datetime.now().strftime("%H:%M:%S"))

    if arguments.infiles and arguments.outfile is not None:
        candidates = arguments.infiles
    elif arguments.project:
        shared_libs.emma_helper.checkIfFolderExists(arguments.project)
        fileSelector = emma_delta_libs.FileSelector.FileSelector(projectDir=arguments.project)
        filePresenter = emma_delta_libs.FilePresenter.FilePresenter(fileSelector=fileSelector)
        candidates = filePresenter.chooseCandidates()
    elif not arguments.r:
        rootpath = emma_delta_libs.RootSelector.selectRoot()
        emma_delta_libs.RootSelector.saveNewRootpath(rootpath)
        fileSelector = emma_delta_libs.FileSelector.FileSelector(projectDir=rootpath)
        filePresenter = emma_delta_libs.FilePresenter.FilePresenter(fileSelector=fileSelector)
        candidates = filePresenter.chooseCandidates()
    else:
        sc().error("No matching arguments.")

    delta = emma_delta_libs.Delta.Delta(files=candidates, outfile=arguments.outfile)
    delta.tocsv()
    sc().info("Saved delta to " + arguments.outfile)

    # Stop and display time measurement
    TIME_END = timeit.default_timer()
    sc().info("Finished job at:", datetime.datetime.now().strftime("%H:%M:%S"), "(duration: " + "{0:.2f}".format(TIME_END - TIME_START) + "s)")


def runEmmaDeltas():
    """
    Runs Emma Deltas application
    :return: None
    """
    # Parsing the command line arguments
    parsedArguments = parseArgs()

    # Execute Emma Deltas
    main(parsedArguments)


if __name__ == "__main__":
    runEmmaDeltas()
