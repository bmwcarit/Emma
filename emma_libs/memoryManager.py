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


import sys
import os
import re
import bisect
import csv
import datetime

import pypiscout as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper
import emma_libs.mapfileRegexes
import emma_libs.memoryEntry


# Global timestamp
# (parsed from the .csv file from ./memStats)
timestamp = datetime.datetime.now().strftime("%Y-%m-%d - %Hh%Ms%S")


class MemoryManager:
    # TODO : After discussions with MSc, this class could be cut up into more parts. (AGK)
    """
    Class for reading and saving/sorting the mapfiles
    """
    def __init__(self, args, categoriesPath, categoriesKeywordsPath, fileIdentifier, regexData):
        """
        Memory manager for mapfile information aggregation.
        :param args: command line arguments
        :param categoriesPath: Path to a projects categories JSON
        :param categoriesKeywordsPath: Path to a projects categoriesKeywords JSON
        :param fileIdentifier: String for the summary filename written in writeSummary()
        :param regexData: An object derived from class RegexPatternBase holding the regex patterns
        """
        def readGlobalConfigJson(configPath):
            """
            :param configPath: file path
            :return: the globalConfig dict
            """
            # Load global config file
            globalConfig = shared_libs.emma_helper.readJson(configPath)

            # Loading the config files of the defined configID-s
            for configID in list(globalConfig.keys()):                              # List of keys required so we can remove the ignoreConfigID entrys
                if IGNORE_CONFIG_ID in globalConfig[configID].keys():
                    # Skip configID if ["ignoreConfigID"] is True
                    if type(globalConfig[configID][IGNORE_CONFIG_ID]) is not bool:
                        # Check that flag has the correct type
                        sc.error("The " + IGNORE_CONFIG_ID + " of " + configID + " has a type " + str(type(globalConfig[configID][IGNORE_CONFIG_ID])) + " instead of bool. " +
                                    "Please be sure to use correct JSON syntax: boolean constants are written true and false.")
                        sys.exit(-10)
                    elif globalConfig[configID][IGNORE_CONFIG_ID] is True:
                        globalConfig.pop(configID)
                        if len(globalConfig) < 1 and self.args.verbosity <= 1:
                            sc.warning("No configID left; all were ignored.")
                        continue

                # Loading the addressSpaces
                if "addressSpacesPath" in globalConfig[configID].keys():
                    globalConfig[configID]["addressSpaces"] = shared_libs.emma_helper.readJson(shared_libs.emma_helper.joinPath(self.projectPath, globalConfig[configID]["addressSpacesPath"]))

                    # Removing the imported memory entries if they are listed in IGNORE_MEM_TYPE key
                    if IGNORE_MEMORY in globalConfig[configID]["addressSpaces"].keys():
                        for memoryToIgnore in globalConfig[configID]["addressSpaces"][IGNORE_MEMORY]:
                            if globalConfig[configID]["addressSpaces"]["memory"][memoryToIgnore]:
                                globalConfig[configID]["addressSpaces"]["memory"].pop(memoryToIgnore)
                                sc.info("The memory entry \"" + memoryToIgnore + "\" of the configID \"" + configID + "\" is marked to be ignored...")
                            else:
                                sc.error("The key " + memoryToIgnore + " which is in the ignore list, does not exist in the memory object of " + globalConfig[configID]["addressSpacesPath"])
                                sys.exit(-10)
                else:
                    sc.error("The " + CONFIG_ID + " does not have the key: " + "addressSpacesPath")
                    sys.exit(-10)

                # Loading the sections if the file is present (only needed in case of VAS-es)
                if "virtualSectionsPath" in globalConfig[configID].keys():
                    globalConfig[configID]["virtualSections"] = shared_libs.emma_helper.readJson(shared_libs.emma_helper.joinPath(self.projectPath, globalConfig[configID]["virtualSectionsPath"]))

                # Loading the patterns
                if "patternsPath" in globalConfig[configID].keys():
                    globalConfig[configID]["patterns"] = shared_libs.emma_helper.readJson(shared_libs.emma_helper.joinPath(self.projectPath, globalConfig[configID]["patternsPath"]))
                else:
                    sc.error("The " + CONFIG_ID + " does not have the key: " + "patternsPath")
                    sys.exit(-10)

                # Flag to load a monolith file only once; we don't do it here since we might work with DMA only
                globalConfig[configID]["monolithLoaded"] = False
                # Flag to sort monolith table only once; we don't do it here since we might work with DMA only
                globalConfig[configID]["sortMonolithTabularised"] = False
            return globalConfig

        self.args = args
        # Attributes for file paths
        self.analyseDebug = args.analyse_debug
        self.projectPath = args.project
        self.project = shared_libs.emma_helper.projectNameFromPath(shared_libs.emma_helper.joinPath(args.project))
        self.mapfileRootPath = shared_libs.emma_helper.joinPath(args.mapfiles)
        self.__categoriesFilePath = categoriesPath
        self.__categoriesKeywordsPath = categoriesKeywordsPath
        shared_libs.emma_helper.checkIfFolderExists(self.projectPath)

        # Regex data, has to be a sub-class of RegexPatternBase
        self.regexPatternData = regexData

        # Load local config JSONs from global config
        self.globalConfig = readGlobalConfigJson(configPath=shared_libs.emma_helper.joinPath(self.projectPath, "globalConfig.json"))
        sc.info("Imported " + str(len(self.globalConfig)) + " global config entries")

        # Loading the categories config files. These files are optional, if they are not present we will store None instead.
        if os.path.exists(self.__categoriesFilePath):
            self.categoriesJson = shared_libs.emma_helper.readJson(self.__categoriesFilePath)
        else:
            self.categoriesJson = None
            sc.warning("There was no " + os.path.basename(self.__categoriesFilePath) + " file found, the categorization based on this will be skipped.")
        if os.path.exists(self.__categoriesKeywordsPath):
            self.categorisedKeywordsJson = shared_libs.emma_helper.readJson(self.__categoriesKeywordsPath)
        else:
            self.categorisedKeywordsJson = None
            sc.warning("There was no " + os.path.basename(self.__categoriesKeywordsPath) + " file found, the categorization based on this will be skipped.")

        # Init consumer data
        self.consumerCollection = []        # the actual data (contains instances of `MemEntry`)
        self.categorisedFromKeywords = []   # This list will be filled with matches from category keywords, needed in createCategoriesJson()
        # self.containingOthers = set()

        # The file identifier is used for the filename in writeReport()
        self.__fileIdentifier = fileIdentifier

        # Add map and monolith files
        self.__addMonolithsToGlobalConfig()
        self.__addMapfilesToGlobalConfig()
        self.__validateConfigIDs()

        # Filename for csv file
        self.outputPath = createMemStatsFilepath(args.dir, args.subdir, self.__fileIdentifier, self.project)

        def checkMonolithSections():
            """
            The function collects the VAS sections from the monolith files and from the global config and from the monolith mapfile
            :return: nothing
            """
            foundInConfigID = []
            foundInMonolith = []

            # Extract sections from monolith file
            monolithPattern = emma_libs.mapfileRegexes.UpperMonolithPattern()
            for configID in self.globalConfig:
                # Check if a monolith was loaded to this configID that can be checked
                if self.globalConfig[configID]["monolithLoaded"]:
                    for entry in self.globalConfig[configID]["patterns"]["monoliths"]:
                        with open(self.globalConfig[configID]["patterns"]["monoliths"][entry]["associatedFilename"], "r") as monolithFile:
                            monolithContent = monolithFile.readlines()
                        for line in monolithContent:
                            lineComponents = re.search(monolithPattern.pattern, line)
                            if lineComponents:  # if match
                                foundInMonolith.append(lineComponents.group(monolithPattern.Groups.section))

                    for vas in self.globalConfig[configID]["virtualSections"]:
                        foundInConfigID += self.globalConfig[configID]["virtualSections"][vas]

                    # Compare sections from configID with found in monolith file
                    sectionsNotInConfigID = set(foundInMonolith) - set(foundInConfigID)
                    if sectionsNotInConfigID:
                        sc.warning("Monolith File has the following sections. You might want to add it to the respective VAS in " + self.globalConfig[configID]["virtualSectionsPath"] + "!")
                        print(sectionsNotInConfigID)
                        sc.warning("Still continue? (y/n)") if not self.args.Werror else sys.exit(-10)
                        text = input("> ") if not self.args.noprompt else sys.exit(-10)
                        if text != "y":
                            sys.exit(-10)
            return

        checkMonolithSections()

    def __addTabularisedMonoliths(self, configID):
        """
        Manages Monolith selection, parsing and converting to a list
        :param configID: configID
        :return: nothing
        """
        def loadMonolithMapfileOnce(configID):
            """
            Load monolith mapfile (only once)
            :return: Monolith file content
            """

            if not self.globalConfig[configID]["monolithLoaded"]:
                mapfileIndexChosen = 0                  # Take the first monolith file in list (default case)
                numMonolithFiles = len(self.globalConfig[configID]["patterns"]["monoliths"])
                keyMonolithMapping = {}

                # Update globalConfig with all monolith filenames
                for key, monolith in enumerate(self.globalConfig[configID]["patterns"]["monoliths"]):
                    keyMonolithMapping.update({str(key): self.globalConfig[configID]["patterns"]["monoliths"][monolith]["associatedFilename"]})

                if numMonolithFiles > 1:
                    sc.info("More than one monolith file detected. Which to chose (1, 2, ...)?")
                    # Display files
                    for key, monolith in keyMonolithMapping.items():
                        print(" ", key.ljust(10), monolith)
                    # Ask for index which file to chose
                    mapfileIndexChosen = shared_libs.emma_helper.Prompt.idx() if not self.args.noprompt else sys.exit(-10)
                    while not (0 <= mapfileIndexChosen < numMonolithFiles):
                        sc.warning("Invalid value; try again:")
                        if self.args.Werror:
                            sys.exit(-10)
                        mapfileIndexChosen = shared_libs.emma_helper.Prompt.idx() if not self.args.noprompt else sys.exit(-10)
                elif numMonolithFiles < 1:
                    sc.error("No monolith file found but needed for processing")
                    sys.exit(-10)

                # Finally load the file
                self.globalConfig[configID]["monolithLoaded"] = True
                with open(keyMonolithMapping[str(mapfileIndexChosen)], "r") as fp:
                    content = fp.readlines()
                return content

        def tabulariseAndSortOnce(monolithContent, configID):
            """
            Parses the monolith file and returns a "table" (addresses are int's) of the following structure:
            table[n-th_entry][0] = virtual(int), ...[1] = physical(int), ...[2] = offset(int), ...[3] = size(int), ...[4] = section(str)
            Offset = physical - virtual
            :param monolithContent: Content from monolith as text (all lines)
            :return: list of lists
            """
            table = []  # "headers": virtual, physical, size, section
            monolithPattern = emma_libs.mapfileRegexes.UpperMonolithPattern()
            for line in monolithContent:
                match = re.search(emma_libs.mapfileRegexes.UpperMonolithPattern().pattern, line)
                if match:
                    table.append([
                        int(match.group(monolithPattern.Groups.virtualAdress), 16),
                        int(match.group(monolithPattern.Groups.physicalAdress), 16),
                        int(match.group(monolithPattern.Groups.physicalAdress), 16) - int(match.group(monolithPattern.Groups.virtualAdress), 16),
                        int(match.group(monolithPattern.Groups.size), 16),
                        match.group(monolithPattern.Groups.section)
                    ])
            self.globalConfig[configID]["sortMonolithTabularised"] = True
            return table

        # Load and register Monoliths
        monolithContent = loadMonolithMapfileOnce(configID)
        if not self.globalConfig[configID]["sortMonolithTabularised"]:
            self.globalConfig[configID]["sortMonolithTabularised"] = tabulariseAndSortOnce(monolithContent, configID)

    # TODO : This could be renamed to "__addFileTypesForAConfigId" (AGK)
    def __addFilesPerConfigID(self, configID, fileType):
        """
        Adds the found full absolute path of the found file as new element to `self.globalConfig[configID]["patterns"]["mapfiles"]["associatedFilename"]`
        Deletes elements from `self.globalConfig[configID]["patterns"]["mapfiles"]` which were not found and prints a warning for each
        :param fileType: Either "patterns" (=default) for mapfiles or "monoliths" for monolith files
        :return: Number of files detected
        """
        # Find mapfiles
        # TODO : Would this not make more sense to execute it the other way around? (for every regex, for every file) (AGK)
        # TODO : Also, could we save time by breaking earlier and not checking all the files if we have found something? (that would remove config error detection) (AGK)
        # TODO : The function name is __addFilesPerConfigID but the search path is fixed to the self.mapfileRootPath. This is confusing. It shall be either more generic or renamed (AGK)
        for file in os.listdir(self.mapfileRootPath):
            for entry in self.globalConfig[configID]["patterns"][fileType]:
                foundFiles = []
                for regex in self.globalConfig[configID]["patterns"][fileType][entry]["regex"]:
                    searchCandidate = shared_libs.emma_helper.joinPath(self.mapfileRootPath, file)
                    match = re.search(regex, searchCandidate)
                    if match:
                        foundFiles.append(os.path.abspath(searchCandidate))
                if foundFiles:
                    self.globalConfig[configID]["patterns"][fileType][entry]["associatedFilename"] = foundFiles[0]
                    print("\t\t\t Found " + fileType + ": ", foundFiles[0])
                    if len(foundFiles) > 1:
                        sc.warning("Ambiguous regex pattern in '" + self.globalConfig[configID]["patternsPath"] + "'. Selected '" + foundFiles[0] + "'. Regex matched: " + "".join(foundFiles))
                        # TODO : we could have a logging class that could handle this exit if all warnings are errors thing. (AGK)
                        if self.args.Werror:
                            sys.exit(-10)

        # Check for found files in patterns and do some clean-up
        # We need to convert the keys into a temporary list in order to avoid iterating on the original which may be changed during the loop, that causes a runtime error
        for entry in list(self.globalConfig[configID]["patterns"][fileType]):
            if "associatedFilename" not in self.globalConfig[configID]["patterns"][fileType][entry]:
                sc.warning("No file found for ", str(entry).ljust(20), "(pattern:", ''.join(self.globalConfig[configID]["patterns"][fileType][entry]["regex"]) + " );", "skipping...")
                if self.args.Werror:
                    sys.exit(-10)
                del self.globalConfig[configID]["patterns"][fileType][entry]
        return len(self.globalConfig[configID]["patterns"][fileType])

    def __addMonolithsToGlobalConfig(self):

        def ifAnyNonDMA(configID):
            """
            Checks if non-DMA files were found
            Do not run this before mapfiles are searched (try: `findMapfiles` and evt. `findMonolithMapfiles` before)
            :return: True if files which require address translation were found; otherwise False
            """
            entryFound = False
            for entry in self.globalConfig[configID]["patterns"]["mapfiles"]:
                if "VAS" in self.globalConfig[configID]["patterns"]["mapfiles"][entry]:
                    entryFound = True
                    # TODO : here, a break could improve the performance (AGK)
            return entryFound

        for configID in self.globalConfig:
            sc.info("Processing configID \"" + configID + "\" for monolith files")
            if ifAnyNonDMA(configID):
                numMonolithMapFiles = self.__addFilesPerConfigID(configID, fileType="monoliths")
                if numMonolithMapFiles > 1:
                    sc.warning("More than one monolith file found; Result may be non-deterministic")
                    if self.args.Werror:
                        sys.exit(-10)
                elif numMonolithMapFiles < 1:
                    sc.error("No monolith files was detected but some mapfiles require address translation (VASes used)")
                    sys.exit(-10)
                self.__addTabularisedMonoliths(configID)

    def __addMapfilesToGlobalConfig(self):
        for configID in self.globalConfig:
            sc.info("Processing configID \"" + configID + "\"")
            numMapfiles = self.__addFilesPerConfigID(configID=configID, fileType="mapfiles")
            sc.info(str(numMapfiles) + " mapfiles found")

    def __validateConfigIDs(self):
        configIDsToDelete = []

        # Search for invalid configIDs
        for configID in self.globalConfig:
            numMapfiles = len(self.globalConfig[configID]["patterns"]["mapfiles"])
            if numMapfiles < 1:
                if self.args.Werror:
                    sc.error("No mapfiles found for configID: '" + configID + "'")
                    sys.exit(-10)
                else:
                    sc.warning("No mapfiles found for configID: '" + configID + "', skipping...")
                configIDsToDelete.append(configID)

        # Remove invalid configIDs separately (for those where no mapfiles were found)
        # Do this in a separate loop since we cannot modify and iterate in the same loop
        for invalidConfigID in configIDsToDelete:
            del self.globalConfig[invalidConfigID]
            if self.args.verbosity <= 2:
                sc.warning("Removing the configID " + invalidConfigID + " because no mapfiles were found for it...")
        else:
            if 0 == len(self.globalConfig):
                sc.error("No mapfiles were found for any of the configIDs...")
                sys.exit(-10)

    def __evalMemRegion(self, physAddr, configID):
        """
        Search within the memory regions to find the address given from a line
        :param configID: Configuration ID from globalConfig.json (referenced in patterns.json)
        :param physAddr: input address in hex or dec
        :return: None if nothing was found; otherwise the unique name of the memory region defined in addressSpaces*.json (DDR, ...)
        """
        address = shared_libs.emma_helper.unifyAddress(physAddr)[1]    # we only want dec >> [1]
        memRegion = None
        memType = None
        memoryCandidates = self.globalConfig[configID]["addressSpaces"]["memory"]

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

    def __translateAddress(self, elementVirtualStartAddress, elementSize, virtualSectionsOfThisMapfile, monolithFileContent):
        """
        Calculates the physical address for an element (= section or object).
        The patterns config file can assign a VAS to a mapfile. Every VAS has VAS sections that are defined in the
        virtualSections file. The monolith file contains all the virtual sections of all the VAS-es with data
        based on which the address translation can be done.
        In order to do the translation we loop trough the entries in the monolith file and see whether the entry belongs
        to the VAS of this element. If so, when we need to make sure that the element resides within the virtual section.
        If that is also true, the address translation can be easily done with the data found in the monolith file.
        :param elementVirtualStartAddress: The start address of the element in the VAS
        :param elementSize: The size of the element in bytes
        :param virtualSectionsOfThisMapfile: List of virtual sections that belong to the VAS of the element
        :param monolithFileContent: List of all the virtual sections from the monolith file.
        :return: Physical start address of the element and the name of the virtual section the translation was done with.
        """
        # This are indexes used for accessing the elements of one monolith file entry
        monolithIndexVirtual = 0
        monolithIndexOffset = 2
        monolithIndexSize = 3
        monolithIndexSectionName = 4
        # Converting the received start address and size to decimal
        _, elementVirtualStartAddress = shared_libs.emma_helper.unifyAddress(elementVirtualStartAddress)
        _, elementSize = shared_libs.emma_helper.unifyAddress(elementSize)
        # Setting up the return values with default values
        elementPhysicalStartAddress = None
        virtualSectionName = None

        # We will go trough all the entries in the monolith file to find the virtual section this element belongs to
        for entry in monolithFileContent:
            # If the element belongs to this virtual section we will try to do the address translation
            virtualSectionName = entry[monolithIndexSectionName]
            if virtualSectionName in virtualSectionsOfThisMapfile:
                # Setting up data for the translation (for the end addresses we need to be careful in case we have zero lengths)
                virtualSectionStartAddress = entry[monolithIndexVirtual]
                virtualSectionEndAddress = virtualSectionStartAddress + (entry[monolithIndexSize] - 1) if 0 < entry[monolithIndexSize] else virtualSectionStartAddress
                elementVirtualEndAddress = elementVirtualStartAddress + (elementSize - 1) if 0 < elementSize else elementVirtualStartAddress
                # If the element is contained by this virtual section then we will use this one for the translation
                if virtualSectionStartAddress <= elementVirtualStartAddress <= elementVirtualEndAddress <= virtualSectionEndAddress:
                    addressTranslationOffset = entry[monolithIndexOffset]
                    elementPhysicalStartAddress = elementVirtualStartAddress + addressTranslationOffset
                    # FIXME: maybe it should be displayed/captured if we got more than one matches! (It should never happen but still...) (MSc)
                    break
        return elementPhysicalStartAddress, virtualSectionName

    def __addMemEntry(self, tag, vasName, vasSectionName, section, moduleName, mapfileName, configID, memType, category, addressStart, addressLength):
        """
        Add an entry to the consumerCollection list with insort algorithm.
        Params are constructor arguments for memEntry object.
        :param tag:
        :param vasName:
        :param vasSectionName
        :param section:
        :param moduleName:
        :param mapfileName:
        :param configID:
        :param memType:
        :param category:
        :param addressStart:
        :param addressLength:
        :return: nothing
        """

        # TODO: Fix this architectural error (FM)
        mapfileEntryToAdd = None
        if isinstance(self.regexPatternData, emma_libs.mapfileRegexes.ImageSummaryPattern):
            # Create Section entry
            mapfileEntryToAdd = emma_libs.memoryEntry.SectionEntry(tag, vasName, vasSectionName, section, moduleName, mapfileName, configID, memType, category, addressStart, addressLength)
        elif isinstance(self.regexPatternData, emma_libs.mapfileRegexes.ModuleSummaryPattern):
            # Create Object entry
            mapfileEntryToAdd = emma_libs.memoryEntry.ObjectEntry(tag, vasName, vasSectionName, section, moduleName, mapfileName, configID, memType, category, addressStart, addressLength)

        # Insert elements by address in progressing order
        i = bisect.bisect_right(self.consumerCollection, mapfileEntryToAdd)
        self.consumerCollection.insert(i, mapfileEntryToAdd)  # Inserts at i, elements to right will be pushed "one inedx up"

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

    def __evalCategory(self, nameString):
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

    def __evalRegexPattern(self, configID, entry):
        """
        Method to determine if the default pattern can be used or if a unique patter is configured
        :param configID: Needed to navigate to the correct configID entry
        :param entry: See param configID
        :return: regex pattern object
        """
        if isinstance(self.regexPatternData, emma_libs.mapfileRegexes.ImageSummaryPattern):
            if UNIQUE_PATTERN_SECTIONS in self.globalConfig[configID]["patterns"]["mapfiles"][entry].keys():
                # If a unique regex pattern is needed, e.g. when the mapfile has a different format and cannot be parsed with the default pattern
                sectionPattern = emma_libs.mapfileRegexes.ImageSummaryPattern()  # Create new instance of pattern class when a unique pattern is needed
                sectionPattern.pattern = self.globalConfig[configID]["patterns"]["mapfiles"][entry][UNIQUE_PATTERN_SECTIONS]  # Overwrite default pattern with unique one
            else:
                # When there is no unique pattern needed the default pattern object can be used
                sectionPattern = self.regexPatternData

            return sectionPattern

        elif isinstance(self.regexPatternData, emma_libs.mapfileRegexes.ModuleSummaryPattern):
            if UNIQUE_PATTERN_OBJECTS in self.globalConfig[configID]["patterns"]["mapfiles"][entry].keys():
                # If a unique regex pattern is needed, e.g. when the mapfile has a different format and cannot be parsed with the default pattern
                objectPattern = emma_libs.mapfileRegexes.ModuleSummaryPattern()  # Create new instance of pattern class when a unique pattern is needed
                objectPattern.pattern = self.globalConfig[configID]["patterns"]["mapfiles"][entry][UNIQUE_PATTERN_OBJECTS]  # Overwrite default pattern with unique one
            else:
                # When there is no unique pattern needed the default pattern object can be used
                objectPattern = self.regexPatternData

            return objectPattern

    def importData(self):
        """
        Processes all input data and adds it to our container (`consumerCollection`)
        :return: number of configIDs
        """

        # Importing for every configID
        for configID in self.globalConfig:
            sc.info("Importing Data for \"" + configID + "\", this may take some time...")

            # Reading the hexadecimal offset value from the addresSpaces*.json. This value is optional, in case it is not defined, we will assume that it is 0.
            offset = int(self.globalConfig[configID]["addressSpaces"]["offset"], 16) if "offset" in self.globalConfig[configID]["addressSpaces"].keys() else 0
            # Defining a list of sections that will be excluded (including the objects residing in it) from the analysis based on the value that was loaded from the arguments
            listOfExcludedSections = [".unused_ram"] if self.analyseDebug else SECTIONS_TO_EXCLUDE

            # Importing every mapfile that was found
            for mapfile in self.globalConfig[configID]["patterns"]["mapfiles"]:
                # Opening the mapfile and reading in its content
                with open(self.globalConfig[configID]["patterns"]["mapfiles"][mapfile]["associatedFilename"], "r") as mapfile_file_object:
                    mapfileContent = mapfile_file_object.readlines()
                # If there is a VAS defined for the mapfile, then the addresses found in it are virtual addresses, otherwise they are physical addresses
                mapfileContainsVirtualAddresses = True if "VAS" in self.globalConfig[configID]["patterns"]["mapfiles"][mapfile] else False
                # Loading the regex pattern that will be used for this mapfile
                regexPatternData = self.__evalRegexPattern(configID, mapfile)

                # Analysing the mapfile with the loaded regex line-by-line
                lineNumber = 0
                for line in mapfileContent:
                    lineNumber += 1

                    # Extracting the components from the line with the regex, if there was no match, we will continue with the next line
                    lineComponents = re.search(regexPatternData.pattern, line)
                    if lineComponents:
                        # If the section name of this element is in the list that we want to exclude then we can continue with the next line
                        if lineComponents.group(regexPatternData.Groups.section).rstrip() in listOfExcludedSections:
                            continue
                        # If this mapfile contains virtual addresses then we need to translate the address of this element
                        vasName = None
                        vasSectionName = None
                        if mapfileContainsVirtualAddresses:
                            # Name of the Virtual address space to which the elements of this mapfile belongs
                            vasName = self.globalConfig[configID]["patterns"]["mapfiles"][mapfile]["VAS"]
                            # List of the virtual sections that were belong to this mapfile. The address translation is done with the help of these sections.
                            virtualSectionsOfThisMapfile = self.globalConfig[configID]["virtualSections"][vasName]
                            # The part of the monolith file that contains the address translation data
                            monolithFileContent = self.globalConfig[configID]["sortMonolithTabularised"]
                            # Calculating the physical address and getting the name of the virtual section based on which the translation was done
                            physicalAddress, vasSectionName = self.__translateAddress(lineComponents.group(regexPatternData.Groups.origin),
                                                                                      lineComponents.group(regexPatternData.Groups.size),
                                                                                      virtualSectionsOfThisMapfile,
                                                                                      monolithFileContent)
                            # Check whether the address translation was successful
                            if physicalAddress is None:
                                if self.args.verbosity <= 2:
                                    warning_section_name = lineComponents.group(regexPatternData.Groups.section).rstrip()
                                    warning_object_name = ("::" + lineComponents.group(regexPatternData.Groups.module).rstrip()) if hasattr(regexPatternData.Groups, "module") else ""
                                    sc.warning("The address translation failed for the element: \"" + mapfile + "(line " + str(lineNumber) + ")::" +
                                                  warning_section_name + warning_object_name + " (size: " + str(int(lineComponents.group(regexPatternData.Groups.size), 16)) + " B)\" of the configID \"" +
                                                  configID + "\"!")
                                if self.args.Werror:
                                    sys.exit(-10)
                                continue
                        # In case the mapfile contains phyisical addresses, no translation is needed, we are just reading the address that is in the mapfile
                        else:
                            physicalAddress = int(lineComponents.group(regexPatternData.Groups.origin), 16) - offset

                        # Finding the memory region and memory type this element belongs to
                        memoryRegion, memType = self.__evalMemRegion(physicalAddress, configID)

                        # If a memory region was NOT found, we will continue with the next line
                        if memoryRegion is not None:
                            # Finding the category this element belongs to
                            category = self.__evalCategory(lineComponents.group(regexPatternData.Groups.name))
                            # Skip memTypes to exclude
                            # TODO : We could write a function to replace this often executed code to make the program to be readable (AGK)
                            # TODO :    def checkAndGetStuffFromDictionary(stuff, dictionary):
                            # TODO :        result = None
                            # TODO :        if stuff in dictionary.keys():
                            # TODO :            result = dictionary[stuff]
                            # TODO :        return result
                            memoryRegionsToExclude = []
                            if MEM_REGION_TO_EXCLUDE in self.globalConfig[configID]["patterns"]["mapfiles"][mapfile].keys():
                                # If a memory types should be excluded on a mapfile basis
                                memoryRegionsToExclude = self.globalConfig[configID]["patterns"]["mapfiles"][mapfile][MEM_REGION_TO_EXCLUDE]
                            if memoryRegion in memoryRegionsToExclude:
                                continue

                            # Determining the addressLength
                            addressLength = int(lineComponents.group(regexPatternData.Groups.size), 16)
                            # Check whether the address is valid
                            if 0 > addressLength:
                                if self.args.verbosity <= 2:
                                    sc.warning("Negative addressLength found.")
                                if self.args.Werror:
                                    sys.exit(-10)

                            # Add the memory entry to the collection
                            self.__addMemEntry(
                                tag=memoryRegion,
                                vasName=vasName if mapfileContainsVirtualAddresses else None,
                                vasSectionName=vasSectionName if mapfileContainsVirtualAddresses else None,
                                section=lineComponents.group(regexPatternData.Groups.section).rstrip(),
                                moduleName=regexPatternData.getModuleName(lineComponents),
                                mapfileName=os.path.split(self.globalConfig[configID]["patterns"]["mapfiles"][mapfile]["associatedFilename"])[-1],
                                configID=configID,
                                memType=memType,
                                category=category,
                                addressStart=physicalAddress,
                                addressLength=addressLength)
                        else:
                            if self.args.verbosity <= 1:
                                warning_section_name = lineComponents.group(regexPatternData.Groups.section).rstrip()
                                warning_object_name = ("::" + lineComponents.group(regexPatternData.Groups.module).rstrip()) if hasattr(regexPatternData.Groups, "module") else ""
                                sc.warning("The element: \"" + mapfile + "(line " + str(lineNumber) + ")::" +
                                              warning_section_name + warning_object_name + " (size: " + str(int(lineComponents.group(regexPatternData.Groups.size), 16)) + " B)\" of the configID \"" +
                                              configID + "\" does not belong to any of the memory regions!")
                            if self.args.Werror:
                                sys.exit(-1)
                            continue

        return len(self.globalConfig)

    def writeSummary(self):
        """
        Wrapper for writing consumerCollection to file
        :return: nothing
        """
        consumerCollectionToCSV(self.outputPath, self.consumerCollection)

    def removeUnmatchedFromCategoriesJson(self):
        """
        Removes unused module names from categories.json.
        The function prompts the user to confirm the overwriting of categories.json
        :return: Bool if file has been overwritten
        """
        sc.info("Remove unmatched modules from" + self.__categoriesFilePath + "?\n" + self.__categoriesFilePath + " will be overwritten.\n`y` to accept, any other key to discard.")
        text = input("> ") if not self.args.noprompt else sys.exit(-10)
        if text == "y":
            # Make a dict of {modulename: category} from consumerCollection
            # Remember: consumerCollection is a list of memEntry objects
            rawCategorisedModulesConsumerCollection = {memEntry.moduleName: memEntry.category for memEntry in self.consumerCollection}

            # Format rawCategorisedModulesConsumerCollection to {Categ1: [Modulename1, Modulename2, ...], Categ2: [...]}
            categorisedModulesConsumerCollection = {}
            for k, v in rawCategorisedModulesConsumerCollection.items():
                categorisedModulesConsumerCollection[v] = categorisedModulesConsumerCollection.get(v, [])
                categorisedModulesConsumerCollection[v].append(k)

            for category in self.categoriesJson:  # For every category in categories.json
                if category not in categorisedModulesConsumerCollection:
                    # If category is in categories.json but has never occured in the mapfiles (hence not present in consumerCollection)
                    # Remove the not occuring category entirely
                    self.categoriesJson.pop(category)
                else:  # Category occurs in consumerCollection, hence is present in mapfiles,
                    # overwrite old category module list with the ones acutally occuring in mapfiles
                    self.categoriesJson[category] = categorisedModulesConsumerCollection[category]

            # Sort self.categories case-insensitive in alphabetical order
            for x in self.categoriesJson.keys():
                self.categoriesJson[x].sort(key=lambda s: s.lower())

            shared_libs.emma_helper.writeJson(self.__categoriesFilePath, self.categoriesJson)

            return True

        else:
            sc.warning(self.__categoriesFilePath + " not changed.")
            if self.args.Werror:
                sys.exit(-10)
            return False

    def createCategoriesJson(self):
        """
        Updates/overwrites the present categories.json
        :return Bool if CategoriesJson has been created
        """
        # FIXME: Clearer Output (FM)
        sc.info("Merge categories.json with categorised modules from categoriesKeywords.json?\ncategories.json will be overwritten.\n`y` to accept, any other key to discard.")
        text = input("> ") if not self.args.noprompt else sys.exit(-10)
        if text == "y":
            # Format moduleCategories to {Categ1: [Modulename1, Modulename2, ...], Categ2: [...]}
            formatted = {}
            for k, v in dict(self.categorisedFromKeywords).items():
                formatted[v] = formatted.get(v, [])
                formatted[v].append(k)

            # Merge categories from keyword search with categories from categories.json
            moduleCategories = {**formatted, **self.categoriesJson}

            # Sort moduleCategories case-insensitive in alphabetical order
            for x in moduleCategories.keys():
                moduleCategories[x].sort(key=lambda s: s.lower())

            shared_libs.emma_helper.writeJson(self.__categoriesKeywordsPath, self.__categoriesKeywordsPath)

            return True
        else:
            sc.warning(self.__categoriesFilePath + " not changed.")
            if self.args.Werror:
                sys.exit(-10)
            return False

    def resolveDuplicateContainmentOverlap(self, nameGetter):
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
        for actualElement in self.consumerCollection:
            for otherElement in self.consumerCollection:

                # Don't compare element with itself and only compare the same configID
                if actualElement.equalConfigID(otherElement) and not actualElement == otherElement:

                    # Case 0: actualElement and otherElement are completely separated
                    if actualElement.addressEnd < otherElement.addressStart or actualElement.addressStart > otherElement.addressEnd:
                        # There is not much to do here...
                        pass
                    else:
                        # Case 1: actualElement and otherElement are duplicates
                        if actualElement.addressStart == otherElement.addressStart and actualElement.addressEnd == otherElement.addressEnd:
                            # Setting the actualElement´s duplicateFlag if it was not already set
                            if actualElement.duplicateFlag is None:
                                actualElement.duplicateFlag = "Duplicate of (" + nameGetter(otherElement) + ", " + otherElement.configID + ", " + otherElement.mapfile + ")"
                            # Setting the actualElement to zero addressLength if this was not the first element of the duplicates
                            # This is needed to include only one of the duplicate elements with the real size in the report and not to distort the results
                            if otherElement.duplicateFlag is not None:
                                actualElement.addressLength = 0
                                actualElement.addressLengthHex = hex(actualElement.addressLength)
                        else:
                            # Case 2: actualElement contains otherElement
                            if actualElement.addressStart <= otherElement.addressStart and actualElement.addressEnd >= otherElement.addressEnd:
                                actualElement.containingOthersFlag = True
                            else:
                                # Case 3: actualElement is contained by otherElement
                                if actualElement.addressStart >= otherElement.addressStart and actualElement.addressEnd <= otherElement.addressEnd:
                                    # Setting the actualElement´s containmentFlag if it was not already set
                                    if actualElement.containmentFlag is None:
                                        actualElement.containmentFlag = "Contained by (" + nameGetter(otherElement) + ", " + otherElement.configID + ", " + otherElement.mapfile + ")"
                                        # Setting the actualElement to zero addressLength because this was contained by the otherElement
                                        # This is needed to include only one of these elements with the real size in the report and not to distort the results
                                        actualElement.addressLength = 0
                                        actualElement.addressLengthHex = hex(actualElement.addressLength)
                                else:
                                    # Case 4: actualElement overlaps otherElement: otherElement starts inside and ends outside actualElement
                                    if actualElement.addressStart < otherElement.addressStart and actualElement.addressEnd < otherElement.addressEnd:
                                        actualElement.overlappingOthersFlag = True
                                    else:
                                        # Case 5: actualElement is overlapped by otherElement: otherElement starts before and ends inside actualElement
                                        if actualElement.addressStart > otherElement.addressStart and actualElement.addressEnd > otherElement.addressEnd:
                                            actualElement.overlapFlag = "Overlapped by (" + nameGetter(otherElement) + ", " + otherElement.configID + ", " + otherElement.mapfile + ")"
                                            # Adjusting the addresses and length of the actualElement: reducing its size by the overlapping part
                                            actualElement.addressStart = otherElement.addressEnd + 1
                                            actualElement.addressStartHex = hex(actualElement.addressStart)
                                            actualElement.addressLength = actualElement.addressEnd - actualElement.addressStart + 1
                                            actualElement.addressLengthHex = hex(actualElement.addressLength)
                                        # Case X: SW error, unhandled case...
                                        else:
                                            sc.error("MemoryManager::resolveOverlap(): Case X: SW error, unhandled case...")


