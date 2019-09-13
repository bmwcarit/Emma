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
import pstats
import subprocess

from pypiscout.SCout_Logger import Logger as sc
import gprof2dot    # pylint: disable=unused-import
                    # Rationale: Not directly used, but later we do a sys-call wich needs the library. This is needed to inform the user to install the package.

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import Emma.shared_libs.emma_helper

sys.path.append("..")


EMMA_ROOT_FOLDER_RELATIVE = r"."
FILTERED_PROFILE_SUFFIX = r"_filtered.profile"
EMMA_EXECUTION_STRING = r"-m Emma.emma --project doc/test_project --mapfiles doc/test_project/mapfiles --dir doc/test_project/results"
EMMA_PROFILE_FILE_PATH = README_CALL_GRAPH_AND_UML_PATH + r"/emma.profile"
EMMA_VIS_EXECUTION_STRING = r"-m Emma.emma_vis --projectDir doc/test_project --inOutDir doc/test_project/results --overview --quiet"
EMMA_VIS_PROFILE_FILE_PATH = README_CALL_GRAPH_AND_UML_PATH + r"/emma_vis.profile"


class ProfilerFilter:   # pylint: disable=too-few-public-methods
                        # Rationale: There is no other functionality that shall be realized by this class. There is no need for more public methods.

    """
    This is a filtering class for the profiler data of the Lib/pstats.py library. The typical use case is when a after
    profiling a python code (with the Lib/profile.py library) the output data contains a lot of calls from our code to
    external libraries that will appear in the generated call graph leading to a huge and complex graph.
    If we are only interested in displaying the calls between specific source files, or typically source files found in
    our project´s root folder and its subfolder, we can filter the output data of the profiler with this class.

    After profiler_data was read with pstats.Stats(profile_file) the received variable has the following structure:
        .
        .
        .
        + stats:
            + callee_1
                + caller_1
                + caller_2
                .
                .
                .
                + caller_n
            + callee_2
            .
            .
            .
            + callee_n
        .
        .
        .

    The filterProfilerData method of this class can be used to filter these data structure.
    For detailed description, see the method´s docstring.

    Usage:
        1 - Read in a profiler file (created with the Lib/profile.py library) with pstats.Stats(profile_file)
        2 - Construct an object of this class
        3 - Call the filterProfilerData with the profiler data
    """

    def __init__(self, rootFolder, listOfFilters=None):
        if os.path.isdir(rootFolder):
            self.rootFolder = rootFolder
            self.sourceFileList = []
            if None is listOfFilters:
                self.__collectSourceFiles()
            elif all(isinstance(element, str) for element in listOfFilters):
                self.sourceFileList = listOfFilters
            else:
                raise ValueError("The list_of_filters needs to be a list of strings or set to None for a default filter based on the root_folder argument!")
        else:
            raise ValueError("The root_folder parameter must be a valid path to the project root folder!")

    def __collectSourceFiles(self):
        for root, _, files in os.walk(self.rootFolder):
            for file in files:
                if os.path.splitext(file)[1] == ".py":
                    self.sourceFileList.append(Emma.shared_libs.emma_helper.joinPath(root, file))

    def __isThisOurCode(self, fileName):
        result = False
        for sourceFile in self.sourceFileList:
            if -1 != fileName.find(sourceFile):
                result = True
                break
        return result

    def filterProfilerData(self, tree):
        """
        Function to filter the profile data so that it contains only code that is ours or it is called by our code.
        This function is recursive it´s return value does not have any meaning for the caller.
        :param tree: Profile tree that needs to be filtered.
        :return: True if this element shall not be cut off, False otherwise.
        """
        doNotCutThisOff = False         # Reason is that we can get a tree that is empty and in that case the variable would be uninitialized
        listOfKeys = list(tree.keys())  # This needs to be done like this because the keys() method returns an iterator not a list

        for key in listOfKeys:
            thisIsOurCode = self.__isThisOurCode(key[0])
            weHaveCodeBelowThis = False
            value = tree.get(key)
            for element in value:
                if isinstance(element, dict):
                    if self.filterProfilerData(element):
                        weHaveCodeBelowThis |= True
            doNotCutThisOff = thisIsOurCode or weHaveCodeBelowThis
            if not doNotCutThisOff:
                del tree[key]

        return doNotCutThisOff


