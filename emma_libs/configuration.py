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

import pypiscout as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper
import emma_libs.ghsConfiguration


class Configuration:
    def __init__(self, configurationPath, mapfilesPath):
        # Check whether the configurationPath exists
        shared_libs.emma_helper.checkIfFolderExists(configurationPath)

        # Processing the globalConfig.json
        globalConfigPath = shared_libs.emma_helper.joinPath(configurationPath, "globalConfig.json")
        self.globalConfig = self.readGlobalConfigJson(globalConfigPath)
        sc.info("Imported " + str(len(self.globalConfig)) + " global config entries")

        # Processing the addressSpaces*.json for all the configIds
        for configId in self.globalConfig:
            if "addressSpacesPath" in self.globalConfig[configId].keys():
                addressSpacesPath = shared_libs.emma_helper.joinPath(configurationPath, self.globalConfig[configId]["addressSpacesPath"])
                self.globalConfig[configId]["addressSpaces"] = self.readAddressSpacesJson(addressSpacesPath)
            else:
                sc.error("The " + configId + " does not have the key: " + "addressSpacesPath")
                sys.exit(-10)

        # Loading the categories config files. These files are optional, if they are not present we will store None instead.
        categoriesObjectsPath = shared_libs.emma_helper.joinPath(configurationPath, CATEGORIES_OBJECTS_JSON)
        self.categoriesObjects = self.readCategoriesJson(categoriesObjectsPath)
        categoriesObjectsKeywordsPath = shared_libs.emma_helper.joinPath(configurationPath, CATEGORIES_KEYWORDS_OBJECTS_JSON)
        self.categoriesObjectsKeywords = self.readCategoriesJson(categoriesObjectsKeywordsPath)
        categoriesSectionsPath = shared_libs.emma_helper.joinPath(configurationPath, CATEGORIES_SECTIONS_JSON)
        self.categoriesSections = self.readCategoriesJson(categoriesSectionsPath)
        categoriesSectionsKeywordsPath = shared_libs.emma_helper.joinPath(configurationPath, CATEGORIES_KEYWORDS_SECTIONS_JSON)
        self.categoriesSectionsKeywords = self.readCategoriesJson(categoriesSectionsKeywordsPath)

        # FIXME The mapfiles and other non-compiler dependent parts of the patterns*.json needs to be read in here

        # Processing the compiler dependent parts of the configuration
        for configId in self.globalConfig:
            sc.info("Processing configID \"" + configId + "\"")
            usedCompiler = self.globalConfig[configId]["compiler"]
            if "GreenHills" == usedCompiler:
                emma_libs.ghsConfiguration.GhsConfiguration(configurationPath, mapfilesPath, self.globalConfig[configId])
            else:
                sc.error("The " + configId + " contains an unexpected compiler value: " + usedCompiler)
                sys.exit(-10)

    def readGlobalConfigJson(self, path):
        # Load the globalConfig file
        globalConfig = shared_libs.emma_helper.readJson(path)

        # Loading the config files of the defined configID-s
        for configId in list(globalConfig.keys()):  # List of keys required so we can remove the ignoreConfigID entrys
            if IGNORE_CONFIG_ID in globalConfig[configId].keys():
                # Skip configID if ["ignoreConfigID"] is True
                if type(globalConfig[configId][IGNORE_CONFIG_ID]) is not bool:
                    # Check that flag has the correct type
                    sc.error("The " + IGNORE_CONFIG_ID + " of " + configId + " has a type " +
                             str(type(globalConfig[configId][IGNORE_CONFIG_ID])) + " instead of bool. " +
                             "Please be sure to use correct JSON syntax: boolean constants are written true and false.")
                    sys.exit(-10)
                elif globalConfig[configId][IGNORE_CONFIG_ID] is True:
                    globalConfig.pop(configId)

        if len(globalConfig):
            sc.warning("No configID was defined or all of them were ignored.")

        return globalConfig

    def readAddressSpacesJson(self, path):
        # Load the addressSpaces file
        addressSpaces = shared_libs.emma_helper.readJson(path)

        # Removing the imported memory entries if they are listed in the IGNORE_MEMORY
        if IGNORE_MEMORY in addressSpaces.keys():
            for memoryToIgnore in addressSpaces[IGNORE_MEMORY]:
                if addressSpaces["memory"][memoryToIgnore]:
                    addressSpaces["memory"].pop(memoryToIgnore)
                    sc.info("The memory entry \"" + memoryToIgnore + "\" of the \"" + path + "\" is marked to be ignored...")
                else:
                    sc.error("The key " + memoryToIgnore + " which is in the ignore list, does not exist in the memory object of " + path)
                    sys.exit(-10)

        return addressSpaces

    def readCategoriesJson(self, path):
        if os.path.exists(path):
            categoriesJson = shared_libs.emma_helper.readJson(path)
        else:
            categoriesJson = None
            sc.warning("There was no " + os.path.basename(path) + " file found, the categorization based on this will be skipped.")

        return categoriesJson


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




