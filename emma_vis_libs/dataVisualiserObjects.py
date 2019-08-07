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

# Objects/Modules Visualiser:
#     This ModuleConsumptionList class plots and aggregates the objects/module data from the memStats directory


import os

import pandas
import matplotlib.pyplot
from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper
import emma_vis_libs.dataVisualiser


class ModuleConsumptionList(emma_vis_libs.dataVisualiser.Visualiser):
    """
    Class for module data. The module summary inherits everything from the image summary, but since the image summary
    does not have categories or the like they need to be added here.
    """

    def __init__(self, projectPath, fileToUse, resultsPath):
        super().__init__(fileToUse, resultsPath, projectPath)
        self.projectPath = projectPath
        self.project = os.path.split(projectPath)[-1]
        self.consumptionByCategorisedModules = self.calcConsumptionByCategorisedModules()

    def printCategorisedModules(self):
        print(self.consumptionByCategorisedModules)

    def plotByCategorisedModules(self, plotShow=True):
        myFigure = self.displayConsumptionByCategorisedModules(self.consumptionByCategorisedModules)
        filename = self.project + MEMORY_ESTIMATION_PARTITION_OF_ALLOCATED_MEMORY_PICTURE_NAME_FIX_PART + self.statsTimestamp.replace(" ", "") + "." + MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION
        shared_libs.emma_helper.saveMatplotlibPicture(myFigure, os.path.join(self.resultsPath, filename), MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION, MEMORY_ESTIMATION_PICTURE_DPI, False)
        if plotShow:
            matplotlib.pyplot.show()

    def calcConsumptionByCategorisedModules(self):
        """
        Calculate and group the module data by category in percent
        :return: dataframe of grouped memStats
        """
        # Resolve the containment/overlap/duplicate flags
        usedByModules = emma_vis_libs.dataVisualiser.removeDataWithFlags(self.data).reset_index()

        # Calculate memory used by modules
        usedByModules = usedByModules[[SIZE_DEC, CONFIG_ID, MEM_TYPE]]                  # Extract sizeDec, memType and configID
        usedByModules = usedByModules.groupby([CONFIG_ID, MEM_TYPE]).sum()              # Group by memType and configID, sum sizeDec
        usedByModules = usedByModules.rename(columns={SIZE_DEC: "used by modules"})     # Rename sizeDec, as it is now the sum of memory used ba modules
        usedByModules = usedByModules.reset_index()                                     # Reset index for later merge

        # Select data
        # columns = [5, 9, 7, 11]                                                       # ["sizeDec", "moduleName", "memType", "category"]
        # categorized = self.data[[self.header[i] for i in columns]]
        categorized = self.data[[SIZE_DEC, MEM_TYPE, CONFIG_ID, CATEGORY]]
        categorized = categorized.reset_index()
        categorized = categorized.drop([ADDR_START_DEC], 1)
        categorized = pandas.merge(left=categorized, right=usedByModules, on=[CONFIG_ID, MEM_TYPE], how='left')

        # Normalize data
        categorized["percentage share"] = 100.0 * categorized[SIZE_DEC] / categorized["used by modules"].astype(float)  # Calculate percent value
        categorized = categorized.groupby([CONFIG_ID, MEM_TYPE, CATEGORY]).sum()        # Group by configID, memType and category, sum module percentages
        categorized = categorized.drop([SIZE_DEC, "used by modules"], 1)                # Remove sizeDec and budget and used by modules as it's only needed for percentage calc
        categorized = categorized.groupby([CONFIG_ID, MEM_TYPE, CATEGORY]).sum()

        pandas.options.display.float_format = '{:,.2f}'.format

        return categorized

    def displayConsumptionCategorisedPie(self, consumptionPerMemory):
        title = "Categorised Memory Estimation of Modules - " + self.project + "    (Created " + self.statsTimestamp + ")"
        consumptionPerMemory = consumptionPerMemory.reset_index()
        consumptionPerMemory = consumptionPerMemory.groupby(["configID", MEM_TYPE, "category"]).sum()
        consumptionPerMemory = consumptionPerMemory.unstack().fillna(0)

        # FIXME: Fix this plot (FM)
        pieGraph = consumptionPerMemory.plot.pie(subplots=True,
                                                 figsize=(28, 4),
                                                 colormap='tab20c',
                                                 # List of colormaps: https://matplotlib.org/examples/color/colormaps_reference.html
                                                 autopct='%.2f',
                                                 fontsize=8,
                                                 legend=False,
                                                 title=title)

        return pieGraph[0].get_figure()

    def displayConsumptionByCategorisedModules(self, consumptionPerMemory):
        # Plot bar graph
        title = "Partition of allocated Memory - " + self.project + "    (Created " + self.statsTimestamp + ")"
        consumptionPerMemory = consumptionPerMemory.unstack()  # Unstack so dataframe can be plotted
        consumptionPerMemory = consumptionPerMemory.reset_index()  # Reset index so wen can set it again
        consumptionPerMemory = consumptionPerMemory.set_index(["configID", MEM_TYPE])  # Set index to plot by "configID", "memType"

        barGraph = consumptionPerMemory.plot(kind='bar',  # Enable stacked bars
                                             stacked='reverse',
                                             # FIXME: This doesn't reverse(FM) Possible workaround: barh, reverse x-Axis
                                             figsize=(18, 10),  # Adjust figure size
                                             rot=45,  # Rotate x-Axis labels
                                             colormap='tab20',
                                             # List of colormaps: https://matplotlib.org/examples/color/colormaps_reference.html
                                             title=title,  # Set title
                                             legend='reverse',  # Enable legend FIXME: This reverses neither(FM)
                                             ylim=(0, 105))  # Set limit for y-axis

        indices = consumptionPerMemory.keys().get_level_values("category")
        barGraph.legend(title=None,  # Disable title
                        labels=indices)  # Only show "category" in the legend

        matplotlib.pyplot.ylabel("Partition of allocated Memory in %")

        matplotlib.pyplot.subplots_adjust(top=0.9, bottom=0.26, left=0.06, right=0.92)  # Adjust space around our plot
        matplotlib.pyplot.gcf().canvas.set_window_title("Emma -- Visualiser - " + title)  # Set window name

        return barGraph.get_figure()

    def plotByCategorisedModulesPie(self, plotShow=True):
        myfigure = self.displayConsumptionCategorisedPie(self.consumptionByCategorisedModules)
        filename = self.project + "-Memory_Estimation_by_Category_Pie_Chart_generated_" + self.statsTimestamp.replace(
            " ", "")
        myfigure.savefig(self.resultsPath + filename + ".png", dpi=MEMORY_ESTIMATION_PICTURE_DPI, transparent=False)
        if plotShow:
            matplotlib.pyplot.show()  # Show plots after results in console output are shown

    def appendModuleConsumptionToMarkdownOverview(self, markdownFilePath):
        """
        Appends consumptionByCategorisedModules and the corresponding plot to the Markdown file
        :param markdownFilePath: The path of the Markdown file to which the data will be appended to.
        :return: nothing
        """

        sc().info("Appending module summary to overview...")

        # TODO: This should be better explained (AGK)
        self.plotByCategorisedModules(plotShow=False)  # Re-write .png to ensure up-to-date overview

        with open(markdownFilePath, 'a') as markdown:
            markdown.write("\n# Percentage share of modules\n")
            markdown.write(
                "    \n    " + self.consumptionByCategorisedModules.to_string().replace("\n", "\n    ") + "\n")
            markdown.write("\n\n*percentage share: share of the used memory*\n\n")
            markdown.write("<div align=\"center\"> <img src=\"" + os.path.join(self.project + MEMORY_ESTIMATION_BY_MODULES_PICTURE_NAME_FIX_PART + self.statsTimestamp + "." + MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION) + "\" width=\"1000\"> </div>")
            markdown.write("\n\n")
            markdown.write("<div align=\"center\"> <img src=\"" + os.path.join(self.project + MEMORY_ESTIMATION_PARTITION_OF_ALLOCATED_MEMORY_PICTURE_NAME_FIX_PART + self.statsTimestamp + "." + MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION) + "\" width=\"1000\"> </div>")
            markdown.write("\n")
