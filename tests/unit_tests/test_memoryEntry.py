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
import collections

from pypiscout.SCout_Logger import Logger as sc

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import emma_libs.memoryEntry


class TestData:
    def __init__(self):
        self.configID = "MCU"
        self.mapfileName = "MapFile.map"
        self.addressStart = 0x1000
        self.addressLength = 0x100
        self.addressEnd = 0x1000 + 0x100 - 0x01
        self.sectionName = "SectionName"
        self.objectName = "ObjectName"
        self.memType = "INT_RAM"
        self.memTypeTag = "Tag"
        self.category = "MyCategory"
        self.vasName = "Vas"
        self.vasSectionName = "VasSectionName"

        self.compilerSpecificData = collections.OrderedDict()
        self.compilerSpecificData["DMA"] = (self.vasName is None)
        self.compilerSpecificData["vasName"] = self.vasName
        self.compilerSpecificData["vasSectionName"] = self.vasSectionName

        self.basicMemEntry = emma_libs.memoryEntry.MemEntry(configID=self.configID, mapfileName=self.mapfileName,
                                                            addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd,
                                                            sectionName=self.sectionName, objectName=self.objectName,
                                                            memType=self.memType, memTypeTag=self.memTypeTag, category=self.category,
                                                            compilerSpecificData=self.compilerSpecificData)


