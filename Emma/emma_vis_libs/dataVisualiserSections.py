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

# Sections/Image Visualiser:
#     This ImageConsumptionList class plots and aggregates the section/image data from the memStats directory

import os

import pandas
import matplotlib.pyplot
from pypiscout.SCout_Logger import Logger as sc

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.shared_libs.emma_helper
import Emma.emma_vis_libs.dataVisualiser


class ImageConsumptionList(Emma.emma_vis_libs.dataVisualiser.Visualiser):
    """
    Class holding the image data from .csv Memstats, plus methods for printing/plotting,
    file writing and .md/.html creation
    """
    def __init__(self, projectPath, fileToUse, resultsPath):
        super().__init__(fileToUse, resultsPath, projectPath)
        self.projectPath = projectPath
        self.project = os.path.split(projectPath)[-1]
        self.consumptionByMemType = self.calcConsumptionByMemType()
        self.consumptionByMemTypeDetailed = self.calcConsumptionByMemTypeDetailed()
        self.consumptionByMemTypePerMap = self.calcConsumptionByMemTypePerMap()

    def __appendStatsConsumption(self, groupedAccIndexedPrint, filename):
        # self.resultsPath is not used here because the reports should appear in the top level results folder
        path = Emma.shared_libs.emma_helper.joinPath(self.projectPath, "results")
        Emma.shared_libs.emma_helper.mkDirIfNeeded(path)

        # Prepare data for export (reset index and add timestamp)
        saved = groupedAccIndexedPrint.reset_index()
        saved.insert(0, "timestamp", self.statsTimestamp)

        filePath = Emma.shared_libs.emma_helper.joinPath(path, filename + ".csv")
        headersNeeded = not os.path.isfile(filePath)
        saved.to_csv(filePath,
                     sep=";",
                     columns=["timestamp", CONFIG_ID, MEM_TYPE, USED_PERCENT],  # The columns which will be written into the reports
                     mode="a+",
                     index=False,
                     header=headersNeeded,
                     float_format="%.3f")

    def groupDataByMemType(self, indices):
        """
        Group and aggregate (sum) data per **configID > memType**
        :param indices: list of int's defining on what data to group (see headers)
        :return: pandas DataFrame (sizeDec grouped by: configID > memType)
        """

        # Resolve the containment/overlap/duplicate flags
        groupedByMemType = Emma.emma_vis_libs.dataVisualiser.removeDataWithFlags(self.data)

        # "Select" data that we really use
        groupedByMemType = groupedByMemType[[SIZE_DEC] + [self.header[i] for i in indices]]          # Get only columns we need

        # Grouping
        groupedByMemType = groupedByMemType.groupby([self.header[i] for i in indices]).sum()     # magic numbers: see in header (Visualiser)
        groupedByMemTypeAcc = groupedByMemType.groupby([CONFIG_ID, MEM_TYPE]).sum()

        # Set formats and cast type
        pandas.options.display.float_format = '{:14,.0f}'.format
        groupedByMemTypeAcc[SIZE_DEC] = groupedByMemTypeAcc[SIZE_DEC].astype(float)

        return groupedByMemTypeAcc

    def groupDataByMemTypeDetailed(self, indices):
        """
        Group and aggregate (sum) data per **configID > tag**
        :param indices: list of int's defining on what data to group (see headers)
        :return: pandas DataFrame (sizeDec grouped by: configID > tag)
        """

        # Resolve the containment/overlap/duplicate flags
        groupedByMemType = Emma.emma_vis_libs.dataVisualiser.removeDataWithFlags(self.data)

        # "Select" data that we really use
        groupedByMemType = groupedByMemType[[SIZE_DEC] + [self.header[i] for i in indices]]          # Get only columns we need

        # Grouping
        groupedByMemTypeAcc = groupedByMemType.groupby([CONFIG_ID, MEM_TYPE_TAG]).sum()

        # Set formats and cast type
        pandas.options.display.float_format = '{:14,.0f}'.format
        groupedByMemTypeAcc[SIZE_DEC] = groupedByMemTypeAcc[SIZE_DEC].astype(float)
        return groupedByMemTypeAcc

    def groupDataByMemTypePerMap(self, indices):
        """
        Group and aggregate (sum) data per **configID > mapfile > memType**
        :param indices: list of int's defining on what data to group (see headers)
        :return: pandas DataFrame (sizeDec grouped by: configID > mapfile > memType)
        """
        # "Select" data that we really use
        groupedByMemType = self.data[[self.header[i] for i in indices]]          # Get only columns we need

        # Grouping
        groupedByMemTypeAcc = groupedByMemType.groupby([self.header[7], self.header[13], self.header[9]]).sum().astype(float)     # Order matters!!

        # Set formats and cast type
        pandas.options.display.float_format = '{:14,.0f}'.format
        return groupedByMemTypeAcc

    def calcConsumptionByMemType(self):
        """
        Calculate and aggregate grouped data from `groupDataByMemType()`
        :return:
        """
        # Get condensed report from csv
        groupedByMemTypeAcc = self.groupDataByMemType([7, 9, 10, 13])

        # Prepare budgets
        budgetsData = pandas.DataFrame(self.budgets, columns=[self.header[7], self.header[9], BUDGET])                      # magic numbers: see in header (Visualiser)
        budgetsData[BUDGET] = budgetsData[BUDGET].astype(float)

        # Merge and group by configID & memType
        groupedByMemTypeAcc = groupedByMemTypeAcc.reset_index()                                                             # We need to reset the index first for merging
        groupedByMemTypeAcc = pandas.merge(groupedByMemTypeAcc, budgetsData, on=[self.header[7], self.header[9]])           # Some bars might not be shown in the graph if you forget to adapt the `configID`s in `budgets.json`
        groupedByMemTypeAcc = groupedByMemTypeAcc.groupby([self.header[7], self.header[9]]).sum()

        # Normalise and calculate percent (used/available)
        groupedByMemTypeAcc[USED_PERCENT] = groupedByMemTypeAcc[self.header[5]] / groupedByMemTypeAcc[BUDGET] * 100
        groupedByMemTypeAcc[AVAILABLE_PERCENT] = (100 - groupedByMemTypeAcc[USED_PERCENT])                                  # Check for negative value in next line

        # Cap percentage -> if negative it has to be set to 0%
        groupedByMemTypeAcc.loc[groupedByMemTypeAcc[AVAILABLE_PERCENT] < 0, AVAILABLE_PERCENT] = 0

        return groupedByMemTypeAcc

    def calcConsumptionByMemTypeDetailed(self):
        """
        Calculates grouped data from `groupDataByMemTypeDetailed()`
        :return: nothing
        """
        # Get condensed report from csv
        groupedByMemTypeAcc = self.groupDataByMemTypeDetailed([7, 10, 13])

        # Merge and group with budgets
        groupedByMemTypeAcc = groupedByMemTypeAcc.reset_index()         # We need to reset the index first for merging
        groupedByMemTypeAcc = groupedByMemTypeAcc.groupby([self.header[7], self.header[10]]).sum()

        return groupedByMemTypeAcc

    def calcConsumptionByMemTypePerMap(self):
        """
        Calculates grouped data from `groupDataByMemTypePerMap()`
        :return: the dataframe
        """
        # Get condensed report from csv
        groupedByMemTypeAcc = self.groupDataByMemTypePerMap([5, 9, 7, 10, 13])

        return groupedByMemTypeAcc

    def displayConsumptionByMemType(self):
        """
        `plt.show()` must invoked at the end manually if figure should be displayed on screen
        You might want to call `.savefig("filename", <options>...)` from the returning object to save the figure as a file
        :return: the figure (=figure object)
        """

        # Plot bar graph
        title = "Memory Estimation - " + self.project + "    (Created " + self.statsTimestamp + ")"

        barGraph = self.consumptionByMemType[[USED_PERCENT, AVAILABLE_PERCENT]].plot.bar(stacked=True,
                                                                                               figsize=(18, 10),
                                                                                               rot=45,
                                                                                               title=title,
                                                                                               color=["#2D9CDB", "#bbbbbb"])
        matplotlib.pyplot.subplots_adjust(top=0.9, bottom=0.26, left=0.06, right=0.92)    # Adjust space around our plot
        matplotlib.pyplot.gcf().canvas.set_window_title("Emma -- Visualiser - " + title)
        matplotlib.pyplot.ylabel("Allocated Memory in %")

        # Show Values over bars in graph
        for i, bar in enumerate(barGraph.patches):
            if i >= len(barGraph.patches) / 2:
                # Show budgets annotations in kiB
                barGraph.annotate(
                    s=Emma.shared_libs.emma_helper.toHumanReadable(int(self.consumptionByMemType[BUDGET][i % (len(barGraph.patches) / 2)])),  # Format of budget text
                    xy=(bar.get_x(), 100),                                                                         # Location of budget annotation, set to 100 so the annotation appears at the 100% line
                    color="#505359")
            else:
                # Show percentage and absolute value
                annotationUsagePercentage = "{:.1f} %".format(bar.get_height())
                annotationUsageAbsoluteValue = Emma.shared_libs.emma_helper.toHumanReadable(int(self.consumptionByMemType[self.header[5]][i]))
                barGraph.annotate(
                    s=annotationUsagePercentage + "\n" + annotationUsageAbsoluteValue,
                    xy=(bar.get_x(), bar.get_height() + 0.01),
                    color="#505359")

        # Make a project threshold line
        barGraph.axhline(y=self.projectThreshold,
                         linewidth=1,
                         color="#df1f1f",
                         linestyle="dotted"
                         )

        barGraph.annotate("Project Threshold",
                          xy=(0, 0),                                                # Annotation does not work without this argument
                          xytext=(barGraph.get_xlim()[1] - 0.065, self.projectThreshold + 0.75),
                          color="#505359",
                          fontsize=8)

        return barGraph.get_figure()

    def writeReportToFile(self):
        """
        Write each report to file
        """
        title = self.project + "-Memory_Report_by_configID-memType"
        self.__appendStatsConsumption(self.consumptionByMemType, title)

    def printStats(self):
        """
        Print all three consumption lists
        """
        print(self.consumptionByMemType)
        print(self.consumptionByMemTypeDetailed)
        print(self.consumptionByMemTypePerMap)

    def plotByMemType(self, plotShow=True):
        """
        function to display and save to file the figure created in self.displayConsumptionByMemType()
        :param plotShow: Show plot or write to file only
        :return: nothing
        """

        myfigure = self.displayConsumptionByMemType()
        filename = self.project + MEMORY_ESTIMATION_BY_PERCENTAGES_PICTURE_NAME_FIX_PART + self.statsTimestamp.replace(" ", "") + "." + MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION
        Emma.shared_libs.emma_helper.saveMatplotlibPicture(myfigure, os.path.join(self.resultsPath, filename), MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION, MEMORY_ESTIMATION_PICTURE_DPI, False)
        if plotShow:
            matplotlib.pyplot.show()              # Show plots after results in console output are shown

    def createMarkdownOverview(self):
        """
        Creates the [PROJECT] overview md
        """

        self.plotByMemType(plotShow=False)  # Re-write .png to ensure up-to-date overview
        markdownFilePath = Emma.shared_libs.emma_helper.joinPath(self.resultsPath, self.project + "-Memory_Overview_" + self.statsTimestamp.replace(" ", "") + ".md")

        try:
            with open(markdownFilePath, 'w') as markdown:
                markdown.write("Memory Estimation Overview - " + self.project + "\n==========================\n\n")

                markdown.write("<div align=\"center\"> <img src=\"" +Emma.shared_libs.emma_helper.joinPath(self.project + MEMORY_ESTIMATION_BY_PERCENTAGES_PICTURE_NAME_FIX_PART + self.statsTimestamp + "." + MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION) + "\" width=\"1000\"> </div>")

                markdown.write("\n")

                markdown.write("\n# Usage by Memory Type\n")
                markdown.write("    \n    " + self.consumptionByMemType.to_string().replace("\n", "\n    ") + "\n")
                markdown.write("\n\n*" + SIZE_DEC + ": Used Memory in Byte* | *" + BUDGET + ": Total Memory Size* | *" + USED_PERCENT + ": Used Memory in %* | *" + AVAILABLE_PERCENT + ": Available Memory in %*\n\n")

                markdown.write("\n# Usage by Mapfile\n")
                markdown.write("    \n    " + self.consumptionByMemTypePerMap.to_string().replace("\n", "\n    ") + "\n")
                markdown.write("\n\n*" + SIZE_DEC + ": Used Memory in Byte*\n\n")
        except FileNotFoundError:
            sc().error(f"The file `{os.path.abspath(markdownFilePath)}` was not found!")

        return markdownFilePath

    def appendSupplementToMarkdownOverview(self, markdownFilePath):
        """
        Append .md files from supplements folder (searches all files recursively within the supplement folder)
        :param markdownFilePath: The path of the Markdown file to which the data will be appended to
        :return: nothing
        """
        supplementDirPath =Emma.shared_libs.emma_helper.joinPath(self.projectPath, SUPPLEMENT)
        supplementFiles = []

        with open(markdownFilePath, 'a') as markdown:
            if os.path.isdir(supplementDirPath):
                for supplementRootPath, directories, filesInSupplementDir in os.walk(supplementDirPath):
                    for aSupplementFile in filesInSupplementDir:
                        aAbsSupplementFilePath =Emma.shared_libs.emma_helper.joinPath(supplementRootPath, aSupplementFile)
                        supplementFiles.append(aAbsSupplementFilePath)
            else:
                sc().error(f"Supplement path (`{supplementDirPath}`) is not a directory!")
            for supplementFile in supplementFiles:
                try:
                    with open(supplementFile, "r") as supplement:
                        markdown.write(supplement.read())
                except FileNotFoundError:                                                               # This case should hardly appear since the files were found milliseconds before
                    sc().error(f"The file `{os.path.abspath(supplementFile)}` was not found!")
