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

import gc
import sys
import os
import timeit
import datetime
import argparse
import pandas

from pypiscout.SCout_Logger import Logger as sc

import Emma
from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.shared_libs.emma_helper
import Emma.emma_vis_libs.dataVisualiserSections
import Emma.emma_vis_libs.dataVisualiserObjects
import Emma.emma_vis_libs.dataVisualiserCategorisedSections
import Emma.emma_vis_libs.dataVisualiserMemoryMap
import Emma.emma_vis_libs.dataReports
import Emma.emma_vis_libs.helper


# Set display settings for unwrapped console output (pandas)
pandas.set_option('display.max_rows', 500)
pandas.set_option('display.max_columns', 500)
pandas.set_option('display.expand_frame_repr', False)


def initParser():
    """
    Prepare the parser for Emma
    We need this as a separate function for the top level sub commands (argparse).
    :return: Set-up parser
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
        version="%(prog)s, Version: " + Emma.EMMA_VISUALISER_VERSION
    )
    parser.add_argument(
        "--verbosity",
        "-v",
        default=0,
        help="Adjust verbosity of console output. DECREASE verbosity by adding more `v`s"
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
        "--Werror",
        help="Treat all warnings as errors.",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--noprompt",
        help="Exit program with an error if a user prompt occurs; useful for CI systems",
        action="store_true",
        default=False
    )
    return parser


def parseArgs(arguments=""):
    """
    Argument parser
    :param arguments: List of strings specifying the arguments to be parsed
    :return: Argparse object
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
    # Prepare final paths
    arguments.inOutPath = ""

    # Check given paths
    if arguments.projectDir is None:                  # This should not happen since it is a required argument
        sc().error("No project path given. Exiting...")
    else:
        arguments.projectDir = Emma.shared_libs.emma_helper.joinPath(arguments.projectDir)           # Unify path
        Emma.shared_libs.emma_helper.checkIfFolderExists(arguments.projectDir)

        arguments.inOutPath = arguments.projectDir
    if arguments.inOutDir is None:
        arguments.inOutDir = arguments.projectDir
    else:
        arguments.inOutDir = Emma.shared_libs.emma_helper.joinPath(arguments.inOutDir)               # Unify path
        Emma.shared_libs.emma_helper.checkIfFolderExists(arguments.inOutDir)

        arguments.inOutPath = arguments.inOutDir
        if arguments.subDir is None:
            arguments.subDir = ""
        else:
            arguments.subDir = Emma.shared_libs.emma_helper.joinPath(arguments.subDir)               # Unify path

            joinedInputPath = Emma.shared_libs.emma_helper.joinPath(arguments.inOutDir, arguments.subDir)
            Emma.shared_libs.emma_helper.checkIfFolderExists(joinedInputPath)
            arguments.inOutPath = joinedInputPath

    # Clean-up paths
    del arguments.subDir
    del arguments.inOutDir

    return arguments.verbosity, arguments.inOutPath, arguments.quiet, arguments.append, arguments.noprompt, arguments.projectDir, arguments.categorised_image_csv, arguments.overview, arguments.Werror