class MemEntryTestCase(unittest.TestCase, TestData):
    # pylint: disable=invalid-name, missing-docstring
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>(). It is not necessary to add a docstring for every unit test.

    def setUp(self):
        TestData.__init__(self)

        # Setting up the logger
        # This syntax will default init it and then change the settings with the __call__()
        # This is needed so that the unit tests can have different settings and not interfere with each other
        sc()(4, actionWarning=None, actionError=self.actionError)
        self.actionWarningWasCalled = False
        self.actionErrorWasCalled = False

    def actionWarning(self):
        self.actionWarningWasCalled = True

    def actionError(self):
        self.actionErrorWasCalled = True

    def test_constructorBasicCase(self):
        # Do not use named parameters here so that the order of parameters are also checked
        self.assertEqual(self.basicMemEntry.addressStart, self.addressStart)
        self.assertEqual(self.basicMemEntry.addressLength, self.addressLength)
        self.assertEqual(self.basicMemEntry.addressEnd(), self.addressEnd)
        self.assertEqual(self.basicMemEntry.addressStartHex(), hex(self.addressStart))
        self.assertEqual(self.basicMemEntry.addressLengthHex(), hex(self.addressLength))
        self.assertEqual(self.basicMemEntry.addressEndHex(), hex(self.addressEnd))
        self.assertEqual(self.basicMemEntry.memTypeTag, "Tag")
        self.assertEqual(self.basicMemEntry.compilerSpecificData["DMA"], (self.vasName is None))
        self.assertEqual(self.basicMemEntry.compilerSpecificData["vasName"], self.vasName)
        self.assertEqual(self.basicMemEntry.compilerSpecificData["vasSectionName"], self.vasSectionName)
        self.assertEqual(self.basicMemEntry.sectionName, self.sectionName)
        self.assertEqual(self.basicMemEntry.objectName, self.objectName)
        self.assertEqual(self.basicMemEntry.mapfile, self.mapfileName)
        self.assertEqual(self.basicMemEntry.configID, self.configID)
        self.assertEqual(self.basicMemEntry.memType, self.memType)
        self.assertEqual(self.basicMemEntry.category, self.category)
        self.assertEqual(self.basicMemEntry.overlapFlag, None)
        self.assertEqual(self.basicMemEntry.containmentFlag, None)
        self.assertEqual(self.basicMemEntry.duplicateFlag, None)
        self.assertEqual(self.basicMemEntry.containingOthersFlag, None)
        self.assertEqual(self.basicMemEntry.overlappingOthersFlag, None)
        self.assertEqual(self.basicMemEntry.addressStartOriginal, self.addressStart)
        self.assertEqual(self.basicMemEntry.addressLengthOriginal, self.addressLength)
        self.assertEqual(self.basicMemEntry.addressEndOriginal(), self.addressEnd)
        self.assertEqual(self.basicMemEntry.addressStartHexOriginal(), hex(self.addressStart))
        self.assertEqual(self.basicMemEntry.addressLengthHexOriginal(), hex(self.addressLength))
        self.assertEqual(self.basicMemEntry.addressEndHexOriginal(), hex(self.addressEnd))

    def test_constructorAddressLengthAndAddressEnd(self):
        # Modifying the self.addressEnd to make sure it is wrong
        self.addressEnd = self.addressStart + self.addressLength + 0x100
        entryWithLengthAndAddressEnd = emma_libs.memoryEntry.MemEntry(configID=self.configID, mapfileName=self.mapfileName,
                                                                      addressStart=self.addressStart, addressLength=self.addressLength, addressEnd=self.addressEnd,
                                                                      sectionName=self.sectionName, objectName=self.objectName,
                                                                      memType=self.memType, memTypeTag=self.memTypeTag, category=self.category,
                                                                      compilerSpecificData=self.compilerSpecificData)
        # We expect that only the addressLength will be used and the addressEnd will be recalculated based on this
        self.assertEqual(entryWithLengthAndAddressEnd.addressStart, self.addressStart)
        self.assertEqual(entryWithLengthAndAddressEnd.addressLength, self.addressLength)
        self.assertEqual(entryWithLengthAndAddressEnd.addressEnd(), (self.addressStart + self.addressLength - 1))

    def test_constructorNoAddressLengthNorAddressEnd(self):
        self.assertFalse(self.actionErrorWasCalled)
        entryWithoutLengthAndAddressEnd = emma_libs.memoryEntry.MemEntry(configID=self.configID, mapfileName=self.mapfileName,
                                                                         addressStart=self.addressStart, addressLength=None, addressEnd=None,
                                                                         sectionName=self.sectionName, objectName=self.objectName,
                                                                         memType=self.memType, memTypeTag=self.memTypeTag, category=self.category,
                                                                         compilerSpecificData=self.compilerSpecificData)
        self.assertTrue(self.actionErrorWasCalled)

    def test___setAddressesGivenEnd(self):
        entry = emma_libs.memoryEntry.MemEntry(configID=self.configID, mapfileName=self.mapfileName,
                                               addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd,
                                               sectionName=self.sectionName, objectName=self.objectName,
                                               memType=self.memType, memTypeTag=self.memTypeTag, category=self.category,
                                               compilerSpecificData=self.compilerSpecificData)
        self.assertEqual(entry.addressStart, self.addressStart)
        self.assertEqual(entry.addressLength, self.addressLength)
        self.assertEqual(entry.addressLengthHex(), hex(self.addressLength))
        self.assertEqual(entry.addressEnd(), self.addressEnd)
        self.assertEqual(entry.addressEndHex(), hex(self.addressEnd))

        EXTENSION = 0x1000
        self.addressEnd = self.addressEnd + EXTENSION
        self.addressLength = self.addressLength + EXTENSION
        entry.setAddressesGivenEnd(self.addressEnd)

        self.assertEqual(entry.addressStart, self.addressStart)
        self.assertEqual(entry.addressLength, self.addressLength)
        self.assertEqual(entry.addressLengthHex(), hex(self.addressLength))
        self.assertEqual(entry.addressEnd(), self.addressEnd)
        self.assertEqual(entry.addressEndHex(), hex(self.addressEnd))

    def test___setAddressesGivenLength(self):
        entry = emma_libs.memoryEntry.MemEntry(configID=self.configID, mapfileName=self.mapfileName,
                                               addressStart=self.addressStart, addressLength=self.addressLength, addressEnd=None,
                                               sectionName=self.sectionName, objectName=self.objectName,
                                               memType=self.memType, memTypeTag=self.memTypeTag, category=self.category,
                                               compilerSpecificData=self.compilerSpecificData)
        self.assertEqual(entry.addressStart, self.addressStart)
        self.assertEqual(entry.addressLength, self.addressLength)
        self.assertEqual(entry.addressLengthHex(), hex(self.addressLength))
        self.assertEqual(entry.addressEnd(), self.addressEnd)
        self.assertEqual(entry.addressEndHex(), hex(self.addressEnd))

        EXTENSION = 0x1000
        self.addressEnd = self.addressEnd + EXTENSION
        self.addressLength = self.addressLength + EXTENSION
        entry.setAddressesGivenLength(self.addressLength)

        self.assertEqual(entry.addressStart, self.addressStart)
        self.assertEqual(entry.addressLength, self.addressLength)
        self.assertEqual(entry.addressLengthHex(), hex(self.addressLength))
        self.assertEqual(entry.addressEnd(), self.addressEnd)
        self.assertEqual(entry.addressEndHex(), hex(self.addressEnd))

    def test_compilerSpecificDataWrongType(self):
        self.assertFalse(self.actionErrorWasCalled)
        otherMemEntry = emma_libs.memoryEntry.MemEntry(configID=self.configID, mapfileName=self.mapfileName,
                                                       addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd,
                                                       sectionName=self.sectionName, objectName=self.objectName,
                                                       memType=self.memType, memTypeTag=self.memTypeTag, category=self.category,
                                                       compilerSpecificData="This is obviously not a correct CompilerSpecificData here...")
        self.assertTrue(self.actionErrorWasCalled)

    def test_equalConfigID(self):
        otherMemEntry = emma_libs.memoryEntry.MemEntry(configID=self.configID, mapfileName=self.mapfileName,
                                                       addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd,
                                                       sectionName=self.sectionName, objectName=self.objectName,
                                                       memType=self.memType, memTypeTag=self.memTypeTag, category=self.category,
                                                       compilerSpecificData=self.compilerSpecificData)
        self.assertEqual(self.basicMemEntry.equalConfigID(otherMemEntry), True)
        otherMemEntry.configID = "ChangedConfigId"
        self.assertEqual(self.basicMemEntry.equalConfigID(otherMemEntry), False)

    def test___lt__(self):
        otherMemEntry = emma_libs.memoryEntry.MemEntry(configID=self.configID, mapfileName=self.mapfileName,
                                                       addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd,
                                                       sectionName=self.sectionName, objectName=self.objectName,
                                                       memType=self.memType, memTypeTag=self.memTypeTag, category=self.category,
                                                       compilerSpecificData=self.compilerSpecificData)
        self.assertEqual(self.basicMemEntry < otherMemEntry, False)
        self.assertEqual(self.basicMemEntry > otherMemEntry, False)
        otherMemEntry.addressStart += otherMemEntry.addressLength
        self.assertEqual(self.basicMemEntry < otherMemEntry, True)
        self.assertEqual(self.basicMemEntry > otherMemEntry, False)
        self.assertEqual(otherMemEntry < self.basicMemEntry, False)
        self.assertEqual(otherMemEntry > self.basicMemEntry, True)

    def test___calculateAddressEnd(self):
        self.assertEqual(emma_libs.memoryEntry.MemEntry._MemEntry__calculateAddressEnd(self.addressStart, self.addressLength), self.addressEnd)
        self.assertEqual(emma_libs.memoryEntry.MemEntry._MemEntry__calculateAddressEnd(self.addressStart, 0), self.addressStart)

    def test___eq__(self):
        with self.assertRaises(NotImplementedError):
            self.assertEqual(self.basicMemEntry, self.basicMemEntry)

    def test_setAddressesGivenEnd(self):
        # Basic case
        self.assertEqual(self.basicMemEntry.addressStart, self.addressStart)
        self.assertEqual(self.basicMemEntry.addressLength, self.addressLength)

        # End == Start
        self.basicMemEntry.setAddressesGivenEnd(self.addressStart)
        self.assertEqual(self.basicMemEntry.addressStart, self.addressStart)
        self.assertEqual(self.basicMemEntry.addressLength, 0)

        # Going back to the basic case
        self.basicMemEntry.setAddressesGivenEnd(self.addressEnd)
        self.assertEqual(self.basicMemEntry.addressStart, self.addressStart)
        self.assertEqual(self.basicMemEntry.addressLength, self.addressLength)

        # End < Start (We expect no change but a call to sc().error!)
        self.assertFalse(self.actionErrorWasCalled)
        self.basicMemEntry.setAddressesGivenEnd(self.addressStart - 1)
        self.assertTrue(self.actionErrorWasCalled)
        self.assertEqual(self.basicMemEntry.addressStart, self.addressStart)
        self.assertEqual(self.basicMemEntry.addressLength, self.addressLength)

    def test_setAddressGivenLength(self):
        # Basic case
        self.assertEqual(self.basicMemEntry.addressStart, self.addressStart)
        self.assertEqual(self.basicMemEntry.addressLength, self.addressLength)

        # Negative length (We expect no change but a call to sc().error!)
        self.assertFalse(self.actionErrorWasCalled)
        self.basicMemEntry.setAddressesGivenLength(-1)
        self.assertTrue(self.actionErrorWasCalled)
        self.assertEqual(self.basicMemEntry.addressStart, self.addressStart)
        self.assertEqual(self.basicMemEntry.addressLength, self.addressLength)


