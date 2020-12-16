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

import tempfile
import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import Emma.emma_libs.configuration
# pylint: disable=wrong-import-position


class ConfigurationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        emmaRootFolder = os.path.join("..", "..")
        self.testProjectFolder = os.path.join(emmaRootFolder, "doc", "test_project")
        self.mapfilesFolder = os.path.join(self.testProjectFolder, "mapfiles")
        self.emptyMapfileFolder = tempfile.TemporaryDirectory(dir=self.testProjectFolder)
        self.conf = Emma.emma_libs.configuration.Configuration()

    def tearDown(self) -> None:
        self.emptyMapfileFolder.cleanup()

    def test_readConfigurationEmpty(self):
        # Check that the function does not fail if no map files are found
        try:
            self.conf.readConfiguration(self.testProjectFolder, self.emptyMapfileFolder.name, True)
        except Exception as e:  # pylint: disable=broad-except
            self.fail("Unexpected exception: " + str(e))

    def test_readConfiguration(self):
        self.conf.readConfiguration(self.testProjectFolder, self.mapfilesFolder, True)
        self.assertEqual(len(self.conf.globalConfig), 2)
        self.assertEqual(list(self.conf.globalConfig.keys())[0], "MCU")
        self.assertEqual(len(self.conf.globalConfig["MCU"]), 7)
        self.assertEqual(list(self.conf.globalConfig.keys())[1], "SOC")
        self.assertEqual((len(self.conf.globalConfig["SOC"])), 9)


if __name__ == '__main__':
    unittest.main()
