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

# Data Reports:
#     This File contains the class for the report creation.
#     It reads ./<PROJECT_NAME>/results/<PROJECT_NAME>-Memory_Report_by_configID-memType.csv and saves the plot as a .png
#     A seperate plot is created For every configID.
#     <PROJECT_NAME>-Memory_Report_by_configID-memType.csv is created by ImageConsumptionList.writeReportToFile() in dataVisualiserSections.py


import os

import pandas
import matplotlib.pyplot

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper


class Reports:
    def __init__(self, projectPath):
        self.projectPath = projectPath
        self.project = os.path.split(projectPath)[-1]
        self.reportFilePath = shared_libs.emma_helper.joinPath(projectPath, "results", self.project + "-Memory_Report_by_configID-memType.csv")
        self.data = pandas.read_csv(self.reportFilePath, sep=";").drop_duplicates(subset=[TIMESTAMP, CONFIG_ID, MEM_TYPE])  # TODO: This is a temporary fix, we actually want to not append duplicates to the csv in the first place

    def plotNdisplay(self, plotShow=True):
        grouped = self.data.groupby([CONFIG_ID])
        for configID in grouped.indices:
            groupedByConfigID = grouped.get_group(configID).groupby([MEM_TYPE, TIMESTAMP]).sum()
            groupedByConfigID = groupedByConfigID.reset_index()

            labels = []
            fig, ax = matplotlib.pyplot.subplots()
            for key, grp in groupedByConfigID.groupby([MEM_TYPE]):
                labels.append(grp.memType.unique()[0])
                grp = grp.drop([MEM_TYPE], axis=1)
                title = "Memory Report - " + self.project + ": " + configID
                ax = grp.plot(kind="line",
                              title=title,
                              ax=ax,
                              x=TIMESTAMP,
                              y="used [%]",
                              figsize=(16, 6),
                              rot=90,
                              stacked=True)

            matplotlib.pyplot.legend(labels=labels,  # Set labels
                                     bbox_to_anchor=(0., -0.2, 1., .102),  # Location of legend
                                     loc="lower right",  # Location of legend
                                     ncol=4,  # Number of columns
                                     mode="expand",  # Span the legend across the whole figure
                                     fontsize="medium")  # Set font size

            matplotlib.pyplot.ylabel("used [%]")

            filename = self.project + "_Memory_Report_" + configID + ".png"
            matplotlib.pyplot.savefig(shared_libs.emma_helper.joinPath(self.projectPath, "results", filename), dpi=MEMORY_ESTIMATION_PICTURE_DPI, transparent=False, bbox_inches="tight")

            if plotShow:
                matplotlib.pyplot.show()  # Show plots after results in console output are shown
