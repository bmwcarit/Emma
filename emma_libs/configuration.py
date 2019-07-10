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


def readGlobalConfigJson(configPath):
    """
    :param configPath: file path
    :return: the globalConfig dict
    """
    # Load global config file
    globalConfig = shared_libs.emma_helper.readJson(configPath)

    # Loading the config files of the defined configID-s
    for configID in list(globalConfig.keys()):  # List of keys required so we can remove the ignoreConfigID entrys
        if IGNORE_CONFIG_ID in globalConfig[configID].keys():
            # Skip configID if ["ignoreConfigID"] is True
            if type(globalConfig[configID][IGNORE_CONFIG_ID]) is not bool:
                # Check that flag has the correct type
                sc.error("The " + IGNORE_CONFIG_ID + " of " + configID + " has a type " + str(
                    type(globalConfig[configID][IGNORE_CONFIG_ID])) + " instead of bool. " +
                         "Please be sure to use correct JSON syntax: boolean constants are written true and false.")
                sys.exit(-10)
            elif globalConfig[configID][IGNORE_CONFIG_ID] is True:
                globalConfig.pop(configID)
                if len(globalConfig) < 1 and self.args.verbosity <= 1:
                    sc.warning("No configID left; all were ignored.")
                continue

        # Loading the addressSpaces
        if "addressSpacesPath" in globalConfig[configID].keys():
            globalConfig[configID]["addressSpaces"] = shared_libs.emma_helper.readJson(
                shared_libs.emma_helper.joinPath(self.projectPath, globalConfig[configID]["addressSpacesPath"]))

            # Removing the imported memory entries if they are listed in IGNORE_MEM_TYPE key
            if IGNORE_MEMORY in globalConfig[configID]["addressSpaces"].keys():
                for memoryToIgnore in globalConfig[configID]["addressSpaces"][IGNORE_MEMORY]:
                    if globalConfig[configID]["addressSpaces"]["memory"][memoryToIgnore]:
                        globalConfig[configID]["addressSpaces"]["memory"].pop(memoryToIgnore)
                        sc.info(
                            "The memory entry \"" + memoryToIgnore + "\" of the configID \"" + configID + "\" is marked to be ignored...")
                    else:
                        sc.error(
                            "The key " + memoryToIgnore + " which is in the ignore list, does not exist in the memory object of " +
                            globalConfig[configID]["addressSpacesPath"])
                        sys.exit(-10)
        else:
            sc.error("The " + CONFIG_ID + " does not have the key: " + "addressSpacesPath")
            sys.exit(-10)

        # Loading the sections if the file is present (only needed in case of VAS-es)
        if "virtualSectionsPath" in globalConfig[configID].keys():
            globalConfig[configID]["virtualSections"] = shared_libs.emma_helper.readJson(
                shared_libs.emma_helper.joinPath(self.projectPath, globalConfig[configID]["virtualSectionsPath"]))

        # Loading the patterns
        if "patternsPath" in globalConfig[configID].keys():
            globalConfig[configID]["patterns"] = shared_libs.emma_helper.readJson(
                shared_libs.emma_helper.joinPath(self.projectPath, globalConfig[configID]["patternsPath"]))
        else:
            sc.error("The " + CONFIG_ID + " does not have the key: " + "patternsPath")
            sys.exit(-10)

        # Flag to load a monolith file only once; we don't do it here since we might work with DMA only
        globalConfig[configID]["monolithLoaded"] = False
        # Flag to sort monolith table only once; we don't do it here since we might work with DMA only
        globalConfig[configID]["sortMonolithTabularised"] = False
    return globalConfig

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




