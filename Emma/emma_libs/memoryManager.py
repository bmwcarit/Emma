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
from enum import IntEnum

from pypiscout.SCout_Logger import Logger as sc
import svgwrite
# import graphviz

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.shared_libs.emma_helper
import Emma.emma_libs.memoryEntry
import Emma.emma_libs.configuration
import Emma.emma_libs.mapfileProcessorFactory
import Emma.emma_libs.memoryMap
import Emma.emma_libs.categorisation


class Element(IntEnum):
    AddressStart = 0
    AddressEnd = 1
    AddressLength = 2
    Fqn = 3
    OriginalAddressStart = 4

class PlottedElement(IntEnum):
    AddressEnd = 0
    yAxe = 1


class MemoryManager:
    """
    A class to organize the processing of the configuration and the mapfiles and the storage of the created reports.
    """

    class Settings:
        # pylint: disable=too-many-instance-attributes, too-many-arguments, too-few-public-methods
        # Rationale: This class´s only purpose is to store settings, thus having too many members and parameters is not an error.
        """
        Settings that influence the operation of the MemoryManager object.
        """
        def __init__(self, projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt, noResolveOverlap, teamScale, dryRun):
            self.projectName = projectName
            self.configurationPath = configurationPath
            self.mapfilesPath = mapfilesPath
            self.outputPath = outputPath
            self.analyseDebug = analyseDebug
            self.createCategories = createCategories
            self.removeUnmatched = removeUnmatched
            self.noPrompt = noPrompt
            self.noResolveOverlap = noResolveOverlap
            self.teamScale = teamScale
            self.dryRun = dryRun

    def __init__(self, projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt, noResolveOverlap, teamScale, dryRun):
        # pylint: disable=too-many-arguments
        # Rationale: We need to initialize the Settings, so the number of arguments are needed.

        # Processing the command line arguments and storing it into the settings member
        self.settings = MemoryManager.Settings(projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt, noResolveOverlap, teamScale, dryRun)
        # Check whether the configuration and the mapfiles folders exist
        Emma.shared_libs.emma_helper.checkIfFolderExists(self.settings.mapfilesPath)
        self.configuration = None           # The configuration is empty at this moment, it can be read in with another method
        # memoryContent [dict(list(memEntry))]
        # Each key of this dict represents a configID; dict values are lists of consumerCollections
        # consumerCollection: [list(memEntry)] lists of memEntry's; e.g. a Section_Summary which contains all memEnty objects per configID)
        self.memoryContent = None           # The memory content is empty at this moment, it can be loaded with another method
        self.categorisation = None          # The categorisation object does not exist yet, it can be created after reading in the configuration

    def readConfiguration(self):
        """
        A method to read the configuration.
        :return: None
        """
        # Reading in the configuration
        self.configuration = Emma.emma_libs.configuration.Configuration()
        self.configuration.readConfiguration(self.settings.configurationPath, self.settings.mapfilesPath, self.settings.noPrompt, self.settings.analyseDebug)
        # Creating the categorisation object
        self.categorisation = Emma.emma_libs.categorisation.Categorisation(Emma.shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_OBJECTS_JSON),
                                                                           Emma.shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_KEYWORDS_OBJECTS_JSON),
                                                                           Emma.shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_SECTIONS_JSON),
                                                                           Emma.shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_KEYWORDS_SECTIONS_JSON),
                                                                           self.settings.noPrompt, self.settings.createCategories
                                                                           )

    def processMapfiles(self):
        """
        A method to process the mapfiles.
        :return: None
        """
        # Check if the configuration loaded
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
                mapfileProcessor = Emma.emma_libs.mapfileProcessorFactory.createSpecificMapfileProcesor(usedCompiler)

                # Importing the mapfile contents for the configId with the created mapfile processor
                sectionCollection, objectCollection = mapfileProcessor.processMapfiles(configId, self.configuration.globalConfig[configId], self.settings.analyseDebug)

                # Filling out the categories in the consumerCollections
                self.categorisation.fillOutCategories(sectionCollection, objectCollection)

                # Updating the categorisation files from the categorisation keywords and remove the unmatched one based on the settings
                self.categorisation.manageCategoriesFiles(self.settings.createCategories, self.settings.removeUnmatched, sectionCollection, objectCollection)

                # Do not resolve duplicate, containment and overlap when createCategories is active
                if not self.settings.createCategories:
                    # Resolving the duplicate, containment and overlap in the consumerCollections
                    if not self.settings.noResolveOverlap:
                        sc().info("Resolving section overlaps. This may take some time...")
                        Emma.emma_libs.memoryMap.resolveDuplicateContainmentOverlap(sectionCollection, Emma.emma_libs.memoryEntry.SectionEntry)
                        sc().info("Resolving object overlaps. This may take some time...")
                        Emma.emma_libs.memoryMap.resolveDuplicateContainmentOverlap(objectCollection, Emma.emma_libs.memoryEntry.ObjectEntry)

                    # Storing the consumer collections
                    self.memoryContent[configId][FILE_IDENTIFIER_SECTION_SUMMARY] = sectionCollection
                    self.memoryContent[configId][FILE_IDENTIFIER_OBJECT_SUMMARY] = objectCollection

                    # Creating a common consumerCollection
                    sc().info("Calculating objects in sections. This may take some time...")
                    self.memoryContent[configId][
                        FILE_IDENTIFIER_OBJECTS_IN_SECTIONS] = Emma.emma_libs.memoryMap.calculateObjectsInSections(
                        self.memoryContent[configId][FILE_IDENTIFIER_SECTION_SUMMARY],
                        self.memoryContent[configId][FILE_IDENTIFIER_OBJECT_SUMMARY])
                else:
                    pass
        else:
            sc().error("The configuration needs to be loaded before processing the mapfiles!")

    def createReports(self, teamscale=False):
        """
        Creates the reports
        :param image: create svg report if True
        :param noprompt: no prompt is active if True
        :return: None
        """

        def consumerCollections2GlobalList():
            """
            Concatenate each type of consumerCollection (memoryContent: dict(list(memEntry)) -> consumerCollection: list(list(memEntry)))
            Concatenates all values (per list (Section_Summary, Object_Summary, Objects_in_Sections)) within the memoryContent dict (-> keys are configIDs)
            :return: [list(list(memEntry))] Concatenated list of consumerCollections
            """
            # Putting the same consumer collection types together
            # (At this points the collections are grouped by configID then by their types)
            consumerCollections = {}
            for configId in self.memoryContent:
                for collectionType in self.memoryContent[configId]:
                    if collectionType not in consumerCollections:
                        consumerCollections[collectionType] = []
                    consumerCollections[collectionType].extend(self.memoryContent[configId][collectionType])
            return consumerCollections

        def createStandardReports():
            """
            Create Section, Object and ObjectsInSections reports
            :return: None
            """
            consumerCollections = consumerCollections2GlobalList()

            # Creating reports from the consumer collections
            for collectionType in consumerCollections:
                reportPath = Emma.emma_libs.memoryMap.createReportPath(self.settings.outputPath, self.settings.projectName, collectionType, ".csv")
                Emma.emma_libs.memoryMap.writeReportToDisk(reportPath, consumerCollections[collectionType])
                sc().info("A report was stored:", os.path.abspath(reportPath))

        # def createDotReports():
        #     GLOBAL_ATTRIBUTES = {
        #         "fontname": "Helvetica",
        #         "shape": "octagon"
        #     }
        #
        #
        #     graph = graphviz.Digraph("newGraph")
        #     graph.attr('node', GLOBAL_ATTRIBUTES)
        #     # for
        #     # graph.node(, 'C', _attributes={'shape': 'triangle'})
        #     graph.node('A', 'A')
        #     graph.node('B', 'B')
        #     graph.node('C', 'C', _attributes={'shape': 'triangle'})
        #
        #     print(graph.source)
        def createSvgReport(startPoint, endPoint):
            """
            plot sections and objects of a given memory area
            :param startPoint: beginning of address area
            :param endPoint: end of address area
            """

            def draw(image, elementstoPlot, startPoint, y, colour):
                yAxe = y
                lastSectionPosition = 5
                biggestEndAddress = 0
                plottedElements = []
                distanceBetweenElements = 15
                for index, element in enumerate(elementstoPlot):
                    xAxeRectStart = element[Element.AddressStart] - startPoint
                    rectLength = element[Element.AddressLength] - 1
                    originalStartAddress = element[Element.AddressStart]
                    fontColour = "black"
                    if len(str(element[Element.AddressEnd])) > 11 or len(str(originalStartAddress)) > 11:          # check if address start / end fits in the rectangle
                        yAxe = yAxe + len(str(element[Element.AddressEnd])) - 10
                    if element[Element.AddressStart] < startPoint:
                        xAxeRectStart = 0
                        rectLength = element[Element.AddressEnd] - startPoint
                        originalStartAddress = element[Element.OriginalAddressStart]
                        fontColour = "red"
                    if index == 0:
                        biggestEndAddress = element[Element.AddressEnd]
                    else:
                        # check if the actual element is overlapped by the last element
                        if element[Element.AddressStart] <= elementstoPlot[index-1][Element.AddressStart] or element[Element.AddressStart] < elementstoPlot[index-1][Element.AddressEnd]:
                            yAxe = yAxe + distanceBetweenElements
                            plottedElements.append((element[Element.AddressEnd], yAxe))
                            if yAxe > lastSectionPosition:
                                lastSectionPosition = yAxe
                            if element[Element.AddressEnd] > biggestEndAddress:
                                biggestEndAddress = element[Element.AddressEnd]
                        elif element[Element.AddressStart] < biggestEndAddress:
                            for el in plottedElements:
                                if element[Element.AddressStart] < el[PlottedElement.AddressEnd] and yAxe <= el[PlottedElement.yAxe]:
                                    yAxe = el[PlottedElement.yAxe] + distanceBetweenElements
                        else:
                            yAxe = y
                            biggestEndAddress = element[Element.AddressEnd]
                    image.add(image.rect((xAxeRectStart, yAxe), size=(rectLength, 10), stroke=colour, fill=colour, opacity='0.3'))
                    # check if the FQN fits in the rectangle
                    if rectLength <= len(element[Element.Fqn]):
                        image.add(image.text(element[Element.Fqn], insert=(xAxeRectStart, yAxe - 1), font_size='2px', writing_mode="lr", font_family="Helvetica, sans-serif", fill=fontColour))
                        xAxeStart = xAxeRectStart + 1
                        xAxeEnd = element[Element.AddressEnd] - startPoint - 1
                        # if the rectangle smaller than 4, then write the end address outside the rectangle
                        if rectLength < 4:
                            xAxeEnd = element[Element.AddressEnd] - startPoint + 1
                        image.add(image.text(hex(originalStartAddress), insert=(xAxeStart, yAxe), font_size='2px', writing_mode="tb", font_family="Helvetica, sans-serif", fill=fontColour))
                        image.add(image.text(hex(element[Element.AddressEnd]), insert=(xAxeEnd, yAxe), font_size='2px', writing_mode="tb", font_family="Helvetica, sans-serif", fill=fontColour))
                        if yAxe > lastSectionPosition:
                            lastSectionPosition = yAxe
                        plottedElements.append((element[Element.AddressEnd] + len(element[Element.Fqn]), yAxe))
                    else:
                        image.add(image.text(hex(originalStartAddress), insert=(xAxeRectStart + 1, yAxe), font_size='2px', writing_mode="tb", font_family="Helvetica, sans-serif", fill=fontColour))
                        image.add(image.text(hex(element[Element.AddressEnd]), insert=(element[Element.AddressEnd] - startPoint - 1, yAxe), font_size='2px', writing_mode="tb", font_family="Helvetica, sans-serif", fill=fontColour))
                        image.add(image.text(element[Element.Fqn], insert=(xAxeRectStart + 5, yAxe + 2), font_size='2px', writing_mode="lr", font_family="Helvetica, sans-serif", fill=fontColour))
                        plottedElements.append((element[Element.AddressEnd], yAxe))
                return lastSectionPosition

            consumerCollections = consumerCollections2GlobalList()
            reportPath = Emma.emma_libs.memoryMap.createReportPath(self.settings.outputPath, self.settings.projectName, str(hex(startPoint)) + '_' + str(hex(endPoint)), ".svg")

            def getElementsToPlot(ElementName):
                elementsToPlot = []
                for elementToPlot in consumerCollections[ElementName]:
                    if elementToPlot.addressLength != 0:
                        if startPoint <= elementToPlot.addressStart < endPoint:
                            elementsToPlot.append((elementToPlot.addressStart, elementToPlot.addressEnd(), elementToPlot.addressLength, elementToPlot.getFQN()))
                        elif elementToPlot.addressEnd() > startPoint and elementToPlot.addressStart < endPoint:
                            elementsToPlot.append((0, elementToPlot.addressEnd(), elementToPlot.addressLength, elementToPlot.getFQN(), elementToPlot.addressStart))
                return elementsToPlot

            imageHeight = 3000      # define some height of the image
            image = svgwrite.Drawing(reportPath, size=(endPoint - startPoint, imageHeight))
            # plot sections
            y2 = draw(image, getElementsToPlot("Section_Summary"), startPoint, 5, "yellow") + 15
            # plot objects
            draw(image, getElementsToPlot("Object_Summary"), startPoint, y2, "green")
            image.save()

        def createTeamScaleReports():
            """
            Write JSON output that can be imported in TeamScale
            :return: None
            """
            consumerCollections = consumerCollections2GlobalList()
            resultsLst = []

            def _createTeamScalePath(memEntryRow):
                """
                Return TeamScale path in the format configID::memType::category::section::object
                :param memEntryRow:
                :return: [str] TeamScale path
                """
                sep = "::"
                row = memEntryRow
                return f"{row.configID}{sep}{row.memType}{sep}{row.category}{sep}{row.sectionName}{sep}{row.objectName}" if row.objectName != "" and row.objectName != OBJECTS_IN_SECTIONS_SECTION_ENTRY and row.objectName != OBJECTS_IN_SECTIONS_SECTION_RESERVE else f"{row.configID}{sep}{row.memType}{sep}{row.category}{sep}{row.sectionName}"

            # Creating reports from the consumer collections
            for memEntryRow in consumerCollections["Section_Summary"]:
                resultsLst.append({"path": _createTeamScalePath(memEntryRow), "count": memEntryRow.addressLength})
            for memEntryRow in consumerCollections["Object_Summary"]:
                resultsLst.append({"path": _createTeamScalePath(memEntryRow), "count": memEntryRow.addressLength})
            reportPath = Emma.emma_libs.memoryMap.createReportPath(self.settings.outputPath, self.settings.projectName, TEAMSCALE_PREFIX, "json")
            Emma.shared_libs.emma_helper.writeJson(reportPath, resultsLst)

        if self.memoryContent is not None:
            # TODO: Implement handling and choosing of which reports to create (via cmd line argument (like a comma separated string) (MSc)
            createStandardReports()

            # createDotReports()
            if teamscale:
                createTeamScaleReports()
        else:
            sc().error("The mapfiles need to be processed before creating the reports!")
