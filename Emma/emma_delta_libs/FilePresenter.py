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

from pypiscout.SCout_Logger import Logger as sc

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.emma_delta_libs.FileSelector


class FilePresenter:
    """
    Class handling the user selection for the to-be compared files
    """

    __filetypes: typing.Dict[int, str] = {
        0: FILE_IDENTIFIER_SECTION_SUMMARY,
        1: FILE_IDENTIFIER_OBJECT_SUMMARY,
        2: FILE_IDENTIFIER_OBJECTS_IN_SECTIONS
    }

    def __init__(self, fileSelector: Emma.emma_delta_libs.FileSelector):
        self.__fileSelector: Emma.emma_delta_libs.FileSelector = fileSelector

    def chooseCandidates(self) -> typing.List[str]:
        """
        Select two files for the further analysis
        :return: list with chosen filenames
        """
        # TODO: Validate all inputs (FM)
        self.__printFileType()
        while True:
            selectedNumber = (input("Choose File type >\n"))
            if len(str(selectedNumber)) == 1:
                if int(selectedNumber) in self.__filetypes:                      # pylint: disable=no-else-break
                    filetype: str = self.__filetypes[int(selectedNumber)]
                    break
                else:
                    sc().warning("Select valid number.\n")
            else:
                sc().warning("Select valid number.\n")
        candidates: typing.Dict = self.__fileSelector.getCandidates(filetype)
        self.__printCandidates(candidates)

        while True:
            indices: str = input("Select two indices separated by one space >")
            indices: typing.List[str] = indices.split(" ")
            if len(indices) == 2:
                if int(indices[0]) in candidates and int(indices[1]) in candidates:      # pylint: disable=no-else-break
                    break
                else:
                    sc().warning("select two of the numbers presented above")
            else:
                sc().warning("Select exactly two files.")

        selectedFiles: typing.List[str] = self.__fileSelector.selectFiles(indices)
        self.__printSelectedFiles(selectedFiles)
        return selectedFiles

    @staticmethod
    def __printCandidates(candidates) -> None:
        for i in candidates:
            string = "    " + str(i) + ": " + candidates[i]
            print(string)

    @staticmethod
    def __printSelectedFiles( paths: typing.List[str]) -> None:
        sc().info("Selected files:")
        for path in paths:
            pathSplit: typing.List[str] = os.path.split(path)
            version: str = os.path.split(os.path.split(pathSplit[0])[0])[1]
            file: str = pathSplit[1]
            string = "    " + version + " - " + file
            print(string)

    def __printFileType(self) -> None:
        for i, file in self.__filetypes.items():
            print("    " + str(i) + ": " + file)
