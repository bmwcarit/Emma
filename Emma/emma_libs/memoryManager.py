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
        def __init__(self, projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt, noResolveOverlap, memVis, memVisResolved):
            self.projectName = projectName
            self.configurationPath = configurationPath
            self.mapfilesPath = mapfilesPath
            self.outputPath = outputPath
            self.analyseDebug = analyseDebug
            self.createCategories = createCategories
            self.removeUnmatched = removeUnmatched
            self.noPrompt = noPrompt
            self.noResolveOverlap = noResolveOverlap
            self.memVis = memVis
            self.memVisResolved = memVisResolved

    def __init__(self, projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt, noResolveOverlap, memVis, memVisResolved):
        # pylint: disable=too-many-arguments
        # Rationale: We need to initialize the Settings, so the number of arguments are needed.

        # Processing the command line arguments and storing it into the settings member
        self.settings = MemoryManager.Settings(projectName, configurationPath, mapfilesPath, outputPath, analyseDebug, createCategories, removeUnmatched, noPrompt, noResolveOverlap, memVis, memVisResolved)
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
        self.configuration.readConfiguration(self.settings.configurationPath, self.settings.mapfilesPath, self.settings.noPrompt)
        # Creating the categorisation object
        self.categorisation = Emma.emma_libs.categorisation.Categorisation(
            Emma.shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_OBJECTS_JSON),
            Emma.shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_KEYWORDS_OBJECTS_JSON),
            Emma.shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_SECTIONS_JSON),
            Emma.shared_libs.emma_helper.joinPath(self.settings.configurationPath, CATEGORIES_KEYWORDS_SECTIONS_JSON),
            self.settings.noPrompt
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
                    self.memoryContent[configId][FILE_IDENTIFIER_OBJECTS_IN_SECTIONS] = Emma.emma_libs.memoryMap.calculateObjectsInSections(
                        self.memoryContent[configId][FILE_IDENTIFIER_SECTION_SUMMARY],
                        self.memoryContent[configId][FILE_IDENTIFIER_OBJECT_SUMMARY])
                else:
                    pass
        else:
            sc().error("The configuration needs to be loaded before processing the mapfiles!")

    def createReports(self, memVis=False, memVisResolved=False, noprompt=False):
        """
        Creates the reports
        :param memVis: Create svg report with unresolved overlaps if True
        :param noprompt: No prompt is active if True
        :param noResolveOverlap: No overlaps are resolved if True
        :param memVisResolved: Create svg report visualising resolved overlaps if True
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
                reportPath = Emma.emma_libs.memoryMap.createReportPath(self.settings.outputPath, self.settings.projectName, collectionType, "csv")
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
        def createSvgReport(startPoint, endPoint, xScalingValue="1", yScalingValue="1"):
            """
            Plot sections and objects of a given memory area
            :param startPoint: Beginning of address area
            :param endPoint: End of address area
            :param xScalingValue: Scaling value of x axe, default 1
            :param yScalingValue: Scaling value of y axe, default 1
            """
            class Element(IntEnum):
                addressStart = 0
                addressEnd = 1
                addressLength = 2
                fqn = 3
                originalAddressStart = 4

            class PlottedElement(IntEnum):
                addressEnd = 0
                yAxe = 1

            def drawElements(image, elementsToPlot, startPoint, y, colour, scaling):
                """
                :param image: svgwrite.Drawing object
                :param elementsToPlot: [[addressStart, addressEnd, addressLength, fqn, originalAddressStart], ...] List of objects to plot (-> accessed via Element enum)
                :param startPoint: Beginning of the address area
                :param y: Start point on the y axis
                :param colour: [str] Text colour (see HTML reference)
                :param scaling: Scaling value
                :return: None
                """
                currYLvl = y
                biggestYSoFar = 5             # The highest y value section element, used to plot objects so they do not cross section elements; in pixel
                biggestEndAddrSoFar = 0
                plottedElements = []
                drawingOffset = 15
                smallSpacing = 1        # Small spacing in px used for spacing between edges of the rectangle and start/ end address label
                fontSize = 2
                startOfDrawingArea = 3
                fontColour = "black"
                rectHeight = 11

                for index, element in enumerate(elementsToPlot):
                    endAddrBigger = False           # flag that marks that end address of the current element is bigger than given end point
                    xAxeRectStart = element[Element.addressStart] - startPoint + startOfDrawingArea
                    rectLength = element[Element.addressLength] - 1
                    originalStartAddress = element[Element.addressStart]
                    if len(str(element[Element.addressEnd])) > rectHeight or len(str(originalStartAddress)) > rectHeight:          # Check if address start / end fits in the rectangle
                        currYLvl += len(str(element[Element.addressEnd])) - rectHeight
                    if element[Element.addressStart] < startPoint:
                        xAxeRectStart = startOfDrawingArea
                        rectLength = element[Element.addressEnd] - startPoint
                        originalStartAddress = element[Element.originalAddressStart]
                    # Check if address end of a drawing object is bigger than end point
                    if element[Element.addressEnd] > endPoint:
                        rectLength = endPoint - startPoint - xAxeRectStart + startOfDrawingArea
                        xAxeEnd = endPoint - startPoint + startOfDrawingArea
                        endAddrBigger = True
                    else:
                        xAxeEnd = element[Element.addressEnd] - startPoint + startOfDrawingArea
                    if index == 0:
                        biggestEndAddrSoFar = element[Element.addressEnd]
                    else:
                        # Check if the actual element is overlapped by the last element
                        startAddrPrevElement = elementsToPlot[index - 1][Element.addressStart]
                        endAddrPrevElement = elementsToPlot[index - 1][Element.addressEnd]
                        if element[Element.addressStart] <= startAddrPrevElement or element[Element.addressStart] < endAddrPrevElement:
                            currYLvl = currYLvl + drawingOffset
                            plottedElements.append((element[Element.addressEnd], currYLvl))
                            if element[Element.addressEnd] > biggestEndAddrSoFar:
                                biggestEndAddrSoFar = element[Element.addressEnd]
                        elif element[Element.addressStart] < biggestEndAddrSoFar:
                            for plottedElement in plottedElements:
                                if element[Element.addressStart] < plottedElement[PlottedElement.addressEnd] and currYLvl <= plottedElement[PlottedElement.yAxe]:
                                    currYLvl = plottedElement[PlottedElement.yAxe] + drawingOffset
                        # No overlap
                        else:
                            currYLvl = y
                            biggestEndAddrSoFar = element[Element.addressEnd]
                    # Plot new element
                    image.add(image.rect((xAxeRectStart, currYLvl), size=(rectLength, 10), fill=colour, transform=scaling))
                    if endAddrBigger:
                        # Add a shape (triangle) visualising that the end address of a drawing object is bigger than given end point
                        image.add(image.path(d="M " + str(endPoint - startPoint + 6) + " " + str(currYLvl + 5) + " L " + str(endPoint - startPoint + startOfDrawingArea) + " " + str(currYLvl) + " L " + str(endPoint - startPoint + startOfDrawingArea) + " " + str(currYLvl + 10), fill=colour, transform=scaling))
                    if originalStartAddress < startPoint and rectLength > 3:
                        # Add a shape (triangle) visualising that the start address of a drawing object is smaller than given start point
                        image.add(image.path(d="M 0 " + str(currYLvl + 5) + " L" + str(xAxeRectStart + 0.1) + " " + str(currYLvl) + " L " + str(xAxeRectStart + 0.1) + " " + str(currYLvl + 10), fill=colour, transform=scaling))
                    # Add metadata to drawn element

                    # Check if the FQN fits in the rectangle (assumption: FQN is always longer than start, end address + obj/sec length)
                    if rectLength <= len(element[Element.fqn]):
                        image.add(image.text(element[Element.fqn], insert=(xAxeRectStart, currYLvl - smallSpacing), font_size=str(fontSize)+"px", writing_mode="lr", font_family="Helvetica, sans-serif", fill=fontColour, transform=scaling))
                        # Prepare plot of start and end address
                        xAxeStart = xAxeRectStart + smallSpacing            # Add spacing for start address (one px); rectangles do have no border
                        xAxeEnd = element[Element.addressEnd] - startPoint + startOfDrawingArea - smallSpacing
                        # If the rectangle smaller than 4, then write the end address outside the rectangle
                        if rectLength < fontSize * 2:
                            xAxeEnd = element[Element.addressEnd] - startPoint + startOfDrawingArea + smallSpacing
                        image.add(image.text(hex(originalStartAddress), insert=(xAxeStart, currYLvl), font_size=str(fontSize)+"px", writing_mode="tb", font_family="Helvetica, sans-serif", fill=fontColour, transform=scaling))
                        image.add(image.text(hex(element[Element.addressEnd]), insert=(xAxeEnd, currYLvl), font_size=str(fontSize)+"px", writing_mode="tb", font_family="Helvetica, sans-serif", fill=fontColour, transform=scaling))
                        additionalSpace = len(element[Element.fqn]) - rectLength            # compute how much space after the rectangle is needed to plot FQN
                        plottedElements.append((element[Element.addressEnd] + additionalSpace, currYLvl))
                        if biggestEndAddrSoFar < element[Element.addressEnd] + additionalSpace:
                            biggestEndAddrSoFar = element[Element.addressEnd] + additionalSpace
                    # FQN fits into element
                    else:
                        image.add(image.text(hex(originalStartAddress), insert=(xAxeRectStart + smallSpacing, currYLvl), font_size=str(fontSize)+"px", writing_mode="tb", font_family="Helvetica, sans-serif", fill=fontColour, transform=scaling))
                        image.add(image.text(hex(element[Element.addressEnd]), insert=(xAxeEnd - smallSpacing, currYLvl), font_size=str(fontSize) + "px", writing_mode="tb", font_family="Helvetica, sans-serif", fill=fontColour, transform=scaling))
                        image.add(image.text(element[Element.fqn], insert=(xAxeRectStart + 5, currYLvl + 2), font_size=str(fontSize)+"px", writing_mode="lr", font_family="Helvetica, sans-serif", fill=fontColour, transform=scaling))
                        plottedElements.append((element[Element.addressEnd], currYLvl))
                    # Update y level
                    if currYLvl > biggestYSoFar:
                        biggestYSoFar = currYLvl
                return biggestYSoFar

            consumerCollections = consumerCollections2GlobalList()
            reportPath = Emma.emma_libs.memoryMap.createReportPath(self.settings.outputPath, self.settings.projectName, str(hex(startPoint)) + '-' + str(hex(endPoint)), "svg")

            def getElementsToPlot(ElementName):
                elementsToPlot = []
                if memVisResolved:
                    for elementToPlot in consumerCollections[ElementName]:
                        if elementToPlot.addressLength != 0:
                            if startPoint <= elementToPlot.addressStart < endPoint:
                                elementsToPlot.append((elementToPlot.addressStart, elementToPlot.addressEnd(), elementToPlot.addressLength, elementToPlot.getFQN()))
                            elif elementToPlot.addressEnd() > startPoint and elementToPlot.addressStart < endPoint:
                                elementsToPlot.append((0, elementToPlot.addressEnd(), elementToPlot.addressLength, elementToPlot.getFQN(), elementToPlot.addressStart))
                if memVis:
                    for elementToPlot in consumerCollections[ElementName]:
                        if elementToPlot.addressLengthOriginal != 0:
                            if startPoint <= elementToPlot.addressStartOriginal < endPoint:
                                elementsToPlot.append((elementToPlot.addressStartOriginal, elementToPlot.addressEndOriginal(),
                                                       elementToPlot.addressLengthOriginal, elementToPlot.getFQN()))
                            elif elementToPlot.addressEndOriginal() > startPoint and elementToPlot.addressStartOriginal < endPoint:
                                elementsToPlot.append((0, elementToPlot.addressEndOriginal(), elementToPlot.addressLengthOriginal,
                                                       elementToPlot.getFQN(), elementToPlot.addressStartOriginal))

                return elementsToPlot

            imageHeight = 3000      # Define some height of the image
            imageWidth = endPoint - startPoint + 100
            scaling = "scale(" + xScalingValue + ", " + yScalingValue + ")"
            image = svgwrite.Drawing(reportPath, size=(imageWidth, imageHeight))
            # Plot a line defining the beginning of the chosen address area
            image.add(image.rect((3, 0), size=(0.2, imageHeight), fill="grey", opacity=0.1, transform=scaling))
            # Plot a line defining the end of the chosen address area
            image.add(image.rect((endPoint - startPoint + 3, 0), size=(0.2, imageHeight), fill="grey", opacity=0.1, transform=scaling))
            # Plot sections
            y2 = drawElements(image, getElementsToPlot("Section_Summary"), startPoint, 5, svgwrite.rgb(255, 230, 128), scaling) + 15       # Distance 15 px from the lowest section element
            # Plot objects
            imageHeight = drawElements(image, getElementsToPlot("Object_Summary"), startPoint, y2, svgwrite.rgb(198, 233, 175), scaling) + 15
            image.update({"height": str(imageHeight * float(yScalingValue)), "width": imageWidth * float(xScalingValue)})
            image.save()
            sc().info("An SVG file was stored:", os.path.abspath(reportPath))

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
            createTeamScaleReports()
            svgReport = False
            if memVis or memVisResolved:
                svgReport = True
            if svgReport and noprompt:
                sc().wwarning("No prompt is active. No SVG report will be created")
            elif svgReport and noprompt is False:
                while True:
                    print("Enter the start address of the region to be plotted (start with `0x` for hex; otherwise dec is assumed):")
                    startRegion = input("> ")
                    if startRegion.startswith("0x"):
                        try:
                            startRegion = int(startRegion, 16)
                        except ValueError:
                            sc().wwarning("The input is not a valid hex number. Please enter the start and end address again: \n")
                            continue
                    print("Enter the end address of the region to be plotted (start with `0x` for hex; otherwise dec is assumed):")
                    endRegion = input("> ")
                    if endRegion.startswith("0x"):
                        try:
                            endRegion = int(endRegion, 16)
                        except ValueError:
                            sc().wwarning("The input is not a valid hex number. Please enter the start and end address again: \n")
                            continue
                    if str(startRegion).isdigit() and str(endRegion).isdigit():
                        startRegion = int(startRegion)
                        endRegion = int(endRegion)
                        # Exit while loop and continue when everything is O.K.
                        break
                    else:
                        sc().wwarning("The input is not a valid dec number. Please enter the start and end address again: \n")
                # Define scaling value of x axe.
                print("Enter the scaling x-value. If you don't enter the valid float number, scaling value 1 will be assumed.")
                xValue = input("> ")
                try:
                    float(xValue)
                except ValueError:
                    xValue = "1"
                # Define scaling value of y axe.
                print("Enter the scaling y-value. If you don't enter the valid float number, scaling value 1 will be assumed.")
                yValue = input("> ")
                try:
                    float(yValue)
                except ValueError:
                    yValue = "1"
                createSvgReport(startRegion, endRegion, xValue, yValue)
        else:
            sc().error("The mapfiles need to be processed before creating the reports!")
