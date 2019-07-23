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

from shared_libs.stringConstants import *
import shared_libs.emma_helper


class MapfileProcessor(abc.ABC):
    @abc.abstractmethod
    def processMapfiles(self, configId, configuration, analyseDebug):
        pass

    @staticmethod
    def fillOutMemoryRegionsAndMemoryTypes(listOfMemEntryObjects, configuration, removeElementsWithoutMemoryRegionOrType, memoryRegionsToExcludeFromMapfiles=None):
        """
        Search within the memory regions to find the address given from a line
        :param configID: Configuration ID from globalConfig.json (referenced in patterns.json)
        :param physAddr: input address in hex or dec
        :return: None if nothing was found; otherwise the unique name of the memory region defined in addressSpaces*.json (DDR, ...)
        """
        def printElementRemovalMessage(memEntry, loggerLevel, reason):
            object_name = ("::" + memEntry.objectName) if hasattr(memEntry, "module") else ""
            loggerLevel("The element: \"" + memEntry.mapfile + "::" + memEntry.sectionName + object_name +
                        " (@" + memEntry.addressStartHex() + ", size: " + str(memEntry.addressLength) + " B)\" of the configID \"" +
                        memEntry.configID + "\" was removed. Reason: " + reason)

        def isElementMarkedAsExcluded(excludedMemoryRegionsFromMapfiles, memEntry):
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
                if (int(memoryCandidates[memoryRegion]["start"], 16) <= element.addressStart) and (element.addressEnd() <= int(memoryCandidates[memoryRegion]["end"], 16)):
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
                    element.Tag = UNKNOWN_MEM_REGION
                    element.memType = UNKNOWN_MEM_TYPE
                    listOfElementsToKeep.append(element)
                # If we have to remove it, then we will print a report
                else:
                    printElementRemovalMessage(element, sc().warning, "It does not belong to any of the memory regions!")
        # Overwriting the content of the list of memory entry objects with the elements that we will keep
        listOfMemEntryObjects[:] = listOfElementsToKeep