class MemEntryHandlerTestCase(unittest.TestCase):
    # pylint: disable=invalid-name, missing-docstring
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>(). It is not necessary to add a docstring for every unit test.

    def setUp(self):
        # Setting up the logger
        def exitProgam():
            sys.exit(-10)
        sc(4, None, exitProgam)

    def test_abstractness(self):
        with self.assertRaises(TypeError):
            memEntryHandler = emma_libs.memoryEntry.MemEntryHandler()


class SectionEntryTestCase(unittest.TestCase, TestData):
    # pylint: disable=invalid-name, missing-docstring
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>(). It is not necessary to add a docstring for every unit test.

    def setUp(self):
        TestData.__init__(self)

        # Setting up the logger
        # This syntax will default init it and then change the settings with the __call__()
        # This is needed so that the unit tests can have different settings and not interfere with each other
        sc()(4, actionWarning=None, actionError=self.actionError)
        self.actionWarningWasCalled = False
        self.actionErrorWasCalled = False

    def actionWarning(self):
        self.actionWarningWasCalled = True

    def actionError(self):
        self.actionErrorWasCalled = True

    def test_isEqual(self):
        self.assertTrue(emma_libs.memoryEntry.SectionEntry.isEqual(self.basicMemEntry, self.basicMemEntry))
        with self.assertRaises(TypeError):
            emma_libs.memoryEntry.SectionEntry.isEqual(self.basicMemEntry, "This is obviously not a MemEntry object!")

    def test_getName(self):
        name = emma_libs.memoryEntry.SectionEntry.getName(self.basicMemEntry)
        self.assertEqual(name, self.sectionName)


class ObjectEntryTestCase(unittest.TestCase, TestData):
    # pylint: disable=invalid-name, missing-docstring
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>(). It is not necessary to add a docstring for every unit test.

    def setUp(self):
        TestData.__init__(self)

        # Setting up the logger
        # This syntax will default init it and then change the settings with the __call__()
        # This is needed so that the unit tests can have different settings and not interfere with each other
        sc()(4, actionWarning=None, actionError=self.actionError)
        self.actionWarningWasCalled = False
        self.actionErrorWasCalled = False

    def actionWarning(self):
        self.actionWarningWasCalled = True

    def actionError(self):
        self.actionErrorWasCalled = True

    def test_isEqual(self):
        self.assertTrue(emma_libs.memoryEntry.ObjectEntry.isEqual(self.basicMemEntry, self.basicMemEntry))
        with self.assertRaises(TypeError):
            emma_libs.memoryEntry.ObjectEntry.isEqual(self.basicMemEntry, "This is obviously not a MemEntry object!")

    def test_getName(self):
        name = emma_libs.memoryEntry.ObjectEntry.getName(self.basicMemEntry)
        self.assertEqual(name, (self.sectionName + "::" + self.objectName))


if __name__ == "__main__":
    unittest.main()
