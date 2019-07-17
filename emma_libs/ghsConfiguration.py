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
import re

from pypiscout.SCout_Logger import Logger as sc

import shared_libs.emma_helper
import emma_libs.specificConfiguration
import emma_libs.ghsMapfileRegexes


class GhsConfiguration(emma_libs.specificConfiguration.SpecificConfiguration):

    def readConfiguration(self, configurationPath, mapfilesPath, configId, configuration) -> None:
        # Loading the patterns*.json
        if "patternsPath" in configuration:
            patternsPath = shared_libs.emma_helper.joinPath(configurationPath, configuration["patternsPath"])
            configuration["patterns"] = shared_libs.emma_helper.readJson(patternsPath)
        else:
            sc().error("Missing patternsPath definition in the globalConfig,json!")
            sys.exit(-10)

        # Loading the virtualSections*.json if the file is present (only needed in case of VAS-es)
        if "virtualSectionsPath" in configuration:
            virtualSectionsPath = shared_libs.emma_helper.joinPath(configurationPath, configuration["virtualSectionsPath"])
            configuration["virtualSections"] = shared_libs.emma_helper.readJson(virtualSectionsPath)

        # Loading the mapfiles
        self.__addMapfilesToConfiguration(mapfilesPath, configuration)

        # Loading the monolith file
        # Flag to load a monolith file only once; we don't do it here since we might work with DMA only
        configuration["monolithLoaded"] = False
        # Flag to sort monolith table only once; we don't do it here since we might work with DMA only
        configuration["sortMonolithTabularised"] = False
        self.__addMonolithsToConfiguration(mapfilesPath, configuration)

    def validateConfiguration(self, configId, configuration, noPrompt) -> bool:
        result = False
        if self.__checkNumberOfFoundMapfiles(configId, configuration):
            if self.__checkMonolithSections(configId, configuration, noPrompt):
                result = True
        return result

    def __addFilesToConfiguration(self, path, configuration, fileType):
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
        for file in os.listdir(path):
            for entry in configuration["patterns"][fileType]:
                foundFiles = []
                for regex in configuration["patterns"][fileType][entry]["regex"]:
                    searchCandidate = shared_libs.emma_helper.joinPath(path, file)
                    match = re.search(regex, searchCandidate)
                    if match:
                        foundFiles.append(os.path.abspath(searchCandidate))
                if foundFiles:
                    configuration["patterns"][fileType][entry]["associatedFilename"] = foundFiles[0]
                    print("\t\t\t Found " + fileType + ": ", foundFiles[0])
                    if len(foundFiles) > 1:
                        sc.warning("Ambiguous regex pattern in '" + configuration["patternsPath"] + "'. Selected '" + foundFiles[0] + "'. Regex matched: " + "".join(foundFiles))

        # Check for found files in patterns and do some clean-up
        # We need to convert the keys into a temporary list in order to avoid iterating on the original which may be changed during the loop, that causes a runtime error
        for entry in list(configuration["patterns"][fileType]):
            if "associatedFilename" not in configuration["patterns"][fileType][entry]:
                sc().warning("No file found for ", str(entry).ljust(20), "(pattern:", ''.join(configuration["patterns"][fileType][entry]["regex"]) + " );", "skipping...")
                del configuration["patterns"][fileType][entry]
        return len(configuration["patterns"][fileType])

    def __addMapfilesToConfiguration(self, mapfilesPath, configuration):
        numMapfiles = self.__addFilesToConfiguration(mapfilesPath, configuration, "mapfiles")
        sc().info(str(numMapfiles) + " mapfiles found")

    def __addMonolithsToConfiguration(self, mapfilesPath, configuration):

        def ifAnyNonDMA(configuration):
            """
            Checks if non-DMA files were found
            Do not run this before mapfiles are searched (try: `findMapfiles` and evt. `findMonolithMapfiles` before)
            :return: True if files which require address translation were found; otherwise False
            """
            entryFound = False
            for entry in configuration["patterns"]["mapfiles"]:
                if "VAS" in configuration["patterns"]["mapfiles"][entry]:
                    entryFound = True
                    # TODO : here, a break could improve the performance (AGK)
            return entryFound

        if ifAnyNonDMA(configuration):
            numMonolithMapFiles = self.__addFilesToConfiguration(mapfilesPath, configuration, "monoliths")
            if numMonolithMapFiles > 1:
                sc().warning("More than one monolith file found; Result may be non-deterministic")
            elif numMonolithMapFiles < 1:
                sc().error("No monolith files was detected but some mapfiles require address translation (VASes used)")
            self.__addTabularisedMonoliths(configuration)

    def __addTabularisedMonoliths(self, configuration):
        """
        Manages Monolith selection, parsing and converting to a list
        :param configID: configID
        :return: nothing
        """

        def loadMonolithMapfileOnce(configuration, noPrompt):
            """
            Load monolith mapfile (only once)
            :return: Monolith file content
            """

            if not configuration["monolithLoaded"]:
                mapfileIndexChosen = 0  # Take the first monolith file in list (default case)
                numMonolithFiles = len(configuration["patterns"]["monoliths"])
                keyMonolithMapping = {}

                # Update globalConfig with all monolith filenames
                for key, monolith in enumerate(configuration["patterns"]["monoliths"]):
                    keyMonolithMapping.update({str(key): configuration["patterns"]["monoliths"][monolith]["associatedFilename"]})

                if numMonolithFiles > 1:
                    sc().info("More than one monolith file detected. Which to chose (1, 2, ...)?")
                    # Display files
                    for key, monolith in keyMonolithMapping.items():
                        print(" ", key.ljust(10), monolith)
                    # Ask for index which file to chose
                    mapfileIndexChosen = shared_libs.emma_helper.Prompt.idx() if not noPrompt else sys.exit(-10)
                    while not (0 <= mapfileIndexChosen < numMonolithFiles):
                        sc().warning("Invalid value; try again:")
                        mapfileIndexChosen = shared_libs.emma_helper.Prompt.idx() if not noPrompt else sys.exit(-10)
                elif numMonolithFiles < 1:
                    sc().error("No monolith file found but needed for processing")

                # Finally load the file
                configuration["monolithLoaded"] = True
                with open(keyMonolithMapping[str(mapfileIndexChosen)], "r") as fp:
                    content = fp.readlines()
                return content

        def tabulariseAndSortOnce(monolithContent, configuration):
            """
            Parses the monolith file and returns a "table" (addresses are int's) of the following structure:
            table[n-th_entry][0] = virtual(int), ...[1] = physical(int), ...[2] = offset(int), ...[3] = size(int), ...[4] = section(str)
            Offset = physical - virtual
            :param monolithContent: Content from monolith as text (all lines)
            :return: list of lists
            """
            table = []  # "headers": virtual, physical, size, section
            monolithPattern = emma_libs.ghsMapfileRegexes.UpperMonolithPattern()
            for line in monolithContent:
                match = re.search(emma_libs.ghsMapfileRegexes.UpperMonolithPattern().pattern, line)
                if match:
                    table.append([
                        int(match.group(monolithPattern.Groups.virtualAdress), 16),
                        int(match.group(monolithPattern.Groups.physicalAdress), 16),
                        (int(match.group(monolithPattern.Groups.physicalAdress), 16) - int(match.group(monolithPattern.Groups.virtualAdress), 16)),
                        int(match.group(monolithPattern.Groups.size), 16),
                        match.group(monolithPattern.Groups.section)
                    ])
            configuration["sortMonolithTabularised"] = True
            return table

        # Load and register Monoliths
        monolithContent = loadMonolithMapfileOnce(configuration)
        if not configuration["sortMonolithTabularised"]:
            configuration["sortMonolithTabularised"] = tabulariseAndSortOnce(monolithContent, configuration)

    def __checkNumberOfFoundMapfiles(self, configId, configuration):
        result = False
        # Checking the number of the mapfiles that were found with the regexes
        if 0 < len(configuration["patterns"]["mapfiles"]):
            # If there is at least one, then the check was passed
            result = True
        else:
            sc().warning("No mapfiles found for configID: \"" + configId + "\"!")
        return result

    def __checkMonolithSections(self, configId, configuration, noPrompt):
        """
        The function collects the VAS sections from the monolith files and from the global config and from the monolith mapfile
        :return: nothing
        """
        result = False
        foundInConfigID = []
        foundInMonolith = []

        # Extract sections from monolith file
        monolithPattern = emma_libs.ghsMapfileRegexes.UpperMonolithPattern()

        # Check if a monolith was loaded to this configID that can be checked
        if configuration[configId]["monolithLoaded"]:
            for entry in configuration["patterns"]["monoliths"]:
                with open(configuration["patterns"]["monoliths"][entry]["associatedFilename"], "r") as monolithFile:
                    monolithContent = monolithFile.readlines()
                for line in monolithContent:
                    lineComponents = re.search(monolithPattern.pattern, line)
                    if lineComponents:  # if match
                        foundInMonolith.append(lineComponents.group(monolithPattern.Groups.section))

            for vas in configuration["virtualSections"]:
                foundInConfigID += configuration["virtualSections"][vas]

            # Compare sections from configID with found in monolith file
            sectionsNotInConfigID = set(foundInMonolith) - set(foundInConfigID)
            if sectionsNotInConfigID:
                sc().warning("Monolith File has the following sections. You might want to add it them the respective VAS in " + configuration["virtualSectionsPath"] + "!")
                print(sectionsNotInConfigID)
                sc().warning("Still continue? (y/n)")
                text = input("> ") if not noPrompt else sys.exit(-10)
                if text != "y":
                    sys.exit(-10)
            else:
                result = True

        return result
