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
import bisect
import copy

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import emma_libs.memoryManager


def calculateObjectsInSections(sectionContainer, objectContainer):
    """
        Assumptions:
            - The sectionCollection is a list of MemEntry objects:
                - It is ordered based on the startAddress attribute
                - The overlapping sections are already edited and the addresses corrected
            - The objectCollection is a list of MemEntry objects
                - It is ordered based on the startAddress attribute
                - The overlapping objects are already edited and the addresses corrected
    """
    objectsInSections = []

    def createASectionEntry():
        sectionEntry = copy.deepcopy(sectionContainerElement)
        sectionEntry.moduleName = OBJECTS_IN_SECTIONS_SECTION_ENTRY
        sectionEntry.addressLength = 0
        sectionEntry.addressLengthHex = hex(sectionEntry.addressLength)
        objectsInSections.append(sectionEntry)

    def createASectionReserve(sourceSection, addressEnd=None):
        # If we have received a specific addressEnd then we will use that one and recalculate the size of the section
        # In this case we need to make a deepcopy of the sourceSection because the SW will continue to work with it
        if addressEnd is not None:
            sourceSectionCopy = copy.deepcopy(sourceSection)
            sourceSectionCopy.moduleName = OBJECTS_IN_SECTIONS_SECTION_RESERVE
            sourceSectionCopy.addressEnd = addressEnd
            sourceSectionCopy.addressEndHex = hex(sourceSectionCopy.addressEnd)
            sourceSectionCopy.addressLength = sourceSectionCopy.addressEnd - sourceSectionCopy.addressStart + 1
            sourceSectionCopy.addressLengthHex = hex(sourceSectionCopy.addressLength)
            objectsInSections.append(sourceSectionCopy)
        # If not, then the whole sourceSection will be stored as a reserve
        # In this case no copy needed because the SW does not need it anymore
        else:
            sourceSection.moduleName = OBJECTS_IN_SECTIONS_SECTION_RESERVE
            objectsInSections.append(sourceSection)

    def cutOffTheBeginningOfTheSection(sectionToCut, newAddressStart):
        sectionToCut.addressStart = newAddressStart
        sectionToCut.addressStartHex = hex(sectionToCut.addressStart)
        sectionToCut.addressLength = sectionToCut.addressEnd - sectionToCut.addressStart + 1
        sectionToCut.addressLengthHex = hex(sectionToCut.addressLength)

    for sectionContainerElement in sectionContainer:
        # Creating a section entry
        createASectionEntry()

        # We will skip the sections that are contained by other sections or have a zero length
        if sectionContainerElement.containmentFlag is not None:
            continue
        if sectionContainerElement.addressLength == 0:
            continue

        # This is the section we are working with in this loop. We will take it apart and create other objects from it.
        # In order not to have any influence on the original sectionContainer elements, we will create a copy of it
        sectionCopy = copy.deepcopy(sectionContainerElement)

        for objectContainerElement in objectContainer:
            # We will skip the objects if:
            #   - is not belonging to the same configID as the section
            #   - or have a zero length or
            #   - if it ends before this section, because it means that this object is outside the section.
            if sectionCopy.configID != objectContainerElement.configID or objectContainerElement.addressLength == 0 or sectionCopy.addressStart > objectContainerElement.addressEnd:
                continue

            # Case 0: The object is completely overlapping the section
            if objectContainerElement.addressStart <= sectionCopy.addressStart and sectionCopy.addressEnd <= objectContainerElement.addressEnd:
                # This object is overlapping the section completely. This means that all the following objects will be
                # outside the section, so we can continue with the next section.
                # We also need to mark that the section is fully loaded with the object
                sectionCopy = None
                break

            # Case 1: The object is overlapping the beginning of the section
            elif objectContainerElement.addressStart <= sectionCopy.addressStart and objectContainerElement.addressEnd < sectionCopy.addressEnd:
                # Cutting off the beginning of the section
                cutOffTheBeginningOfTheSection(sectionCopy, objectContainerElement.addressEnd + 1)

            # Case 2: The object is overlapping a part in the middle of the section
            elif sectionCopy.addressStart < objectContainerElement.addressStart and objectContainerElement.addressEnd < sectionCopy.addressEnd:
                # Creating a sectionReserve
                createASectionReserve(sectionCopy, objectContainerElement.addressStart - 1)
                # Setting up the remaining section part
                cutOffTheBeginningOfTheSection(sectionCopy, objectContainerElement.addressEnd + 1)

            # Case 3: The object is overlapping the end of the section
            elif sectionCopy.addressStart < objectContainerElement.addressStart <= sectionCopy.addressEnd < objectContainerElement.addressEnd:
                # Creating the sectionReserve
                createASectionReserve(sectionCopy, objectContainerElement.addressStart - 1)
                # This object is overlapping the end of the section. This means that all the following objects will be
                # outside the section, so we can continue with the next section.
                # We also need to mark that the section is fully loaded with the objects
                sectionCopy = None
                break

            # Case 4: The object is only starting after this section, it means that the following objects will also be outside the section.
            # So we have to create a reserve for the remaining part of the section and we can exit the object loop now and continue with the next section.
            elif sectionCopy.addressEnd < objectContainerElement.addressStart:
                # There is not much to do here, the reserve will be created after the object loop
                break

        # If we have ran out of objects for this section (at this point, we are out of the object loop)
        # And there is still some remaining part of the section, then we need to add it as reserve
        if sectionCopy is not None:
            createASectionReserve(sectionCopy, None)

    # We will need to add all the objects to the objectsInSections
    # In order not to have any influence on the original objectContainer elements, we will create a copy of the elements
    for objectContainerElement in objectContainer:
        index = bisect.bisect_right(objectsInSections, objectContainerElement)
        objectsInSections.insert(index, copy.deepcopy(objectContainerElement))

    return objectsInSections


def memoryMapToCSV(argsDir, argsSubdir, argsProject, memoryMap):
    """
    Writes the memoryMap created in calculateObjectsInSections(...) to CSV
    """
    filepath = emma_libs.memoryManager.createMemStatsFilepath(argsDir, argsSubdir, FILE_IDENTIFIER_OBJECTS_IN_SECTIONS, os.path.split(os.path.normpath(argsProject))[-1])
    emma_libs.memoryManager.consumerCollectionToCSV(filepath, memoryMap)
