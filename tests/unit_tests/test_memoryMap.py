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
import collections
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
# pylint: disable=wrong-import-position
# Rationale: This module needs to access modules that are above them in the folder structure.

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.emma_libs.memoryEntry
import Emma.emma_libs.memoryMap


class MemEntryData:
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    # Rationale: This class needs to contain all the data needed for the creation of MemEntry objects as attributes and it does not need to have any methods.

    """
    The purpose of this class is that from its objects we can generate MemEntry Objects that
    only differ from each other by the address and length values.
    If the addressEnd is None, then we an entry with zero length will be created.
    In this case the addressEnd needs to have the same value as addressStart.
    The reason why not the addressLength is used here that the specific cases can be easier defined with the addressEnd.
    The MemEntry objects can be generated with the createMemEntryObjects() function from these objects.
    """

    def __init__(self, addressStart, addressEnd, configId=None, section=None, moduleName=None):
        # pylint: disable=too-many-arguments
        # Rationale: The objects needs to be able to fully set up with data during construction.
        self.addressStart = addressStart
        self.addressEnd = addressEnd
        self.configId = configId
        self.section = section
        self.moduleName = moduleName


def createMemEntryObjects(sectionDataContainer=None, objectDataContainer=None):
    # pylint: disable=invalid-name, missing-docstring
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>(). It is not necessary to add a docstring for every unit test.

    def createMemEntryObject(memEntryData):
        compilerSpecificData = collections.OrderedDict()
        compilerSpecificData["DMA"] = True
        compilerSpecificData["vasName"] = ""
        compilerSpecificData["vasSectionName"] = ""
        return Emma.emma_libs.memoryEntry.MemEntry(configID="MCU" if memEntryData.configId is None else memEntryData.configId,
                                              mapfileName="mapfile.map",
                                              addressStart=memEntryData.addressStart,
                                              addressLength=0 if memEntryData.addressEnd is None else None,
                                              addressEnd=memEntryData.addressEnd,
                                              sectionName=".text" if memEntryData.section is None else memEntryData.section,
                                              objectName="" if memEntryData.moduleName is None else memEntryData.moduleName,
                                              memType="INT_FLASH",
                                              memTypeTag="",
                                              category="<Unspecified>",
                                              compilerSpecificData=compilerSpecificData)

    sectionContainer = []
    if sectionDataContainer is not None:
        for element in sectionDataContainer:
            sectionContainer.append(createMemEntryObject(element))

    objectContainer = []
    if objectDataContainer is not None:
        for element in objectDataContainer:
            objectContainer.append(createMemEntryObject(element))

    return sectionContainer, objectContainer


