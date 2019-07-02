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


import timeit
import datetime
import argparse

import pypiscout as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper
import emma_libs.memoryManager
import emma_libs.memoryMap


def main(args):
    sc.header("Preparing image summary", symbol=".")

    # Create MemoryManager instance with Variables for image summary
    sectionSummary = emma_libs.memoryManager.SectionParser(args)                            # String identifier for outfilenames

    # FIXME: Something before importData() takes quite a lot of processing time (MSc)
    numAnalyzedConfigIDs = sectionSummary.importData()                                      # Read Data

    if numAnalyzedConfigIDs >= 1:
        sectionSummary.resolveDuplicateContainmentOverlap()

        if not args.create_categories and not args.remove_unmatched:
            # Normal run; write csv report
            sectionSummary.writeSummary()
        else:
            # Categorisation-only run: do not write a csv report
            pass

    sc.header("Preparing module summary", symbol=".")

    objectSummary = emma_libs.memoryManager.ObjectParser(args)                              # String identifier for outfilenames

    # FIXME: Something before importData() takes quite a lot of processing time (MSc)
    numAnalyzedConfigIDs = objectSummary.importData()                                       # Read Data
    if numAnalyzedConfigIDs >= 1:
        objectSummary.resolveDuplicateContainmentOverlap()

        if args.create_categories:
            fileChanged = objectSummary.createCategoriesJson()                              # Create categories.json from keywords
            if fileChanged:
                objectSummary.importData()                                                  # Re-read Data
        elif args.remove_unmatched:
            objectSummary.removeUnmatchedFromCategoriesJson()
        else:
            objectSummary.writeSummary()

    sc.header("Preparing objects in sections summary", symbol=".")

    objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionSummary.consumerCollection, objectSummary.consumerCollection)
    emma_libs.memoryMap.memoryMapToCSV(args.dir, args.subdir, args.project, objectsInSections)


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

    if "" == arguments:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arguments)

    if args.dir is None:
        args.dir = args.project
    else:
        # Get paths straight (only forward slashes)
        args.dir = shared_libs.emma_helper.joinPath(args.dir)

    if args.subdir is not None:
        # Get paths straight (only forward slashes)
        args.subdir = shared_libs.emma_helper.joinPath(args.subdir)

    args.mapfiles = shared_libs.emma_helper.joinPath(args.mapfiles)

    return args


if __name__ == "__main__":
    args = parseArgs()

    sc.header("Emma Memory and Mapfile Analyser", symbol="/")

    timeStart = timeit.default_timer()
    sc.info("Started processing at", datetime.datetime.now().strftime("%H:%M:%S"))

    main(args)

    timeEnd = timeit.default_timer()
    sc.info("Finished job at:", datetime.datetime.now().strftime("%H:%M:%S"), "(duration: " "{0:.2f}".format(timeEnd - timeStart) + "s)")
