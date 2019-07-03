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

sys.path.append(os.path.join(sys.path[0], "..", ".."))

import emma_libs.memoryEntry


class MemEntryTestCase(unittest.TestCase):
    def setUp(self):
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

    def test_ConstructorBasicCase(self):
        # Do not use named parameters here so that the order of parameters are also checked
        basicEntry = emma_libs.memoryEntry.MemEntry(self.tag, self.vasName, self.vasSectionName, self.section,
                                                    self.moduleName, self.mapfileName, self.configID, self.memType,
                                                    self.category, self.addressStart, self.addressLength, None)
        self.assertEqual(basicEntry.addressStart, self.addressStart)
        self.assertEqual(basicEntry.addressLength, self.addressLength)
        self.assertEqual(basicEntry.addressEnd, self.addressEnd)
        self.assertEqual(basicEntry.addressStartHex, hex(self.addressStart))
        self.assertEqual(basicEntry.addressLengthHex, hex(self.addressLength))
        self.assertEqual(basicEntry.addressEndHex, hex(self.addressEnd))
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
        self.assertEqual(basicEntry.addressStartOriginal, hex(self.addressStart))
        self.assertEqual(basicEntry.addressLengthOriginal, self.addressLength)
        self.assertEqual(basicEntry.addressLengthHexOriginal, hex(self.addressLength))
        self.assertEqual(basicEntry.addressEndOriginal, hex(self.addressEnd))

    def test_ConstructorDmaEntry(self):
        # Testing the creation of a DMA entry
        entryWithDma = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=None, vasSectionName=self.vasSectionName,
                                                      section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                      configID=self.configID, memType=self.memType, category=self.category,
                                                      addressStart=self.addressStart, addressLength=self.addressLength,
                                                      addressEnd=None)
        self.assertEqual(entryWithDma.dma, True)

    def test_ConstructorNoAddressLengthNorAddressEnd(self):
        # Testing the creation of a DMA entry
        with self.assertRaises(SystemExit) as contextManager:
            entryWithoutLengthAndAddressEnd = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                                                             section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                                                             configID=self.configID, memType=self.memType, category=self.category,
                                                                             addressStart=self.addressStart, addressLength=None,
                                                                             addressEnd=None)
        self.assertEqual(contextManager.exception.code, -10)

    def test___setAddressesGivenEnd(self):
        entry = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                               section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                               configID=self.configID, memType=self.memType, category=self.category,
                                               addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)
        self.assertEqual(entry.addressStart, self.addressStart)
        self.assertEqual(entry.addressLength, self.addressLength)
        self.assertEqual(entry.addressLengthHex, hex(self.addressLength))
        self.assertEqual(entry.addressEnd, self.addressEnd)
        self.assertEqual(entry.addressEndHex, hex(self.addressEnd))

        extension = 0x1000
        self.addressEnd = self.addressEnd + extension
        self.addressLength = self.addressLength + extension
        entry._MemEntry__setAddressesGivenEnd(self.addressEnd)

        self.assertEqual(entry.addressStart, self.addressStart)
        self.assertEqual(entry.addressLength, self.addressLength)
        self.assertEqual(entry.addressLengthHex, hex(self.addressLength))
        self.assertEqual(entry.addressEnd, self.addressEnd)
        self.assertEqual(entry.addressEndHex, hex(self.addressEnd))

    def test___setAddressesGivenLength(self):
        entry = emma_libs.memoryEntry.MemEntry(tag=self.tag, vasName=self.vasName, vasSectionName=self.vasSectionName,
                                               section=self.section, moduleName=self.moduleName, mapfileName=self.mapfileName,
                                               configID=self.configID, memType=self.memType, category=self.category,
                                               addressStart=self.addressStart, addressLength=None, addressEnd=self.addressEnd)
        self.assertEqual(entry.addressStart, self.addressStart)
        self.assertEqual(entry.addressLength, self.addressLength)
        self.assertEqual(entry.addressLengthHex, hex(self.addressLength))
        self.assertEqual(entry.addressEnd, self.addressEnd)
        self.assertEqual(entry.addressEndHex, hex(self.addressEnd))

        extension = 0x1000
        self.addressEnd = self.addressEnd + extension
        self.addressLength = self.addressLength + extension
        entry._MemEntry__setAddressesGivenLength(self.addressLength)

        self.assertEqual(entry.addressStart, self.addressStart)
        self.assertEqual(entry.addressLength, self.addressLength)
        self.assertEqual(entry.addressLengthHex, hex(self.addressLength))
        self.assertEqual(entry.addressEnd, self.addressEnd)
        self.assertEqual(entry.addressEndHex, hex(self.addressEnd))

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

# TODO Implement these... (AGK)
"""
class SectionEntryTestCase(unittest.TestCase):
    def test_constructor(self):
        raise NotImplementedError

    def test___eq__(self):
        raise NotImplementedError

    def test___hash__(self):
        raise NotImplementedError


class ObjectEntryTestCase(unittest.TestCase):
    def test_constructor(self):
        raise NotImplementedError

    def test___eq__(self):
        raise NotImplementedError

    def test___hash__(self):
        raise NotImplementedError
"""

if __name__ == '__main__':
    unittest.main()
