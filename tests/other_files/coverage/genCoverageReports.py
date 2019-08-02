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
import sys
import shutil
import unittest
import datetime
import coverage

from pypiscout.SCout_Logger import Logger as sc


def main():
    """
    Script to create code coverage reports for the unit tests of Emma.

    Output folder of the report (relative):
        reports/<TIMESTAMP>

    In this folder the "source" sub-folder contains the .coverage file from which the .html report can be generated.

    If the report folder (or its sub-folder) exists then script will break with an error, in order not to overwrite the previous report.
    """

    def exitProgram():
        sys.exit(-10)

    sc()(-1, actionWarning=None, actionError=exitProgram)

    sc().header("Generating Unit Test Coverage Report")

    # Setting up the variables (folder and file names...etc.)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Ms%S")
    coverageDataFileName = ".coverage"
    reportsFolder = os.path.join(os.path.dirname(__file__), "reports")
    unitTestFolder = os.path.join(os.path.dirname(__file__), "..", "..", "unit_tests")
    # These are the folders that will belong to this specific run
    actualReportFolder = os.path.join(reportsFolder, timestamp)
    actualReportSourceFolder = os.path.join(reportsFolder, timestamp, "source")

    # Checking whether the output folders exist
    if not os.path.isdir(actualReportFolder):
        os.mkdir(actualReportFolder)
        if not os.path.isdir(actualReportSourceFolder):
            os.mkdir(actualReportSourceFolder)
        else:
            sc().error("Error! The folder " + actualReportSourceFolder + " already exists!")
    else:
        sc().error("Error! The folder " + actualReportFolder + " already exists!")

    # Switching to the folder where this script is and setting up the objects needed for the unit tests and coverage reports
    sc().info("Running the unit tests...")
    os.chdir(os.path.dirname(__file__))
    testLoader = unittest.TestLoader()
    testSuite = testLoader.discover(unitTestFolder)
    testRunner = unittest.TextTestRunner()
    coverageTool = coverage.Coverage()

    # Starting the coverage measurement
    coverageTool.start()

    # Running the unit tests and storing whether every test passed
    testReults = testRunner.run(testSuite)
    atLeastOneTestFailed = False
    if testReults.failures or testReults.errors:
        atLeastOneTestFailed = True

    # Stopping the coverage measurement
    coverageTool.stop()

    # Re-initializing the logger since it could have been used in the unittest and that would override our settings
    sc()(-1, actionWarning=None, actionError=exitProgram)

    # We will only generate a html report if all the unit tests passed
    if atLeastOneTestFailed:
        sc().error("Could not generate coverage report because one of the tests have failed!")
    else:
        sc().info("Creating the .html report...")
        coverageTool.save()
        coverageTool.html_report(directory=actualReportFolder)
        shutil.move(coverageDataFileName, actualReportSourceFolder)


if __name__ == '__main__':
    main()
