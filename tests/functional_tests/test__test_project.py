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


import os
import sys
import shutil
import subprocess
import unittest
import datetime
import pandas


sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
# pylint: disable=wrong-import-position
# Rationale: This module needs to access modules that are above them in the folder structure.

from shared_libs.stringConstants import *   # pylint: disable=unused-wildcard-import, wildcard-import, wrong-import-order


class EmmaTestProject(unittest.TestCase):
    # pylint: disable=invalid-name
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>().

    """
    A test case to test the Emma with the test_project.
    """
    def setUp(self):
        # pylint: disable=too-many-locals
        # Rationale: This is only a test file, it does not need to have production grade quality.
        """
        A function to setup the variables used in the tests and to run the Emma on the test_project.
        :return: None
        """
        # Changing the working directory to the scripts path
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Setting up the variables
        emmaRootFolder = os.path.join("..", "..")
        emmaPath = os.path.join(emmaRootFolder, "emma.py")
        testProjectFolder = os.path.join(emmaRootFolder, "doc", "test_project")
        mapfilesFolder = os.path.join(testProjectFolder, "mapfiles")
        self.resultsFolder = os.path.join("..", "other_files", "test__test_project")
        self.memStatsFolder = os.path.join(self.resultsFolder, OUTPUT_DIR)

        # Checking whether the result folder exists, deleting it if it does,
        # and then creating it again, so we have a clean results folder
        if os.path.isdir(self.resultsFolder):
            shutil.rmtree(self.resultsFolder)
        os.mkdir(self.resultsFolder)

        # Running the test_project to create the CSV tables
        subprocess.run(["python", emmaPath, "--project", testProjectFolder, "--mapfile", mapfilesFolder, "--dir", self.resultsFolder])

        for _, directories, files in os.walk(self.memStatsFolder):
            # The result folder shall have 0 subdirectories and three summary files
            self.assertEqual(len(directories), 0)
            self.assertEqual(len(files), 3)

        # Setting up the file name related variables
        projectName = "test_project"
        timeStampLength = len(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Ms%S"))
        reportFileExtension = ".csv"
        reportFileExtensionLength = len(reportFileExtension)
        imageSummaryFileNameFixPart = projectName + "_" + FILE_IDENTIFIER_SECTION_SUMMARY + "_"
        moduleSummaryFileNameFixPart = projectName + "_" + FILE_IDENTIFIER_OBJECT_SUMMARY + "_"
        objectsInSectionsFileNameFixPart = projectName + "_" + FILE_IDENTIFIER_OBJECTS_IN_SECTIONS + "_"

        # Checking whether the expected report names are there and setting up the variables with their paths
        for file in os.listdir(self.memStatsFolder):
            if imageSummaryFileNameFixPart == file[:-(timeStampLength + reportFileExtensionLength)]:
                self.imageSummaryPath = os.path.join(self.memStatsFolder, file)
            elif moduleSummaryFileNameFixPart == file[:-(timeStampLength + reportFileExtensionLength)]:
                self.moduleSummaryPath = os.path.join(self.memStatsFolder, file)
            elif objectsInSectionsFileNameFixPart == file[:-(timeStampLength + reportFileExtensionLength)]:
                self.objectsInSectionsPath = os.path.join(self.memStatsFolder, file)
            else:
                raise EnvironmentError("Unexpected file: " + os.path.join(self.memStatsFolder, file))

        # Setting up the variable with the expected column values
        self.expectedColumns = [ADDR_START_HEX, ADDR_END_HEX, SIZE_HEX, ADDR_START_DEC, ADDR_END_DEC,
                                SIZE_DEC, SIZE_HUMAN_READABLE, SECTION_NAME, OBJECT_NAME, CONFIG_ID,
                                DMA, VAS_NAME, VAS_SECTION_NAME,
                                MEM_TYPE, MEM_TYPE_TAG, CATEGORY, MAPFILE,
                                OVERLAP_FLAG, CONTAINMENT_FLAG, DUPLICATE_FLAG, CONTAINING_OTHERS_FLAG,
                                ADDR_START_HEX_ORIGINAL, ADDR_END_HEX_ORIGINAL, SIZE_HEX_ORIGINAL, SIZE_DEC_ORIGINAL]

    def tearDown(self):
        """
        A function to clean up after the tests.
        :return: None
        """
        # Checking whether the result folder exists, deleting it if it does
        if os.path.isdir(self.resultsFolder):
            shutil.rmtree(self.resultsFolder)

    class ExpectedDataTypeData:
        """
        A class that contains the expected data of a data type.
        """
        def __init__(self, name, numberOfRows, totalSizeDec):
            self.name = name
            self.numberOfRows = numberOfRows
            self.totalSizeDec = totalSizeDec

    class ExpectedConfigIdData:
        """
        A class that contains the expected data of a configId.
        """
        def __init__(self, name, numberOfRows, listOfDataTypeData):
            self.name = name
            self.numerOfRows = numberOfRows
            self.listOfDataTypeData = listOfDataTypeData

    class ExpectedReportData:
        """
        A class that contains the expected data of a report.
        """
        def __init__(self, numberOfRows, listOfColumns, listOfConfigIdData):
            self.numberOfRows = numberOfRows
            self.listOfColumns = listOfColumns
            self.listOfConfigIdData = listOfConfigIdData

    def checkDataTypeData(self, dataTypeData: pandas.DataFrame, expectedDataTypeData: ExpectedDataTypeData):
        """
        A function to test a data type.
        :param dataTypeData: The data frame containing the data of a data type.
        :param expectedDataTypeData: The expected data of the data type.
        :return: None
        """
        dataTypeNumberOfRows, _ = dataTypeData.shape
        dataTypeTotalSizeDec = dataTypeData[SIZE_DEC].sum()

        # Checking the number of elements
        self.assertEqual(dataTypeNumberOfRows, expectedDataTypeData.numberOfRows)

        # Checking the total consumption
        self.assertEqual(dataTypeTotalSizeDec, expectedDataTypeData.totalSizeDec)

    def checkConfigIdData(self, configIdData: pandas.DataFrame, expectedConfigIdData: ExpectedConfigIdData):
        """
        A function to test a configId.
        :param configIdData: The data frame containing the data of the configId.
        :param expectedConfigIdData: The expected data of the configId.
        :return: None
        """
        configIdNumberOfRows, _ = configIdData.shape

        # Checking the number of the elements
        self.assertEqual(configIdNumberOfRows, expectedConfigIdData.numerOfRows)

        # Checking the data types
        for expectedDataTypeData in expectedConfigIdData.listOfDataTypeData:
            dataTypeData = configIdData[configIdData.memType == expectedDataTypeData.name]
            self.checkDataTypeData(dataTypeData, expectedDataTypeData)

    def checkReport(self, reportData: pandas.DataFrame, expectedReportData: ExpectedReportData):
        """
        A functon to test a report.
        :param reportData: The data frame containing the data of the report.
        :param expectedReportData: The expected data of the report.
        :return: None
        """
        # Checking the type of the imageSummary
        self.assertEqual(type(reportData).__name__, "DataFrame")
        numberOfRows, numberOfColumns = reportData.shape

        # Checking the number of rows
        self.assertEqual(numberOfRows, expectedReportData.numberOfRows)

        # Checking the number of columns
        self.assertEqual(numberOfColumns, len(expectedReportData.listOfColumns))

        # Checking the column values and their order
        self.assertEqual(reportData.columns.tolist(), expectedReportData.listOfColumns)
        uniqueConfigIdValues = reportData.configID.unique().tolist()

        # Checking the configIDs and their data
        self.assertEqual(len(uniqueConfigIdValues), len(expectedReportData.listOfConfigIdData))
        for expectedConfigIdData in expectedReportData.listOfConfigIdData:
            self.assertIn(expectedConfigIdData.name, uniqueConfigIdValues)
            configIdData = reportData[reportData.configID == expectedConfigIdData.name]
            self.checkConfigIdData(configIdData, expectedConfigIdData)

    def test_imageSummaryReport(self):
        """
        A function to test the Image Summary report of the test_project.
        :return: None
        """
        # Loading the report data
        reportData = pandas.read_csv(self.imageSummaryPath, sep=";")

        # Define the expected data of the MCU configId
        expectedMcuIntFlashData = self.ExpectedDataTypeData("INT_FLASH", 9, 393336)
        expectedMcuIntRamData = self.ExpectedDataTypeData("INT_RAM", 4, 134656)
        expectedMcuData = self.ExpectedConfigIdData("MCU", 13, [expectedMcuIntFlashData, expectedMcuIntRamData])

        # Define the expected data of the SOC configId
        expectedSocExtRamData = self.ExpectedDataTypeData("EXT_RAM", 18, 6164824)
        expectedSocData = self.ExpectedConfigIdData("SOC", 18, [expectedSocExtRamData])

        # Define the expected data of the report
        expectedReportData = self.ExpectedReportData(31, self.expectedColumns, [expectedMcuData, expectedSocData])

        # Checking the report data
        self.checkReport(reportData, expectedReportData)

    def test_moduleSummaryReport(self):
        """
        A function to test the Module Summary report of the test_project.
        :return: None
        """
        # Loading the report data
        reportData = pandas.read_csv(self.moduleSummaryPath, sep=";")

        # Define the expected data of the MCU configId
        expectedMcuIntFlashData = self.ExpectedDataTypeData("INT_FLASH", 20, 89280)
        expectedMcuIntRamData = self.ExpectedDataTypeData("INT_RAM", 2, 3584)
        expectedMcuData = self.ExpectedConfigIdData("MCU", 22, [expectedMcuIntFlashData, expectedMcuIntRamData])

        # Define the expected data of the SOC configId
        expectedSocExtRamData = self.ExpectedDataTypeData("EXT_RAM", 26, 5181784)
        expectedSocData = self.ExpectedConfigIdData("SOC", 26, [expectedSocExtRamData])

        # Define the expected data of the report
        expectedReportData = self.ExpectedReportData(48, self.expectedColumns, [expectedMcuData, expectedSocData])

        # Checking the report data
        self.checkReport(reportData, expectedReportData)

    def test_objectsInSectionsReport(self):
        """
        A function to test the Objects In Sections report of the test_project.
        :return: None
        """
        # Loading the report data
        reportData = pandas.read_csv(self.objectsInSectionsPath, sep=";")

        # Define the expected data of the MCU configId
        expectedMcuIntFlashData = self.ExpectedDataTypeData("INT_FLASH", 32, 393336)
        expectedMcuIntRamData = self.ExpectedDataTypeData("INT_RAM", 8, 134656)
        expectedMcuData = self.ExpectedConfigIdData("MCU", 40, [expectedMcuIntFlashData, expectedMcuIntRamData])

        # Define the expected data of the SOC configId
        expectedSocExtRamData = self.ExpectedDataTypeData("EXT_RAM", 59, 6164824)
        expectedSocData = self.ExpectedConfigIdData("SOC", 59, [expectedSocExtRamData])

        # Define the expected data of the report
        expectedReportData = self.ExpectedReportData(99, self.expectedColumns, [expectedMcuData, expectedSocData])

        # Checking the report data
        self.checkReport(reportData, expectedReportData)


if __name__ == "__main__":
    unittest.main()
