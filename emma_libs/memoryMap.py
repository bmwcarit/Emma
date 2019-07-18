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


import csv
import bisect
import copy
import datetime

from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper


# Timestamp for the report file names
timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Ms%S")


def resolveDuplicateContainmentOverlap(consumerCollection, memEntryHandler):
    """
    Goes trough the consumerCollection and checks all the elements for the following situations:
        1 - Duplicate
        2 - Containment
        3 - Overlap

    Assumptions:
        - The consumerCollection is a list of MemEntry objects:
            - It is ordered based on the startAddress attribute

    :param nameGetter: A function to get the name of the element. This is solved in this abstract way so it can work for section and object resolving as well.
    """
    for actualElement in consumerCollection:
        for otherElement in consumerCollection:

            # Don't compare element with itself and only compare the same configID
            if actualElement.equalConfigID(otherElement) and not memEntryHandler.isEqual(actualElement, otherElement):

                # Case 0: actualElement and otherElement are completely separated
                if actualElement.addressEnd() < otherElement.addressStart or actualElement.addressStart > otherElement.addressEnd():
                    # There is not much to do here...
                    pass
                else:
                    # Case 1: actualElement and otherElement are duplicates
                    if actualElement.addressStart == otherElement.addressStart and actualElement.addressEnd() == otherElement.addressEnd():
                        # Setting the actualElement´s duplicateFlag if it was not already set
                        if actualElement.duplicateFlag is None:
                            actualElement.duplicateFlag = "Duplicate of (" + memEntryHandler.getName(otherElement) + ", " + otherElement.configID + ", " + otherElement.mapfile + ")"
                        # Setting the actualElement to zero addressLength if this was not the first element of the duplicates
                        # This is needed to include only one of the duplicate elements with the real size in the report and not to distort the results
                        if otherElement.duplicateFlag is not None:
                            actualElement.addressLength = 0
                    else:
                        # Case 2: actualElement contains otherElement
                        if actualElement.addressStart <= otherElement.addressStart and actualElement.addressEnd() >= otherElement.addressEnd():
                            actualElement.containingOthersFlag = True
                        else:
                            # Case 3: actualElement is contained by otherElement
                            if actualElement.addressStart >= otherElement.addressStart and actualElement.addressEnd() <= otherElement.addressEnd():
                                # Setting the actualElement´s containmentFlag if it was not already set
                                if actualElement.containmentFlag is None:
                                    actualElement.containmentFlag = "Contained by (" + memEntryHandler.getName(otherElement) + ", " + otherElement.configID + ", " + otherElement.mapfile + ")"
                                    # Setting the actualElement to zero addressLength because this was contained by the otherElement
                                    # This is needed to include only one of these elements with the real size in the report and not to distort the results
                                    actualElement.addressLength = 0
                            else:
                                # Case 4: actualElement overlaps otherElement: otherElement starts inside and ends outside actualElement
                                if actualElement.addressStart < otherElement.addressStart and actualElement.addressEnd() < otherElement.addressEnd():
                                    actualElement.overlappingOthersFlag = True
                                else:
                                    # Case 5: actualElement is overlapped by otherElement: otherElement starts before and ends inside actualElement
                                    if actualElement.addressStart > otherElement.addressStart and actualElement.addressEnd() > otherElement.addressEnd():
                                        actualElement.overlapFlag = "Overlapped by (" + memEntryHandler.getName(otherElement) + ", " + otherElement.configID + ", " + otherElement.mapfile + ")"
                                        # Adjusting the addresses and length of the actualElement: reducing its size by the overlapping part
                                        actualElement.addressStart = otherElement.addressEnd() + 1
                                        actualElement.addressLength = actualElement.addressEnd() - actualElement.addressStart + 1
                                    # Case X: SW error, unhandled case...
                                    else:
                                        sc().error("MemoryManager::resolveOverlap(): Case X: SW error, unhandled case...")


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
        objectsInSections.append(sectionEntry)

    def createASectionReserve(sourceSection, addressEnd=None):
        # If we have received a specific addressEnd then we will use that one and recalculate the size of the section
        # In this case we need to make a deepcopy of the sourceSection because the SW will continue to work with it
        if addressEnd is not None:
            sourceSectionCopy = copy.deepcopy(sourceSection)
            sourceSectionCopy.moduleName = OBJECTS_IN_SECTIONS_SECTION_RESERVE
            sourceSectionCopy.setAddressesGivenEnd(addressEnd)
            objectsInSections.append(sourceSectionCopy)
        # If not, then the whole sourceSection will be stored as a reserve
        # In this case no copy needed because the SW does not need it anymore
        else:
            sourceSection.moduleName = OBJECTS_IN_SECTIONS_SECTION_RESERVE
            objectsInSections.append(sourceSection)

    def cutOffTheBeginningOfTheSection(sectionToCut, newAddressStart):
        # We need to store the addressEnd before cutting because after setting the new addressStart the addressEnd() calculation will return another value
        addressEndBeforeCutting = sectionToCut.addressEnd()
        if newAddressStart < addressEndBeforeCutting:
            sectionToCut.addressStart = newAddressStart
            sectionToCut.addressLength = addressEndBeforeCutting - sectionToCut.addressStart + 1
        else:
            sc().error("memoryMap.py::calculateObjectsInSections::cutOffTheBeginningOfTheSection(): " +
                       sectionToCut.configID + "::" + sectionToCut.section + ": The new newAddressStart(" +
                       newAddressStart + ") is after the addressEnd(" + addressEndBeforeCutting + ")!")

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
            if sectionCopy.configID != objectContainerElement.configID or objectContainerElement.addressLength == 0 or sectionCopy.addressStart > objectContainerElement.addressEnd():
                continue

            # Case 0: The object is completely overlapping the section
            if objectContainerElement.addressStart <= sectionCopy.addressStart and sectionCopy.addressEnd() <= objectContainerElement.addressEnd():
                # This object is overlapping the section completely. This means that all the following objects will be
                # outside the section, so we can continue with the next section.
                # We also need to mark that the section is fully loaded with the object
                sectionCopy = None
                break

            # Case 1: The object is overlapping the beginning of the section
            elif objectContainerElement.addressStart <= sectionCopy.addressStart and objectContainerElement.addressEnd() < sectionCopy.addressEnd():
                # Cutting off the beginning of the section
                cutOffTheBeginningOfTheSection(sectionCopy, objectContainerElement.addressEnd() + 1)

            # Case 2: The object is overlapping a part in the middle of the section
            elif sectionCopy.addressStart < objectContainerElement.addressStart and objectContainerElement.addressEnd() < sectionCopy.addressEnd():
                # Creating a sectionReserve
                createASectionReserve(sectionCopy, objectContainerElement.addressStart - 1)
                # Setting up the remaining section part
                cutOffTheBeginningOfTheSection(sectionCopy, objectContainerElement.addressEnd() + 1)

            # Case 3: The object is overlapping the end of the section
            elif sectionCopy.addressStart < objectContainerElement.addressStart <= sectionCopy.addressEnd() <= objectContainerElement.addressEnd():
                # Creating the sectionReserve
                createASectionReserve(sectionCopy, objectContainerElement.addressStart - 1)
                # This object is overlapping the end of the section. This means that all the following objects will be
                # outside the section, so we can continue with the next section.
                # We also need to mark that the section is fully loaded with the objects
                sectionCopy = None
                break

            # Case 4: The object is only starting after this section, it means that the following objects will also be outside the section.
            # So we have to create a reserve for the remaining part of the section and we can exit the object loop now and continue with the next section.
            elif sectionCopy.addressEnd() < objectContainerElement.addressStart:
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


