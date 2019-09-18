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

# Data Visualiser:
#     This File containes the base class for the sections/image summary, objects/module summary.


import os
import json

import pandas
import matplotlib
import matplotlib.style

from pypiscout.SCout_Logger import Logger as sc

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.shared_libs.emma_helper


def removeDataWithFlags(sourceData, rmContained=True, rmDuplicate=True, rmOverlap=True):
    """
    This function resolves containment/overlap/duplicate flags
    :param sourceData: the memstats dataframe
    :param rmOverlap: Remove overlapping entries
    :param rmDuplicate: Remove duplicates
    :param rmContained: Remove containments
    :return: Resolved dataframe
    """
    resolvedFlagsData = pandas.DataFrame.empty

    if rmContained:
        # Remove sections with a containment flag
        resolvedFlagsData = sourceData[~sourceData[CONTAINMENT_FLAG].astype(str).str.startswith("Contained")]       # TODO: Make this prettier for example: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.isna.html (FM)
        # Now that all contained entries are deleted we can remove the 'CONTAINMENT_FLAG' column
        resolvedFlagsData = resolvedFlagsData.drop([CONTAINMENT_FLAG], axis=1)

    if rmDuplicate:
        # Remove the duplicates and delete the 'duplicateFlag' column
        resolvedFlagsData = resolvedFlagsData.drop_duplicates(subset=[ADDR_START_HEX,
                                                                      ADDR_END_HEX,
                                                                      SIZE_HEX,
                                                                      CONFIG_ID])
        resolvedFlagsData = resolvedFlagsData.drop([DUPLICATE_FLAG], axis=1)

    if rmOverlap:
        # The overlapFlag column can be removed, too. Overlaps are already resolved in emma.py
        resolvedFlagsData = resolvedFlagsData.drop([OVERLAP_FLAG], axis=1)

    return resolvedFlagsData


def getConfigIDsFromDf(dataframe):
    """
    Function to return the possible configIDs
    :param dataframe:
    :return: List of available configIDs
    """
    configIDs = dataframe.reset_index()[[CONFIG_ID]].drop_duplicates().values
    return [configID[0] for configID in configIDs]


class Visualiser:
    """
    Abstract class for reading and holding the data from memStats .csv and budget files
    """
    def __init__(self, fileToUse, resultsPath, projectPath):
        self.projectPath = projectPath
        self.project = os.path.split(projectPath)[-1]
        self.memStatsFile = fileToUse
        self.statsTimestamp = Emma.shared_libs.emma_helper.getTimestampFromFilename(fileToUse)  # This is the timestamp parsed from the module/image summary filename
        self.resultsPath = resultsPath
        self.projectThreshold = None
        # default header
        self.header = [
            # Later indexes are used (therefore the numbers commented inline)
            ADDR_START_HEX,        # 0
            ADDR_END_HEX,
            SIZE_HEX,              # 2
            ADDR_START_DEC,
            ADDR_END_DEC,
            SIZE_DEC,              # 5
            OBJECT_NAME,
            CONFIG_ID,             # 7
            VAS_NAME,
            MEM_TYPE,
            MEM_TYPE_TAG,          # 10
            CATEGORY,
            DMA,
            MAPFILE                # 13
        ]
        self.data = pandas.DataFrame(columns=self.header)
        matplotlib.style.use("ggplot")      # Pycharm might claim there is no reference 'style' in `__init__.py` (you can ignore this)(https://stackoverflow.com/a/23839976/4773274)
        self.budgets = ""
        self.budgetsFilename = Emma.shared_libs.emma_helper.joinPath(self.projectPath, "budgets.json")

        if not self.__readMemStatsFile():
            raise ValueError("No data")
        self.__readBudgets()

    def __readBudgets(self):
        """
        Reads the budgets.json file
        :return: nothing
        """
        self.budgets = None
        self.projectThreshold = None

        filepath = Emma.shared_libs.emma_helper.joinPath(self.projectPath, "budgets.json")
        try:
            with open(filepath, "r") as fp:
                budgets = json.load(fp)
        except FileNotFoundError:
            sc().error(f"The file `{os.path.abspath(filepath)}` was not found!")
        except json.JSONDecodeError:
            sc().error(f"JSON syntax error in `{os.path.abspath(filepath)}`!")

        self.budgets = budgets["Budgets"]
        self.projectThreshold = budgets["Project Threshold in %"]

    def __readMemStatsFile(self):
        """
        Reads a csv file into self.dataframe
        :return: Pandas dataframe
        """
        self.data = pandas.read_csv(self.memStatsFile, index_col=3, sep=";")     # 3 is column addrStartDec (see pos in header)
        if self.data.empty:
            return False
        else:
            return True