def createMemStatsFilepath(rootdir, subdir, csvFilename, projectName):
    memStatsRootPath = shared_libs.emma_helper.joinPath(rootdir, subdir, OUTPUT_DIR)
    shared_libs.emma_helper.mkDirIfNeeded(memStatsRootPath)
    memStatsFileName = projectName + "_" + csvFilename + "_" + timestamp.replace(" ", "") + ".csv"
    return shared_libs.emma_helper.joinPath(memStatsRootPath, memStatsFileName)


def consumerCollectionToCSV(filepath, consumerCollection):
    """
    Writes the consumerCollection containig MemoryEntrys to CSV
    :param filepath: Absolute path to the csv file
    :param consumerCollection: List containing memEntrys
    """
    with open(filepath, "w") as fp:
        writer = csv.writer(fp, delimiter=";", lineterminator="\n")
        header = [ADDR_START_HEX, ADDR_END_HEX, SIZE_HEX, ADDR_START_DEC, ADDR_END_DEC, SIZE_DEC, SIZE_HUMAN_READABLE,
                  SECTION_NAME, MODULE_NAME, CONFIG_ID, VAS_NAME, VAS_SECTION_NAME, MEM_TYPE, TAG, CATEGORY, DMA, MAPFILE, OVERLAP_FLAG,
                  CONTAINMENT_FLAG, DUPLICATE_FLAG, CONTAINING_OTHERS_FLAG, ADDR_START_HEX_ORIGINAL,
                  ADDR_END_HEX_ORIGINAL, SIZE_HEX_ORIGINAL, SIZE_DEC_ORIGINAL]
        writer.writerow(header)
        for row in consumerCollection:
            writer.writerow([
                row.addressStartHex,
                row.addressEndHex,
                row.addressLengthHex,
                row.addressStart,
                row.addressEnd,
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
                row.addressEndOriginal if (row.overlapFlag is not None) else "",
                # Lengths are modified in case of overlapping, containment and duplication so we will post the original values so that the changes can be seen
                row.addressLengthHexOriginal if ((row.overlapFlag is not None) or (row.containmentFlag is not None) or (row.duplicateFlag is not None)) else "",
                row.addressLengthOriginal if ((row.overlapFlag is not None) or (row.containmentFlag is not None) or (row.duplicateFlag is not None)) else ""
            ])

    sc.info("Summary saved in:", os.path.abspath(filepath))
    sc.info("Filename:", os.path.split(filepath)[-1])
    print("\n")


