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

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper
import emma_libs.specificConfiguration
import emma_libs.ghsMapfileRegexes


class GhsConfiguration(emma_libs.specificConfiguration.SpecificConfiguration):
    """
    Class to handle a GHS compiler specific configuration.
    """
    def __init__(self, noPrompt):
        super().__init__(noPrompt)
        self.noPrompt = noPrompt

    def readConfiguration(self, configurationPath, mapfilesPath, configId, configuration) -> None:
        """
        Function to read in the GHS compiler specific part of the configuration and extend the already existing configuration with it.
        :param configurationPath: Path of the directory where the configuration is located.
        :param mapfilesPath: Path of the directory where the mapfiles are located.
        :param configId: ConfigId to which the configuration belongs to.
        :param configuration: The configuration dictionary that needs to be extended with the compiler specific data.
        :return: None
        """
        # Loading the patterns*.json
        if "patternsPath" in configuration:
            patternsPath = shared_libs.emma_helper.joinPath(configurationPath, configuration["patternsPath"])
            configuration["patterns"] = shared_libs.emma_helper.readJson(patternsPath)
        else:
            sc().error("Missing patternsPath definition in the globalConfig,json for the configId: " + configId + "!")

        # Loading the virtualSections*.json if the file is present (only needed in case of VAS-es)
        if "virtualSectionsPath" in configuration:
            virtualSectionsPath = shared_libs.emma_helper.joinPath(configurationPath, configuration["virtualSectionsPath"])
            configuration["virtualSections"] = shared_libs.emma_helper.readJson(virtualSectionsPath)

        # Loading the mapfiles
        GhsConfiguration.__addMapfilesToConfiguration(mapfilesPath, configuration)

        # Loading the monolith file
        # Flag to load a monolith file only once; we don't do it here since we might work with DMA only
        configuration["monolithLoaded"] = False
        # Flag to sort monolith table only once; we don't do it here since we might work with DMA only
        configuration["sortMonolithTabularised"] = False
        self.__addMonolithsToConfiguration(mapfilesPath, configuration)

    def checkConfiguration(self, configId, configuration) -> bool:
        """
        Function to check the GHS compiler specific part of the configuration.
        :param configId: The configId the configuration belongs to.
        :param configuration: The configuration dictionary that needs to be checked.
        :return: True if the configuration is correct, False otherwise.
        """
        result = False
        if GhsConfiguration.__checkNumberOfFoundMapfiles(configId, configuration):
            if GhsConfiguration.__checkMonolithSections(configuration, self.noPrompt):
                result = True
        return result

    @staticmethod
    def __addMapfilesToConfiguration(mapfilesPath, configuration):
        """
        Function to add the mapfiles to the configuration.
        :param mapfilesPath: Path of the folder where the mapfiles are located.
        :param configuration: Configuration to which the mapfiles need to be added.
        :return: None
        """
        if os.path.isdir(mapfilesPath):
            GhsConfiguration.__addFilesToConfiguration(mapfilesPath, configuration, "mapfiles")
        else:
            sc().error("The mapfiles folder (\"" + mapfilesPath + "\") does not exist!")

    def __addMonolithsToConfiguration(self, mapfilesPath, configuration):
        """
        Function to add monolith files to the configuration.
        :param mapfilesPath: Path of the folder where the mapfiles (and the monolith files) are located.
        :param configuration: Configuration to which the monolith files need to be added.
        :return: None
        """

        def ifAnyNonDMA(configuration):
            """
            Function to check whether a configuration has any non-DMA mapfiles.
            If a VAS is defined for a mapfile, then it is considered to be non-DMA.
            :param configuration: Configuration whose mapfiles needs to be checked.
            :return: True if any non-DMA mapfile was found, False otherwise.
            """
            result = False
            for entry in configuration["patterns"]["mapfiles"]:
                if "VAS" in configuration["patterns"]["mapfiles"][entry]:
                    result = True
                    break
            return result

        if os.path.isdir(mapfilesPath):
            if ifAnyNonDMA(configuration):
                numMonolithMapFiles = GhsConfiguration.__addFilesToConfiguration(mapfilesPath, configuration, "monoliths")
                if numMonolithMapFiles > 1:
                    sc().warning("More than one monolith file found; Result may be non-deterministic")
                elif numMonolithMapFiles < 1:
                    sc().error("No monolith files was detected but some mapfiles require address translation (VASes used)")
                self.__addTabularisedMonoliths(configuration)
        else:
            sc().error("The mapfiles folder (\"" + mapfilesPath + "\") does not exist!")

    @staticmethod
    def __addFilesToConfiguration(path, configuration, fileType):
        """
        Function to add a specific file type to the configuration.
        :param path: Path where the files needs to be searched for.
        :param configuration: Configuration to which the files need to be added to.
        :param fileType: Filetype that needs to be searched for.
        :return: Number of files found.
        """
        # For every file in the received path
        for file in os.listdir(path):
            # For every entry for the received fileType
            for entry in configuration["patterns"][fileType]:
                foundFiles = []
                # For every regex pattern defined for this entry
                for regex in configuration["patterns"][fileType][entry]["regex"]:
                    # We will try to match the current file with its path and add it to the found files if it matched
                    searchCandidate = shared_libs.emma_helper.joinPath(path, file)
                    if re.search(regex, searchCandidate):
                        foundFiles.append(os.path.abspath(searchCandidate))
                # If we have found any file for this file type
                if foundFiles:
                    # We will add it to the configuration and also check whether more than one file was found to this pattern
                    configuration["patterns"][fileType][entry]["associatedFilename"] = foundFiles[0]
                    sc().info(LISTING_INDENT + "Found " + fileType + ": ", foundFiles[0])
                    if len(foundFiles) > 1:
                        sc().warning("Ambiguous regex pattern in '" + configuration["patternsPath"] + "'. Selected '" + foundFiles[0] + "'. Regex matched: " + "".join(foundFiles))

        # Check for found files in patterns and do some clean-up
        # We need to convert the keys into a temporary list in order to avoid iterating on the original which may be changed during the loop, that causes a runtime error
        for entry in list(configuration["patterns"][fileType]):
            if "associatedFilename" not in configuration["patterns"][fileType][entry]:
                sc().warning("No file found for ", str(entry).ljust(20), "(pattern:", ''.join(configuration["patterns"][fileType][entry]["regex"]) + " );", "skipping...")
                del configuration["patterns"][fileType][entry]

        return len(configuration["patterns"][fileType])

    def __addTabularisedMonoliths(self, configuration):
        """
        Manages Monolith selection, parsing and converting to a list.
        :param configuration: Configuration to which the monoliths need to be added.
        :return: None
        """

        def loadMonolithFile(configuration, noprompt):
            """
            Function to Load monolith file.
            :param configuration: Configuration to which the monoliths need to be added.
            :param noprompt: True if no user prompts shall be made, False otherwise, in which case a program exit will be made.
            :return: Content of the monolith file if it could be read, else None.
            """
            result = None
            mapfileIndexChosen = 0  # Take the first monolith file in list (default case)
            numMonolithFiles = len(configuration["patterns"]["monoliths"])
            keyMonolithMapping = {}

            # Update globalConfig with all monolith filenames
            for key, monolith in enumerate(configuration["patterns"]["monoliths"]):
                keyMonolithMapping.update({str(key): configuration["patterns"]["monoliths"][monolith]["associatedFilename"]})

            if numMonolithFiles > 1:
                sc().info("More than one monolith file detected:")
                # Display files
                for key, monolith in keyMonolithMapping.items():
                    sc().info(LISTING_INDENT, f"{key}: {monolith}")
                if noprompt:
                    sc().wwarning("No prompt is active. Using first monolith file in list: " + str(keyMonolithMapping['0']))
                    mapfileIndexChosen = 0
                else:
                    # Let the user choose the index of the correct file
                    sc().info("Choose the index of the desired monolith file")
                    mapfileIndexChosen = shared_libs.emma_helper.Prompt.idx()
                    while not 0 <= mapfileIndexChosen < numMonolithFiles:               # Accept only values within the range [0, numMonolithFiles)
                        sc().warning("Invalid value; try again:")
                        mapfileIndexChosen = shared_libs.emma_helper.Prompt.idx()
            elif numMonolithFiles < 1:
                sc().error("No monolith file found but needed for processing")

            # Finally load the file
            configuration["monolithLoaded"] = True
            monolithFilepath = keyMonolithMapping[str(mapfileIndexChosen)]
            try:
                with open(monolithFilepath, "r") as fp:
                    result = fp.readlines()
            except FileNotFoundError:
                sc().error(f"The monolith file `{os.path.abspath(monolithFilepath)}` was not found!")

            return result

        def tabulariseAndSortMonolithContent(monolithContent):
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
            return table

        # Load and register Monoliths
        monolithContent = loadMonolithFile(configuration, self.noPrompt)
        configuration["sortMonolithTabularised"] = tabulariseAndSortMonolithContent(monolithContent)

    @staticmethod
    def __checkNumberOfFoundMapfiles(configId, configuration):
        """
        Function to check the number of found mapfiles in a configuration.
        :param configId: The configId the configuration belongs to.
        :param configuration: The configuration in which the found mapfiles need to be checked.
        :return:
        """
        result = False
        # Checking the number of the mapfiles that were found with the regexes
        if configuration["patterns"]["mapfiles"]:
            # If there is at least one, then the check was passed
            result = True
        else:
            sc().warning("No mapfiles found for configID: \"" + configId + "\"!")
        return result

    @staticmethod
    def __checkMonolithSections(configuration, noprompt):
        # pylint: disable=too-many-locals
        # Rationale: The code quality would not increase significantly from fewer local variables.
        """
        The function collects the VAS sections from the monolith files and from the global config and from the monolith mapfile.
        :param configuration: Configuration thats monolith sections need to be checked.
        :param noprompt: True if no user prompts shall be made, False otherwise, in which case a program exit will be made.
        :return: True if the monolith sections were ok, False otherwise.
        """
        result = False
        foundInConfigID = []
        foundInMonolith = []

        # Extract sections from monolith file
        monolithPattern = emma_libs.ghsMapfileRegexes.UpperMonolithPattern()

        # Check if a monolith was loaded to this configID that can be checked
        # In case there was no monolith loaded, the configuration does not need it so the check is passed
        if configuration["monolithLoaded"]:
            for entry in configuration["patterns"]["monoliths"]:
                try:
                    monolithFilepath = configuration["patterns"]["monoliths"][entry]["associatedFilename"]
                    with open(monolithFilepath, "r") as monolithFile:
                        monolithContent = monolithFile.readlines()
                except FileNotFoundError:
                    sc().error(f"The file `{os.path.abspath(monolithFilepath)}` was not found!")
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
                for section in sectionsNotInConfigID:
                    sc().info(LISTING_INDENT, section)
                sc().warning("Still continue? (y/n)")
                if noprompt:
                    sc().wwarning("No prompt is active. Chose `y` to continue.")
                    text = "y"
                else:
                    text = input("> ")
                if text != "y":
                    sys.exit(-10)
            else:
                result = True
        else:
            result = True

        return result