class ResolveDuplicateContainmentOverlapTestCase(unittest.TestCase):
    # pylint: disable=invalid-name, missing-docstring
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>(). It is not necessary to add a docstring for every unit test.

    def assertEqualSections(self, firstSection, secondSection):
        self.assertTrue(Emma.emma_libs.memoryEntry.SectionEntry.isEqual(firstSection, secondSection))

    def assertEqualObjects(self, firstObject, secondObject):
        self.assertTrue(Emma.emma_libs.memoryEntry.ObjectEntry.isEqual(firstObject, secondObject))

    def checkFlags(self, memEntry, memEntryHandler, expectedDuplicate=None, expectedContainingOthers=None, expectedContainedBy=None, expectedOverlappingOthers=None, expectedOverlappedBy=None):  # pylint: disable=too-many-arguments
                                                                                                                                                                                                  # Rationale: This function needs to be able to check all kinds of flags, this is why these arguments needed.
        if expectedDuplicate is not None:
            self.assertEqual(memEntry.duplicateFlag, expectedDuplicate.configID + "::" + expectedDuplicate.mapfile + "::"  + expectedDuplicate.sectionName + ( "::"  + expectedDuplicate.objectName if expectedDuplicate.objectName != "" else ""))
        if expectedContainingOthers is not None:
            self.assertEqual(memEntry.containingOthersFlag, expectedContainingOthers)
        if expectedContainedBy is not None:
            self.assertEqual(memEntry.containmentFlag, expectedContainedBy.configID + "::" + expectedContainedBy.mapfile + "::"  + expectedContainedBy.sectionName + ( "::"  + expectedContainedBy.objectName if expectedContainedBy.objectName != "" else ""))
        if expectedOverlappingOthers is not None:
            self.assertEqual(memEntry.overlappingOthersFlag, expectedOverlappingOthers)
        if expectedOverlappedBy is not None:
            self.assertEqual(memEntry.overlapFlag, expectedOverlappedBy.configID + "::" + expectedOverlappedBy.mapfile + "::"  + expectedOverlappedBy.sectionName + ( "::"  + expectedOverlappedBy.objectName if expectedOverlappedBy.objectName != "" else ""))

    def checkAddressChanges(self, resolvedMemEntry, originalMemEntry, expectedAddressStart=None, expectedAddressLength=None, expectedAddressEnd=None):  # pylint: disable=too-many-arguments
                                                                                                                                                        # Rationale: This function needs to be able to check all kinds of address related data, this is why these arguments needed.
        # If we expect an address change
        if expectedAddressStart is not None or expectedAddressLength is not None or expectedAddressEnd is not None:
            # Then we will check it with the expected values
            self.assertEqual(resolvedMemEntry.addressStart, expectedAddressStart)
            if expectedAddressLength is not None and expectedAddressEnd is None:
                self.assertEqual(resolvedMemEntry.addressLength, expectedAddressLength)
            elif expectedAddressEnd is not None and expectedAddressLength is None:
                self.assertEqual(resolvedMemEntry.addressEnd(), expectedAddressEnd)
            else:
                raise AttributeError("Either expectedAddressLength or expectedAddressEnd shall be provided!")
        else:
            # Otherwise the addresses should be the same as in the original
            self.assertEqual(resolvedMemEntry.addressStart, originalMemEntry.addressStart)
            self.assertEqual(resolvedMemEntry.addressLength, originalMemEntry.addressLength)
        # Also check, whether the original values were stored correctly
        self.assertEqual(resolvedMemEntry.addressStartOriginal, originalMemEntry.addressStart)
        self.assertEqual(resolvedMemEntry.addressLengthOriginal, originalMemEntry.addressLength)

    def test__singleSection(self):
        """
        S  |---|
        """
        # Creating the sections and objects for the test
        ADDRESS_START = 0x0100
        ADDRESS_END = 0x01FF
        listOfMemEntryData = [MemEntryData(ADDRESS_START, ADDRESS_END)]
        memEntryHandler = Emma.emma_libs.memoryEntry.SectionEntry
        originalSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        resolvedSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        # Running the resolveDuplicateContainmentOverlap list
        Emma.emma_libs.memoryMap.resolveDuplicateContainmentOverlap(resolvedSectionContainer, Emma.emma_libs.memoryEntry.SectionEntry)

        # Check the number of elements: no elements shall be removed or added to the container
        self.assertEqual(len(resolvedSectionContainer), len(originalSectionContainer))
        # Check whether the section stayed the same
        self.assertEqualSections(resolvedSectionContainer[0], originalSectionContainer[0])
        # Check whether the flags were set properly
        self.checkFlags(resolvedSectionContainer[0], memEntryHandler)
        # Check whether the addresses were set properly
        self.checkAddressChanges(resolvedSectionContainer[0], originalSectionContainer[0])

    def test__separateSections(self):
        """
        S       |---|
        S  |---|
        """
        # Creating the sections and objects for the test
        FIRST_SECTION_ADDRESS_START = 0x0100
        FIRST_SECTION_ADDRESS_END = 0x01FF
        SECOND_SECTION_ADDRESS_START = 0x0200
        SECOND_SECTION_ADDRESS_END = 0x02FF
        listOfMemEntryData = [MemEntryData(FIRST_SECTION_ADDRESS_START, FIRST_SECTION_ADDRESS_END, section="first"),
                              MemEntryData(SECOND_SECTION_ADDRESS_START, SECOND_SECTION_ADDRESS_END, section="second")]
        memEntryHandler = Emma.emma_libs.memoryEntry.SectionEntry
        originalSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        resolvedSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        # Running the resolveDuplicateContainmentOverlap list
        Emma.emma_libs.memoryMap.resolveDuplicateContainmentOverlap(resolvedSectionContainer, Emma.emma_libs.memoryEntry.SectionEntry)

        # Check the number of elements: no elements shall be removed or added to the container
        self.assertEqual(len(resolvedSectionContainer), len(originalSectionContainer))

        # Check the non changed parts
        for i, _ in enumerate(originalSectionContainer):
            # Check whether the sections stayed the same
            self.assertEqualSections(resolvedSectionContainer[i], originalSectionContainer[i])
            # Check whether the flags were set properly
            self.checkFlags(resolvedSectionContainer[i], memEntryHandler)
            # Check whether the addresses were set properly
            self.checkAddressChanges(resolvedSectionContainer[i], originalSectionContainer[i])

    def test__duplicateSections(self):
        """
        S  |---|
        S  |---|
        """
        # Creating the sections and objects for the test
        FIRST_SECTION_ADDRESS_START = 0x0100
        FIRST_SECTION_ADDRESS_END = 0x01FF
        SECOND_SECTION_ADDRESS_START = 0x0100
        SECOND_SECTION_ADDRESS_END = 0x01FF
        listOfMemEntryData = [MemEntryData(FIRST_SECTION_ADDRESS_START, FIRST_SECTION_ADDRESS_END, section="first"),
                              MemEntryData(SECOND_SECTION_ADDRESS_START, SECOND_SECTION_ADDRESS_END, section="second")]
        memEntryHandler = Emma.emma_libs.memoryEntry.SectionEntry
        originalSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        resolvedSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        # Running the resolveDuplicateContainmentOverlap list
        Emma.emma_libs.memoryMap.resolveDuplicateContainmentOverlap(resolvedSectionContainer, Emma.emma_libs.memoryEntry.SectionEntry)

        # Check the number of elements: no elements shall be removed or added to the container
        self.assertEqual(len(resolvedSectionContainer), len(originalSectionContainer))

        # Check whether the addresses were set properly (it shall be the second section that loses it´s length)
        self.checkAddressChanges(resolvedSectionContainer[0], originalSectionContainer[0])
        self.checkAddressChanges(resolvedSectionContainer[1], originalSectionContainer[1], originalSectionContainer[1].addressStart, 0x00)
        # Check whether the flags were set properly
        self.checkFlags(resolvedSectionContainer[0], memEntryHandler, expectedDuplicate=resolvedSectionContainer[1])
        self.checkFlags(resolvedSectionContainer[1], memEntryHandler, expectedDuplicate=resolvedSectionContainer[0])

    def test__containmentSections(self):
        """
        S  |-----|
        S    |-|
        """
        # Creating the sections and objects for the test
        FIRST_SECTION_ADDRESS_START = 0x0000
        FIRST_SECTION_ADDRESS_END = 0x02FF
        SECOND_SECTION_ADDRESS_START = 0x0100
        SECOND_SECTION_ADDRESS_END = 0x01FF
        listOfMemEntryData = [MemEntryData(FIRST_SECTION_ADDRESS_START, FIRST_SECTION_ADDRESS_END, section="first"),
                              MemEntryData(SECOND_SECTION_ADDRESS_START, SECOND_SECTION_ADDRESS_END, section="second")]
        memEntryHandler = Emma.emma_libs.memoryEntry.SectionEntry
        originalSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        resolvedSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        # Running the resolveDuplicateContainmentOverlap list
        Emma.emma_libs.memoryMap.resolveDuplicateContainmentOverlap(resolvedSectionContainer, Emma.emma_libs.memoryEntry.SectionEntry)

        # Check the number of elements: no elements shall be removed or added to the container
        self.assertEqual(len(resolvedSectionContainer), len(originalSectionContainer))

        # Check whether the addresses were set properly (it shall be the second section that loses it´s length)
        self.checkAddressChanges(resolvedSectionContainer[0], originalSectionContainer[0])
        self.checkAddressChanges(resolvedSectionContainer[1], originalSectionContainer[1], originalSectionContainer[1].addressStart, 0x00)
        # Check whether the flags were set properly
        self.checkFlags(resolvedSectionContainer[0], memEntryHandler, expectedContainingOthers=True)
        self.checkFlags(resolvedSectionContainer[1], memEntryHandler, expectedContainedBy=resolvedSectionContainer[0])

    def test__overlapSections(self):
        """
        S  |---|
        S    |---|
        """
        # Creating the sections and objects for the test
        FIRST_SECTION_ADDRESS_START = 0x0100
        FIRST_SECTION_ADDRESS_END = 0x01FF
        SECOND_SECTION_ADDRESS_START = 0x0180
        SECOND_SECTION_ADDRESS_END = 0x027F
        listOfMemEntryData = [MemEntryData(FIRST_SECTION_ADDRESS_START, FIRST_SECTION_ADDRESS_END, section="first"),
                              MemEntryData(SECOND_SECTION_ADDRESS_START, SECOND_SECTION_ADDRESS_END, section="second")]
        memEntryHandler = Emma.emma_libs.memoryEntry.SectionEntry
        originalSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        resolvedSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        # Running the resolveDuplicateContainmentOverlap list
        Emma.emma_libs.memoryMap.resolveDuplicateContainmentOverlap(resolvedSectionContainer, Emma.emma_libs.memoryEntry.SectionEntry)

        # Check the number of elements: no elements shall be removed or added to the container
        self.assertEqual(len(resolvedSectionContainer), len(originalSectionContainer))

        # Check whether the addresses were set properly (the second section shall lose its beginning)
        self.checkAddressChanges(resolvedSectionContainer[0], originalSectionContainer[0],
                                 expectedAddressStart=originalSectionContainer[0].addressStart,
                                 expectedAddressEnd=originalSectionContainer[0].addressEnd())
        self.checkAddressChanges(resolvedSectionContainer[1], originalSectionContainer[1],
                                 expectedAddressStart=(originalSectionContainer[0].addressEnd() + 1),
                                 expectedAddressEnd=originalSectionContainer[1].addressEnd())
        # Check whether the flags were set properly
        self.checkFlags(resolvedSectionContainer[0], memEntryHandler, expectedOverlappingOthers=True)
        self.checkFlags(resolvedSectionContainer[1], memEntryHandler, expectedOverlappedBy=originalSectionContainer[0])

    def test__overlapMultipleSections(self):
        """
        S1  |------|
        S2    |---------|
        S3      |----------|
        S4           |-----|
        """
        # Creating the sections and objects for the test
        FIRST_SECTION_ADDRESS_START = 0x0100
        FIRST_SECTION_ADDRESS_END = 0x016F
        SECOND_SECTION_ADDRESS_START = 0x0120
        SECOND_SECTION_ADDRESS_END = 0x021F
        THIRD_SECTION_ADDRESS_START = 0x0140
        THIRD_SECTION_ADDRESS_END = 0x023F
        FOURTH_SECTION_ADDRESS_START = 0x0190
        FOURTH_SECTION_ADDRESS_END = 0x023F
        listOfMemEntryData = [MemEntryData(FIRST_SECTION_ADDRESS_START, FIRST_SECTION_ADDRESS_END, section="first"),
                              MemEntryData(SECOND_SECTION_ADDRESS_START, SECOND_SECTION_ADDRESS_END, section="second"),
                              MemEntryData(THIRD_SECTION_ADDRESS_START, THIRD_SECTION_ADDRESS_END, section="third"),
                              MemEntryData(FOURTH_SECTION_ADDRESS_START, FOURTH_SECTION_ADDRESS_END, section="fourth")]
        memEntryHandler = Emma.emma_libs.memoryEntry.SectionEntry
        originalSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        resolvedSectionContainer, _ = createMemEntryObjects(listOfMemEntryData)
        # Running the resolveDuplicateContainmentOverlap list
        Emma.emma_libs.memoryMap.resolveDuplicateContainmentOverlap(resolvedSectionContainer, Emma.emma_libs.memoryEntry.SectionEntry)

        # Check the number of elements: no elements shall be removed or added to the container
        self.assertEqual(len(resolvedSectionContainer), len(originalSectionContainer))

        # Check whether the addresses were set properly (the second section shall lose its beginning)
        self.checkAddressChanges(resolvedSectionContainer[0], originalSectionContainer[0], expectedAddressStart=originalSectionContainer[0].addressStart, expectedAddressEnd=originalSectionContainer[0].addressEnd())
        self.checkAddressChanges(resolvedSectionContainer[1], originalSectionContainer[1], expectedAddressStart=(originalSectionContainer[0].addressEnd() + 1), expectedAddressLength=0)
        self.checkAddressChanges(resolvedSectionContainer[2], originalSectionContainer[2], expectedAddressStart=(originalSectionContainer[0].addressEnd() + 1), expectedAddressEnd=originalSectionContainer[2].addressEnd())
        self.checkAddressChanges(resolvedSectionContainer[3], originalSectionContainer[3], expectedAddressStart=originalSectionContainer[3].addressStart, expectedAddressLength=0)

        # Check whether the flags were set properly
        self.checkFlags(resolvedSectionContainer[0], memEntryHandler, expectedOverlappingOthers=True)
        self.checkFlags(resolvedSectionContainer[1], memEntryHandler, expectedOverlappedBy=originalSectionContainer[0], expectedContainedBy=originalSectionContainer[2])
        self.checkFlags(resolvedSectionContainer[2], memEntryHandler, expectedOverlappedBy=originalSectionContainer[0], expectedContainingOthers=True)
        self.checkFlags(resolvedSectionContainer[3], memEntryHandler, expectedContainedBy=originalSectionContainer[2])