class SectionParser(MemoryManager):
    def __init__(self, args):
        regexData = emma_libs.mapfileRegexes.ImageSummaryPattern()                                                  # Regex Data containing the groups
        categoriesPath = shared_libs.emma_helper.joinPath(args.project, CATEGORIES_SECTIONS_JSON)                   # The file path to categories.JSON
        categoriesKeywordsPath = shared_libs.emma_helper.joinPath(args.project, CATEGORIES_KEYWORDS_SECTIONS_JSON)  # The file path to categoriesKeyowrds.JSON
        fileIdentifier = FILE_IDENTIFIER_SECTION_SUMMARY
        super().__init__(args, categoriesPath, categoriesKeywordsPath, fileIdentifier, regexData)

    def resolveDuplicateContainmentOverlap(self):
        nameGetter = lambda target: target.section
        super().resolveDuplicateContainmentOverlap(nameGetter)


class ObjectParser(MemoryManager):
    def __init__(self, args):
        regexData = emma_libs.mapfileRegexes.ModuleSummaryPattern()                                                 # Regex Data containing the groups
        categoriesPath = shared_libs.emma_helper.joinPath(args.project, CATEGORIES_OBJECTS_JSON)                    # The filepath to categories.JSON
        categoriesKeywordsPath = shared_libs.emma_helper.joinPath(args.project, CATEGORIES_KEYWORDS_OBJECTS_JSON)   # The filepath to categoriesKeyowrds.JSON
        fileIdentifier = FILE_IDENTIFIER_OBJECT_SUMMARY
        super().__init__(args, categoriesPath, categoriesKeywordsPath, fileIdentifier, regexData)

    def resolveDuplicateContainmentOverlap(self):
        nameGetter = lambda target: target.section + "::" + target.moduleName
        super().resolveDuplicateContainmentOverlap(nameGetter)
