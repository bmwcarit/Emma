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

from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper
import emma_libs.memoryEntry
import emma_libs.configuration
import emma_libs.mapfileProcessorFactory
import emma_libs.memoryMap
import emma_libs.categorisation


class MemoryManager:
    """
    A class to organize the processing of the configuration and the mapfiles and the storage of the created reports.
    """
    class Settings:
        """
        Settings that influence the operation of the MemoryManager object.
        """
        def __init__(self, projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt):
            self.projectName = projectName
            self.configurationPath = configurationPath
            self.mapfilesPath = mapfilesPath
            self.outputPath = outputPath
            self.analyseDebug = analyseDebug
            self.createCategories = createCategories
            self.removeUnmatched = removeUnmatched
            self.noPrompt = noPrompt

    def __init__(self, projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt):
        # Processing the command line arguments and storing it into the settings member
        self.settings = MemoryManager.Settings(projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt)
        # Check whether the configuration and the mapfiles folders exist
        shared_libs.emma_helper.checkIfFolderExists(self.settings.mapfilesPath)
        # The configuration is empty at this moment, it can be read in with another method
        self.configuration = None
        # The memory content is empty at this moment, it can be loaded with another method
        self.memoryContent = None
        # The categorisation object does not exist yet, it can be created after reading in the configuration
        self.categorisation = None

    def readConfiguration(self):
        """
        A method to read the configuration.
        :return: None
        """
        # Reading in the configuration
        self.configuration = emma_libs.configuration.Configuration()
        self.configuration.readConfiguration(self.settings.configurationPath, self.settings.mapfilesPath, self.settings.noPrompt)
        # Creating the categorisation object
        self.categorisation = emma_libs.categorisation.Categorisation(shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_OBJECTS_JSON),
                                                                      shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_KEYWORDS_OBJECTS_JSON),
                                                                      shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_SECTIONS_JSON),
                                                                      shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_KEYWORDS_SECTIONS_JSON),
                                                                      self.settings.noPrompt)

    def processMapfiles(self):
        """
        A method to process the mapfiles.
        :return: None
        """
        # If the configuration was already loaded
        if self.configuration is not None:

            # We will create an empty memory content that will be filled now
            self.memoryContent = {}

            # Processing the mapfiles for every configId
            for configId in self.configuration.globalConfig:

                # Creating the configId in the memory content
                self.memoryContent[configId] = {}

                sc().info("Importing Data for \"" + configId + "\", this may take some time...")

                # Creating a mapfile processor based on the compiler that was defined for the configId
                usedCompiler = self.configuration.globalConfig[configId]["compiler"]
                mapfileProcessor = emma_libs.mapfileProcessorFactory.createSpecificMapfileProcesor(usedCompiler)

                # Importing the mapfile contents for the configId with the created mapfile processor
                sectionCollection, objectCollection = mapfileProcessor.processMapfiles(configId, self.configuration.globalConfig[configId], self.settings.analyseDebug)

                # Filling out the categories in the consumerCollections
                self.categorisation.fillOutCategories(sectionCollection, objectCollection)

                # Updating the categorisation files from the categorisation keywords and remove the unmatched one based on the settings
                self.categorisation.manageCategoriesFiles(self.settings.createCategories, self.settings.removeUnmatched, sectionCollection, objectCollection)

                # Resolving the duplicate, containment and Overlap in the consumerCollections
                emma_libs.memoryMap.resolveDuplicateContainmentOverlap(sectionCollection, emma_libs.memoryEntry.SectionEntry)
                emma_libs.memoryMap.resolveDuplicateContainmentOverlap(objectCollection, emma_libs.memoryEntry.ObjectEntry)

                # Storing the consumer collections
                self.memoryContent[configId][FILE_IDENTIFIER_SECTION_SUMMARY] = sectionCollection
                self.memoryContent[configId][FILE_IDENTIFIER_OBJECT_SUMMARY] = objectCollection

                # Creating a common consumerCollection
                self.memoryContent[configId][FILE_IDENTIFIER_OBJECTS_IN_SECTIONS] = emma_libs.memoryMap.calculateObjectsInSections(self.memoryContent[configId][FILE_IDENTIFIER_SECTION_SUMMARY],
                                                                                                                                   self.memoryContent[configId][FILE_IDENTIFIER_OBJECT_SUMMARY])
        else:
            sc().error("The configuration needs to be loaded before processing the mapfiles!")

    def createReports(self):
        """
        A method to create the reports.
        :return: None
        """
        # If the mapfiles were already processed
        if self.memoryContent is not None:
            # Putting the same consumer collection types together
            # (At this points the collections are grouped by configId then by their types)
            consumerCollections = {}
            for configId in self.memoryContent.keys():
                for collectionType in self.memoryContent[configId].keys():
                    if collectionType not in consumerCollections:
                        consumerCollections[collectionType] = []
                    consumerCollections[collectionType].extend(self.memoryContent[configId][collectionType])

            # Creating reports from the consumer colections
            for collectionType in consumerCollections.keys():
                reportPath = emma_libs.memoryMap.createReportPath(self.settings.outputPath, self.settings.projectName, collectionType)
                emma_libs.memoryMap.writeReportToDisk(reportPath, consumerCollections[collectionType])
                sc().info("A report was stored:", os.path.abspath(reportPath))
        else:
            sc().error("The mapfiles need to be processed before creating the reports!")
