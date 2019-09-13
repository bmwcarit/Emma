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
import Emma.emma_delta_libs.Delta
import Emma.emma_delta_libs.FilePresenter
import Emma.emma_delta_libs.FileSelector
import Emma.emma_delta_libs.RootSelector


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
        version="%(prog)s, Version: " + Emma.EMMA_DELTAS_VERSION
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

    # We will either parse the arguments string if it is not empty,
    # or (in the default case) the data from sys.argv
    if "" == arguments:
        parsedArguments = parser.parse_args()
    else:
        # Arguments were passed to this function (e.g. for unit testing)
        parsedArguments = parser.parse_args(arguments)

    return parsedArguments


def main(args):
    if args.infiles and args.outfile is not None:
        candidates = args.infiles
    elif args.project:
        Emma.shared_libs.emma_helper.checkIfFolderExists(args.project)
        fileSelector = Emma.emma_delta_libs.FileSelector.FileSelector(projectDir=args.project)
        filePresenter = Emma.emma_delta_libs.FilePresenter.FilePresenter(fileSelector=fileSelector)
        candidates = filePresenter.chooseCandidates()
    elif not args.r:
        rootpath = Emma.emma_delta_libs.RootSelector.selectRoot()
        Emma.emma_delta_libs.RootSelector.saveNewRootpath(rootpath)
        fileSelector = Emma.emma_delta_libs.FileSelector.FileSelector(projectDir=rootpath)
        filePresenter = Emma.emma_delta_libs.FilePresenter.FilePresenter(fileSelector=fileSelector)
        candidates = filePresenter.chooseCandidates()
    else:
        sc().error("No matching arguments.")

    delta = Emma.emma_delta_libs.Delta.Delta(files=candidates, outfile=args.outfile)
    delta.tocsv()
    sc().info("Saved delta to " + args.outfile)


def runEmmaDeltas():
    """
    Runs Emma Deltas application
    :return: None
    """
    # Parsing the command line arguments
    ARGS = parseArgs()

    # Setup SCout
    sc(invVerbosity=-1, actionWarning=(lambda : sys.exit(-10) if ARGS.Werror is not None else None), actionError=lambda : sys.exit(-10))

    sc().header("Emma Memory and Mapfile Analyser - Deltas", symbol="/")

    # Start and display time measurement
    TIME_START = timeit.default_timer()
    sc().info("Started processing at", datetime.datetime.now().strftime("%H:%M:%S"))

    # Execute Emma Deltas
    main(ARGS)

    # Stop and display time measurement
    TIME_END = timeit.default_timer()
    sc().info("Finished job at:", datetime.datetime.now().strftime("%H:%M:%S"), "(duration: " + "{0:.2f}".format(TIME_END - TIME_START) + "s)")


if __name__ == "__main__":
    runEmmaDeltas()
