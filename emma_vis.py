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

import pypiscout as sc

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import                           # pylint: disable=unused-wildcard-import
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
    # Evaluate files and directories and make directories if necessary
    projectPath = args.project

    # Check project path before results path (=dir); this is our results path default if nothing was given
    if projectPath is None:
        sc.error("No project path given. Exiting...")
        sys.exit(-10)
    else:
        shared_libs.emma_helper.checkIfFolderExists(projectPath)

        # Set default value for results path
        resultsPath = projectPath

    # Overwrite results if path is given
    if args.dir is not None:
        resultsPath = shared_libs.emma_helper.joinPath(args.dir, args.subdir, OUTPUT_DIR_VISUALISER)
        shared_libs.emma_helper.mkDirIfNeeded(resultsPath)

    imageFile = emma_vis_libs.helper.getLastModFileOrPrompt(FILE_IDENTIFIER_SECTION_SUMMARY, args)
    moduleFile = emma_vis_libs.helper.getLastModFileOrPrompt(FILE_IDENTIFIER_OBJECT_SUMMARY, args)
    objectsInSectionsFile = emma_vis_libs.helper.getLastModFileOrPrompt(FILE_IDENTIFIER_OBJECTS_IN_SECTIONS, args)

    # Init classes for summaries
    consumptionObjectsInSections = emma_vis_libs.dataVisualiserMemoryMap.MemoryMap(projectPath=projectPath,
                                                                                   args=args,
                                                                                   fileToUse=objectsInSectionsFile,
                                                                                   resultsPath=resultsPath)
    consumptionObjectsInSections.plotPieChart(plotShow=False)

    # Image Summary object
    sc.info("Analysing", imageFile)
    consumptionImage = emma_vis_libs.dataVisualiserSections.ImageConsumptionList(projectPath=projectPath,
                                                                                 args=args,
                                                                                 fileToUse=imageFile,
                                                                                 resultsPath=resultsPath)

    # Module Summary object
    sc.info("Analysing", moduleFile)
    try:
        consumptionModule = emma_vis_libs.dataVisualiserObjects.ModuleConsumptionList(projectPath=projectPath,
                                                                                      args=args,
                                                                                      fileToUse=moduleFile,
                                                                                      resultsPath=resultsPath)
    except ValueError:
        sc.error("Data does not contain any module/object entry - exiting...")
        sys.exit(-10)

    # Object for visualisation fo image and module summary
    categorisedImage = emma_vis_libs.dataVisualiserCategorisedSections.CategorisedImageConsumptionList(resultsPath=resultsPath,
                                                                                                       projectPath=projectPath,
                                                                                                       statsTimestamp=consumptionImage.statsTimestamp,
                                                                                                       imageSumObj=consumptionImage,
                                                                                                       moduleSumObj=consumptionModule)

    # Do prints and plots
    consumptionImage.plotByMemType(plotShow=False)
    # TODO: Why is this method call needed? What do we get from it? Why don´t we use its return value? (AGK)
    consumptionImage.calcConsumptionByMemType()
    categorisedImage.printModulesInImage()
    categorisedImage.plotNdisplay(plotShow=False)

    # Save the categorsied sections as csv
    if args.categorised_image_csv:
        categorisedImage.categorisedImagetoCSV()

    # Write each report to file if append mode in args is selected
    if args.append:
        sc.info("Appending reports...")
        consumptionImage.writeReportToFile()
        report = emma_vis_libs.dataReports.Reports(projectPath=projectPath)
        report.plotNdisplay(plotShow=False)

    # Create a Markdown overview document and add all parts to it
    elif args.overview:
        markdown_file_path = consumptionImage.createMarkdownOverview()
        consumptionModule.appendModuleConsumptionToMarkdownOverview(markdown_file_path)
        consumptionImage.appendSupplementToMarkdownOverview(markdown_file_path)
        shared_libs.emma_helper.convertMarkdownFileToHtmlFile(markdown_file_path, (os.path.splitext(markdown_file_path)[0] + ".html"))


def parseArgs(arguments=""):
    """
    Argument parser
    :return: nothing
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
        "--project",
        "-p",
        required=True,
        help="Path of directory holding the configs files. The project name will be derived from the root folder",
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
        "--dir",
        "-d",
        help="User defined path to the statistics root directory.",
        default=None
    )
    parser.add_argument(
        "--subdir",
        help="User defined subdirectory in results folder.",
        default=""
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

    if "" == arguments:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arguments)

    if args.dir is None:
        args.dir = args.project
    else:
        args.dir = shared_libs.emma_helper.joinPath(args.dir)

    # Get paths straight (only forward slashes)
    args.dir = shared_libs.emma_helper.joinPath(args.dir)
    args.subdir = shared_libs.emma_helper.joinPath(args.subdir)

    return args


if __name__ == "__main__":
    args = parseArgs()

    sc.header("Emma Memory and Mapfile Analyser - Visualiser", symbol="/")

    timeStart = timeit.default_timer()
    sc.info("Started processing at:", datetime.datetime.now().strftime("%H:%M:%S"))

    main(args)

    timeEnd = timeit.default_timer()
    sc.info("Finished job at:", datetime.datetime.now().strftime("%H:%M:%S"), "(duration: " + "{0:.2f}".format(timeEnd - timeStart) + "s)")
