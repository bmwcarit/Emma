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

import pypiscout as sc

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import emma_delta_libs.FileSelector


class FilePresenter:
    """
    Class handling the user selection for the to-be compared files
    """

    __filetypes: typing.Dict[int, str] = {
        0: FILE_IDENTIFIER_SECTION_SUMMARY,
        1: FILE_IDENTIFIER_OBJECT_SUMMARY,
        2: FILE_IDENTIFIER_OBJECTS_IN_SECTIONS
    }

    def __init__(self, fileSelector: emma_delta_libs.FileSelector):
        self.__fileSelector: emma_delta_libs.FileSelector = fileSelector

    def chooseCandidates(self) -> typing.List[str]:
        # TODO: Validate all inputs (FM)
        self.__printFileType()
        try:
            filetype: str = self.__filetypes[int(input("Choose File type >"))]
        except KeyError:
            sc.error("Select valid Summary.")
            sys.exit(-10)

        candidates: typing.List[str] = self.__fileSelector.getCandidates()
        self.__printCandidates(candidates)
        indices: str = input("Select two indices seperated by one space >")
        indices: typing.List[str] = indices.split(" ")
        indices: typing.List[int] = [int(i) for i in indices]
        if len(indices) <= 1:
            sc.error("Select more than one file.")
            sys.exit(-10)

        selectedFiles: typing.List[str] = self.__fileSelector.selectFiles(indices, filetype)
        self.__printSelectedFiles(selectedFiles)
        return selectedFiles

    def __printCandidates(self, candidates: typing.List[str]) -> None:
        print("")
        for i, candidate in enumerate(candidates):
            string = "    " + str(i) + ": " + candidate
            print(string)

    def __printSelectedFiles(self, paths: typing.List[str]) -> None:
        sc.info("Selected files:")
        for i, path in enumerate(paths):
            pathSplit: typing.List[str] = os.path.split(path)
            version: str = os.path.split(os.path.split(pathSplit[0])[0])[1]
            file: str = pathSplit[1]
            string = "    " + version + " - " + file
            print(string)

    def __printFileType(self) -> None:
        print("")
        for i, file in self.__filetypes.items():
            print("    " + str(i) + ": " + file)
