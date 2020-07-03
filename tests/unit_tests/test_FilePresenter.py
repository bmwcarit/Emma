""""
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
import tempfile
from unittest import TestCase

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
# pylint: disable=wrong-import-position
# Rationale: This module needs to access modules that are above them in the folder structure.

import Emma.emma_delta_libs.FilePresenter
import Emma.emma_delta_libs.FileSelector


class FilePresenterTestCase(TestCase):
    def setUp(self) -> None:
        self.thisDir = os.path.dirname(os.path.abspath(__file__))
        tempdir = tempfile.TemporaryDirectory(dir=self.thisDir)
        pathToDir = os.path.join(tempdir.name, "memStats")
        if not os.path.exists(pathToDir):
            os.makedirs(pathToDir)

        self.testFile1 = os.path.join(pathToDir, "Object_Summary_2020_05_06.csv")
        self.testFile2 = os.path.join(pathToDir, "Object_Summary_2020_04_06.csv")
        self.FileSelector = Emma.emma_delta_libs.FileSelector.FileSelector(tempdir.name)
        self.filePresenter = Emma.emma_delta_libs.FilePresenter.FilePresenter(self.FileSelector)
        self.candidates = {1: self.testFile1, 2: self.testFile2}

    def test_selectNumber(self):
        self.assertEqual(False, Emma.emma_delta_libs.FilePresenter.FilePresenter.validateNumber(self.filePresenter, "1 4"))
        self.assertEqual(False, Emma.emma_delta_libs.FilePresenter.FilePresenter.validateNumber(self.filePresenter, 3))
        self.assertEqual(True, Emma.emma_delta_libs.FilePresenter.FilePresenter.validateNumber(self.filePresenter, 1))

    def test_selectIndices(self):
        self.assertEqual(False, Emma.emma_delta_libs.FilePresenter.FilePresenter.validateIndices(1, self.candidates))
        self.assertEqual(False, Emma.emma_delta_libs.FilePresenter.FilePresenter.validateIndices(["b", 2], self.candidates))
        self.assertEqual(True, Emma.emma_delta_libs.FilePresenter.FilePresenter.validateIndices([2, 1], self.candidates))


if __name__ == '__main__':
    unittest.main()
