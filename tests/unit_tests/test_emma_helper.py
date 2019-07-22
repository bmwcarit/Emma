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

from pypiscout.SCout_Logger import Logger as sc

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from shared_libs.stringConstants import *
import shared_libs.emma_helper


class MemEntryTestCase(unittest.TestCase):
    def setUp(self):

        # Setting up the logger
        # This syntax will default init it and then change the settings with the __call__()
        # This is needed so that the unit tests can have different settings and not interfere with each other
        sc()(4, actionWarning=self.warningAction, actionError=self.errorAction)

    # A warning action that will be registered in the logger
    def warningAction(self):
        sys.exit("warning")

    # An error action that will be registered in the logger
    def errorAction(self):
        sys.exit("error")

    def test_checkIfFolderExists(self):
        try:
            shared_libs.emma_helper.checkIfFolderExists(os.path.abspath(os.path.join("..", "unit_tests")))
        except Exception:
            self.fail("Unexpected exception!")
        with self.assertRaises(SystemExit) as contextManager:
            shared_libs.emma_helper.checkIfFolderExists("DefinitelyNonExistingFolder")
        self.assertEqual(contextManager.exception.code, "error")

    def test_checkForFile(self):
        try:
            shared_libs.emma_helper.checkForFile(os.path.join("..", "unit_tests", "test_emma_helper.py"))
        except Exception:
            self.fail("Unexpected exception!")
        with self.assertRaises(SystemExit) as contextManager:
            shared_libs.emma_helper.checkForFile("DefinitelyNonExisting.file")
        self.assertEqual(contextManager.exception.code, "error")

    def test_mkDirIfNeeded(self):
        directoryName = "TestDirectoryNameThatShouldNotExist"
        self.assertFalse(os.path.isdir(directoryName))
        shared_libs.emma_helper.mkDirIfNeeded(directoryName)
        self.assertTrue(os.path.isdir(directoryName))
        os.rmdir(directoryName)

    def test_readJsonWriteJson(self):
        jsonTestFilePath = os.path.join("..", "other_files", "testJson.json")
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
        with self.assertRaises(SystemExit) as contextManager:
            hexResult, decResult = shared_libs.emma_helper.unifyAddress(True)
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
        self.assertEqual("c:Documents\Projects\Emma", shared_libs.emma_helper.joinPath("c:", "Documents", "Projects", "Emma"))
        self.assertEqual("c:Documents\Projects\Emma", shared_libs.emma_helper.joinPath("c:Documents", "Projects/Emma"))
