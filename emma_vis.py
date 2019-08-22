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

# Emma Memory and Mapfile Analyser - visualiser

import sys
import os
import timeit
import datetime
import argparse
import pandas

from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper
import emma_vis_libs.dataVisualiserSections
import emma_vis_libs.dataVisualiserObjects
import emma_vis_libs.dataVisualiserCategorisedSections
import emma_vis_libs.dataVisualiserMemoryMap
import emma_vis_libs.dataReports
import emma_vis_libs.helper


# Set display settings for unwrapped console output (pandas)
pandas.set_option('display.max_rows', 500)
pandas.set_option('display.max_columns', 500)
pandas.set_option('display.expand_frame_repr', False)


def main(args):
    imageFile = emma_vis_libs.helper.getLastModFileOrPrompt(FILE_IDENTIFIER_SECTION_SUMMARY, args.inOutPath, args.quiet, args.append, args.noprompt)
    moduleFile = emma_vis_libs.helper.getLastModFileOrPrompt(FILE_IDENTIFIER_OBJECT_SUMMARY, args.inOutPath, args.quiet, args.append, args.noprompt)
    objectsInSectionsFile = emma_vis_libs.helper.getLastModFileOrPrompt(FILE_IDENTIFIER_OBJECTS_IN_SECTIONS, args.inOutPath, args.quiet, args.append, args.noprompt)

    resultsPath = shared_libs.emma_helper.joinPath(args.inOutPath, OUTPUT_DIR_VISUALISER)        # We don't have to check the existance of this path since this was done during parseArgs
    shared_libs.emma_helper.mkDirIfNeeded(resultsPath)

    # Init classes for summaries
    consumptionObjectsInSections = emma_vis_libs.dataVisualiserMemoryMap.MemoryMap(projectPath=args.projectDir,
                                                                                   fileToUse=objectsInSectionsFile,
                                                                                   resultsPath=resultsPath)
    consumptionObjectsInSections.plotPieChart(plotShow=False)

    # Image Summary object
    sc().info("Analysing", imageFile)
    consumptionImage = emma_vis_libs.dataVisualiserSections.ImageConsumptionList(projectPath=args.projectDir,
                                                                                 fileToUse=imageFile,
                                                                                 resultsPath=resultsPath)

    # Module Summary object
    sc().info("Analysing", moduleFile)
    try:
        consumptionModule = emma_vis_libs.dataVisualiserObjects.ModuleConsumptionList(projectPath=args.projectDir,
                                                                                      fileToUse=moduleFile,
                                                                                      resultsPath=resultsPath)
    except ValueError:
        sc().error("Data does not contain any module/object entry - exiting...")

    # Object for visualisation fo image and module summary
    categorisedImage = emma_vis_libs.dataVisualiserCategorisedSections.CategorisedImageConsumptionList(resultsPath=resultsPath,
                                                                                                       projectPath=args.projectDir,
                                                                                                       statsTimestamp=consumptionImage.statsTimestamp,
                                                                                                       imageSumObj=consumptionImage,
                                                                                                       moduleSumObj=consumptionModule)

    # Do prints and plots
    consumptionImage.plotByMemType(plotShow=False)
    sc().info("\n", consumptionImage.calcConsumptionByMemType())

    # FIXME: Deactivated; colours of legend in figure not correct - possibly this figure is not even needed/useful (MSc)
    # categorisedImage.plotNdisplay(plotShow=False)

    # Save the categorised sections as csv
    if args.categorised_image_csv:
        categorisedImage.categorisedImagetoCSV()

    # Write each report to file if append mode in args is selected
    if args.append:
        sc().info("Appending reports...")
        consumptionImage.writeReportToFile()
        report = emma_vis_libs.dataReports.Reports(projectPath=args.projectDir)
        report.plotNdisplay(plotShow=False)

    # Create a Markdown overview document and add all parts to it
    elif args.overview:
        markdownFilePath = consumptionImage.createMarkdownOverview()
        consumptionModule.appendModuleConsumptionToMarkdownOverview(markdownFilePath)
        consumptionImage.appendSupplementToMarkdownOverview(markdownFilePath)
        shared_libs.emma_helper.convertMarkdownFileToHtmlFile(markdownFilePath, (os.path.splitext(markdownFilePath)[0] + ".html"))


