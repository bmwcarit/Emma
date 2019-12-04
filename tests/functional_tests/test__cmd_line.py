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

# Emma Memory and Mapfile Analyser - command-line tests


import unittest
import sys
import os
import shutil

from pypiscout.SCout_Logger import Logger as sc
from matplotlib import pyplot as plt

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
# pylint: disable=wrong-import-position
# Rationale: This module needs to access modules that are above them in the folder structure.

import Emma.emma
import Emma.emma_vis
from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import


class TestHelper(unittest.TestCase):
    """
    Helper class for tests that creates an environment basic setup.
    This includes making a copy of the test_project so we can work on a separate copy and not modify the original one.
    This also ensures that all the tests can work on a clean test_project state.
    """
    def init(self, testCaseName):
        # pylint: disable=attribute-defined-outside-init
        # Rationale: This class does not have an __init__() member so the member variables will be created here.

        """
        Creating the environment of the test.
        :param testCaseName: The name of the test case. This will be used to create the output folder with the name of the test case.
        :return: None
        """
        # Setting up the logger
        # This syntax will default init it and then change the settings with the __call__()
        # This is needed so that the unit tests can have different settings and not interfere with each other
        # Suppress Emma output for tests (-> invVerbosity=4)
        sc()(invVerbosity=4, actionWarning=None, actionError=lambda: sys.exit(-10))

        # Switching to the Emma root folder
        os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

        # Defining the paths of the folders used during the tests
        self.cmdLineTestRootFolder = os.path.join("tests", "other_files", "test__cmd_line")
        # Defining a path that shall contain the project files
        self.cmdLineTestProjectFolder = os.path.join(self.cmdLineTestRootFolder, "test_project")
        # Defining a path that shall contain the mapfiles
        self.cmdLineTestProjectMapfilesFolder = os.path.join(self.cmdLineTestProjectFolder, MAPFILES)
        # Defining a path for supplements
        self.cmdLineTestProjectSupplementFolder = os.path.join(self.cmdLineTestProjectFolder, SUPPLEMENT)
        # Defining a path that shall contain the output
        self.cmdLineTestOutputFolder = os.path.join("tests", "other_files", "test__cmd_line", testCaseName)
        # Defining a path that shall not exist
        self.nonExistingPath = os.path.join(self.cmdLineTestRootFolder, "this", "directory", "does", "not", "exist")

        # Checking whether the root folder still exist from the previous run, if it does, we shall not erase it, but ask the user to do it manually
        self.assertFalse(os.path.isdir(self.cmdLineTestRootFolder), "The temporary folder (\"" + self.cmdLineTestRootFolder + "\") still exists! Please delete it manually.")

        # Defining the location of the source test_project
        sourceTestProjectFolder = os.path.join("doc", "test_project")

        # Creating the root folder
        os.makedirs(self.cmdLineTestProjectFolder)
        os.makedirs(self.cmdLineTestProjectSupplementFolder)
        # Copying the project files
        for file in os.listdir(sourceTestProjectFolder):
            if os.path.splitext(file)[-1].lower() == ".json":
                shutil.copy(os.path.join(sourceTestProjectFolder, file), self.cmdLineTestProjectFolder)
        # Copying the mapfiles
        shutil.copytree(os.path.join(sourceTestProjectFolder, MAPFILES), os.path.join(self.cmdLineTestProjectFolder, MAPFILES))
        # Creating the output folder for the results with the test case name
        os.makedirs(self.cmdLineTestOutputFolder)

    def deInit(self):
        """
        Clearing up the environment of the test.
        :return: None
        """
        # Checking whether the non existing Path exists. If it does then it was created by the software, which is an error. We will delete it so it does not influence the other tests.
        nonExistingPathErrorDetected = os.path.isdir(self.nonExistingPath)
        # Deleting the output folder of this test case
        shutil.rmtree(self.cmdLineTestRootFolder)
        self.assertFalse(nonExistingPathErrorDetected, "\nThe path (\"" + self.nonExistingPath + "\") that is used to simulate a non-existing path given as a command line argument exists at tearDown!\nThis means that this path was somehow created during the test execution by the software.\nThe path was now deleted by the TestHelper::deInit() to avoid effects on other tests.")


