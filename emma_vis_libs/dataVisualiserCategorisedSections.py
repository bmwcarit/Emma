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

# Categorised Sections:
#     This class combines the data from the sections/image and objects/module summaries taken from the memStats folder

import os
import json

import pandas
import matplotlib.pyplot
from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper
import emma_vis_libs.dataVisualiser


class CategorisedImageConsumptionList:
    """
    This class combines module and image summary to categorise the image summary via its contained modules.
    """
    def __init__(self, resultsPath, projectPath, statsTimestamp, imageSumObj, moduleSumObj):
        # Utility attributes for filenames etc.
        self.resultsPath = resultsPath
        self.projectPath = projectPath
        self.project = os.path.split(projectPath)[-1]
        self.statsTimestamp = statsTimestamp

        # Data attributes
        self.imageSumObj = imageSumObj
        self.imageData = emma_vis_libs.dataVisualiser.removeDataWithFlags(imageSumObj.data)
        self.moduleSumObj = moduleSumObj
        self.moduleData = emma_vis_libs.dataVisualiser.removeDataWithFlags(moduleSumObj.data)

        # Attributes created from data
        self.__categorisedImage = self.__categoriseImage()
        self.__usedByModulesInImage = self.__calcUsedByModulesInImage()

    def __categoriseImage(self):
        """
        This initialiser function combines image and module summary data to determine which
        module is stored in the memory units.
        :return: A grouped dataframe containing the grouped image and modules
        """
        # Prepare image summary data
        self.imageData.reset_index()
        self.imageData = self.imageData.drop([CATEGORY, ADDR_START_HEX, ADDR_END_HEX, SIZE_HEX, ADDR_END_DEC, VAS_NAME, DMA, MAPFILE, OBJECT_NAME], 1)
        self.imageData = self.imageData.groupby([CONFIG_ID, MEM_TYPE, SECTION_NAME]).sum()
        self.imageData = self.imageData.rename(index=str, columns={SIZE_DEC: SECTION_SIZE_BYTE})
        self.imageData = self.imageData.reset_index()

        # Prepare module summary data
        self.moduleData = self.moduleData.reset_index()
        self.moduleData = self.moduleData.drop([MEM_TYPE_TAG, ADDR_START_DEC, ADDR_START_HEX, ADDR_END_HEX, SIZE_HEX, ADDR_END_DEC, VAS_NAME, DMA, MAPFILE], 1)
        self.moduleData = self.moduleData.groupby([CONFIG_ID, MEM_TYPE, SECTION_NAME, OBJECT_NAME, CATEGORY]).sum()
        self.moduleData = self.moduleData.rename(index=str, columns={SIZE_DEC: MODULE_SIZE_BYTE})
        self.moduleData = self.moduleData.reset_index()

        # Merge module and image data and save to categorisedImage
        categorisedImage = pandas.merge(left=self.imageData,
                                        right=self.moduleData,
                                        on=[CONFIG_ID, MEM_TYPE, SECTION_NAME])

        # Aggregate categorisedImage to desired form
        categorisedImage = categorisedImage.groupby([CONFIG_ID, MEM_TYPE, SECTION_NAME, SECTION_SIZE_BYTE, CATEGORY, OBJECT_NAME]).sum()

        return categorisedImage

    def __calcUsedByModulesInImage(self):
        """
        Initialiser function to calculate how much space the modules take up in the image summary
        :return: dataframe
        """
        usedByModules = self.moduleData.groupby([CONFIG_ID, MEM_TYPE, CATEGORY]).sum()
        usedByModules = usedByModules.reset_index()

        usedByImage = self.imageData.groupby([CONFIG_ID, MEM_TYPE]).sum()
        usedByImage = usedByImage.rename(index=str, columns={SECTION_SIZE_BYTE: "Used [Byte]"})
        usedByImage = usedByImage.reset_index()

        usedByModulesInImage = pandas.merge(left=usedByImage,
                                            right=usedByModules,
                                            how='right',
                                            on=[CONFIG_ID, MEM_TYPE])
        usedByModulesInImage = usedByModulesInImage.groupby([CONFIG_ID, MEM_TYPE, USED_BYTE, CATEGORY]).sum()

        return usedByModulesInImage

    def __groupCategorisedImage(self):
        """
        Function to group __categorisedImage
        :return: The grouped dataframe
        """
        groupedImage = self.__categorisedImage.reset_index()
        groupedImage = groupedImage.groupby([CONFIG_ID, MEM_TYPE, CATEGORY, SECTION_NAME, SECTION_SIZE_BYTE, OBJECT_NAME]).sum()
        return groupedImage

    # FIXME: Colours of the legend are not working (MSc)
    def displayUsedByModulesInImage(self):
        """
        Creates the figure for the plot.
        :return: matplotlib figure of the plot
        """
        usedByModulesInImage = self.__usedByModulesInImage
        usedByModulesInImage = usedByModulesInImage.reset_index().merge(right=self.imageSumObj.consumptionByMemType.reset_index().drop(['sizeDec', ], 1))
        usedByModulesInImage[MODULE_SIZE_PERCENT] = 100 * usedByModulesInImage[MODULE_SIZE_BYTE] / usedByModulesInImage[BUDGET].astype(float)
        usedByModulesInImage = usedByModulesInImage.drop([BUDGET, MODULE_SIZE_BYTE, USED_BYTE, USED_PERCENT, AVAILABLE_PERCENT], 1)
        usedByModulesInImage = usedByModulesInImage.groupby([CONFIG_ID, MEM_TYPE, CATEGORY]).sum()

        # Constants for plot
        figsize = (18, 10)
        title = "Partition of allocated Memory - " + self.project + "    (Created " + self.statsTimestamp + ")"

        # Plot right bars ("Used [Byte]")
        barGraph = self.imageSumObj.consumptionByMemType[USED_PERCENT].plot(kind='bar',  # Set bar graph
                                                                            stacked=True,  # Enable stacked bars
                                                                            figsize=figsize,  # Adjust figure size
                                                                            rot=45,  # Rotate x-Axis labels
                                                                            colormap='tab20',
                                                                            title=title)

        # Plot left bars
        usedByModulesInImage.unstack().plot(kind='bar',
                                            stacked=True,  # Enable stacked bars
                                            figsize=figsize,  # Adjust figure size
                                            rot=45,  # Rotate x-Axis labels
                                            colormap='tab20',  # List of colormaps: https://matplotlib.org/examples/color/colormaps_reference.html
                                            ax=barGraph)

        for i in range(len(self.imageSumObj.consumptionByMemType[USED_PERCENT])):
            # Show budgets annotations in kiB
            barWidth = [p.get_width() for p in barGraph.patches][0]
            annotationUsagePercentage = "{:.1f} %".format(self.imageSumObj.consumptionByMemType[USED_PERCENT][i])
            annotationUsageAbsoluteValue = shared_libs.emma_helper.toHumanReadable(int(self.imageSumObj.consumptionByMemType[SIZE_DEC][i]))
            barGraph.annotate(s=annotationUsagePercentage + "\n" + annotationUsageAbsoluteValue,
                              xy=(i-barWidth/2, self.imageSumObj.consumptionByMemType[USED_PERCENT][i] + 0.01),         # Make annotation on the left side of each bar, xy= accepts a tuple of XY location
                              color="#505359")

        # TODO : This needs to be corrected because now the legend elements have different colours from the diagram content. (AGK)
        # Configure legend
        labels = usedByModulesInImage[MODULE_SIZE_PERCENT].unstack().keys().get_level_values(0)                         # Extract indices from dataframes for legend
        barGraph.legend(title=None,     # Disable title
                        labels=labels)  # Only show "category" in the legend

        # Add y-label
        matplotlib.pyplot.ylabel("Allocated Memory in %")
        matplotlib.pyplot.subplots_adjust(top=0.9, bottom=0.26, left=0.06, right=0.92)  # Adjust space around plot

        return barGraph.get_figure()

    def printModulesInImage(self):
        """
        Print wrapper for self.__usedByModulesInImage
        :return: nothing
        """
        print(self.__usedByModulesInImage)

    def printCategorisedImage(self):
        """
        Print wrapper for self.__usedByModulesInImage
        :return: nothing
        """
        print(self.__categorisedImage)

    def appendCategorisedImageToMarkdownOverview(self, markdownFilePath):
        """
        Appends categorisedImage to the markdown file
        :param markdownFilePath: The path of the Markdown file to which the data will be appended to.
        :return: nothing
        """
        sc().info("Appending object summary to overview...")

        with open(markdownFilePath, 'a') as markdown:
            markdown.write("\n# Modules included in allocated Memory\n")
            markdown.write("    \n    " + self.__groupCategorisedImage().to_string().replace("\n", "\n    ") + "\n")
            markdown.write("\n\n")

    # FIXME: Deactivated; colours of legend in figure not correct - possibly this figure is not even needed/useful (MSc)
    # def plotNdisplay(self, plotShow=True):
    #     """
    #     function to display and save to file the figure created in self.displayUsedByModulesInImage()
    #     :param plotShow: Show plot or write to file only
    #     :return: nothing
    #     """
    #
    #     figure = self.displayUsedByModulesInImage()
    #     filename = self.project + MEMORY_ESTIMATION_BY_MODULES_PICTURE_NAME_FIX_PART + self.statsTimestamp.replace(" ", "") + "." + MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION
    #
    #     shared_libs.emma_helper.saveMatplotlibPicture(figure, shared_libs.emma_helper.joinPath(self.resultsPath, filename), MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION, MEMORY_ESTIMATION_PICTURE_DPI, False)
    #
    #     if plotShow:
    #         matplotlib.pyplot.show()  # Show plots after results in console output are shown

    def categorisedImagetoCSV(self):
        """
        Function to write the info from categorised image to file
        :return: nothing
        """
        filename = self.project + MEMORY_ESTIMATION_CATEGORISED_IMAGE_CVS_NAME_FIX_PART + self.statsTimestamp.replace(" ", "") + ".csv"
        self.__categorisedImage.to_csv(shared_libs.emma_helper.joinPath(self.resultsPath, filename), sep=";", mode="w", index=True)

    def createCategoriesSections(self):
        csvfilepath = self.resultsPath + self.project + MEMORY_ESTIMATION_CATEGORISED_IMAGE_CVS_NAME_FIX_PART + self.statsTimestamp.replace(" ", "") + ".csv"
        jsonfile = open('categoriesSections.json', 'w')

        # Read csv and group it to desired form
        categoriesCSV = pandas.read_csv(csvfilepath, index_col=6, sep=";")\
            .reset_index()\
            .drop([SECTION_SIZE_BYTE, MODULE_SIZE_BYTE], 1)\
            .groupby([CONFIG_ID, MEM_TYPE, SECTION_NAME, CATEGORY])\
            .agg({OBJECT_NAME: "count"})
        categoriesCSV.sort_values(OBJECT_NAME, ascending=False, inplace=True)
        categoriesCSV = {k: list(categoriesCSV.ix[k].index) for k in categoriesCSV.index.levels[0]}

        # Extract desired data for section -> category matching
        categoriesList = []
        for key in categoriesCSV:
            for entry in range(len(categoriesCSV[key])):
                categoriesList.append(categoriesCSV[key][entry][1:3])

        # Convert list of tuples to dict
        categoriesDict = {}
        for entry in categoriesList:
            categoriesDict[entry[0]] = entry[1]  # entry[0].strip('.') for stripping the "." before section names

        # Format from section:category to category:list_of_sections
        formatted = {}
        for k, v in categoriesDict.items():
            formatted[v] = formatted.get(v, [])
            formatted[v].append(k)

        # Sort list_of_sections case-insensitive in alphabetical order
        for k in formatted.keys():
            formatted[k].sort(key=lambda s: s.lower())

        # Merge existing sectionCategories with our newly found categories
        with open(shared_libs.emma_helper.joinPath(self.projectPath + "/categoriesSections.json"), "r") as fp:
            visteonCategories = json.load(fp)

        formatted = {**formatted, **visteonCategories}

        # Print to .json
        json.dump(formatted, jsonfile, indent=" ", sort_keys=True)
