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

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper


# Timestamp for the report file names
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Ms%S")


def resolveDuplicateContainmentOverlap(consumerCollection, memEntryHandler):
    # pylint: disable=too-many-nested-blocks, too-many-branches
    # Rationale: Because of the complexity of the task this function implements, reducing the number of nested blocks and branches is not possible.

    """
    Goes trough the consumerCollection and checks  and resolves all the elements for the following situations:
        1 - Duplicate
        2 - Containment
        3 - Overlap

    :param consumerCollection: A list of MemEntry objects. It must be ordered increasingly based on the startAddress attribute of the elements.
                               The elements of the list will be changed during the processing.
    :param memEntryHandler: A subclass of the MemEntryHandler class.
    :return: None
    """
    for actualElement in consumerCollection:
        for otherElement in consumerCollection:

            # Don't compare element with itself and only compare the same configID
            if actualElement.equalConfigID(otherElement) and not memEntryHandler.isEqual(actualElement, otherElement):

                # Case 0: actualElement and otherElement are completely separated : the otherElement begins only after the actualElement or the actualElement begins only after the otherElement
                if (actualElement.addressStart + actualElement.addressLength) <= otherElement.addressStart or actualElement.addressStart >= (otherElement.addressStart + otherElement.addressLength):
                    # There is not much to do here...
                    pass
                else:
                    # Case 1: actualElement and otherElement are duplicates
                    if actualElement.addressStart == otherElement.addressStart and actualElement.addressLength == otherElement.addressLength:
                        # Setting the actualElement´s duplicateFlag if it was not already set
                        if actualElement.duplicateFlag is None:
                            actualElement.duplicateFlag =  otherElement.configID + "::" + otherElement.mapfile + "::"  + otherElement.sectionName + ( "::"  + otherElement.objectName if otherElement.objectName != "" else "")
                        # Setting the actualElement to zero addressLength if this was not the first element of the duplicates
                        # This is needed to include only one of the duplicate elements with the real size in the report and not to distort the results
                        if otherElement.duplicateFlag is not None:
                            actualElement.addressLength = 0
                    else:
                        # Case 2: actualElement contains otherElement
                        if actualElement.addressStart <= otherElement.addressStart and (actualElement.addressStart + actualElement.addressLength) >= (otherElement.addressStart + otherElement.addressLength):
                            actualElement.containingOthersFlag = True
                        else:
                            # Case 3: actualElement is contained by otherElement
                            if actualElement.addressStart >= otherElement.addressStart and (actualElement.addressStart + actualElement.addressLength) <= (otherElement.addressStart + otherElement.addressLength):
                                # Setting the actualElement´s containmentFlag if it was not already set
                                if actualElement.containmentFlag is None:
                                    actualElement.containmentFlag = otherElement.configID + "::" + otherElement.mapfile + "::"  + otherElement.sectionName + ( "::"  + otherElement.objectName if otherElement.objectName != "" else "")
                                    # Setting the actualElement to zero addressLength because this was contained by the otherElement
                                    # This is needed to include only one of these elements with the real size in the report and not to distort the results
                                    actualElement.addressLength = 0
                            else:
                                # Case 4: actualElement overlaps otherElement: otherElement starts inside and ends outside actualElement
                                if actualElement.addressStart < otherElement.addressStart and (actualElement.addressStart + actualElement.addressLength) < (otherElement.addressStart + otherElement.addressLength):
                                    actualElement.overlappingOthersFlag = True
                                else:
                                    # Case 5: actualElement is overlapped by otherElement: otherElement starts before and ends inside actualElement
                                    if actualElement.addressStart > otherElement.addressStart and (actualElement.addressStart + actualElement.addressLength) > (otherElement.addressStart + otherElement.addressLength):
                                        actualElement.overlapFlag =  otherElement.configID + "::" + otherElement.mapfile + "::"  + otherElement.sectionName + ( "::"  + otherElement.objectName if otherElement.objectName != "" else "")
                                        # Adjusting the addresses and length of the actualElement: reducing its size by the overlapping part
                                        newAddressStart = otherElement.addressStart + otherElement.addressLength
                                        sizeOfOverlappingPart = newAddressStart - actualElement.addressStart
                                        actualElement.addressStart = newAddressStart
                                        actualElement.addressLength -= sizeOfOverlappingPart
                                    # Case X: SW error, unhandled case...
                                    else:
                                        sc().error("MemoryManager::resolveOverlap(): Case X: SW error, unhandled case...")


