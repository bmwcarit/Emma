import os
import sys
import unittest
from unittest import TestCase
import Emma.emma_delta_libs.FilePresenter
import Emma.emma_delta_libs.FileSelector

sys.path.append(os.path.join(os.path.dirname(__file__)))


class FilePresenterTestCase(TestCase):

    def setUp(self) -> None:
        newFolder = os.path.join("..", "..")
        projectDir = os.path.join(newFolder, "testcase")
        testFile1 = os.path.join(projectDir, "memStats", "Object_Summary_2020_05_06.csv")
        testFile2 = os.path.join(projectDir, "memStats", "Object_Summary_2020_04_06.csv")
        self.FileSelector = Emma.emma_delta_libs.FileSelector.FileSelector(projectDir)
        self.filePresenter = Emma.emma_delta_libs.FilePresenter.FilePresenter(self.FileSelector)
        self.candidates = {1: testFile1, 2: testFile2}

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
