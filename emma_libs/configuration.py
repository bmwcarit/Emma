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
import abc

from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper
import emma_libs.specificConfigurationFactory


class Configuration:
    def __init__(self):
        self.specificConfigurations = dict()
        self.globalConfig = None
        pass

    def readConfiguration(self, configurationPath, mapfilesPath, noPrompt) -> None:
        # Check whether the configurationPath exists
        shared_libs.emma_helper.checkIfFolderExists(configurationPath)

        # Processing the globalConfig.json
        globalConfigPath = shared_libs.emma_helper.joinPath(configurationPath, "globalConfig.json")
        self.globalConfig = self.__readGlobalConfigJson(globalConfigPath)
        sc().info("Imported " + str(len(self.globalConfig)) + " global config entries:" + str(list(self.globalConfig.keys())))

        # Processing the addressSpaces*.json for all the configIds
        for configId in self.globalConfig:
            if "addressSpacesPath" in self.globalConfig[configId].keys():
                addressSpacesPath = shared_libs.emma_helper.joinPath(configurationPath, self.globalConfig[configId]["addressSpacesPath"])
                self.globalConfig[configId]["addressSpaces"] = self.__readAddressSpacesJson(addressSpacesPath)
            else:
                sc().error("The " + configId + " does not have the key: " + "addressSpacesPath")

        # Creating the SpecificConfiguration objects
        for configId in self.globalConfig:
            usedCompiler = self.globalConfig[configId]["compiler"]
            self.specificConfigurations[configId] = emma_libs.specificConfigurationFactory.createSpecificConfiguration(usedCompiler, noPrompt)
            # Processing the compiler dependent parts of the configuration
            sc().info("Processing the mapfiles of the configID \"" + configId + "\"")
            self.specificConfigurations[configId].readConfiguration(configurationPath, mapfilesPath, configId, self.globalConfig[configId])
            # Validating the the configuration
            if not self.specificConfigurations[configId].validateConfiguration(configId, self.globalConfig[configId]):
                sc().warning("The specificConfiguration object of the configId \"" +
                             configId + "\" reported that the configuration is invalid!\n" +
                             "The configId \"" + configId + "\" will not be analysed!")

    def __readGlobalConfigJson(self, path):
        # Load the globalConfig file
        globalConfig = shared_libs.emma_helper.readJson(path)

        # Loading the config files of the defined configID-s
        for configId in list(globalConfig.keys()):  # List of keys required so we can remove the ignoreConfigID entrys
            if IGNORE_CONFIG_ID in globalConfig[configId].keys():
                # Skip configID if ["ignoreConfigID"] is True
                if type(globalConfig[configId][IGNORE_CONFIG_ID]) is not bool:
                    # Check that flag has the correct type
                    sc().error("The " + IGNORE_CONFIG_ID + " of " + configId + " has a type " +
                               str(type(globalConfig[configId][IGNORE_CONFIG_ID])) + " instead of bool. " +
                               "Please be sure to use correct JSON syntax: boolean constants are written true and false.")
                elif globalConfig[configId][IGNORE_CONFIG_ID] is True:
                    globalConfig.pop(configId)

        if not len(globalConfig):
            sc().warning("No configID was defined or all of them were ignored.")

        return globalConfig

    def __readAddressSpacesJson(self, path):
        # Load the addressSpaces file
        addressSpaces = shared_libs.emma_helper.readJson(path)

        # Removing the imported memory entries if they are listed in the IGNORE_MEMORY
        if IGNORE_MEMORY in addressSpaces.keys():
            for memoryToIgnore in addressSpaces[IGNORE_MEMORY]:
                if addressSpaces["memory"][memoryToIgnore]:
                    addressSpaces["memory"].pop(memoryToIgnore)
                    sc().info("The memory entry \"" + memoryToIgnore + "\" of the \"" + path + "\" is marked to be ignored...")
                else:
                    sc().error("The key " + memoryToIgnore + " which is in the ignore list, does not exist in the memory object of " + path)

        return addressSpaces
