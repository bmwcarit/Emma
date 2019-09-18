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


import abc

from pypiscout.SCout_Logger import Logger as sc

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import


class MapfileProcessor(abc.ABC):
    """
    A partly abstract parent class for the compiler specific mapfile processors.
    Defining interfaces and common functionality for subclasses that will be used for mapfile processing.
    """
    @abc.abstractmethod
    def processMapfiles(self, configId, configuration, analyseDebug):
        """
        Abstract function to process mapfiles.
        :param configId: The configId to which the configuration belongs to.
        :param configuration: The configuration based on which the mapfiles can be processed.
        :param analyseDebug: True if the debug sections and objects need to be analysed as well, False otherwise.
        :return: A tuple of two lists of MemEntry objects representing the sections and objects.
                 Illustration: (sectionCollection, objectCollection), where sectionCollection is list(MemEntry) and objectCollection is list(MemEntry).
        """

    @staticmethod
    def fillOutMemoryRegionsAndMemoryTypes(listOfMemEntryObjects, configuration, removeElementsWithoutMemoryRegionOrType, memoryRegionsToExcludeFromMapfiles=None):
        """
        Fills out the memory type and the memory regions in a list of MemEntry objects.
        This function needs to be called by the subclasses of this class during the mapfile processing,
        after creating a list of MemEntry objects that have the following data filled out in them:
            - configID
            - mapfileName
            - addressStart
            - addressLength
            - sectionName
            - objectName
            - compilerSpecificData
        :param listOfMemEntryObjects: The list or MemEntry objects that will be updated.
        :param configuration: That belongs to the same configId as the MemEntry objects.
        :param removeElementsWithoutMemoryRegionOrType: True if elements to which no memory type or region was found shall be removed, False otherwise.
        :param memoryRegionsToExcludeFromMapfiles: Dictionary, based on which MemEntry objects can be excluded if they belong to a memory region that is ignored for the mapfile, the object was created from.
                                                   The dictionary contains mapfile names as keys and lists of strings with memory region names as values.
                                                   If the functionality is not needed, then it shall be set to None.
        :return: None
        """
        def printElementRemovalMessage(memEntry, loggerLevel, reason):
            """
            Function to print out a message informing the user that an element will be removed.
            :param memEntry: MemoryEntry that will be removed.
            :param loggerLevel: Loglevel with which the message needs to be printed.
            :param reason: Reason why the element will be removed.
            :return: None
            """
            objectName = ("::" + memEntry.objectName) if hasattr(memEntry, "module") else ""
            loggerLevel(f"Element: {memEntry.configID}::{memEntry.mapfile}::{memEntry.sectionName}" + ("::"  + memEntry.objectName if memEntry.objectName != "" else "")
                        + f" `(size: " + str(memEntry.addressLength) + f" B, starts @{memEntry.addressStartHex()}) was removed. Reason: " + reason)

        def isElementMarkedAsExcluded(excludedMemoryRegionsFromMapfiles, memEntry):
            """
            Function to check whether the element was marked as excluded.
            :param excludedMemoryRegionsFromMapfiles: See docstring of fillOutMemoryRegionsAndMemoryTypes().
            :param memEntry: MemEntry object for which it should be decided whether it is excluded or not.
            :return: True if element was marked as excluded, False otherwise.
            """
            result = False
            # If there is an exclusion list for memory regions per mapfiles
            if excludedMemoryRegionsFromMapfiles is not None:
                # If there is an excluded memory region for the mapfile of the memory entry
                if memEntry.mapfile in excludedMemoryRegionsFromMapfiles.keys():
                    # If the memory region of the mem entry is excluded
                    if memEntry.memTypeTag in excludedMemoryRegionsFromMapfiles[memEntry.mapfile]:
                        result = True
            return result

        listOfElementsToKeep = []
        memoryCandidates = configuration["addressSpaces"]["memory"]

        # For every memEntryObject
        for element in listOfMemEntryObjects:
            # For every defined memory region
            for memoryRegion in memoryCandidates:
                # If the element is in this memoryRegion
                # For elements that do not have addressEnd the addressStart comparison is enough
                if int(memoryCandidates[memoryRegion]["start"], 16) <= element.addressStart:
                    if element.addressEnd() is None or (element.addressEnd() <= int(memoryCandidates[memoryRegion]["end"], 16)):
                        # Then we store the memoryRegion data in the element
                        element.memTypeTag = memoryRegion
                        element.memType = memoryCandidates[memoryRegion]["type"]
                        # If this region is not excluded for the mapfile the element belongs to then we will keep it
                        if not isElementMarkedAsExcluded(memoryRegionsToExcludeFromMapfiles, element):
                            listOfElementsToKeep.append(element)
                        else:
                            printElementRemovalMessage(element, sc().debug, "Its memory region was excluded for this mapfile!")
                        break
            # If we have reached this point, then we did not find a memory region
            else:
                # If we do not have to remove elements without a memory region then we will fill it out with the default values and keep it
                if not removeElementsWithoutMemoryRegionOrType:
                    element.memTypeTag = UNKNOWN_MEM_REGION
                    element.memType = UNKNOWN_MEM_TYPE
                    listOfElementsToKeep.append(element)
                # If we have to remove it, then we will print a report
                else:
                    printElementRemovalMessage(element, sc().warning, "It does not belong to any of the memory regions!")
        # Overwriting the content of the list of memory entry objects with the elements that we will keep
        listOfMemEntryObjects[:] = listOfElementsToKeep