def generateCallGraph(profileFile, executionString, verbose):
    """
    Function to generate callgraphs for an executable.
    :param profileFile: This is the path where the profile file will be stored.
    :param executionString: This is the string that will be given to subprocess.run to be executed.
    :param verbose: If True, then more info will be printed during execution.
    :return: None
    """

    sc().info("Generating call graphs for: " + executionString)
    sc().info("The results will be stored in: " + os.path.abspath(README_CALL_GRAPH_AND_UML_PATH))

    sc().info("Analysing the program and creating the .profile file...\n")
    subprocess.run("python -m cProfile -o " + profileFile + " " + executionString, shell=True)#, cwd=os.path.join(os.path.dirname(__file__), "../Emma"))

    profilerData = pstats.Stats(profileFile)
    profilerData.sort_stats(pstats.SortKey.CUMULATIVE)
    if verbose:
        sc().info("The content of the profile file:")
        profilerData.print_stats()

    sc().info("Filtering the profiler data...")
    profilerFilter = ProfilerFilter(os.path.abspath(EMMA_ROOT_FOLDER_RELATIVE))
    profilerFilter.filterProfilerData(profilerData.stats)

    filteredProfileFile = os.path.splitext(profileFile)[0] + FILTERED_PROFILE_SUFFIX
    sc().info("Storing the filtered profile file to:", os.path.abspath(filteredProfileFile))
    profilerData.dump_stats(filteredProfileFile)

    sc().info("Creating the .dot file from the .profile file...")
    subprocess.run("gprof2dot -f pstats " + profileFile + " -o " + profileFile + ".dot", shell=True)

    sc().info("Creating the .dot file from the filtered .profile file...")
    subprocess.run("gprof2dot -f pstats " + filteredProfileFile + " -o " + filteredProfileFile + ".dot", shell=True)

    sc().info("Creating the .png file from the .dot file...")
    subprocess.run("dot -T" + README_PICTURE_FORMAT + " -Gdpi=" + str(DPI_DOCUMENTATION) + " " + profileFile + ".dot -o" + profileFile + "." + README_PICTURE_FORMAT, shell=True)

    sc().info("Creating the .png file from the filtered .dot file...")
    subprocess.run("dot -T" + README_PICTURE_FORMAT + " -Gdpi=" + str(DPI_DOCUMENTATION) + " " + filteredProfileFile + ".dot -o" + filteredProfileFile + "." + README_PICTURE_FORMAT, shell=True)

    print("")


def main(arguments):
    """
    Main function of the script.
    :param arguments: Dictionary that contains the arguments that influence the execution.
                      Currently avalaible arguments:
                        - verbose : Extra info will be printed during execution.
    :return: None
    """
    # Store original path variables
    pathOldValue = os.environ["PATH"]
    if "Graphviz" not in os.environ["PATH"]:
        graphvizBinAbspath = os.path.abspath(arguments.graphviz_bin_folder)
        # Add to path
        os.environ["PATH"] += (graphvizBinAbspath + ";")

    try:
        os.chdir("..")              # Only do this here (not within generateCallGraph() in order to avoid race conditions)
        generateCallGraph(EMMA_PROFILE_FILE_PATH, EMMA_EXECUTION_STRING, arguments.verbose)
        generateCallGraph(EMMA_VIS_PROFILE_FILE_PATH, EMMA_VIS_EXECUTION_STRING, arguments.verbose)

    except Exception as exception:  # pylint: disable=broad-except
                                    # Rationale: We are not trying to catch a specific exception type here.
                                    # The purpose of this is, that the PATH environment variable will be set back in case of an error.
        sc().error("An exception was caught:", exception)

    # Get back initial path config
    os.environ["PATH"] = pathOldValue
