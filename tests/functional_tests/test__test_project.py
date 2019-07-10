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
import shutil
import subprocess
import unittest
import pandas
import datetime

from shared_libs.stringConstants import *


class EmmaTestProject(unittest.TestCase):
    def setUp(self):
        # Changing the working directory to the scripts path
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Setting up the variables
        emmaRootFolder = os.path.join("..", "..")
        emmaPath = os.path.join(emmaRootFolder, "emma.py")
        testProjectFolder = os.path.join(emmaRootFolder, "doc", "test_project")
        mapfilesFolder = os.path.join(testProjectFolder, "mapfiles")
        self.resultsFolder = os.path.join("..", "other_files", "test__test_project")
        self.memStatsFolder = os.path.join(self.resultsFolder, "memStats")

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

        projectName = "test_project"
        timeStampLength = len(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Ms%S"))
        reportFileExtension = ".csv"
        reportFileExtensionLength = len(reportFileExtension)
        imageSummaryFileNameFixPart = projectName + "_Image_Summary_"
        moduleSummaryFileNameFixPart = projectName + "_Module_Summary_"
        objectsInSectionsFileNameFixPart = projectName + "_Objects_in_Sections_"

        # Checking whether the expected report names are there and setting up the variables with their paths
        for file in os.listdir(self.memStatsFolder):
            if imageSummaryFileNameFixPart == file[:-(timeStampLength + reportFileExtensionLength)]:
                self.imageSummaryPath = os.path.join(self.memStatsFolder, file)
            elif moduleSummaryFileNameFixPart == file[:-(timeStampLength + reportFileExtensionLength)]:
                self.moduleSummaryPath = os.path.join(self.memStatsFolder, file)
            elif objectsInSectionsFileNameFixPart == file[:-(timeStampLength + reportFileExtensionLength)]:
                self.objectsInSectionsPath = os.path.join(self.memStatsFolder, file)
            else:
                self.assert_(False, "Unexpected file: " + os.path.join(self.memStatsFolder, file))

        # Setting up the variable with the expected column values
        self.expectedColumns = ['addrStartHex', 'addrEndHex', 'sizeHex', 'addrStartDec', 'addrEndDec',
                                'sizeDec', 'sizeHumanReadable', 'section', 'moduleName', 'configID',
                                'vasName', 'vasSectionName', 'memType', 'tag', 'category', 'DMA',
                                'mapfile', 'overlapFlag', 'containmentFlag', 'duplicateFlag',
                                'containgOthers', 'addrStartHexOriginal', 'addrEndHexOriginal',
                                'sizeHexOriginal', 'sizeDecOriginal']

    def tearDown(self):
        # Checking whether the result folder exists, deleting it if it does
        if os.path.isdir(self.resultsFolder):
            shutil.rmtree(self.resultsFolder)

    class ExpectedDataTypeData:
        def __init__(self, name, numberOfRows, totalSizeDec):
            self.name = name
            self.numberOfRows = numberOfRows
            self.totalSizeDec = totalSizeDec

    class ExpectedConfigIdData:
        def __init__(self, name, numberOfRows, listOfDataTypeData):
            self.name = name
            self.numerOfRows = numberOfRows
            self.listOfDataTypeData = listOfDataTypeData

    class ExpectedReportData:
        def __init__(self, numberOfRows, listOfColumns, listOfConfigIdData):
            self.numberOfRows = numberOfRows
            self.listOfColumns = listOfColumns
            self.listOfConfigIdData = listOfConfigIdData

    def checkDataTypeData(self, dataTypeData, expectedDataTypeData: ExpectedDataTypeData):
        dataTypeNumberOfRows, _ = dataTypeData.shape
        dataTypeTotalSizeDec = dataTypeData["sizeDec"].sum()

        # Checking the number of elements
        self.assertEqual(dataTypeNumberOfRows, expectedDataTypeData.numberOfRows)

        # Checking the total consumption
        self.assertEqual(dataTypeTotalSizeDec, expectedDataTypeData.totalSizeDec)

    def checkConfigIdData(self, configIdData, expectedConfigIdData: ExpectedConfigIdData):
        configIdNumberOfRows, _ = configIdData.shape

        # Checking the number of the elements
        self.assertEqual(configIdNumberOfRows, expectedConfigIdData.numerOfRows)

        # Checking the data types
        for expectedDataTypeData in expectedConfigIdData.listOfDataTypeData:
            dataTypeData = configIdData[configIdData.memType == expectedDataTypeData.name]
            self.checkDataTypeData(dataTypeData, expectedDataTypeData)

    def checkReport(self, reportData, expectedReportData: ExpectedReportData):
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


if "__main__" == __name__:
    unittest.main()
