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
        def printElementRemovalWarning(element):
            object_name = ("::" + element.moduleName) if hasattr(element, "module") else ""
            sc().warning("The element: \"" + element.mapfile + "::" + element.section + object_name +
                         " (@" + element.addressStartHex + ", size: " + str(element.addressLength) + " B)\" of the configID \"" +
                         element.configID + "\" does not belong to any of the memory regions!")

        def isElementInTheFromMapfileExcludedRegions(memoryRegionsToExcludeFromMapfiles, element):
            result = False
            if memoryRegionsToExcludeFromMapfiles is not None:
                if element.mapfile in memoryRegionsToExcludeFromMapfiles.keys():
                    if element.memTypeTag in memoryRegionsToExcludeFromMapfiles[element.mapfile]:
                        # Here we do not need to print the warning because they are ignored with purpose
                        result = True
            return result

        listOfElementsToKeep = []
        memoryCandidates = configuration["addressSpaces"]["memory"]

        # For every memEntryObject
        for element in listOfMemEntryObjects:
            # Store the addresses of the element
            _, addressStart = shared_libs.emma_helper.unifyAddress(element.addressStart)
            _, addressEnd = shared_libs.emma_helper.unifyAddress(element.addressEnd)

            # For every defined memory region
            for memoryRegion in memoryCandidates:
                # If the element is in this memoryRegion
                if (int(memoryCandidates[memoryRegion]["start"], 16) <= addressStart) and (addressEnd <= int(memoryCandidates[memoryRegion]["end"], 16)):
                    # Then we store the memoryRegion data in the element
                    element.memTypeTag = memoryRegion
                    element.memType = memoryCandidates[memoryRegion]["type"]
                    # If this region is not excluded for the mapfile the element belongs to then we will keep it
                    if not isElementInTheFromMapfileExcludedRegions(memoryRegionsToExcludeFromMapfiles, element):
                        listOfElementsToKeep.append(element)
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
                    printElementRemovalWarning(element)
        # Overwriting the content of the list of memory entry objects with the elements that we will keep
        listOfMemEntryObjects[:] = listOfElementsToKeep
