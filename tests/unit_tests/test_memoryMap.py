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
    The purpose of this class is that from its objects we can generate MemEntry Objects that
    only differ from each other by the address and length values.
    If the addressEnd is None, then we an entry with zero length will be created.
    In this case the addressEnd needs to have the same value as addressStart.
    The reason why not the addressLength is used here that the specific cases can be easier defined with the addressEnd.
    The MemEntry objects can be generated with the createMemEntryObjects() function from these objects.
    """

    def __init__(self, addressStart, addressEnd):
        self.addressStart = addressStart
        self.addressEnd = addressEnd


def createMemEntryObjects(sectionDataContainer, objectDataContainer):
    """
    Function to create a two list as input for the testing of the caluclateObjectsInSections() function.
    :param sectionDataContainer: List of MemEntry objects from which the sectionContainer elements will be created.
    :param objectDataContainer: List of MemEntry objects from which the objectContainer elements will be created.
    :return: sectionContainer, objectContainer lists that can be processed with the caluclateObjectsInSections() function.
    """

    sectionContainer = []
    for element in sectionDataContainer:
        sectionContainer.append(emma_libs.memoryEntry.SectionEntry(tag="", vasName="", section=".text", moduleName="",
                                                                   mapfileName="", configID="MCU", memType="INT_FLASH",
                                                                   category="<Unspecified>", vasSectionName=None,
                                                                   addressStart=element.addressStart,
                                                                   addressLength=0 if element.addressEnd is None else None,
                                                                   addressEnd=element.addressEnd))
    objectContainer = []
    for element in objectDataContainer:
        objectContainer.append(emma_libs.memoryEntry.ObjectEntry(tag="", vasName="", section=".text", moduleName=".object",
                                                                 mapfileName="", configID="MCU", memType="INT_FLASH",
                                                                 category="<Unspecified>", vasSectionName=None,
                                                                 addressStart=element.addressStart,
                                                                 addressLength=0 if element.addressEnd is None else None,
                                                                 addressEnd=element.addressEnd))
    return sectionContainer, objectContainer


class CalculateObjectsInSectionsTestCase(unittest.TestCase):
    def checkSectionNonChangingData(self, sectionToCheck, sourceSection):
        """
        Checks the data of a section that shall never be changed during caluclateObjectsInSections().
        :param sectionToCheck: This is the section that was calculated.
        :param sourceSection: This is the section from which the sectionToCheck was calculated.
        :return: None
        """
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

    def checkSectionEntry(self, sectionEntry, sourceSection):
        """
        Checks a section entry, whether it was created correctly.
        :param sectionEntry: This is the section entry that was calculated.
        :param sourceSection: This is the section from which the section entry was calculated
        :return: None
        """
        self.checkSectionNonChangingData(sectionEntry, sourceSection)
        self.assertEqual(sectionEntry.addressStart, sourceSection.addressStart)
        self.assertEqual(sectionEntry.addressLength, 0)
        self.assertEqual(sectionEntry.addressEnd, sourceSection.addressEnd)
        self.assertEqual(sectionEntry.addressStartHex, hex(sourceSection.addressStart))
        self.assertEqual(sectionEntry.addressLengthHex, hex(0))
        self.assertEqual(sectionEntry.addressEndHex, hex(sourceSection.addressEnd))
        self.assertEqual(sectionEntry.moduleName, OBJECTS_IN_SECTIONS_SECTION_ENTRY)

    def checkSectionReserve(self, sectionReserve, sourceSection, expectedAddressStart, expectedAddressEnd):
        """
        Checks a section reserve, whether it was created correctly.
        :param sectionReserve: This is the section reserve that was calculated.
        :param sourceSection: This is the section from which the section reserve was calculated.
        :param expectedAddressStart: The AddressStart value that the section reserve must have.
        :param expectedAddressEnd: The AddressEnd value that the section reserve must have.
        :return: None
        """
        self.checkSectionNonChangingData(sectionReserve, sourceSection)
        self.assertEqual(sectionReserve.addressStart, expectedAddressStart)
        self.assertEqual(sectionReserve.addressLength, (expectedAddressEnd - expectedAddressStart + 1))
        self.assertEqual(sectionReserve.addressEnd, expectedAddressEnd)
        self.assertEqual(sectionReserve.addressStartHex, hex(expectedAddressStart))
        self.assertEqual(sectionReserve.addressLengthHex, hex((expectedAddressEnd - expectedAddressStart + 1)))
        self.assertEqual(sectionReserve.addressEndHex, hex(expectedAddressEnd))
        self.assertEqual(sectionReserve.moduleName, OBJECTS_IN_SECTIONS_SECTION_RESERVE)

    def test_singleSection(self):
        """
        S  |---|
        O
        """
        # Creating the sections and objects for the test
        addressStart = 0x0100
        addressEnd = 0x01FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(addressStart, addressEnd)], [])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], addressStart, addressEnd)

    def test_singleSectionWithZeroObjects(self):
        """
        S    |-------|
        O  | |   |   | |
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0200
        sectionAddressEnd = 0x03FF
        firstObjectAddressStart = 0x00100
        secondObjectAddressStart = 0x0200
        thirdObjectAddressStart = 0x0300
        fourthObjectAddressStart = 0x03FF
        fifthObjectAddressStart = 0x0500
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)],
                                                                  [MemEntryData(firstObjectAddressStart, None),
                                                                   MemEntryData(secondObjectAddressStart, None),
                                                                   MemEntryData(thirdObjectAddressStart, None),
                                                                   MemEntryData(fourthObjectAddressStart, None),
                                                                   MemEntryData(fifthObjectAddressStart, None)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: firstObject +
        #                                       sectionEntry +
        #                                       secondObject +
        #                                       thirdObject +
        #                                       fourthObject +
        #                                       sectionReserve +
        #                                       fifthObject
        self.assertEqual(len(objectsInSections), 7)
        # Check whether the firstObject was created properly
        self.assertEqual(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[2], sectionContainer[0], sectionAddressStart, sectionAddressEnd)
        # Check whether the secondObject was created properly
        self.assertEqual(objectsInSections[3], objectContainer[1])
        # Check whether the thirdObject was created properly
        self.assertEqual(objectsInSections[4], objectContainer[2])
        # Check whether the fourthObject was created properly
        self.assertEqual(objectsInSections[5], objectContainer[3])
        # Check whether the fifthObject was created properly
        self.assertEqual(objectsInSections[6], objectContainer[4])

    def test_multipleSectionsAndObjectsWithZeroLengths(self):
        """
        S     | | | | |
        O   |   | |---|
        """
        # Creating the sections and objects for the test
        firstSectionAddressStart = 0x0150
        secondSectionAddressStart = 0x0200
        thirdSectionAddressStart = 0x0300
        fourthSectionAddressStart = 0x0350
        fifthSectionAddressStart = 0x03FF
        firstObjectAddressStart = 0x0100
        secondObjectAddressStart = 0x0200
        thirdObjectAddressStart = 0x0300
        thirdObjectAddressEnd = 0x03FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(firstSectionAddressStart, None),
                                                                   MemEntryData(secondSectionAddressStart, None),
                                                                   MemEntryData(thirdSectionAddressStart, None),
                                                                   MemEntryData(fourthSectionAddressStart, None),
                                                                   MemEntryData(fifthSectionAddressStart, None)],
                                                                  [MemEntryData(firstObjectAddressStart, None),
                                                                   MemEntryData(secondObjectAddressStart, None),
                                                                   MemEntryData(thirdObjectAddressStart, thirdObjectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: firstObject +
        #                                       firstSectionEntry +
        #                                       secondSectionEntry +
        #                                       secondObject +
        #                                       thirdSectionEntry +
        #                                       thirdObject +
        #                                       fourthSectionEntry +
        #                                       fifthSectionEntry
        self.assertEqual(len(objectsInSections), 8)
        # Check whether the firstObject was created properly
        self.assertEqual(objectsInSections[0], objectContainer[0])
        # Check whether the firstSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the secondSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[2], sectionContainer[1])
        # Check whether the secondObject was created properly
        self.assertEqual(objectsInSections[3], objectContainer[1])
        # Check whether the thirdSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[4], sectionContainer[2])
        # Check whether the thirdObject was created properly
        self.assertEqual(objectsInSections[5], objectContainer[2])
        # Check whether the fourthSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[6], sectionContainer[3])
        # Check whether the fifthSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[7], sectionContainer[4])

    def test_multipleSectionsAndObjectsWithContainmentFlag(self):
        """
        S  |--| |--|
        O    |---|
        """
        # Creating the sections and objects for the test
        firstSectionAddressStart = 0x0100
        firstSectionAddressEnd = 0x01FF
        secondSectionAddressStart = 0x0300
        secondSectionAddressEnd = 0x03FF
        objectAddressStart = 0x0150
        objectAddressEnd = 0x034F
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(firstSectionAddressStart, firstSectionAddressEnd),
                                                                   MemEntryData(secondSectionAddressStart, secondSectionAddressEnd)],
                                                                  [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Editing the sections: switching the the containmentFlags on
        sectionContainer[0].containmentFlag = True
        sectionContainer[1].containmentFlag = True
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: firstSectionEntry +
        #                                       object +
        #                                       secondSectionEntry
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the firstSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[1], objectContainer[0])
        # Check whether the secondSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[2], sectionContainer[1])

    def test_sectionFullWithSingleObject(self):
        """
        S  |----|
        O  |----|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0200
        sectionAddressEnd = 0x02FF
        objectAddressStart = 0x0200
        objectAddressEnd = 0x02FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + object
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[1], objectContainer[0])

    def test_sectionFullWithTwoObjects(self):
        """
        S  |-----|
        O  |--|--|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0400
        sectionAddressEnd = 0x05FF
        firstObjectAddressStart = 0x0400
        firstObjectAddressEnd = 0x04FF
        secondObjectAddressStart = 0x0500
        secondObjectAddressEnd = 0x05FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)],
                                                                  [MemEntryData(firstObjectAddressStart, firstObjectAddressEnd), MemEntryData(secondObjectAddressStart, secondObjectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + firstObject + secondObject
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the firstObject was created properly
        self.assertEqual(objectsInSections[1], objectContainer[0])
        # Check whether the secondObject was created properly
        self.assertEqual(objectsInSections[2], objectContainer[1])

    def test_sectionFullWithOverlappingSingleObjectAtStart(self):
        """
        S     |-----|
        O  |--------|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0800
        sectionAddressEnd = 0x09FF
        objectAddressStart = 0x0700
        objectAddressEnd = 0x09FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: object + sectionEntry
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])

    def test_sectionFullWithOverlappingSingleObjectAtEnd(self):
        """
        S  |-----|
        O  |--------|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0600
        sectionAddressEnd = 0x06FF
        objectAddressStart = 0x0600
        objectAddressEnd = 0x07FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + object
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[1], objectContainer[0])

    def test_sectionFullWithOverlappingSingleObjectAtStartAndEnd(self):
        """
        S     |-----|
        O  |-----------|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0200
        sectionAddressEnd = 0x02FF
        objectAddressStart = 0x0100
        objectAddressEnd = 0x03FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: object + sectionEntry
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])

    def test_sectionNotFullWithSingleObjectAtStart(self):
        """
        S     |-----|
        O     |--|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0400
        sectionAddressEnd = 0x04FF
        objectAddressStart = 0x0400
        objectAddressEnd = 0x0410
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + object + sectionReserve
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[1], objectContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[2], sectionContainer[0], (objectAddressEnd + 1), sectionAddressEnd)

    def test_sectionNotFullWithSingleObjectAtEnd(self):
        """
        S     |-----|
        O        |--|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0500
        sectionAddressEnd = 0x05FF
        objectAddressStart = 0x0550
        objectAddressEnd = 0x05FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve + object
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], sectionAddressStart, (objectAddressStart - 1))
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[2], objectContainer[0])

    def test_sectionNotFullWithSingleObjectAtMiddle(self):
        """
        S    |------|
        O      |--|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0500
        sectionAddressEnd = 0x05FF
        objectAddressStart = 0x0550
        objectAddressEnd = 0x05A0
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve + object + sectionReserve
        self.assertEqual(len(objectsInSections), 4)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], sectionAddressStart, (objectAddressStart - 1))
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[2], objectContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[3], sectionContainer[0], (objectAddressEnd + 1), sectionAddressEnd)

    def test_sectionNotFullWithSingleObjectBeforeStart(self):
        """
        S          |--|
        O    |--|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0500
        sectionAddressEnd = 0x05FF
        objectAddressStart = 0x0300
        objectAddressEnd = 0x03FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: object + sectionEntry + sectionReserve
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[2], sectionContainer[0], sectionAddressStart, sectionAddressEnd)

    def test_sectionNotFullWithSingleObjectAfterEnd(self):
        """
        S    |--|
        O          |--|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0300
        sectionAddressEnd = 0x03FF
        objectAddressStart = 0x0500
        objectAddressEnd = 0x05FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve + object
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], sectionAddressStart, sectionAddressEnd)
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[2], objectContainer[0])

    def test_sectionNotFullWithOverlappingSingleObjectBeforeStart(self):
        """
        S        |--------|
        O    |-------|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0500
        sectionAddressEnd = 0x06FF
        objectAddressStart = 0x0400
        objectAddressEnd = 0x05FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: object + sectionEntry + sectionReserve
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[2], sectionContainer[0], (objectAddressEnd + 1), sectionAddressEnd)

    def test_sectionNotFullWithOverlappingSingleObjectAfterEnd(self):
        """
        S    |--------|
        O         |-------|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0200
        sectionAddressEnd = 0x03FF
        objectAddressStart = 0x0300
        objectAddressEnd = 0x04FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)], [MemEntryData(objectAddressStart, objectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve + object
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], sectionAddressStart, (objectAddressStart - 1))
        # Check whether the object was created properly
        self.assertEqual(objectsInSections[2], objectContainer[0])

    def test_sectionNotFullWithMultipleObjects(self):
        """
        S         |-------------|
        O   |-| |---| |--| |--|   |--|
        """
        # Creating the sections and objects for the test
        sectionAddressStart = 0x0100
        sectionAddressEnd = 0x01FF
        firstObjectAddressStart = 0x0080
        firstObjectAddressEnd = 0x0085
        secondObjectAddressStart = 0x0090
        secondObjectAddressEnd = 0x00110
        thirdObjectAddressStart = 0x0150
        thirdObjectAddressEnd = 0x0180
        fourthObjectAddressStart = 0x01A0
        fourthObjectAddressEnd = 0x01D0
        fifthObjectAddressStart = 0x0210
        fifthObjectAddressEnd = 0x0220
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(sectionAddressStart, sectionAddressEnd)],
                                                                  [MemEntryData(firstObjectAddressStart, firstObjectAddressEnd),
                                                                   MemEntryData(secondObjectAddressStart, secondObjectAddressEnd),
                                                                   MemEntryData(thirdObjectAddressStart, thirdObjectAddressEnd),
                                                                   MemEntryData(fourthObjectAddressStart, fourthObjectAddressEnd),
                                                                   MemEntryData(fifthObjectAddressStart, fifthObjectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry +
        #                                       firstObject +
        #                                       secondObject + firstSectionReserve +
        #                                       thirdObject + secondSectionReserve +
        #                                       fourthObject + thirdSectionReserve +
        #                                       fifthObject
        self.assertEqual(len(objectsInSections), 9)
        # Check whether the firstObject was created properly
        self.assertEqual(objectsInSections[0], objectContainer[0])
        # Check whether the secondObject was created properly
        self.assertEqual(objectsInSections[1], objectContainer[1])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[2], sectionContainer[0])
        # Check whether the firstSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[3], sectionContainer[0], (secondObjectAddressEnd + 1), (thirdObjectAddressStart - 1))
        # Check whether the thirdObject was created properly
        self.assertEqual(objectsInSections[4], objectContainer[2])
        # Check whether the secondSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[5], sectionContainer[0], (thirdObjectAddressEnd + 1), (fourthObjectAddressStart - 1))
        # Check whether the fourthObject was created properly
        self.assertEqual(objectsInSections[6], objectContainer[3])
        # Check whether the thirdSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[7], sectionContainer[0], (fourthObjectAddressEnd + 1), sectionAddressEnd)
        # Check whether the fifthObject was created properly
        self.assertEqual(objectsInSections[8], objectContainer[4])

    def test_multipleSectionsWithMultipleObjects(self):
        """
        S       |--|---| |------|    |--|
        O   |-| |-|  |---| |--| |--|
        """
        # Creating the sections and objects for the test
        firstSectionAddressStart = 0x0100
        firstSectionAddressEnd = 0x01FF
        secondSectionAddressStart = 0x0200
        secondSectionAddressEnd = 0x02FF
        thirdSectionAddressStart = 0x0400
        thirdSectionAddressEnd = 0x05FF
        fourthSectionAddressStart = 0x0700
        fourthSectionAddressEnd = 0x07FF
        firstObjectAddressStart = 0x0080
        firstObjectAddressEnd = 0x008F
        secondObjectAddressStart = 0x0100
        secondObjectAddressEnd = 0x001AF
        thirdObjectAddressStart = 0x0250
        thirdObjectAddressEnd = 0x03FF
        fourthObjectAddressStart = 0x0450
        fourthObjectAddressEnd = 0x04FF
        fifthObjectAddressStart = 0x0600
        fifthObjectAddressEnd = 0x063F
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(firstSectionAddressStart, firstSectionAddressEnd),
                                                                   MemEntryData(secondSectionAddressStart, secondSectionAddressEnd),
                                                                   MemEntryData(thirdSectionAddressStart, thirdSectionAddressEnd),
                                                                   MemEntryData(fourthSectionAddressStart, fourthSectionAddressEnd)],
                                                                  [MemEntryData(firstObjectAddressStart, firstObjectAddressEnd),
                                                                   MemEntryData(secondObjectAddressStart, secondObjectAddressEnd),
                                                                   MemEntryData(thirdObjectAddressStart, thirdObjectAddressEnd),
                                                                   MemEntryData(fourthObjectAddressStart, fourthObjectAddressEnd),
                                                                   MemEntryData(fifthObjectAddressStart, fifthObjectAddressEnd)])
        # Calculating the objectsInSections list
        objectsInSections = emma_libs.memoryMap.caluclateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: firstObject +
        #                                       firstSectionEntry +
        #                                       secondObject + firstSectionReserve +
        #                                       secondSectionEntry + secondSectionReserve +
        #                                       thirdSectionObject +
        #                                       thirdSectionEntry + thirdSectionReserve +
        #                                       fourthObject + thirdSectionReserve +
        #                                       fifthObject +
        #                                       fourthSectionEntry + fourthSectionReserve
        self.assertEqual(len(objectsInSections), 14)
        # Check whether the firstObject was created properly
        self.assertEqual(objectsInSections[0], objectContainer[0])
        # Check whether the firstSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the secondObject was created properly
        self.assertEqual(objectsInSections[2], objectContainer[1])
        # Check whether the firstSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[3], sectionContainer[0], (secondObjectAddressEnd + 1), firstSectionAddressEnd)
        # Check whether the secondSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[4], sectionContainer[1])
        # Check whether the secondSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[5], sectionContainer[1], secondSectionAddressStart, (thirdObjectAddressStart - 1))
        # Check whether the thirdObject was created properly
        self.assertEqual(objectsInSections[6], objectContainer[2])
        # Check whether the thirdSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[7], sectionContainer[2])
        # Check whether the thirdSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[8], sectionContainer[2], thirdSectionAddressStart, (fourthObjectAddressStart - 1))
        # Check whether the fourthObject was created properly
        self.assertEqual(objectsInSections[9], objectContainer[3])
        # Check whether the thirdSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[10], sectionContainer[2], (fourthObjectAddressEnd + 1), thirdSectionAddressEnd)
        # Check whether the fifthObject was created properly
        self.assertEqual(objectsInSections[11], objectContainer[4])
        # Check whether the fourthSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[12], sectionContainer[3])
        # Check whether the fourthSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[13], sectionContainer[3], fourthSectionAddressStart, fourthSectionAddressEnd)


if "__main__" == __name__:
    unittest.main()
