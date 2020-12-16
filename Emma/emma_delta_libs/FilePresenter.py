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

    def validateNumber(self, selectedNumber):
        """
        Check if the given file type index is valid
        :param selectedNumber: Index of file type
        :return: valid(= True) or invalid (= False)
        """
        try:
            if int(selectedNumber) in self.__filetypes:
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def validateIndices(indices, candidates):
        """
        Check if the given file names indices are valid
        :param indices: List with indices of 2 file names
        :param candidates: Dictionary with file names candidates (= value) and their indices (= key)
        :return: [bool] checks successful
        """
        if not isinstance(indices, list):
            return False
        if len(indices) == 2:
            try:
                if int(indices[0]) in candidates and int(indices[1]) in candidates:
                    return True
                else:
                    return False
            except Exception:
                return False
        else:
            return False

    def chooseCandidates(self) -> typing.List[str]:
        """
        Select two files for the further analysis
        :return: List of chosen file names
        """
        self.__printFileType()

        while True:
            selectedNumber = (input("Choose File type >\n"))
            if len(str(selectedNumber)) == 1:
                if self.validateNumber(selectedNumber):                      # pylint: disable=no-else-break
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
            if self.validateIndices(indices, candidates):          # pylint: disable=no-else-break
                break
            else:
                sc().warning("Select two numbers presented above.")

        selectedFiles: typing.List[str] = self.__fileSelector.selectFiles(indices)
        self.__printSelectedFiles(selectedFiles)
        return selectedFiles

    @staticmethod
    def __printCandidates(candidates) -> None:
        for i in candidates:
            string = "    " + str(i) + ": " + candidates[i]
            print(string)

    @staticmethod
    def __printSelectedFiles(paths: typing.List[str]) -> None:
        sc().info("Selected files:")
        for path in paths:
            pathSplit: typing.List[str] = os.path.split(path)
            version: str = os.path.split(os.path.split(pathSplit[0])[0])[1]
            file: str = pathSplit[1]
            string = "    " + version + " - " + file
            sc().info(string)

    def __printFileType(self) -> None:
        for i, file in self.__filetypes.items():
            sc().info("    " + str(i) + ": " + file)