def main(arguments):
    """
    Emma visualiser application
    :param arguments: parsed arguments
    :return: None
    """
    verbosity, inOutPath, quiet, append, noprompt, projectDir, categorised_image_csv, overview, Werror = processArguments(arguments)

    # Setup SCout
    sc(invVerbosity=verbosity, actionWarning=(lambda: sys.exit(-10) if Werror is not None else None), actionError=lambda: sys.exit(-10))

    sc().header("Emma Memory and Mapfile Analyser - Visualiser", symbol="/")

    # Start and display time measurement
    TIME_START = timeit.default_timer()
    sc().info("Started processing at", datetime.datetime.now().strftime("%H:%M:%S"))

    imageFile = Emma.emma_vis_libs.helper.getLastModFileOrPrompt(FILE_IDENTIFIER_SECTION_SUMMARY, inOutPath, quiet, append, noprompt)
    moduleFile = Emma.emma_vis_libs.helper.getLastModFileOrPrompt(FILE_IDENTIFIER_OBJECT_SUMMARY, inOutPath, quiet, append, noprompt)
    objectsInSectionsFile = Emma.emma_vis_libs.helper.getLastModFileOrPrompt(FILE_IDENTIFIER_OBJECTS_IN_SECTIONS, inOutPath, quiet, append, noprompt)

    resultsPath = Emma.shared_libs.emma_helper.joinPath(inOutPath, OUTPUT_DIR_VISUALISER)        # We don't have to check the existance of this path since this was done during parseArgs

    Emma.shared_libs.emma_helper.mkDirIfNeeded(resultsPath)

    # Init classes for summaries
    consumptionObjectsInSections = Emma.emma_vis_libs.dataVisualiserMemoryMap.MemoryMap(projectPath=projectDir, fileToUse=objectsInSectionsFile, resultsPath=resultsPath)
    consumptionObjectsInSections.plotPieChart(plotShow=False)

    # Image Summary object
    sc().info("Analysing", imageFile)
    consumptionImage = Emma.emma_vis_libs.dataVisualiserSections.ImageConsumptionList(projectPath=projectDir, fileToUse=imageFile, resultsPath=resultsPath)

    # Module Summary object
    sc().info("Analysing", moduleFile)
    try:
        consumptionModule = Emma.emma_vis_libs.dataVisualiserObjects.ModuleConsumptionList(projectPath=projectDir, fileToUse=moduleFile, resultsPath=resultsPath)
    except ValueError:
        sc().error("Data does not contain any module/object entry - exiting...")

    # Object for visualisation fo image and module summary
    categorisedImage = Emma.emma_vis_libs.dataVisualiserCategorisedSections.CategorisedImageConsumptionList(resultsPath=resultsPath, projectPath=projectDir, statsTimestamp=consumptionImage.statsTimestamp, imageSumObj=consumptionImage, moduleSumObj=consumptionModule)

    # Do prints and plots
    consumptionImage.plotByMemType(plotShow=False)

    # Prevent out of memory errors (-> `AssertionError: Unexpected exception: In RendererAgg: Out of memory`)
    gc.collect()

    sc().info("\n", consumptionImage.calcConsumptionByMemType())

    # FIXME: Deactivated; colours of legend in figure not correct - possibly this figure is not even needed/useful (MSc)
    # categorisedImage.plotNdisplay(plotShow=False)

    # Save the categorised sections as csv
    if categorised_image_csv:
        categorisedImage.categorisedImagetoCSV()

    # Write each report to file if append mode in parsedArguments is selected
    if append:
        sc().info("Appending report...")
        consumptionImage.writeReportToFile()
        report = Emma.emma_vis_libs.dataReports.Reports(projectPath=projectDir)
        report.plotNdisplay(plotShow=False)

    # Create a Markdown overview document and add all parts to it
    if overview:
        sc().info("Generating markdown report...")
        markdownFilePath = consumptionImage.createMarkdownOverview()
        consumptionModule.appendModuleConsumptionToMarkdownOverview(markdownFilePath)
        consumptionImage.appendSupplementToMarkdownOverview(markdownFilePath)
        sc().info("Generating html report...")
        Emma.shared_libs.emma_helper.convertMarkdownFileToHtmlFile(markdownFilePath, (os.path.splitext(markdownFilePath)[0] + ".html"))

    # Stop and display time measurement
    TIME_END = timeit.default_timer()
    sc().info("Finished job at:", datetime.datetime.now().strftime("%H:%M:%S"), "(duration: " + "{0:.2f}".format(TIME_END - TIME_START) + "s)")


def runEmmaVis():
    """
    Runs Emma Visualiser application
    :return: None
    """
    # Parsing the command line arguments
    parsedArguments = parseArgs()

    # Execute Emma Visualiser
    main(parsedArguments)


if __name__ == "__main__":
    runEmmaVis()