def createReportPath(outputPath, projectName, reportName):
    shared_libs.emma_helper.mkDirIfNeeded(outputPath)
    memStatsFileName = projectName + "_" + reportName + "_" + timestamp + ".csv"
    return shared_libs.emma_helper.joinPath(outputPath, memStatsFileName)


def writeReportToDisk(reportPath, consumerCollection):
    """
    Writes the consumerCollection containig MemoryEntrys to CSV
    :param filepath: Absolute path to the csv file
    :param consumerCollection: List containing memEntrys
    """
    with open(reportPath, "w") as fp:
        writer = csv.writer(fp, delimiter=";", lineterminator="\n")
        header = [ADDR_START_HEX, ADDR_END_HEX, SIZE_HEX, ADDR_START_DEC, ADDR_END_DEC, SIZE_DEC, SIZE_HUMAN_READABLE,
                  SECTION_NAME, MODULE_NAME, CONFIG_ID, VAS_NAME, VAS_SECTION_NAME, MEM_TYPE, TAG, CATEGORY, DMA, MAPFILE, OVERLAP_FLAG,
                  CONTAINMENT_FLAG, DUPLICATE_FLAG, CONTAINING_OTHERS_FLAG, ADDR_START_HEX_ORIGINAL,
                  ADDR_END_HEX_ORIGINAL, SIZE_HEX_ORIGINAL, SIZE_DEC_ORIGINAL]
        writer.writerow(header)
        for row in consumerCollection:
            writer.writerow([
                row.addressStartHex(),
                row.addressEndHex(),
                row.addressLengthHex(),
                row.addressStart,
                row.addressEnd(),
                row.addressLength,
                shared_libs.emma_helper.toHumanReadable(row.addressLength),
                row.section,
                row.moduleName,
                row.configID,
                row.vasName,
                row.vasSectionName,
                row.memType,
                row.memTypeTag,
                row.category,
                row.dma,
                row.mapfile,
                row.overlapFlag,
                row.containmentFlag,
                row.duplicateFlag,
                row.containingOthersFlag,
                # Addresses are modified in case of overlapping so we will post the original values so that the changes can be seen
                row.addressStartOriginal if (row.overlapFlag is not None) else "",
                row.addressEndOriginal() if (row.overlapFlag is not None) else "",
                # Lengths are modified in case of overlapping, containment and duplication so we will post the original values so that the changes can be seen
                row.addressLengthHexOriginal() if ((row.overlapFlag is not None) or (row.containmentFlag is not None) or (row.duplicateFlag is not None)) else "",
                row.addressLengthOriginal if ((row.overlapFlag is not None) or (row.containmentFlag is not None) or (row.duplicateFlag is not None)) else ""
            ])
