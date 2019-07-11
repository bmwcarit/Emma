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


import re
import abc

import pypiscout as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper


class MapfileProcessor(abc.ABC):
    @abc.abstractmethod
    def __init__(self, configId, analyseDebug, verbosity, Werror):
        pass

    @abc.abstractmethod
    def processMapfiles(self, configuration):
        pass

    def evalMemRegion(self, physAddr, memoryCandidates):
        """
        Search within the memory regions to find the address given from a line
        :param configID: Configuration ID from globalConfig.json (referenced in patterns.json)
        :param physAddr: input address in hex or dec
        :return: None if nothing was found; otherwise the unique name of the memory region defined in addressSpaces*.json (DDR, ...)
        """
        address = shared_libs.emma_helper.unifyAddress(physAddr)[1]  # we only want dec >> [1]
        memRegion = None
        memType = None

        # Find the address in the memory map and set its type (int, ext RAM/ROM)
        for currAddrSpace in memoryCandidates:
            # TODO : This is wrong here, because it does not take into account that we have a size as well.
            # TODO : This means that it can be that the start of the element is inside of the memory region but it reaches trough it´s borders.
            # TODO : This could mean an error in either in the config or the mapfiles. Because of this info needs to be noted. (AGK)
            if int(memoryCandidates[currAddrSpace]["start"], 16) <= address <= int(memoryCandidates[currAddrSpace]["end"], 16):
                memRegion = currAddrSpace
                memType = memoryCandidates[currAddrSpace]["type"]
                # TODO : Maybe we should break here to improve performance. (AGK)
        # TODO: Do we want to save mapfile entrys which don't fit into the pre-configured adresses from addressSpaces*.json? If so add the needed code here (FM)

        # # Debug Print
        # if memRegion is None:
        #     if address != 0:
        #         print("<<<<memReg=None<<<<<<", physAddr, hex(physAddr))
        #         print(int(memoryCandidates[currAddrSpace]["start"], 16) <= address <= int(memoryCandidates[currAddrSpace]["end"], 16), ">>>>>",
        #               currAddrSpace, ">>>>>", memoryCandidates[currAddrSpace]["start"], "<=", hex(address), "<=", memoryCandidates[currAddrSpace]["end"])
        return memRegion, memType

    # FIXME This might probably belong to the Configuration class
    #       See ghsMapfileProcessor.py::__importData()
    def evalCategory(self, nameString):
        """
        Returns the category of a module. This function calls __categoriseModuleByKeyword()
        and __searchCategoriesJson() to evaluate a matching category.
        :param nameString: The name string of the module/section to categorise.
        :return: Category string
        """
        category = self.__searchCategoriesJson(nameString)

        if category is None:
            # If there is no match check for keyword specified in categoriesKeywordsJson
            category = self.__categoriseByKeyword(nameString)			# FIXME: add a training parameter; seems very dangerous for me having wildcards as a fallback option (MSc)

        if category is None:
            # If there is still no match
            category = "<unspecified>"
            # Add all unmatched module names so they can be appended to categories.json under "<unspecified>"
            self.categorisedFromKeywords.append((nameString, category))

        return category

    def __categoriseByKeyword(self, nameString):
        """
        Categorise a nameString by a keyword specified in categoriesKeywords.json
        :param nameString: The name-string of the module to categorise
        :return: The category string, None if no matching keyword found or the categoriesKeywords.json was not loaded
        """
        if self.categorisedKeywordsJson is not None:
            for category in self.categorisedKeywordsJson:
                for keyword in range(len(self.categorisedKeywordsJson[category])):
                    pattern = r"""\w*""" + self.categorisedKeywordsJson[category][keyword] + r"""\w*"""     # Search module name for substring specified in categoriesKeywords.json
                    if re.search(pattern, nameString) is not None:                                          # Check for first occurence
                        self.categorisedFromKeywords.append((nameString, category))                         # Append categorised module, is list of tuples because dict doesn't support duplicate keys
                        return category
        return None

    def __searchCategoriesJson(self, nameString):
        if self.categoriesJson is not None:
            categoryEval = []
            for category in self.categoriesJson:  # Iterate through keys
                for i in range(len(self.categoriesJson[category])):  # Look through category array
                    if nameString == self.categoriesJson[category][i]:  # If there is a match append the category
                        categoryEval.append(category)

            if categoryEval:
                categoryEval.sort()
                return ", ".join(categoryEval)
            else:
                return None
        else:
            return None


