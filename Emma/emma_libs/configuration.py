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


from pypiscout.SCout_Logger import Logger as sc

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.shared_libs.emma_helper
import Emma.emma_libs.specificConfigurationFactory


class Configuration:
    # pylint: disable=too-few-public-methods
    # Rationale: This class does not need to provide more functionality than reading in the configuration.

    """
    Class for handling the configuration reading and processing.
    """
    def __init__(self):
        self.specificConfigurations = dict()
        self.globalConfig = None

    def readConfiguration(self, configurationPath, mapfilesPath, noPrompt):
        """
        Function to read in the configuration and process it´s data.
        :param configurationPath: This is the path of the folder where the configuration files are.
        :param mapfilesPath: This is the path of the folder where the mapfiles are.
        :param noPrompt: True if user prompts are allowed, False otherwise, in which caseThis is the path of the folder where the configuration files are.
        :return: None
        """
        # Check whether the configurationPath exists
        Emma.shared_libs.emma_helper.checkIfFolderExists(configurationPath)

        # Processing the globalConfig.json
        globalConfigPath = Emma.shared_libs.emma_helper.joinPath(configurationPath, "globalConfig.json")
        self.globalConfig = Configuration.__readGlobalConfigJson(globalConfigPath)
        sc().info("Imported " + str(len(self.globalConfig)) + " global config entries:" + str(list(self.globalConfig.keys())))

        # Processing the generic configuration parts for all the configId
        configIDsToRemove = []
        for configId in self.globalConfig:
            # Processing the addressSpaces*.json
            if ADDR_SPACES_PATH in self.globalConfig[configId]:
                addressSpacesPath = Emma.shared_libs.emma_helper.joinPath(configurationPath, self.globalConfig[configId][ADDR_SPACES_PATH])
                self.globalConfig[configId]["addressSpaces"] = Configuration.__readAddressSpacesJson(addressSpacesPath)
            else:
                sc().error(f"The {configId} does not have the key: {ADDR_SPACES_PATH}.")

            # Setting up the mapfile search paths for the configId
            # TODO: add option for recursive search (MSc)
            if MAPFILES in self.globalConfig[configId]:
                mapfilesPathForThisConfigId = Emma.shared_libs.emma_helper.joinPath(mapfilesPath, self.globalConfig[configId][MAPFILES])
            else:
                mapfilesPathForThisConfigId = mapfilesPath
            Emma.shared_libs.emma_helper.checkIfFolderExists(mapfilesPathForThisConfigId)

            # Check if globalConfig file contains a patternsPath key
            if PATTERNS_PATH in self.globalConfig[configId]:
                patternsPath = Emma.shared_libs.emma_helper.joinPath(configurationPath, self.globalConfig[configId][PATTERNS_PATH])
                # Process patterns*.json
                self.globalConfig[configId]["patterns"] = Emma.shared_libs.emma_helper.readJson(patternsPath)
                for mapfilePath in self.globalConfig[configId]["patterns"]["mapfiles"].keys():
                    # Check the correctness of patterns files
                    if REGEX not in self.globalConfig[configId]["patterns"]["mapfiles"][mapfilePath]:
                        sc().error(f"The key {REGEX} does not exist in {patternsPath}.")
                    else:
                        if type(self.globalConfig[configId]["patterns"]["mapfiles"][mapfilePath][REGEX]) != list:
                            sc().error(f"The value of the regex in {patternsPath} is not a list.")
                        else:
                            if len(self.globalConfig[configId]["patterns"]["mapfiles"][mapfilePath][REGEX]) < 1:
                                sc().error(f"The list of the regex in {patternsPath} must contain at least one element.")
                            else:
                                for element in self.globalConfig[configId]["patterns"]["mapfiles"][mapfilePath][REGEX]:
                                    if type(element) != str:
                                        sc().error(f"The element of the regex list in  {patternsPath}  must be a str.")
            else:
                sc().error(f"Missing patternsPath definition in the globalConfig.json for the configId: {configId}!")
            # Creating the SpecificConfiguration object
            if COMPILER in self.globalConfig[configId]:
                usedCompiler = self.globalConfig[configId][COMPILER]
                self.specificConfigurations[configId] = Emma.emma_libs.specificConfigurationFactory.createSpecificConfiguration(usedCompiler, noPrompt=noPrompt)
                # Processing the compiler dependent parts of the configuration
                sc().info(f"Processing the mapfiles of the configID `{configId}`")
                self.specificConfigurations[configId].readConfiguration(configurationPath, mapfilesPathForThisConfigId, configId, self.globalConfig[configId])
                # Validating the the configuration
                if not self.specificConfigurations[configId].checkConfiguration(configId, self.globalConfig[configId]):
                    sc().warning("The specificConfiguration of the configId \"" + configId + "\" is invalid!\n" + "The configId \"" + configId + "\" will not be analysed!")
                    configIDsToRemove.append(configId)
            else:
                sc().error(f"The configuration of the configID `{configId}` does not contain a `compiler` key!")

        # Remove unwanted configIDs
        for configId in configIDsToRemove:
            self.globalConfig.pop(configId, None)

    @staticmethod
    def __readGlobalConfigJson(path):
        """
        Function to read in and process the globalConfig.
        :param path: Path of the globalConfig file.
        :return: The content of the globalConfig.
        """
        # Load the globalConfig file
        globalConfig = Emma.shared_libs.emma_helper.readJson(path)

        # Loading the config files of the defined configID-s
        for configId in list(globalConfig.keys()):  # List of keys required so we can remove the ignoreConfigID entries
            if IGNORE_CONFIG_ID in globalConfig[configId].keys():
                # Check that flag has the correct type
                if not isinstance(globalConfig[configId][IGNORE_CONFIG_ID], bool):
                    sc().error("The " + IGNORE_CONFIG_ID + " of " + configId + " has a type " +
                               str(type(globalConfig[configId][IGNORE_CONFIG_ID])) + " instead of bool. " +
                               "Please be sure to use correct JSON syntax: boolean constants are written true and false.")
                elif globalConfig[configId][IGNORE_CONFIG_ID] is True:
                    globalConfig.pop(configId)

        # Check whether the globalConfig is empty
        if not globalConfig:
            sc().warning("No configID was defined or all of them were ignored.")

        return globalConfig

    @staticmethod
    def __readAddressSpacesJson(path):
        """
        Function to read in and process the addressSpaces config file.
        :param path: Path of the addressSpaces config file.
        :return: The content of the addressSpaces config file.
        """
        # Load the addressSpaces file
        addressSpaces = Emma.shared_libs.emma_helper.readJson(path)
        for memType in addressSpaces["memory"].keys():
            if START not in addressSpaces["memory"][memType].keys():
                sc().error(f"The {path} does not have the key: {START}")
            else:
                try:
                    startAddress = addressSpaces["memory"][memType][START]
                    int(startAddress, 16)
                except ValueError:
                    sc().error(f"The start address {startAddress} in {path} is not valid.")
            if END not in addressSpaces["memory"][memType].keys():
                sc().error(f"The {path} does not have the key: {END}.")
            else:
                try:
                    endAddress = addressSpaces["memory"][memType][END]
                    int(endAddress, 16)
                except ValueError:
                    sc().error(f"The end address {endAddress} in {path} is not valid.")
            if TYPE not in addressSpaces["memory"][memType].keys():
                sc().error(f"The {path} does not have the key: {TYPE}.")
        # Removing the imported memory entries if they are listed in the IGNORE_MEMORY
        if IGNORE_MEMORY in addressSpaces.keys():
            for memoryToIgnore in addressSpaces[IGNORE_MEMORY]:
                if addressSpaces["memory"][memoryToIgnore]:
                    addressSpaces["memory"].pop(memoryToIgnore)
                    sc().debug("Memory entry \"" + memoryToIgnore + "\" defined in \"" + path + "\" is marked to be ignored...")
                else:
                    sc().error(f"The key {memoryToIgnore} which is in the ignore list, does not exist in the memory object of {path}.")

        return addressSpaces