class CmdEmma(TestHelper):
    # pylint: disable=invalid-name
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>().

    """
    Class containing tests for testing the command line argument processing for 
    """
    def setUp(self):
        plt.clf()
        self.init("CmdEmma")

    def tearDown(self):
        plt.clf()
        self.deInit()

    def test_normalRun(self):
        """
        Check that an ordinary run is successful
        """
        try:
            args = Emma.emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesFolder, "--dir", self.cmdLineTestOutputFolder])
            Emma.emma.main(args)
        except Exception as e:  # pylint: disable=broad-except
                                # Rationale: The purpose here is to catch any exception.
            self.fail("Unexpected exception: " + str(e))

    def test_help(self):
        """
        Check that `--help` does not raise an exception but exits with SystemExit(0)
        """
        with self.assertRaises(SystemExit) as context:
            args = Emma.emma.parseArgs(["--help"])
            Emma.emma.main(args)
        self.assertEqual(context.exception.code, 0)

    def test_unrecognisedArgs(self):
        """
        Check that an unexpected argument does raise an exception
        """
        with self.assertRaises(SystemExit) as context:
            args = Emma.emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesFolder, "--dir", self.cmdLineTestOutputFolder, "--blahhhhhh"])
            Emma.emma.main(args)
        self.assertEqual(context.exception.code, 2)

    def test_noProjDir(self):
        """
        Check run with non-existing project folder
        """
        with self.assertRaises(SystemExit) as context:
            args = Emma.emma.parseArgs(["--project", self.nonExistingPath, "--mapfiles", self.cmdLineTestProjectMapfilesFolder, "--dir", self.cmdLineTestOutputFolder])
            Emma.emma.main(args)
        self.assertEqual(context.exception.code, -10)

    def test_noMapfileDir(self):
        """
        Check run with non-existing mapfile folder
        """
        with self.assertRaises(SystemExit) as context:
            args = Emma.emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.nonExistingPath, "--dir", self.cmdLineTestOutputFolder])
            Emma.emma.main(args)
        self.assertEqual(context.exception.code, -10)

    def test_noDirOption(self):
        """
        Check run without a --dir parameter
        """
        try:
            args = Emma.emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesFolder])
            Emma.emma.main(args)
        except Exception as e:  # pylint: disable=broad-except
                                # Rationale: The purpose here is to catch any exception.
            self.fail("Unexpected exception: " + str(e))


class CmdEmmaVis(TestHelper):
    # pylint: disable=invalid-name
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>().

    """
    Class containing tests for testing the command line argument processing for Emma-Vis.
    """

    def setUp(self):
        self.init("CmdEmmaVis")
        self.runEmma(self.cmdLineTestOutputFolder)

    def tearDown(self):
        self.deInit()

    def runEmma(self, outputFolder=None):
        """
        Function to run the 
        :param outputFolder: The output folder that will be given as the --dir parameter. If it is None, the --dir parameter will not be given to 
        :return: None
        """
        if outputFolder is not None:
            args = Emma.emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesFolder, "--dir", outputFolder, "--noprompt"])
        else:
            args = Emma.emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesFolder, "--noprompt"])
        Emma.emma.main(args)

    def test_normalRun(self):
        """
        Check that an ordinary run is successful
        """
        try:
            argsEmmaVis = Emma.emma_vis.parseArgs(["--project", self.cmdLineTestProjectFolder, "--overview", "--inOutDir", self.cmdLineTestOutputFolder, "--noprompt", "--quiet"])
            Emma.emma_vis.main(argsEmmaVis)
        except Exception as e:  # pylint: disable=broad-except
                                # Rationale: The purpose here is to catch any exception.
            self.fail("Unexpected exception: " + str(e))

    def test_help(self):
        """
        Check that `--help` does not raise an exception but exits with SystemExit(0)
        """
        with self.assertRaises(SystemExit) as context:
            args = Emma.emma_vis.parseArgs(["--help"])
            Emma.emma_vis.main(args)
        self.assertEqual(context.exception.code, 0)

    def test_unrecognisedArgs(self):
        """
        Check that an unexpected argument does raise an exception
        """
        with self.assertRaises(SystemExit) as context:
            args = Emma.emma_vis.parseArgs(["--project", self.cmdLineTestProjectFolder, "overview", "--dir", self.cmdLineTestOutputFolder, "--blahhhhhh", "--noprompt", "--quiet"])
            Emma.emma_vis.main(args)
        self.assertEqual(context.exception.code, 2)

    def test_noProjDir(self):
        """
        Check run with non-existing project folder
        """
        with self.assertRaises(SystemExit) as context:
            args = Emma.emma_vis.parseArgs(["--project", self.nonExistingPath, "--overview", "--inOutDir", self.cmdLineTestOutputFolder, "--noprompt", "--quiet"])
            Emma.emma_vis.main(args)
        self.assertEqual(context.exception.code, -10)

    def test_noMemStats(self):
        """
        Check run with non-existing memStats folder
        """
        with self.assertRaises(SystemExit) as context:
            args = Emma.emma_vis.parseArgs(["--project", self.cmdLineTestProjectFolder, "--overview", "--inOutDir", self.nonExistingPath, "--noprompt", "--quiet"])
            Emma.emma_vis.main(args)
        self.assertEqual(context.exception.code, -10)

    def test_noDirOption(self):
        """
        Check run without a --dir parameter
        """
        try:
            # This a is a specific case, the default Emma results will not work here. Because of this, we will delete it and run the Emma again.
            shutil.rmtree(self.cmdLineTestOutputFolder)
            self.runEmma()
            args = Emma.emma_vis.parseArgs(["--project", self.cmdLineTestProjectFolder, "--overview", "--noprompt", "--quiet"])
            Emma.emma_vis.main(args)
            plt.close('all')
        except Exception as e:  # pylint: disable=broad-except
                                # Rationale: The purpose here is to catch any exception.
            self.fail("Unexpected exception: " + str(e))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.argv.pop()
    unittest.main()
