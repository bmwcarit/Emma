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
import subprocess

from pypiscout.SCout_Logger import Logger as sc
import gprof2dot    # pylint: disable=unused-import
                    # Rationale: Not directly used, but later we do a sys-call wich needs the library. This is needed to inform the user to install the package.

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import


LIST_OF_SOURCE_FILE_PATHS = [           # "../../*" instead of "../*" since we change the working directory within the system call
    "../../emma_libs/categorisation.py",
    "../../emma_libs/configuration.py",
    "../../emma_libs/ghsConfiguration.py",
    "../../emma_libs/ghsMapfileProcessor.py",
    "../../emma_libs/ghsMapfileRegexes.py",
    "../../emma_libs/mapfileProcessor.py",
    "../../emma_libs/mapfileProcessorFactory.py",
    "../../emma_libs/memoryEntry.py",
    "../../emma_libs/memoryManager.py",
    "../../emma_libs/memoryMap.py",
    "../../emma_libs/specificConfiguration.py",
    "../../emma_libs/specificConfigurationFactory.py",
    "../../emma_delta_libs/Delta.py",
    "../../emma_delta_libs/FilePresenter.py",
    "../../emma_delta_libs/FileSelector.py",
    "../../emma_delta_libs/RootSelector.py",
    "../../emma_vis_libs/dataReports.py",
    "../../emma_vis_libs/dataVisualiser.py",
    "../../emma_vis_libs/dataVisualiserCategorisedSections.py",
    "../../emma_vis_libs/dataVisualiserMemoryMap.py",
    "../../emma_vis_libs/dataVisualiserObjects.py",
    "../../emma_vis_libs/dataVisualiserSections.py",
    "../../shared_libs/emma_helper.py",
    "../../emma.py",
    "../../emma_deltas.py",
    "../../emma_vis.py"
]


def main():
    sc().info("Generating UML Class diagrams from the source files...")
    for sourceFilePath in LIST_OF_SOURCE_FILE_PATHS:
        sourceFileName = os.path.splitext(os.path.basename(sourceFilePath))[0]
        subprocess.run("pyreverse -AS -o " + README_PICTURE_FORMAT + " " + sourceFilePath + " -p " + sourceFileName, cwd=README_CALL_GRAPH_AND_UML_FOLDER_NAME, shell=True)
        # Note that pyreverse MUST be called via subprocess (do NOT import it as a module)
        # The main reason are licencing issues (GPLv2 is incompatible with GPLv3) (https://softwareengineering.stackexchange.com/questions/110380/call-gpl-software-from-non-gpl-software)
        # See also: https://github.com/TeamFlowerPower/kb/wiki/callGraphsUMLdiagrams
