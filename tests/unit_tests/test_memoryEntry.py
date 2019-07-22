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

import emma_libs.memoryEntry


class MemEntryTestCase(unittest.TestCase):
    def setUp(self):
        # Setting up the logger
        # This syntax will default init it and then change the settings with the __call__()
        # This is needed so that the unit tests can have different settings and not interfere with each other
        sc()(4, actionWarning=None, actionError=self.exitProgam)

        self.tag = "Tag"
        self.vasName = "Vas"
        self.vasSectionName = "VasSectionName"
        self.section = "SectionName"
        self.moduleName = "ModuleName"
        self.mapfileName = "MapFile.map"
        self.configID = "MCU"
        self.memType = "INT_RAM"
        self.category = "MyCategory"
        self.addressStart = 0x1000
        self.addressLength = 0x100
        self.addressEnd = 0x1000 + 0x100 - 0x01

    def exitProgam(self):
        sys.exit(-10)

    def test_constructorBasicCase(self):
        # Do not use named parameters here so that the order of parameters are also checked
        basicEntry = emma_libs.memoryEntry.MemEntry(self.vasName, self.vasSectionName, self.section,
                                                    self.moduleName, self.mapfileName, self.configID,
                                                    self.addressStart, self.tag, self.memType,
                                                    self.category, self.addressLength, None)
        self.assertEqual(basicEntry.addressStart, self.addressStart)
        self.assertEqual(basicEntry.addressLength, self.addressLength)
        self.assertEqual(basicEntry.addressEnd(), self.addressEnd)
        self.assertEqual(basicEntry.addressStartHex(), hex(self.addressStart))
        self.assertEqual(basicEntry.addressLengthHex(), hex(self.addressLength))
        self.assertEqual(basicEntry.addressEndHex(), hex(self.addressEnd))
        self.assertEqual(basicEntry.memTypeTag, "Tag")
        self.assertEqual(basicEntry.vasName, self.vasName)
        self.assertEqual(basicEntry.vasSectionName, self.vasSectionName)
        self.assertEqual(basicEntry.dma, (self.vasName is None))
        self.assertEqual(basicEntry.section, self.section)
        self.assertEqual(basicEntry.moduleName, self.moduleName)
        self.assertEqual(basicEntry.mapfile, self.mapfileName)
        self.assertEqual(basicEntry.configID, self.configID)
        self.assertEqual(basicEntry.memType, self.memType)
        self.assertEqual(basicEntry.category, self.category)
        self.assertEqual(basicEntry.overlapFlag, None)
        self.assertEqual(basicEntry.containmentFlag, None)
        self.assertEqual(basicEntry.duplicateFlag, None)
        self.assertEqual(basicEntry.containingOthersFlag, None)
        self.assertEqual(basicEntry.overlappingOthersFlag, None)
        self.assertEqual(basicEntry.addressStartOriginal, self.addressStart)
        self.assertEqual(basicEntry.addressLengthOriginal, self.addressLength)
        self.assertEqual(basicEntry.addressEndOriginal(), self.addressEnd)
        self.assertEqual(basicEntry.addressStartHexOriginal(), hex(self.addressStart))
        self.assertEqual(basicEntry.addressLengthHexOriginal(), hex(self.addressLength))
        self.assertEqual(basicEntry.addressEndHexOriginal(), hex(self.addressEnd))

    def test_constructorAddressLengthAndAddressEnd(self):
        # Modifying the self.addressEnd to make sure it is wrong
        self.addressEnd = self.addressStart + self.addressLength + 0x100
        entryWithLengthAndAddressEnd = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName,
                                                                      vasSectionName=self.vasSectionName,
                                                                      section=self.section,
                                                                      moduleName=self.moduleName,
                                                                      mapfileName=self.mapfileName,
                                                                      configID=self.configID, memType=self.memType,
                                                                      category=self.category,
                                                                      addressStart=self.addressStart,
                                                                      addressLength=self.addressLength,
                                                                      addressEnd=self.addressEnd)
        # We expect that only the addressLength will be used and the addressEnd will be recalculated based on this
        self.assertEqual(entryWithLengthAndAddressEnd.addressStart, self.addressStart)
        self.assertEqual(entryWithLengthAndAddressEnd.addressLength, self.addressLength)
        self.assertEqual(entryWithLengthAndAddressEnd.addressEnd(), (self.addressStart + self.addressLength - 1))

    def test_constructorDmaEntry(self):
        # Testing the creation of a DMA entry
        entryWithDma = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=None, vasSectionName=self.vasSectionName,
                                                      section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                      configID=self.configID, memType=self.memType, category=self.category,
                                                      addressStart=self.addressStart, addressLength=self.addressLength,
                                                      addressEnd=None)
        self.assertEqual(entryWithDma.dma, True)

    def test_constructorNoAddressLengthNorAddressEnd(self):
        # Testing the creation of a DMA entry
        with self.assertRaises(SystemExit) as contextManager:
            entryWithoutLengthAndAddressEnd = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName,
                                                                             vasSectionName=self.vasSectionName,
                                                                             section=self.section, moduleName=self.moduleName,
                                                                             mapfileName=self.mapfileName,
                                                                             configID=self.configID, memType=self.memType,
                                                                             category=self.category, addressStart=self.addressStart,
                                                                             addressLength=None, addressEnd=None)
        self.assertEqual(contextManager.exception.code, -10)

    def test___setAddressesGivenEnd(self):
        entry = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                               section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                               configID=self.configID, memType=self.memType, category=self.category,
                                               addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)
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
        entry = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                               section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                               configID=self.configID, memType=self.memType, category=self.category,
                                               addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)
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

    def test_equalConfigID(self):
        entryFirst = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                    section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                    configID=self.configID, memType=self.memType, category=self.category,
                                                    addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)
        entrySecond = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                     section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                     configID=self.configID, memType=self.memType, category=self.category,
                                                     addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)
        self.assertEqual(entryFirst.equalConfigID(entrySecond), True)
        entrySecond.configID = "ChangedConfigId"
        self.assertEqual(entryFirst.equalConfigID(entrySecond), False)

    def test___lt__(self):
        entryFirst = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                    section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                    configID=self.configID, memType=self.memType, category=self.category,
                                                    addressStart=self.addressStart, addressLength=self.addressLength, addressEnd=None)
        entrySecond = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                     section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                     configID=self.configID, memType=self.memType, category=self.category,
                                                     addressStart=self.addressStart, addressLength=self.addressLength, addressEnd=None)
        self.assertEqual(entryFirst < entrySecond, False)
        self.assertEqual(entryFirst > entrySecond, False)
        entrySecond.addressStart += entrySecond.addressLength
        self.assertEqual(entryFirst < entrySecond, True)
        self.assertEqual(entryFirst > entrySecond, False)
        self.assertEqual(entrySecond < entryFirst, False)
        self.assertEqual(entrySecond > entryFirst, True)

    def test___calculateAddressEnd(self):
        self.assertEqual(emma_libs.memoryEntry.MemEntry._MemEntry__calculateAddressEnd(self.addressStart, self.addressLength), self.addressEnd)
        self.assertEqual(emma_libs.memoryEntry.MemEntry._MemEntry__calculateAddressEnd(self.addressStart, 0), self.addressStart)

    def test___eq__(self):
        memEntry = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                  section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                  configID=self.configID, memType=self.memType, category=self.category,
                                                  addressStart=self.addressStart, addressLength=self.addressLength, addressEnd=None)
        with self.assertRaises(NotImplementedError):
            self.assertEqual(memEntry, memEntry)

    def test_setAddressesGivenEnd(self):
        # Basic case
        memEntry = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                  section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                  configID=self.configID, memType=self.memType, category=self.category,
                                                  addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)
        self.assertEqual(memEntry.addressStart, self.addressStart)
        self.assertEqual(memEntry.addressLength, self.addressLength)

        # End == Start
        memEntry.setAddressesGivenEnd(self.addressStart)
        self.assertEqual(memEntry.addressStart, self.addressStart)
        self.assertEqual(memEntry.addressLength, 0)

        # Going back to the basic case
        memEntry.setAddressesGivenEnd(self.addressEnd)
        self.assertEqual(memEntry.addressStart, self.addressStart)
        self.assertEqual(memEntry.addressLength, self.addressLength)

        # End < Start (We expect no change!)
        with self.assertRaises(SystemExit) as contextManager:
            memEntry.setAddressesGivenEnd(self.addressStart - 1)
        self.assertEqual(contextManager.exception.code, -10)
        self.assertEqual(memEntry.addressStart, self.addressStart)
        self.assertEqual(memEntry.addressLength, self.addressLength)

    def test_setAddressGivenLength(self):
        # Basic case
        memEntry = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                  section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                  configID=self.configID, memType=self.memType, category=self.category,
                                                  addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)
        self.assertEqual(memEntry.addressStart, self.addressStart)
        self.assertEqual(memEntry.addressLength, self.addressLength)

        # Negative length (We expect no change!)
        with self.assertRaises(SystemExit) as contextManager:
            memEntry.setAddressesGivenLength(-1)
        self.assertEqual(contextManager.exception.code, -10)
        self.assertEqual(memEntry.addressStart, self.addressStart)
        self.assertEqual(memEntry.addressLength, self.addressLength)


