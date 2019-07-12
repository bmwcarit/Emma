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
import datetime

import pypiscout as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper
import emma_libs.memoryEntry
import emma_libs.configuration
import emma_libs.ghsMapfileProcessor
import emma_libs.memoryMap


class MemoryManager:
    class Settings:
        def __init__(self, args):
            self.projectName = shared_libs.emma_helper.projectNameFromPath(shared_libs.emma_helper.joinPath(args.project))
            self.configurationPath = args.project
            self.mapfilesPath = shared_libs.emma_helper.joinPath(args.mapfiles)
            self.analyseDebug = args.analyse_debug
            self.verbosity = args.verbosity
            self.Werror = args.Werror
            self.create_categories = args.create_categories
            self.remove_unmatched = args.remove_unmatched
            self.dir = args.dir
            self.subDir = args.subdir

    def __init__(self, args):
        # Processing the command line arguments and storing it into the settings member
        self.settings = MemoryManager.Settings(args)
        # Check whether the configuration and the mapfiles folders exist
        shared_libs.emma_helper.checkIfFolderExists(self.settings.mapfilesPath)
        # The configuration is empty at this moment, it can be read in with another method
        self.configuration = None
        # The memory content is empty at this moment, it can be loaded with another method
        self.memoryContent = None

    def readConfiguration(self):
        # Reading in the configuration
        self.configuration = emma_libs.configuration.Configuration(self.settings.configurationPath, self.settings.mapfilesPath)

    def processMapfiles(self):
        # If the configuration was already loaded
        if self.configuration is not None:

            # We will create an empty memory content that will be filled now
            self.memoryContent = dict()

            # Processing the mapfiles for every configId
            for configId in self.configuration.globalConfig:

                # Creating the configId in the memory content
                self.memoryContent[configId] = dict()

                sc.info("Importing Data for \"" + configId + "\", this may take some time...")

                # Creating a mapfile processor based on the compiler that was defined for the configId
                usedCompiler = self.configuration.globalConfig[configId]["compiler"]
                if "GreenHills" == usedCompiler:
                    mapfileProcessor = emma_libs.ghsMapfileProcessor.GhsMapfileProcessor(configId, self.settings.analyseDebug, self.settings.verbosity, self.settings.Werror)
                else:
                    sc.error("The " + configId + " contains an unexpected compiler value: " + usedCompiler)
                    sys.exit(-10)

                # Importing the mapfile contents for the configId with the created mapfile processor
                sectionCollection, objectCollection = mapfileProcessor.processMapfiles(self.configuration.globalConfig[configId])
                self.memoryContent[configId][FILE_IDENTIFIER_SECTION_SUMMARY] = sectionCollection
                self.memoryContent[configId][FILE_IDENTIFIER_OBJECT_SUMMARY] = objectCollection

                # Resolving the duplicate, containment and Overlap in the consumerCollection
                emma_libs.memoryMap.resolveDuplicateContainmentOverlap(self.memoryContent[configId][FILE_IDENTIFIER_SECTION_SUMMARY], emma_libs.memoryEntry.SectionEntry)
                emma_libs.memoryMap.resolveDuplicateContainmentOverlap(self.memoryContent[configId][FILE_IDENTIFIER_OBJECT_SUMMARY], emma_libs.memoryEntry.ObjectEntry)

                # Creating a common consumerCollection
                self.memoryContent[configId][FILE_IDENTIFIER_OBJECTS_IN_SECTIONS] = emma_libs.memoryMap.calculateObjectsInSections(self.memoryContent[configId][FILE_IDENTIFIER_SECTION_SUMMARY],
                                                                                                                                   self.memoryContent[configId][FILE_IDENTIFIER_OBJECT_SUMMARY])
        else:
            sc.error("The configuration needs to be loaded before processing the mapfiles!")
            sys.exit(-10)

    def createReports(self):
        # The reports will be created in a normal case
        # FIXME Implement the categorization function here (see state before redesign)

        # Putting the same consumer collection types together
        # (At this points the collections are grouped by configId then by their types)
        consumerCollections = dict()
        for configId in self.memoryContent.keys():
            for collectionType in self.memoryContent[configId].keys():
                if collectionType not in consumerCollections:
                    consumerCollections[collectionType] = list()
                consumerCollections[collectionType].extend(self.memoryContent[configId][collectionType])

        for collectionType in consumerCollections.keys():
            reportPath = emma_libs.memoryMap.createReportPath(self.settings.dir,
                                                              self.settings.subDir,
                                                              self.settings.projectName,
                                                              collectionType)
            emma_libs.memoryMap.writeReportToDisk(reportPath, consumerCollections[collectionType])
