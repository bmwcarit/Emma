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

        checkMonolithSections()


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