def calculateObjectsInSections(sectionContainer, objectContainer):
    """
    Creating a list of MemEntry objects from two lists of MemEntry objects that are representing the sections and objects.
    These two lists will merged together.
    From sections, new elements will be created:
        - Section entry: A MemEntry object that describes the section but does not use memory space.
        - Section reserce: A MemEntry object that describes the unused part of a section that was not filled up with objects.

    :param sectionContainer: A list of MemEntry objects. It must be ordered increasingly based on the startAddress attribute of the elements.
                             The overlapping, containing, duplicate sections must be are already edited and the addresses and lengths corrected.
    :param objectContainer: A list of MemEntry objects. It must be ordered increasingly based on the startAddress attribute of the elements.
                            The overlapping, containing, duplicate sections must be are already edited and the addresses and lengths corrected.
    :return: A list of MemEntry objects that contains all the elements of the sectionContainer and the objectContainer.
    """
    objectsInSections = []

    def createASectionEntry(sourceSection):
        """
        Function to create a sectionEntry based on the sourceSection.
        :param sourceSection: MemEntry object to create a section entry from.
        :return: None
        """
        sectionEntry = copy.deepcopy(sourceSection)
        sectionEntry.objectName = OBJECTS_IN_SECTIONS_SECTION_ENTRY
        sectionEntry.addressLength = 0
        objectsInSections.append(sectionEntry)

    def createASectionReserve(sourceSection, addressEnd=None):
        """
        Function to create a sectionReserveEntry based on the sourceSection.
        :param sourceSection: MemEntry object to create a section reserve from.
        :param addressEnd: The end address that the sourceSection shall have after the reserve creation.
                           If it is None, then the whole source section will be converted to a reserve.
        :return: None
        """
        # If we have received a specific addressEnd then we will use that one and recalculate the size of the section
        # In this case we need to make a deepcopy of the sourceSection because the SW will continue to work with it
        if addressEnd is not None:
            sourceSectionCopy = copy.deepcopy(sourceSection)
            sourceSectionCopy.objectName = OBJECTS_IN_SECTIONS_SECTION_RESERVE
            sourceSectionCopy.setAddressesGivenEnd(addressEnd)
            objectsInSections.append(sourceSectionCopy)
        # If not, then the whole sourceSection will be stored as a reserve
        # In this case no copy needed because the SW does not need it anymore
        else:
            sourceSection.objectName = OBJECTS_IN_SECTIONS_SECTION_RESERVE
            objectsInSections.append(sourceSection)

    def cutOffTheBeginningOfTheSection(sectionToCut, newAddressStart):
        """
        Function to cut off the beginning of a section.
        :param sectionToCut: MemEntry object that will have its beginning cut off.
        :param newAddressStart: The new start address value the section will have after the cut.
        :return:
        """
        # We need to make sure that the newAddressStart does not cause a cut more than the available length
        lengthThatWillBeCutOff = newAddressStart - sectionToCut.addressStart
        if lengthThatWillBeCutOff <= sectionToCut.addressLength:
            sectionToCut.addressStart = newAddressStart
            sectionToCut.addressLength -= lengthThatWillBeCutOff
        else:
            sc().error("memoryMap.py::calculateObjectsInSections::cutOffTheBeginningOfTheSection(): " +
                       sectionToCut.configID + "::" + sectionToCut.sectionName + ": The new newAddressStart(" +
                       str(newAddressStart) + ") would cause a cut that is bigger than the addressLength! (" + str(lengthThatWillBeCutOff) + "vs " + str(sectionToCut.addressLengthing) + ")")

    for sectionContainerElement in sectionContainer:
        # Creating a section entry
        createASectionEntry(sectionContainerElement)

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
            if sectionCopy.configID != objectContainerElement.configID or objectContainerElement.addressLength == 0 or sectionCopy.addressStart >= (objectContainerElement.addressStart + objectContainerElement.addressLength):
                continue

            # Case 0: The object is completely overlapping the section
            if objectContainerElement.addressStart <= sectionCopy.addressStart and (sectionCopy.addressStart + sectionCopy.addressLength) <= (objectContainerElement.addressStart + objectContainerElement.addressLength):
                # This object is overlapping the section completely. This means that all the following objects will be
                # outside the section, so we can continue with the next section.
                # We also need to mark that the section is fully loaded with the object
                sectionCopy = None
                break

            # Case 1: The object is overlapping the beginning of the section
            elif objectContainerElement.addressStart <= sectionCopy.addressStart and (objectContainerElement.addressStart + objectContainerElement.addressLength) < (sectionCopy.addressStart + sectionCopy.addressLength):
                # Cutting off the beginning of the section
                newSectionAddressStart = objectContainerElement.addressStart + objectContainerElement.addressLength
                cutOffTheBeginningOfTheSection(sectionCopy, newSectionAddressStart)

            # Case 2: The object is overlapping a part in the middle of the section
            elif sectionCopy.addressStart < objectContainerElement.addressStart and (objectContainerElement.addressStart + objectContainerElement.addressLength) < (sectionCopy.addressStart + sectionCopy.addressLength):
                # Creating a sectionReserve
                createASectionReserve(sectionCopy, objectContainerElement.addressStart - 1)
                # Setting up the remaining section part: the section will start after tge object
                newSectionAddressStart = objectContainerElement.addressStart + objectContainerElement.addressLength
                cutOffTheBeginningOfTheSection(sectionCopy, newSectionAddressStart)

            # Case 3: The object is overlapping the end of the section
            elif sectionCopy.addressStart < objectContainerElement.addressStart <= (sectionCopy.addressStart + sectionCopy.addressLength) <= (objectContainerElement.addressStart + objectContainerElement.addressLength):
                # Creating the sectionReserve
                createASectionReserve(sectionCopy, objectContainerElement.addressStart - 1)
                # This object is overlapping the end of the section. This means that all the following objects will be
                # outside the section, so we can continue with the next section.
                # We also need to mark that the section is fully loaded with the objects
                sectionCopy = None
                break

            # Case 4: The object is only starting after this section, it means that the following objects will also be outside the section.
            # So we have to create a reserve for the remaining part of the section and we can exit the object loop now and continue with the next section.
            elif (sectionCopy.addressStart + sectionCopy.addressLength) <= objectContainerElement.addressStart:
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
    """
    Function to create a string representing the path of a report.
    :param outputPath: The folder where the report will be.
    :param projectName: The name of the project.
    :param reportName: The name of the report.
    :return: The created path string.
    """
    shared_libs.emma_helper.mkDirIfNeeded(outputPath)
    memStatsFileName = projectName + "_" + reportName + "_" + TIMESTAMP + ".csv"
    return shared_libs.emma_helper.joinPath(outputPath, memStatsFileName)