class MemEntryHandlerTestCase(unittest.TestCase):
    def setUp(self):
        # Setting up the logger
        def exitProgam():
            sys.exit(-10)
        sc(4, None, exitProgam)

    def test_abstractness(self):
        with self.assertRaises(TypeError):
            memEntryHandler = emma_libs.memoryEntry.MemEntryHandler()


class SectionEntryTestCase(unittest.TestCase):
    def setUp(self):
        # Setting up the logger
        def exitProgam():
            sys.exit(-10)
        sc(4, None, exitProgam)

        self.tag = "Tag"
        self.vasName = "Vas"
        self.vasSectionName = "VasSectionName"
        self.section = "SectionName"
        self.moduleName = "ModuleName"
        self.mapfileName = "MapFile.map"
        self.configID = "MCU"
        self.memType = "INT_RAM"
        self.category = "MyCategory"
        self.addressStart = 0x1000
        self.addressLength = 0x100
        self.addressEnd = 0x1000 + 0x100 - 0x01

        self.memEntry = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                       section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                       configID=self.configID, memType=self.memType, category=self.category,
                                                       addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)

    def test_isEqual(self):
        self.assertTrue(emma_libs.memoryEntry.SectionEntry.isEqual(self.memEntry, self.memEntry))
        with self.assertRaises(NotImplementedError):
            emma_libs.memoryEntry.SectionEntry.isEqual(self.memEntry, "This is obviously not a MemEntry object!")

    def test_getName(self):
        name = emma_libs.memoryEntry.SectionEntry.getName(self.memEntry)
        self.assertEqual(name, self.section)


