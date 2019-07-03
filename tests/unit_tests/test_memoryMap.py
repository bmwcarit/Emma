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

from shared_libs.stringConstants import *
import emma_libs.memoryEntry
import emma_libs.memoryMap


class MemEntryData:
    """
    This class contains two member variables, the addressStart and the addressEnd.
    The purpose of it is that from the objects of this class we can generate MemEntry Objects that
    only differ from each other by the address and length values.
    The reason why not the addressLength is used here that the specific cases can be easier defined with the addressEnd.
    The MemEntry objects can be generated with the CreateMemEntryObjects() function.
    """

    def __init__(self, addressStart, addressEnd):
        self.addressStart = addressStart
        self.addressEnd = addressEnd


def CreateMemEntryObjects(sectionDataContainer, objectDataContainer):
    """
    Function to create a two list as input for the testing of the caluclateObjectsInSections() function.
    :param sectionDataContainer: List of MemEntry objects from which the sectionContainer elements will be created.
    :param objectDataContainer: List of MemEntry objects from which the objectContainer elements will be created.
    :return: sectionContainer, objectContainer lists that can be processed with the caluclateObjectsInSections() function.
    """
    sectionContainer = []
    objectContainer = []
    for element in sectionDataContainer:
        sectionContainer.append(emma_libs.memoryEntry.MemEntry(tag="", vasName="", section=".text", moduleName="",
                                                               mapfileName="", configID="MCU", memType="INT_FLASH",
                                                               category="<Unspecified>",
                                                               addressStart=element.addressStart,
                                                               addressLength=None, addressEnd=element.addressEnd,
                                                               vasSectionName=None))
    for element in objectDataContainer:
        objectContainer.append(
            emma_libs.memoryEntry.MemEntry(tag="", vasName="", section=".text", moduleName=".object",
                                           mapfileName="", configID="MCU", memType="INT_FLASH",
                                           category="<Unspecified>", addressStart=element.addressStart,
                                           addressLength=None, addressEnd=element.addressEnd, vasSectionName=None))
    return sectionContainer, objectContainer


class CalculateObjectsInSectionsTestCase(unittest.TestCase):
    def CheckSectionNonChangingData(self, sectionToCheck, sourceSection):
        self.assertEqual(sectionToCheck.memTypeTag, sourceSection.memTypeTag)
        self.assertEqual(sectionToCheck.vasName, sourceSection.vasName)
        self.assertEqual(sectionToCheck.vasSectionName, sourceSection.vasSectionName)
        self.assertEqual(sectionToCheck.dma, sourceSection.dma)
        self.assertEqual(sectionToCheck.section, sourceSection.section)
        self.assertEqual(sectionToCheck.mapfile, sourceSection.mapfile)
        self.assertEqual(sectionToCheck.configID, sourceSection.configID)
        self.assertEqual(sectionToCheck.memType, sourceSection.memType)
        self.assertEqual(sectionToCheck.category, sourceSection.category)
        self.assertEqual(sectionToCheck.overlapFlag, sourceSection.overlapFlag)
        self.assertEqual(sectionToCheck.containmentFlag, sourceSection.containmentFlag)
        self.assertEqual(sectionToCheck.duplicateFlag, sourceSection.duplicateFlag)
        self.assertEqual(sectionToCheck.containingOthersFlag, sourceSection.containingOthersFlag)
        self.assertEqual(sectionToCheck.overlappingOthersFlag, sourceSection.overlappingOthersFlag)
        self.assertEqual(sectionToCheck.addressStartOriginal, sourceSection.addressStartOriginal)
        self.assertEqual(sectionToCheck.addressLengthOriginal, sourceSection.addressLengthOriginal)
        self.assertEqual(sectionToCheck.addressLengthHexOriginal, sourceSection.addressLengthHexOriginal)
        self.assertEqual(sectionToCheck.addressEndOriginal, sourceSection.addressEndOriginal)

    def CheckSectionEntry(self, sectionEntry, sourceSection):
        self.CheckSectionNonChangingData(sectionEntry, sourceSection)
        self.assertEqual(sectionEntry.addressStart, sourceSection.addressStart)
        self.assertEqual(sectionEntry.addressLength, 0)
        self.assertEqual(sectionEntry.addressEnd, sourceSection.addressEnd)
        self.assertEqual(sectionEntry.addressStartHex, hex(sourceSection.addressStart))
        self.assertEqual(sectionEntry.addressLengthHex, hex(0))
        self.assertEqual(sectionEntry.addressEndHex, hex(sourceSection.addressEnd))
        self.assertEqual(sectionEntry.moduleName, OBJECTS_IN_SECTIONS_SECTION_ENTRY)

    def CheckSectionReserve(self, sectionReserve, sourceSection, expectedAddressStart, expectedAddressEnd):
        self.CheckSectionNonChangingData(sectionReserve, sourceSection)
        self.assertEqual(sectionReserve.addressStart, expectedAddressStart)
        self.assertEqual(sectionReserve.addressLength, (expectedAddressEnd - expectedAddressStart + 1))
        self.assertEqual(sectionReserve.addressEnd, expectedAddressEnd)
        self.assertEqual(sectionReserve.addressStartHex, hex(expectedAddressStart))
        self.assertEqual(sectionReserve.addressLengthHex, hex((expectedAddressEnd - expectedAddressStart + 1)))
        self.assertEqual(sectionReserve.addressEndHex, hex(expectedAddressEnd))
        self.assertEqual(sectionReserve.moduleName, OBJECTS_IN_SECTIONS_SECTION_RESERVE)

    def test_SingleSection(self):
        addressStart = 0x0100
        addressEnd = 0x0100
        sectionContainer, objectContainer = CreateMemEntryObjects([MemEntryData(addressStart, addressEnd)], [])
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)
        # Check whether the SectionEntry was created properly
        self.CheckSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the SectionReserve was created properly
        self.CheckSectionReserve(objectsInSections[1], sectionContainer[0], addressStart, addressEnd)

"""
TestFunktion(0,
             [TestElement(0x0100, 0x01FF)],
             [TestElement(0x00F0, 0x01FF)])

TestFunktion(1,
             [TestElement(0x0100, 0x01FF)],
             [TestElement(0x0100, 0x0110)])

TestFunktion(2,
             [TestElement(0x0100, 0x01FF)],
             [TestElement(0x0110, 0x0120)])

TestFunktion(3,
             [TestElement(0x0100, 0x01FF)],
             [TestElement(0x01F0, 0x0210)])

TestFunktion(4,
             [TestElement(0x0100, 0x01FF)],
             [TestElement(0x0210, 0x0220)])

TestFunktion(5,
             [TestElement(0x0100, 0x01FF)],
             [TestElement(0x0080, 0x0085), TestElement(0x0090, 0x0110), TestElement(0x0150, 0x0180), TestElement(0x01F0, 0x001FE), TestElement(0x01FF, 0x01FF), TestElement(0x0210, 0x0220)])

TestFunktion(6,
             [TestElement(0x0100, 0x0124), TestElement(0x0125, 0x0149), TestElement(0x0150, 0x0174),TestElement(0x0175, 0x01FF)],
             [TestElement(0x0080, 0x0085), TestElement(0x0090, 0x0110), TestElement(0x0150, 0x0180), TestElement(0x01F0, 0x001FE), TestElement(0x01FF, 0x01FF), TestElement(0x0210, 0x0220)])
"""


if "__main__" == __name__:
    unittest.main()
