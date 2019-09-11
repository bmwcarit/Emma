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

from pypiscout.SCout_Logger import Logger as sc

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper


def selectRoot() -> str:
    """
    Propmpts the user for the root path of the project for the delta analysis
    :return: project root path
    """
    deltaConfigPath: str = shared_libs.emma_helper.joinPath("./", DELTA_CONFIG)
    if os.path.isfile(deltaConfigPath):
        rootpath = shared_libs.emma_helper.readJson(deltaConfigPath)[DELTA_LATEST_PATH]
        sc().info("Using " + rootpath + " as project.")
    else:
        rootpath = input("Enter project root path >")

    shared_libs.emma_helper.checkIfFolderExists(rootpath)
    return rootpath


def saveNewRootpath(rootpath: str) -> None:
    """
    Adds the path to the .deltaconfig file for future use
    :param rootpath: path to add
    """
    shared_libs.emma_helper.writeJson(shared_libs.emma_helper.joinPath("./", DELTA_CONFIG), {DELTA_LATEST_PATH: rootpath})