class CalculateObjectsInSectionsTestCase(unittest.TestCase):
    # pylint: disable=invalid-name, missing-docstring
    # Rationale: Tests need to have the following method names in order to be discovered: test_<METHOD_NAME>(). It is not necessary to add a docstring for every unit test.
    # pylint: disable=too-many-public-methods
    # Rationale: The tests have many repetitive checks that were grouped into these functions.

    def checkSectionNonChangingData(self, sectionToCheck, sourceSection):
        """
        Checks the data of a section that shall never be changed during caluclateObjectsInSections().
        :param sectionToCheck: This is the section that was calculated.
        :param sourceSection: This is the section from which the sectionToCheck was calculated.
        :return: None
        """
        self.assertEqual(sectionToCheck.memTypeTag, sourceSection.memTypeTag)
        self.assertEqual(sectionToCheck.compilerSpecificData, sourceSection.compilerSpecificData)
        self.assertEqual(sectionToCheck.sectionName, sourceSection.sectionName)
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
        self.assertEqual(sectionToCheck.addressLengthHexOriginal(), sourceSection.addressLengthHexOriginal())
        self.assertEqual(sectionToCheck.addressEndOriginal(), sourceSection.addressEndOriginal())

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
        self.assertIsNone(sectionEntry.addressEnd())
        self.assertEqual(sectionEntry.addressStartHex(), hex(sourceSection.addressStart))
        self.assertEqual(sectionEntry.addressLengthHex(), hex(0))
        self.assertEqual(sectionEntry.addressEndHex(), "")
        self.assertEqual(sectionEntry.objectName, OBJECTS_IN_SECTIONS_SECTION_ENTRY)

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
        self.assertEqual(sectionReserve.addressEnd(), expectedAddressEnd)
        self.assertEqual(sectionReserve.addressStartHex(), hex(expectedAddressStart))
        self.assertEqual(sectionReserve.addressLengthHex(), hex((expectedAddressEnd - expectedAddressStart + 1)))
        self.assertEqual(sectionReserve.addressEndHex(), hex(expectedAddressEnd))
        self.assertEqual(sectionReserve.objectName, OBJECTS_IN_SECTIONS_SECTION_RESERVE)

    def assertEqualSections(self, firstSection, secondSection):
        self.assertTrue(Emma.emma_libs.memoryEntry.SectionEntry.isEqual(firstSection, secondSection))

    def assertEqualObjects(self, firstObject, secondObject):
        self.assertTrue(Emma.emma_libs.memoryEntry.ObjectEntry.isEqual(firstObject, secondObject))

    def test_singleSection(self):
        """
        S  |---|
        O
        """
        # Creating the sections and objects for the test
        ADDRESS_START = 0x0100
        ADDRESS_END = 0x01FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(ADDRESS_START, ADDRESS_END)], [])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], ADDRESS_START, ADDRESS_END)

    def test_singleSectionWithZeroObjects(self):
        """
        S    |-------|
        O  | |   |   | |
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0200
        SECTION_ADDRESS_END = 0x03FF
        FIRST_OBJECT_ADDRESS_START = 0x00100
        SECOND_OBJECT_ADDRESS_START = 0x0200
        THIRD_OBJECT_ADDRESS_START = 0x0300
        FOURTH_OBJECT_ADDRESS_START = 0x03FF
        FIFTH_OBJECT_ADDRESS_START = 0x0500
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)],
                                                                  [MemEntryData(FIRST_OBJECT_ADDRESS_START, None),
                                                                   MemEntryData(SECOND_OBJECT_ADDRESS_START, None),
                                                                   MemEntryData(THIRD_OBJECT_ADDRESS_START, None),
                                                                   MemEntryData(FOURTH_OBJECT_ADDRESS_START, None),
                                                                   MemEntryData(FIFTH_OBJECT_ADDRESS_START, None)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: firstObject +
        #                                       sectionEntry +
        #                                       secondObject +
        #                                       thirdObject +
        #                                       fourthObject +
        #                                       sectionReserve +
        #                                       fifthObject
        self.assertEqual(len(objectsInSections), 7)
        # Check whether the firstObject was created properly
        self.assertEqualObjects(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[2], sectionContainer[0], SECTION_ADDRESS_START, SECTION_ADDRESS_END)
        # Check whether the secondObject was created properly
        self.assertEqualObjects(objectsInSections[3], objectContainer[1])
        # Check whether the thirdObject was created properly
        self.assertEqualObjects(objectsInSections[4], objectContainer[2])
        # Check whether the fourthObject was created properly
        self.assertEqualObjects(objectsInSections[5], objectContainer[3])
        # Check whether the fifthObject was created properly
        self.assertEqualObjects(objectsInSections[6], objectContainer[4])

    def test_multipleSectionsAndObjectsWithZeroLengths(self):
        """
        S     | | | | |
        O   |   | |---|
        """
        # Creating the sections and objects for the test
        FIRST_SECTION_ADDRESS_START = 0x0150
        SECOND_SECTION_ADDRESS_START = 0x0200
        THIRD_SECTION_ADDRESS_START = 0x0300
        FOURTH_SECTION_ADDRESS_START = 0x0350
        FIFTH_SECTION_ADDRESS_START = 0x03FF
        FIRST_OBJECT_ADDRESS_START = 0x0100
        SECOND_OBJECT_ADDRESS_START = 0x0200
        THIRD_OBJECT_ADDRESS_START = 0x0300
        THIRD_OBJECT_ADDRESS_END = 0x03FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(FIRST_SECTION_ADDRESS_START, None),
                                                                   MemEntryData(SECOND_SECTION_ADDRESS_START, None),
                                                                   MemEntryData(THIRD_SECTION_ADDRESS_START, None),
                                                                   MemEntryData(FOURTH_SECTION_ADDRESS_START, None),
                                                                   MemEntryData(FIFTH_SECTION_ADDRESS_START, None)],
                                                                  [MemEntryData(FIRST_OBJECT_ADDRESS_START, None),
                                                                   MemEntryData(SECOND_OBJECT_ADDRESS_START, None),
                                                                   MemEntryData(THIRD_OBJECT_ADDRESS_START, THIRD_OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

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
        self.assertEqualObjects(objectsInSections[0], objectContainer[0])
        # Check whether the firstSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the secondSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[2], sectionContainer[1])
        # Check whether the secondObject was created properly
        self.assertEqualObjects(objectsInSections[3], objectContainer[1])
        # Check whether the thirdSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[4], sectionContainer[2])
        # Check whether the thirdObject was created properly
        self.assertEqualObjects(objectsInSections[5], objectContainer[2])
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
        FIRST_SECTION_ADDRESS_START = 0x0100
        FIRST_SECTION_ADDRESS_END = 0x01FF
        SECOND_SECTION_ADDRESS_START = 0x0300
        SECOND_SECTION_ADDRESS_END = 0x03FF
        OBJECT_ADDRESS_START = 0x0150
        OBJECT_ADDRESS_END = 0x034F
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(FIRST_SECTION_ADDRESS_START, FIRST_SECTION_ADDRESS_END),
                                                                   MemEntryData(SECOND_SECTION_ADDRESS_START, SECOND_SECTION_ADDRESS_END)],
                                                                  [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Editing the sections: switching the the containmentFlags on
        sectionContainer[0].containmentFlag = True
        sectionContainer[1].containmentFlag = True
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: firstSectionEntry +
        #                                       object +
        #                                       secondSectionEntry
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the firstSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[1], objectContainer[0])
        # Check whether the secondSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[2], sectionContainer[1])

    def test_sectionFullWithSingleObject(self):
        """
        S  |----|
        O  |----|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0200
        SECTION_ADDRESS_END = 0x02FF
        OBJECT_ADDRESS_START = 0x0200
        OBJECT_ADDRESS_END = 0x02FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + object
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[1], objectContainer[0])

    def test_sectionFullWithTwoObjects(self):
        """
        S  |-----|
        O  |--|--|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0400
        SECTION_ADDRESS_END = 0x05FF
        FIRST_OBJECT_ADDRESS_START = 0x0400
        FIRST_OBJECT_ADDRESS_END = 0x04FF
        SECOND_OBJECT_ADDRESS_START = 0x0500
        SECOND_OBJECT_ADDRESS_END = 0x05FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)],
                                                                  [MemEntryData(FIRST_OBJECT_ADDRESS_START, FIRST_OBJECT_ADDRESS_END), MemEntryData(SECOND_OBJECT_ADDRESS_START, SECOND_OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + firstObject + secondObject
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the firstObject was created properly
        self.assertEqualObjects(objectsInSections[1], objectContainer[0])
        # Check whether the secondObject was created properly
        self.assertEqualObjects(objectsInSections[2], objectContainer[1])

    def test_sectionFullWithOverlappingSingleObjectAtStart(self):
        """
        S     |-----|
        O  |--------|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0800
        SECTION_ADDRESS_END = 0x09FF
        OBJECT_ADDRESS_START = 0x0700
        OBJECT_ADDRESS_END = 0x09FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: object + sectionEntry
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])

    def test_sectionFullWithOverlappingSingleObjectAtEnd(self):
        """
        S  |-----|
        O  |--------|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0600
        SECTION_ADDRESS_END = 0x06FF
        OBJECT_ADDRESS_START = 0x0600
        OBJECT_ADDRESS_END = 0x07FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + object
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[1], objectContainer[0])

    def test_sectionFullWithOverlappingSingleObjectAtStartAndEnd(self):
        """
        S     |-----|
        O  |-----------|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0200
        SECTION_ADDRESS_END = 0x02FF
        OBJECT_ADDRESS_START = 0x0100
        OBJECT_ADDRESS_END = 0x03FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: object + sectionEntry
        self.assertEqual(len(objectsInSections), 2)
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])

    def test_sectionNotFullWithSingleObjectAtStart(self):
        """
        S     |-----|
        O     |--|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0400
        SECTION_ADDRESS_END = 0x04FF
        OBJECT_ADDRESS_START = 0x0400
        OBJECT_ADDRESS_END = 0x0410
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + object + sectionReserve
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[1], objectContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[2], sectionContainer[0], (OBJECT_ADDRESS_END + 1), SECTION_ADDRESS_END)

    def test_sectionNotFullWithSingleObjectAtEnd(self):
        """
        S     |-----|
        O        |--|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0500
        SECTION_ADDRESS_END = 0x05FF
        OBJECT_ADDRESS_START = 0x0550
        OBJECT_ADDRESS_END = 0x05FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve + object
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], SECTION_ADDRESS_START, (OBJECT_ADDRESS_START - 1))
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[2], objectContainer[0])

    def test_sectionNotFullWithSingleObjectAtMiddle(self):
        """
        S    |------|
        O      |--|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0500
        SECTION_ADDRESS_END = 0x05FF
        OBJECT_ADDRESS_START = 0x0550
        OBJECT_ADDRESS_END = 0x05A0
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve + object + sectionReserve
        self.assertEqual(len(objectsInSections), 4)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], SECTION_ADDRESS_START, (OBJECT_ADDRESS_START - 1))
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[2], objectContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[3], sectionContainer[0], (OBJECT_ADDRESS_END + 1), SECTION_ADDRESS_END)

    def test_sectionNotFullWithSingleObjectBeforeStart(self):
        """
        S          |--|
        O    |--|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0500
        SECTION_ADDRESS_END = 0x05FF
        OBJECT_ADDRESS_START = 0x0300
        OBJECT_ADDRESS_END = 0x03FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: object + sectionEntry + sectionReserve
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[2], sectionContainer[0], SECTION_ADDRESS_START, SECTION_ADDRESS_END)

    def test_sectionNotFullWithSingleObjectAfterEnd(self):
        """
        S    |--|
        O          |--|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0300
        SECTION_ADDRESS_END = 0x03FF
        OBJECT_ADDRESS_START = 0x0500
        OBJECT_ADDRESS_END = 0x05FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve + object
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], SECTION_ADDRESS_START, SECTION_ADDRESS_END)
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[2], objectContainer[0])

    def test_sectionNotFullWithOverlappingSingleObjectBeforeStart(self):
        """
        S        |--------|
        O    |-------|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0500
        SECTION_ADDRESS_END = 0x06FF
        OBJECT_ADDRESS_START = 0x0400
        OBJECT_ADDRESS_END = 0x05FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: object + sectionEntry + sectionReserve
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[0], objectContainer[0])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[2], sectionContainer[0], (OBJECT_ADDRESS_END + 1), SECTION_ADDRESS_END)

    def test_sectionNotFullWithOverlappingSingleObjectAfterEnd(self):
        """
        S    |--------|
        O         |-------|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0200
        SECTION_ADDRESS_END = 0x03FF
        OBJECT_ADDRESS_START = 0x0300
        OBJECT_ADDRESS_END = 0x04FF
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)], [MemEntryData(OBJECT_ADDRESS_START, OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry + sectionReserve + object
        self.assertEqual(len(objectsInSections), 3)
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[0], sectionContainer[0])
        # Check whether the sectionReserve was created properly
        self.checkSectionReserve(objectsInSections[1], sectionContainer[0], SECTION_ADDRESS_START, (OBJECT_ADDRESS_START - 1))
        # Check whether the object was created properly
        self.assertEqualObjects(objectsInSections[2], objectContainer[0])

    def test_sectionNotFullWithMultipleObjects(self):
        # pylint: disable=too-many-locals
        # Rationale: These constants are needed to set up the used sections and objects.

        """
        S         |-------------|
        O   |-| |---| |--| |--|   |--|
        """
        # Creating the sections and objects for the test
        SECTION_ADDRESS_START = 0x0100
        SECTION_ADDRESS_END = 0x01FF
        FIRST_OBJECT_ADDRESS_START = 0x0080
        FIRST_OBJECT_ADDRESS_END = 0x0085
        SECOND_OBJECT_ADDRESS_START = 0x0090
        SECOND_OBJECT_ADDRESS_END = 0x00110
        THIRD_OBJECT_ADDRESS_START = 0x0150
        THIRD_OBJECT_ADDRESS_END = 0x0180
        FOURTH_OBJECT_ADDRESS_START = 0x01A0
        FOURTH_OBJECT_ADDRESS_END = 0x01D0
        FIFTH_OBJECT_ADDRESS_START = 0x0210
        FIFTH_OBJECT_ADDRESS_END = 0x0220
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(SECTION_ADDRESS_START, SECTION_ADDRESS_END)],
                                                                  [MemEntryData(FIRST_OBJECT_ADDRESS_START, FIRST_OBJECT_ADDRESS_END),
                                                                   MemEntryData(SECOND_OBJECT_ADDRESS_START, SECOND_OBJECT_ADDRESS_END),
                                                                   MemEntryData(THIRD_OBJECT_ADDRESS_START, THIRD_OBJECT_ADDRESS_END),
                                                                   MemEntryData(FOURTH_OBJECT_ADDRESS_START, FOURTH_OBJECT_ADDRESS_END),
                                                                   MemEntryData(FIFTH_OBJECT_ADDRESS_START, FIFTH_OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

        # Check the number of created elements: sectionEntry +
        #                                       firstObject +
        #                                       secondObject + firstSectionReserve +
        #                                       thirdObject + secondSectionReserve +
        #                                       fourthObject + thirdSectionReserve +
        #                                       fifthObject
        self.assertEqual(len(objectsInSections), 9)
        # Check whether the firstObject was created properly
        self.assertEqualObjects(objectsInSections[0], objectContainer[0])
        # Check whether the secondObject was created properly
        self.assertEqualObjects(objectsInSections[1], objectContainer[1])
        # Check whether the sectionEntry was created properly
        self.checkSectionEntry(objectsInSections[2], sectionContainer[0])
        # Check whether the firstSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[3], sectionContainer[0], (SECOND_OBJECT_ADDRESS_END + 1), (THIRD_OBJECT_ADDRESS_START - 1))
        # Check whether the thirdObject was created properly
        self.assertEqualObjects(objectsInSections[4], objectContainer[2])
        # Check whether the secondSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[5], sectionContainer[0], (THIRD_OBJECT_ADDRESS_END + 1), (FOURTH_OBJECT_ADDRESS_START - 1))
        # Check whether the fourthObject was created properly
        self.assertEqualObjects(objectsInSections[6], objectContainer[3])
        # Check whether the thirdSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[7], sectionContainer[0], (FOURTH_OBJECT_ADDRESS_END + 1), SECTION_ADDRESS_END)
        # Check whether the fifthObject was created properly
        self.assertEqualObjects(objectsInSections[8], objectContainer[4])

    def test_multipleSectionsWithMultipleObjects(self):
        # pylint: disable=too-many-locals
        # Rationale: These constants are needed to set up the used sections and objects.

        """
        S       |--|---| |------|    |--|
        O   |-| |-|  |---| |--| |--|
        """
        # Creating the sections and objects for the test
        FIRST_SECTION_ADDRESS_START = 0x0100
        FIRST_SECTION_ADDRESS_END = 0x01FF
        SECOND_SECTION_ADDRESS_START = 0x0200
        SECOND_SECTION_ADDRESS_END = 0x02FF
        THIRD_SECTION_ADDRESS_START = 0x0400
        THIRD_SECTION_ADDRESS_END = 0x05FF
        FOURTH_SECTION_ADDRESS_START = 0x0700
        FOURTH_SECTION_ADDRESS_END = 0x07FF
        FIRST_OBJECT_ADDRESS_START = 0x0080
        FIRST_OBJECT_ADDRESS_END = 0x008F
        SECOND_OBJECT_ADDRESS_START = 0x0100
        SECOND_OBJECT_ADDRESS_END = 0x001AF
        THIRD_OBJECT_ADDRESS_START = 0x0250
        THIRD_OBJECT_ADDRESS_END = 0x03FF
        FOURTH_OBJECT_ADDRESS_START = 0x0450
        FOURTH_OBJECT_ADDRESS_END = 0x04FF
        FIFTH_OBJECT_ADDRESS_START = 0x0600
        FIFTH_OBJECT_ADDRESS_END = 0x063F
        sectionContainer, objectContainer = createMemEntryObjects([MemEntryData(FIRST_SECTION_ADDRESS_START, FIRST_SECTION_ADDRESS_END),
                                                                   MemEntryData(SECOND_SECTION_ADDRESS_START, SECOND_SECTION_ADDRESS_END),
                                                                   MemEntryData(THIRD_SECTION_ADDRESS_START, THIRD_SECTION_ADDRESS_END),
                                                                   MemEntryData(FOURTH_SECTION_ADDRESS_START, FOURTH_SECTION_ADDRESS_END)],
                                                                  [MemEntryData(FIRST_OBJECT_ADDRESS_START, FIRST_OBJECT_ADDRESS_END),
                                                                   MemEntryData(SECOND_OBJECT_ADDRESS_START, SECOND_OBJECT_ADDRESS_END),
                                                                   MemEntryData(THIRD_OBJECT_ADDRESS_START, THIRD_OBJECT_ADDRESS_END),
                                                                   MemEntryData(FOURTH_OBJECT_ADDRESS_START, FOURTH_OBJECT_ADDRESS_END),
                                                                   MemEntryData(FIFTH_OBJECT_ADDRESS_START, FIFTH_OBJECT_ADDRESS_END)])
        # Calculating the objectsInSections list
        objectsInSections = Emma.emma_libs.memoryMap.calculateObjectsInSections(sectionContainer, objectContainer)

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
        self.assertEqualObjects(objectsInSections[0], objectContainer[0])
        # Check whether the firstSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[1], sectionContainer[0])
        # Check whether the secondObject was created properly
        self.assertEqualObjects(objectsInSections[2], objectContainer[1])
        # Check whether the firstSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[3], sectionContainer[0], (SECOND_OBJECT_ADDRESS_END + 1), FIRST_SECTION_ADDRESS_END)
        # Check whether the secondSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[4], sectionContainer[1])
        # Check whether the secondSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[5], sectionContainer[1], SECOND_SECTION_ADDRESS_START, (THIRD_OBJECT_ADDRESS_START - 1))
        # Check whether the thirdObject was created properly
        self.assertEqualObjects(objectsInSections[6], objectContainer[2])
        # Check whether the thirdSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[7], sectionContainer[2])
        # Check whether the thirdSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[8], sectionContainer[2], THIRD_SECTION_ADDRESS_START, (FOURTH_OBJECT_ADDRESS_START - 1))
        # Check whether the fourthObject was created properly
        self.assertEqualObjects(objectsInSections[9], objectContainer[3])
        # Check whether the thirdSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[10], sectionContainer[2], (FOURTH_OBJECT_ADDRESS_END + 1), THIRD_SECTION_ADDRESS_END)
        # Check whether the fifthObject was created properly
        self.assertEqualObjects(objectsInSections[11], objectContainer[4])
        # Check whether the fourthSectionEntry was created properly
        self.checkSectionEntry(objectsInSections[12], sectionContainer[3])
        # Check whether the fourthSectionReserve was created properly
        self.checkSectionReserve(objectsInSections[13], sectionContainer[3], FOURTH_SECTION_ADDRESS_START, FOURTH_SECTION_ADDRESS_END)


if __name__ == "__main__":
    unittest.main()