def parseArgs(arguments=""):
    """
    Argument parser
    :param arguments: List of strings specifying the arguments to be parsed
    :return: Argparse object
    """

    parser = argparse.ArgumentParser(
        prog="Emma Visualiser",
        description="Data aggregation and visualisation tool for Emma Memory and Mapfile Analyser (Emma).",
        epilog=EPILOG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--version",
        help="Display the version number.",
        action="version",
        version="%(prog)s, Version: " + EMMA_VISUALISER_VERSION
    )
    parser.add_argument(
        "--projectDir",
        "-p",
        required=True,
        help="Path to directory holding the config files. The project name will be derived from this folder name,",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        help="Automatically accepts last modified .csv file in ./memStats folder",
        action="store_true"
    )
    parser.add_argument(
        "--append",
        help="Append reports to file in ./results folder",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--inOutDir",
        "-i",
        help="Path containing the memStats directory (-> Emma output). If not given the `project` directory will be used.",
        default=None
    )
    parser.add_argument(
        "--subDir",
        help="Sub-directory of `inOutDir` where the Emma Visualiser results will be stored. If not given results will be stored in `inOutDir`.",
        default=None
    )
    parser.add_argument(
        "--overview",
        help="Create a .html overview.",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--categorised_image_csv",
        "-cat_img",
        help="Save a .csv of categories found inside the image summary",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--noprompt",
        help="Exit program with an error if a user prompt occurs; useful for CI systems",
        action="store_true",
        default=False
    )

    # We will either parse the arguments string if it is not empty,
    # or (in the default case) the data from sys.argv
    if "" == arguments:
        parsedArguments = parser.parse_args()
    else:
        # Arguments were passed to this function (e.g. for unit testing)
        parsedArguments = parser.parse_args(arguments)

    # Prepare final paths
    parsedArguments.inOutPath = ""

    # Check given paths
    if parsedArguments.projectDir is None:                  # This should not happen since it is a required argument
        sc().error("No project path given. Exiting...")
    else:
        parsedArguments.projectDir = shared_libs.emma_helper.joinPath(parsedArguments.projectDir)           # Unify path
        shared_libs.emma_helper.checkIfFolderExists(parsedArguments.projectDir)

        parsedArguments.inOutPath = parsedArguments.projectDir
    if parsedArguments.inOutDir is None:
        parsedArguments.inOutDir = parsedArguments.projectDir
    else:
        parsedArguments.inOutDir = shared_libs.emma_helper.joinPath(parsedArguments.inOutDir)               # Unify path
        shared_libs.emma_helper.checkIfFolderExists(parsedArguments.inOutDir)

        parsedArguments.inOutPath = parsedArguments.inOutDir
        if parsedArguments.subDir is None:
            parsedArguments.subDir = ""
        else:
            parsedArguments.subDir = shared_libs.emma_helper.joinPath(parsedArguments.subDir)               # Unify path

            joinedInputPath = shared_libs.emma_helper.joinPath(parsedArguments.inOutDir, parsedArguments.subDir)
            shared_libs.emma_helper.checkIfFolderExists(joinedInputPath)
            parsedArguments.inOutPath = joinedInputPath

    # Clean-up paths
    del parsedArguments.subDir
    del parsedArguments.inOutDir

    return parsedArguments


if __name__ == "__main__":
    parsedArguments = parseArgs()
    sc(invVerbosity=-1, actionWarning=(lambda : sys.exit(-10) if parsedArguments.Werror is not None else None), actionError=lambda : sys.exit(-10))

    sc().header("Emma Memory and Mapfile Analyser - Visualiser", symbol="/")

    timeStart = timeit.default_timer()
    sc().info("Started processing at:", datetime.datetime.now().strftime("%H:%M:%S"))

    main(parsedArguments)

    timeEnd = timeit.default_timer()
    sc().info("Finished job at:", datetime.datetime.now().strftime("%H:%M:%S"), "(duration: " + "{0:.2f}".format(timeEnd - timeStart) + "s)")