def collectCompilerSpecificHeaders(consumerCollection):
    """
    Function to create a list of the headers that the compiler specific data of a consumer collection has.
    :param consumerCollection: The consumer collection that has elements with compiler specific data.
    :return: List of strings.
    """
    collectedHeaders = []

    for element in consumerCollection:
        for key in element.compilerSpecificData.keys():
            if key not in collectedHeaders:
                collectedHeaders.append(key)

    return collectedHeaders


def writeReportToDisk(reportPath, consumerCollection):
    """
    Writes the consumerCollection containing MemEntry objects to a CSV file.
    :param reportPath: A path of the CSV that needs to be created.
    :param consumerCollection: A list of MemEntry objects.
    """

    # Opening the file
    with open(reportPath, "w") as fp:
        # The writer object that will be used for creating the CSV data
        writer = csv.writer(fp, delimiter=";", lineterminator="\n")

        # Creating the list with the first part of the static headers
        headers = [ADDR_START_HEX, ADDR_END_HEX, SIZE_HEX, ADDR_START_DEC, ADDR_END_DEC, SIZE_DEC, SIZE_HUMAN_READABLE, SECTION_NAME, OBJECT_NAME, CONFIG_ID]

        # Extending it with the compiler specific headers
        compilerSpecificHeaders = collectCompilerSpecificHeaders(consumerCollection)
        headers.extend(compilerSpecificHeaders)

        # Collecting the rest of the static headers
        headers.extend([MEM_TYPE, MEM_TYPE_TAG, CATEGORY, MAPFILE, OVERLAP_FLAG, CONTAINMENT_FLAG, DUPLICATE_FLAG, CONTAINING_OTHERS_FLAG, ADDR_START_HEX_ORIGINAL, ADDR_END_HEX_ORIGINAL, SIZE_HEX_ORIGINAL, SIZE_DEC_ORIGINAL, FQN])

        # Writing the headers to the CSV file
        writer.writerow(headers)

        # Writing the data lines to the file
        for row in consumerCollection:
            # Collecting the first part of the static data for the current row
            rowData = [row.addressStartHex(), row.addressEndHex(), row.addressLengthHex(), row.addressStart, row.addressEnd(), row.addressLength, shared_libs.emma_helper.toHumanReadable(row.addressLength), row.sectionName, row.objectName, row.configID]

            # Extending it with the data part of the compiler specific data pairs of this MemEntry object
            for compilerSpecificHeader in compilerSpecificHeaders:
                rowData.append(row.compilerSpecificData[compilerSpecificHeader] if compilerSpecificHeader in row.compilerSpecificData else "")

            # Collecting the rest of the static data for the current row
            rowData.extend([
                row.memType,
                row.memTypeTag,
                row.category,
                row.mapfile,
                row.overlapFlag,
                row.containmentFlag,
                row.duplicateFlag,
                row.containingOthersFlag,
                # Addresses are modified in case of overlapping so we will post the original values so that the changes can be seen
                row.addressStartHexOriginal() if (row.overlapFlag is not None) else "",
                row.addressEndHexOriginal() if (row.overlapFlag is not None) else "",
                # Lengths are modified in case of overlapping, containment and duplication so we will post the original values so that the changes can be seen
                row.addressLengthHexOriginal() if ((row.overlapFlag is not None) or (row.containmentFlag is not None) or (row.duplicateFlag is not None)) else "",
                row.addressLengthOriginal if ((row.overlapFlag is not None) or (row.containmentFlag is not None) or (row.duplicateFlag is not None)) else "",
                # FQN
                row.configID + "::" + row.mapfile + "::"  + row.sectionName + ( "::"  + row.objectName if row.objectName != "" and row.objectName != OBJECTS_IN_SECTIONS_SECTION_ENTRY and row.objectName != OBJECTS_IN_SECTIONS_SECTION_RESERVE else "")
            ])

            # Writing the data to the file
            writer.writerow(rowData)
