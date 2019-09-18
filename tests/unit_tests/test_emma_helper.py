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
import unittest
import platform

from pypiscout.SCout_Logger import Logger as sc

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "Emma"))
# pylint: disable=wrong-import-position
# Rationale: This module needs to access modules that are above them in the folder structure.

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper


class EmmaHelperTestCase(unittest.TestCase):
    # pylint: disable=invalid-name, missing-docstring
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>(). It is not necessary to add a docstring for every unit test.

    """
    Unit tests for the emma_helper module.
    """
    def setUp(self):
        """
        Setting up the logger
        This syntax will default init it and then change the settings with the __call__()
        This is needed so that the unit tests can have different settings and not interfere with each other
        :return: None
        """
        sc()(invVerbosity=4, actionWarning=lambda: sys.exit("warning"), actionError=lambda: sys.exit("error"))

    def test_checkIfFolderExists(self):
        try:
            shared_libs.emma_helper.checkIfFolderExists(os.path.dirname(__file__))
        except Exception:   # pylint: disable=broad-except
                            # Rationale: The goal here is to catch any exception types.
            self.fail("Unexpected exception!")
        with self.assertRaises(SystemExit) as contextManager:
            shared_libs.emma_helper.checkIfFolderExists("DefinitelyNonExistingFolder")
        self.assertEqual(contextManager.exception.code, "error")

    def test_checkIfFileExists(self):
        try:
            shared_libs.emma_helper.checkIfFileExists(__file__)
        except Exception:   # pylint: disable=broad-except
                            # Rationale: The goal here is to catch any exception types.
            self.fail("Unexpected exception!")
        with self.assertRaises(SystemExit) as contextManager:
            shared_libs.emma_helper.checkIfFileExists("DefinitelyNonExisting.file")
        self.assertEqual(contextManager.exception.code, "error")

    def test_mkDirIfNeeded(self):
        directoryName = "TestDirectoryNameThatShouldNotExist"
        self.assertFalse(os.path.isdir(directoryName))
        shared_libs.emma_helper.mkDirIfNeeded(directoryName)
        self.assertTrue(os.path.isdir(directoryName))
        os.rmdir(directoryName)

    def test_readJsonWriteJson(self):
        jsonTestFilePath = os.path.join(os.path.dirname(__file__), "..", "other_files", "testJson.json")
        self.assertFalse(os.path.exists(jsonTestFilePath))

        jsonContentToWrite = {"TestDictionary": {}}
        jsonContentToWrite["TestDictionary"]["test_passed"] = True
        shared_libs.emma_helper.writeJson(jsonTestFilePath, jsonContentToWrite)
        self.assertTrue(os.path.exists(jsonTestFilePath))

        jsonContentReadIn = shared_libs.emma_helper.readJson(jsonTestFilePath)
        self.assertIn("TestDictionary", jsonContentReadIn)
        self.assertIn("test_passed", jsonContentReadIn["TestDictionary"])
        self.assertEqual(type(jsonContentReadIn["TestDictionary"]["test_passed"]), bool)

        os.remove(jsonTestFilePath)
        self.assertFalse(os.path.exists(jsonTestFilePath))

    def test_unifyAddress(self):
        hexResult, decResult = shared_libs.emma_helper.unifyAddress("0x16")
        self.assertEqual(hexResult, "0x16")
        self.assertEqual(decResult, 22)
        hexResult, decResult = shared_libs.emma_helper.unifyAddress(22)
        self.assertEqual(hexResult, "0x16")
        self.assertEqual(decResult, 22)
        with self.assertRaises(ValueError) as contextManager:
            hexResult, decResult = shared_libs.emma_helper.unifyAddress("Obviously not a number...")
        with self.assertRaises(SystemExit) as contextManager:
            hexResult, decResult = shared_libs.emma_helper.unifyAddress(0.123)
        self.assertEqual(contextManager.exception.code, "error")

    def test_getTimestampFromFilename(self):
        timestamp = shared_libs.emma_helper.getTimestampFromFilename("MyFile_2017-11-06-14h56s52.csv")
        self.assertEqual(timestamp, "2017-11-06-14h56s52")
        with self.assertRaises(SystemExit) as contextManager:
            shared_libs.emma_helper.getTimestampFromFilename("MyFileWithoutTimeStamp.csv")
        self.assertEqual(contextManager.exception.code, "error")

    def test_toHumanReadable(self):
        self.assertEqual(" 0.00 B", shared_libs.emma_helper.toHumanReadable(0))
        self.assertEqual(" 10.00 B", shared_libs.emma_helper.toHumanReadable(10))
        self.assertEqual(" 1024.00 B", shared_libs.emma_helper.toHumanReadable(1024))
        self.assertEqual(" 1.00 KiB", shared_libs.emma_helper.toHumanReadable(1025))
        self.assertEqual(" 1.01 KiB", shared_libs.emma_helper.toHumanReadable(1035))
        self.assertEqual(" 1.10 KiB", shared_libs.emma_helper.toHumanReadable(1126))
        self.assertEqual(" 157.36 GiB", shared_libs.emma_helper.toHumanReadable(168963795964))

    def test_evalSummary(self):
        self.assertEqual(shared_libs.emma_helper.evalSummary("Projectname_" + FILE_IDENTIFIER_SECTION_SUMMARY + "_2017-11-06-14h56s52.csv"), FILE_IDENTIFIER_SECTION_SUMMARY)
        self.assertEqual(shared_libs.emma_helper.evalSummary("Projectname_" + FILE_IDENTIFIER_OBJECT_SUMMARY + "_2017-11-06-14h56s52.csv"), FILE_IDENTIFIER_OBJECT_SUMMARY)
        self.assertIsNone(shared_libs.emma_helper.evalSummary("Projectname_" + "_2017-11-06-14h56s52.csv"))

    def test_projectNameFromPath(self):
        self.assertEqual("MyProject", shared_libs.emma_helper.projectNameFromPath(os.path.join("C:", "GitRepos", "Emma", "MyProject")))

    def test_joinPath(self):
        if platform.system() == "Windows":
            self.assertEqual(r"c:Documents\Projects\Emma", shared_libs.emma_helper.joinPath("c:", "Documents", "Projects", "Emma"))
            self.assertEqual(r"..\..\Emma\tests\other_files", shared_libs.emma_helper.joinPath("..", "..", "Emma", "tests", "other_files"))
        elif platform.system() == "Linux":
            self.assertEqual(r"Documents/Projects/Emma", shared_libs.emma_helper.joinPath("Documents", "Projects", "Emma"))
            self.assertEqual(r"../../Emma/tests/other_files", shared_libs.emma_helper.joinPath("..", "..", "Emma", "tests", "other_files"))
        else:
            raise EnvironmentError("Unexpected platform value: " + platform.system())
