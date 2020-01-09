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
        self.__versionCandidates: typing.List[str] = [f for f in os.listdir(self.__path) if os.path.isdir(Emma.shared_libs.emma_helper.joinPath(self.__path, f))]       # Store the list of files for the analysis

    def getCandidates(self) -> typing.List[str]:
        return self.__versionCandidates

    def selectFiles(self, indices: typing.List[int], filetype: str) -> typing.List[str]:
        memStatsCandidates: typing.List[str] = []
        for i in indices:
            path = Emma.shared_libs.emma_helper.joinPath(self.__path, self.__versionCandidates[i], OUTPUT_DIR)
            lastModifiedFile: str = self.__fileToUse(filetype, path)
            memStatsCandidates.append(lastModifiedFile)
        return memStatsCandidates

    def __fileToUse(self, subStringIdentifier: str, path: str) -> str:
        fileToUse = None
        lastModifiedFiles: typing.List[str] = Emma.shared_libs.emma_helper.lastModifiedFilesInDir(path, ".csv")  # Newest/youngest file is last element

        if not lastModifiedFiles:
            sc().error("No matching Files in: " + path)

        # Backwards iterate over file list (so newest file will be first)
        for i in range(len(lastModifiedFiles) - 1, -1, -1):
            # Select module/image summary .csv file
            if subStringIdentifier in lastModifiedFiles[i]:
                fileToUse = lastModifiedFiles[i]
                # Exit in first match which is the newest file as we are backwards iterating
                break

        return fileToUse
