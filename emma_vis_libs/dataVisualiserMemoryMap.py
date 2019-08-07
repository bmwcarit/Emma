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

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import emma_vis_libs.dataVisualiser
import shared_libs.emma_helper


class MemoryMap(emma_vis_libs.dataVisualiser.Visualiser):
    def __init__(self, projectPath, fileToUse, resultsPath):
        super().__init__(fileToUse, resultsPath, projectPath)
        self.projectPath = projectPath
        self.project = os.path.split(projectPath)[-1]

    def plotPieChart(self, plotShow=True):
        data = emma_vis_libs.dataVisualiser.removeDataWithFlags(sourceData=self.data, rmContained=True, rmDuplicate=True)

        # Calculate memory used by category
        byCategory = data[[SIZE_DEC, CONFIG_ID, MEM_TYPE, CATEGORY]]
        byCategory = byCategory.rename(columns={SIZE_DEC: SIZE_DEC_BY_CATEGORY})
        byCategory = byCategory.groupby([CONFIG_ID, MEM_TYPE, CATEGORY]).sum()
        byCategory = byCategory.reset_index()

        totalUsed = data[[SIZE_DEC, CONFIG_ID, MEM_TYPE]]
        totalUsed = totalUsed.groupby([CONFIG_ID, MEM_TYPE]).sum()
        totalUsed = totalUsed.reset_index()

        categoryByPercentage = pandas.merge(left=byCategory, right=totalUsed, on=[CONFIG_ID, MEM_TYPE], how='left')
        categoryByPercentage[PERCENTAGE] = 100 * categoryByPercentage[SIZE_DEC_BY_CATEGORY].astype(float).fillna(0.0) / categoryByPercentage[SIZE_DEC].astype(float).fillna(0.0)
        categoryByPercentage = categoryByPercentage.drop([SIZE_DEC, SIZE_DEC_BY_CATEGORY], 1)

        configIDs = emma_vis_libs.dataVisualiser.getConfigIDsFromDf(categoryByPercentage)
        grouped = categoryByPercentage.groupby([CONFIG_ID])
        for configID in configIDs:
            groupedByConfigID = grouped.get_group(configID).groupby([MEM_TYPE, CATEGORY]).sum()
            groupedByConfigID = groupedByConfigID.reset_index()

            memTypes = groupedByConfigID[MEM_TYPE].drop_duplicates().values
            for memType in memTypes:
                title = self.project + " - " + configID + " - " + memType + "   (Created " + self.statsTimestamp + ")"

                byMemType = groupedByConfigID.loc[groupedByConfigID[MEM_TYPE] == memType].drop([MEM_TYPE], 1)
                pieChart = byMemType.set_index(CATEGORY).plot.pie(y=PERCENTAGE, x=CATEGORY, title=title)

                filename = self.project + "_" + configID + "_" + memType + "_" + self.statsTimestamp + ".png"
                matplotlib.pyplot.savefig(shared_libs.emma_helper.joinPath(self.resultsPath, filename), dpi=MEMORY_ESTIMATION_PICTURE_DPI, transparent=False, bbox_inches="tight")
            if plotShow:
                matplotlib.pyplot.show()
        return
