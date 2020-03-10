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


import sys
import os
import typing

from pypiscout.SCout_Logger import Logger as sc

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.shared_libs.emma_helper


class FileSelector:
    """
    Class which searches for file candidates
    """
    def __init__(self, projectDir: str):
        self.__projectDir: str = projectDir
        self.__path: str = Emma.shared_libs.emma_helper.joinPath(projectDir, OUTPUT_DIR)
        self.__versionCandidates = {}

    def getCandidates(self, filetype: str):
        index = 0
        for file in os.listdir(self.__path):
            if filetype in file:
                index += 1
                self.__versionCandidates[index] = file

        return self.__versionCandidates

    def selectFiles(self, indices: typing.List[int]) -> typing.List[str]:
        memStatsCandidates: typing.List[str] = []
        for i in indices:
            candidate = Emma.shared_libs.emma_helper.joinPath(self.__path, self.__versionCandidates[int(i)])
            memStatsCandidates.append(candidate)            
        return memStatsCandidates