class ObjectEntryTestCase(unittest.TestCase):
    def setUp(self):
        # Setting up the logger
        def exitProgam():
            sys.exit(-10)
        sc(4, None, exitProgam)

        self.tag = "Tag"
        self.vasName = "Vas"
        self.vasSectionName = "VasSectionName"
        self.section = "SectionName"
        self.moduleName = "ModuleName"
        self.mapfileName = "MapFile.map"
        self.configID = "MCU"
        self.memType = "INT_RAM"
        self.category = "MyCategory"
        self.addressStart = 0x1000
        self.addressLength = 0x100
        self.addressEnd = 0x1000 + 0x100 - 0x01

        self.memEntry = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                       section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                       configID=self.configID, memType=self.memType, category=self.category,
                                                       addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)

    def test_isEqual(self):
        self.assertTrue(emma_libs.memoryEntry.ObjectEntry.isEqual(self.memEntry, self.memEntry))
        with self.assertRaises(NotImplementedError):
            emma_libs.memoryEntry.ObjectEntry.isEqual(self.memEntry, "This is obviously not a MemEntry object!")

    def test_getName(self):
        name = emma_libs.memoryEntry.ObjectEntry.getName(self.memEntry)
        self.assertEqual(name, (self.section + "::" + self.moduleName))


if "__main__" == __name__:
    unittest.main()
