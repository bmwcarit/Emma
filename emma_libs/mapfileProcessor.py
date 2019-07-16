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
    def processMapfiles(self, configId, configuration, analyseDebug, verbosity, wError):
        pass

    @staticmethod
    def fillOutMemoryRegionsAndMemoryTypes(listOfMemEntryObjects, configuration, removeElementsWithoutMemoryRegionOrType, memoryRegionsToExcludeFromMapfiles = None):
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

        listOfElementsToKeep = []
        memoryCandidates = configuration["addressSpaces"]["memory"]

        for element in listOfMemEntryObjects:
            _, addressStart = shared_libs.emma_helper.unifyAddress(element.addressStart)
            _, addressEnd = shared_libs.emma_helper.unifyAddress(element.addressEnd)

            for memoryRegion in memoryCandidates:
                if (int(memoryCandidates[memoryRegion]["start"], 16) <= addressStart) and (addressEnd <= int(memoryCandidates[memoryRegion]["end"], 16)):
                    element.Tag = memoryRegion
                    element.memType = memoryCandidates[memoryRegion]["type"]
                    elementFoundInMemoryRegionsToExcludeFromMapfiles = False
                    if memoryRegionsToExcludeFromMapfiles is not None:
                        if element.mapfile in memoryRegionsToExcludeFromMapfiles.keys():
                            if element.Tag in memoryRegionsToExcludeFromMapfiles[element.mapfile]:
                                # Here we do not need to print the warning because they are ignored with purpose
                                elementFoundInMemoryRegionsToExcludeFromMapfiles = True
                    if not elementFoundInMemoryRegionsToExcludeFromMapfiles:
                        listOfElementsToKeep.append(element)
                    break
            else:
                if not removeElementsWithoutMemoryRegionOrType:
                    element.Tag = UNKNOWN_MEM_REGION
                    element.memType = UNKNOWN_MEM_TYPE
                    listOfElementsToKeep.append(element)
                else:
                    printElementRemovalWarning(element)
