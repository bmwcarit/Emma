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

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
# pylint: disable=wrong-import-position
# Rationale: This module needs to access modules that are above them in the folder structure.

import emma
import emma_vis


class TestHelper(unittest.TestCase):
    """
    Helper class for tests that creates an environment basic setup.
    This includes making a copy of the test_project so we can work on a separate copy and not modify the original one.
    This also ensures that all the tests can work on a clean test_project state.
    """
    def init(self, testCaseName):
        # Setting up the logger
        # This syntax will default init it and then change the settings with the __call__()
        # This is needed so that the unit tests can have different settings and not interfere with each other
        sc()(4, actionWarning=None, actionError=TestHelper.actionError)

        # Switching to the Emma root folder
        os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

        # Defining the paths of the folders used during the tests
        self.cmdLineTestRootFolder = os.path.join("tests", "other_files", "test__cmd_line")
        # Defining a path that shall contain the project files
        self.cmdLineTestProjectFolder = os.path.join(self.cmdLineTestRootFolder, "test_project")
        # Defining a path that shall contain the mapfiles
        self.cmdLineTestProjectMapfilesfolder = os.path.join(self.cmdLineTestProjectFolder, "mapfiles")
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
        # Copying the project files
        for file in os.listdir(sourceTestProjectFolder):
            if os.path.splitext(file)[-1].lower() == ".json":
                shutil.copy(os.path.join(sourceTestProjectFolder, file), self.cmdLineTestProjectFolder)
        # Copying the mapfiles
        shutil.copytree(os.path.join(sourceTestProjectFolder, "mapfiles"), os.path.join(self.cmdLineTestProjectFolder, "mapfiles"))
        # Creating the output folder for the results with the test case name
        os.makedirs(self.cmdLineTestOutputFolder)

    @staticmethod
    def actionError():
        sys.exit(-10)

    def deInit(self):
        # Checking whether the non existing Path exists. If it does then it was created by the software, which is an error. We will delete it so it does not influence the other tests.
        nonExistingPathErrorDetected = os.path.isdir(self.nonExistingPath)
        # Deleting the output folder of this test case
        shutil.rmtree(self.cmdLineTestRootFolder)
        self.assertFalse(nonExistingPathErrorDetected, "The non-existing path (\"" + self.nonExistingPath + "\") exists at tearDown! This path shall never be created by the software. To avoid effects on other tests, it was now deleted.")


class CmdEmma(TestHelper):
    # pylint: disable=invalid-name
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>().

    """
    Class containing tests for testing the command line argument processing for Emma.
    """
    def setUp(self):
        self.init("CmdEmma")

    def tearDown(self):
        self.deInit()

    def test_normalRun(self):
        """
        Check that an ordinary run is successful
        """
        try:
            args = emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesfolder, "--dir", self.cmdLineTestOutputFolder])
            emma.main(args)
        except Exception as e:
            self.fail("Unexpected exception: " + str(e))

    def test_help(self):
        """
        Check that `--help` does not raise an exeption but exits with SystemExit(0)
        """
        with self.assertRaises(SystemExit) as context:
            args = emma.parseArgs(["--help"])
            emma.main(args)
        self.assertEqual(context.exception.code, 0)

    def test_unrecognisedArgs(self):
        """
        Check that an unexpected argument does raise an exeption
        """
        with self.assertRaises(SystemExit) as context:
            args = emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesfolder, "--dir", self.cmdLineTestOutputFolder, "--blahhhhhh"])
            emma.main(args)
        self.assertEqual(context.exception.code, 2)

    def test_noProjDir(self):
        """
        Check run with non-existing project folder
        """
        with self.assertRaises(SystemExit) as context:
            args = emma.parseArgs(["--project", self.nonExistingPath, "--mapfiles", self.cmdLineTestProjectMapfilesfolder, "--dir", self.cmdLineTestOutputFolder])
            emma.main(args)
        self.assertEqual(context.exception.code, -10)

    def test_noMapfileDir(self):
        """
        Check run with non-existing mapfile folder
        """
        with self.assertRaises(SystemExit) as context:
            args = emma.parseArgs(["--project",  self.cmdLineTestProjectFolder, "--mapfiles", self.nonExistingPath, "--dir", self.cmdLineTestOutputFolder])
            emma.main(args)
        self.assertEqual(context.exception.code, -10)

    def test_noDirOption(self):
        """
        Check run without a --dir parameter
        """
        try:
            args = emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesfolder])
            emma.main(args)
        except Exception as e:
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
        if outputFolder is not None:
            args = emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesfolder, "--dir", outputFolder, "--noprompt"])
        else:
            args = emma.parseArgs(["--project", self.cmdLineTestProjectFolder, "--mapfiles", self.cmdLineTestProjectMapfilesfolder, "--noprompt"])
        emma.main(args)

    def test_normalRun(self):
        """
        Check that an ordinary run is successful
        """
        try:
            args = emma_vis.parseArgs(["--project", self.cmdLineTestProjectFolder, "--overview", "--dir", self.cmdLineTestOutputFolder, "--noprompt", "--quiet"])
            emma_vis.main(args)
        except Exception as e:
            self.fail("Unexpected exception: " + str(e))

    def test_help(self):
        """
        Check that `--help` does not raise an exeption but exits with SystemExit(0)
        """
        with self.assertRaises(SystemExit) as context:
            args = emma_vis.parseArgs(["--help"])
            emma_vis.main(args)
        self.assertEqual(context.exception.code, 0)

    def test_unrecognisedArgs(self):
        """
        Check that an unexpected argument does raise an exeption
        """
        with self.assertRaises(SystemExit) as context:
            args = emma_vis.parseArgs(["--project", self.cmdLineTestProjectFolder, "overview", "--dir", self.cmdLineTestOutputFolder, "--blahhhhhh", "--noprompt", "--quiet"])
            emma_vis.main(args)
        self.assertEqual(context.exception.code, 2)

    def test_noProjDir(self):
        """
        Check run with non-existing project folder
        """
        with self.assertRaises(SystemExit) as context:
            args = emma_vis.parseArgs(["--project", self.nonExistingPath, "--overview", "--dir", self.cmdLineTestOutputFolder, "--noprompt", "--quiet"])
            emma_vis.main(args)
        self.assertEqual(context.exception.code, -10)

    def test_noMemStats(self):
        """
        Check run with non-existing memStats folder
        """
        with self.assertRaises(SystemExit) as context:
            args = emma_vis.parseArgs(["--project", self.cmdLineTestProjectFolder, "--overview", "--dir", self.nonExistingPath, "--noprompt", "--quiet"])
            emma_vis.main(args)
        self.assertEqual(context.exception.code, -10)

    def test_noDirOption(self):
        """
        Check run without a --dir parameter
        """
        try:
            # This a is a specific case, the default Emma results will not work here. Because of this, we will delete it and run the Emma again.
            shutil.rmtree(self.cmdLineTestOutputFolder)
            self.runEmma()
            args = emma_vis.parseArgs(["--project", self.cmdLineTestProjectFolder, "--overview", "--noprompt", "--quiet"])
            emma_vis.main(args)
        except Exception as e:
            self.fail("Unexpected exception: " + str(e))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.argv.pop()
    unittest.main()
