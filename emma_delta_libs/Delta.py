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
import typing

import pandas

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper


class Delta:
    """
    Class used for the delta calculation
    """
    def __init__(self, files: typing.List[str], outfile: str):
        self.__inFilePaths: typing.List[str] = files
        self.__outFilePath: str = outfile

        self.__lhs: pandas.DataFrame = pandas.read_csv(self.__inFilePaths[0], index_col=3, sep=";")
        self.__rhs: pandas.DataFrame = pandas.read_csv(self.__inFilePaths[1], index_col=3, sep=";")
        self.__delta: pandas.DataFrame = self.__buildDelta()

    def __buildDelta(self) -> pandas.DataFrame:
        namelhs = os.path.split(self.__inFilePaths[0])[-1].replace(".csv", "").replace(FILE_IDENTIFIER_SECTION_SUMMARY, "")
        namerhs = os.path.split(self.__inFilePaths[1])[-1].replace(".csv", "").replace(FILE_IDENTIFIER_SECTION_SUMMARY, "")

        LHS_SUFFIX = "_" + namelhs
        RHS_SUFFIX = "_" + namerhs
        DELTA_SIZE_DEC = "Delta sizeDec"
        DELTA_PERCENTAGE = "Delta %"
        DELTA_HUMAN_READABLE = "Delta"

        lhs = self.__lhs.reset_index().set_index([CONFIG_ID, MEM_TYPE, TAG, MAPFILE, SECTION_NAME])
        rhs = self.__rhs.reset_index().set_index([CONFIG_ID, MEM_TYPE, TAG, MAPFILE, SECTION_NAME])
        delta = lhs.join(rhs, lsuffix=LHS_SUFFIX, rsuffix=RHS_SUFFIX)

        delta[DELTA_SIZE_DEC] = delta[SIZE_DEC + LHS_SUFFIX] - delta[SIZE_DEC + RHS_SUFFIX]
        delta[DELTA_HUMAN_READABLE] = delta[DELTA_SIZE_DEC].apply(shared_libs.emma_helper.toHumanReadable)
        delta[DELTA_PERCENTAGE] = delta[DELTA_SIZE_DEC] / delta[SIZE_DEC + LHS_SUFFIX]

        return delta

    def getDelta(self) -> pandas.DataFrame:
        return self.__delta

    def tocsv(self) -> None:
        self.__delta.to_csv(self.__outFilePath, sep=";", mode="w", index=True)

    def __str__(self):
        return self.__delta.to_string()
