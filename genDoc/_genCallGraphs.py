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
import argparse
import pstats
import subprocess

from pypiscout.SCout_Logger import Logger as sc
import gprof2dot                          # Not directly used, but later we do a sys-call wich needs the library. This is needed to inform the user to install the package.

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper

sys.path.append("..")


def ParseArguments():
    """
    Argument parser
    :return: argparse object containing the parsed options
    """
    parser = argparse.ArgumentParser(
        prog="Emma - Call graph generator",
        description="Script to generate call graphs that can be used in the documentation or to examine the run of Emma and the Emma Visualiser.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--graphviz_bin_folder",
        help=r"The bin subfolder of the Graphviz software. Example: c:\Program Files (x86)\Graphviz2.38\bin",
        required=False
    )
    parser.add_argument(
        "--verbose",
        help="Prints out more info during run.",
        default=False
    )
    return parser.parse_args()


EmmaRootFolderRelative = r".."
FilteredProfileSuffix = r"_filtered.profile"
EmmaExecutionString = r"..\emma.py --project ..\doc\test_project --mapfiles ..\doc\test_project\mapfiles --dir ..\doc\test_project\results"
EmmaProfileFile = README_CALL_GRAPH_AND_UML_FOLDER_NAME + r"\emma.profile"
EmmaVisualiserExecutionString = r"..\emma_vis.py --project ..\doc\test_project --dir ..\doc\test_project\results --overview --quiet"
EmmaVisualiserProfileFile = README_CALL_GRAPH_AND_UML_FOLDER_NAME + r"\emma_vis.profile"


class ProfilerFilter:
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

    def __init__(self, root_folder, list_of_filters=None):
        if os.path.isdir(root_folder):
            self.root_folder = root_folder
            self.source_file_list = []
            if None is list_of_filters:
                self.__collectSourceFiles()
            elif all(isinstance(element, str) for element in list_of_filters):
                self.source_file_list = list_of_filters
            else:
                raise ValueError("The list_of_filters needs to be a list of strings or set to None for a default filter based on the root_folder argument!")
        else:
            raise ValueError("The root_folder parameter must be a valid path to the project root folder!")

    def __collectSourceFiles(self):
        for root, directories, files in os.walk(self.root_folder):
            for file in files:
                if os.path.splitext(file)[1] == ".py":
                    self.source_file_list.append(shared_libs.emma_helper.joinPath(root, file))

    def __isThisOurCode(self, file_name):
        result = False
        for source_file in self.source_file_list:
            if -1 != file_name.find(source_file):
                result = True
                break
        return result

    def filterProfilerData(self, tree):
        # Initialization of variables
        do_not_cut_this_off = False         # Reason is that we can get a tree that is empty and in that case the variable would be uninitialized
        list_of_keys = list(tree.keys())    # This needs to be done like this because the keys() method returns an iterator not a list
        for key in list_of_keys:
            this_is_our_code = self.__isThisOurCode(key[0])
            we_have_code_below_this = False
            value = tree.get(key)
            for element in value:
                if type(element) is dict:
                    if self.filterProfilerData(element):
                        we_have_code_below_this |= True
            do_not_cut_this_off = this_is_our_code or we_have_code_below_this
            if not do_not_cut_this_off:
                del tree[key]
        return do_not_cut_this_off


def generateCallGraph(profile_file, execution_string, verbose):
    sc().info("Generating call graphs for: " + execution_string)
    sc().info("The results will be stored in: " + shared_libs.emma_helper.joinPath(os.getcwd(), README_CALL_GRAPH_AND_UML_FOLDER_NAME))

    sc().info("Analyzing the program and creating the .profile file...")
    subprocess.run("python -m cProfile -o " + profile_file + " " + execution_string)

    profiler_data = pstats.Stats(profile_file)
    profiler_data.sort_stats(pstats.SortKey.CUMULATIVE)
    if verbose:
        sc().info("The content of the profile file:")
        profiler_data.print_stats()

    sc().info("Filtering the profiler data...")
    profiler_filter = ProfilerFilter(EmmaRootFolderRelative)
    profiler_filter.filterProfilerData(profiler_data.stats)

    filtered_profile_file = os.path.splitext(profile_file)[0] + FilteredProfileSuffix
    sc().info("Storing the filtered profile file to:", filtered_profile_file)
    profiler_data.dump_stats(filtered_profile_file)

    sc().info("Creating the .dot file from the .profile file...")
    subprocess.run("gprof2dot -f pstats " + profile_file + " -o " + profile_file + ".dot")

    sc().info("Creating the .dot file from the filtered .profile file...")
    subprocess.run("gprof2dot -f pstats " + filtered_profile_file + " -o " + filtered_profile_file + ".dot")

    sc().info("Creating the .png file from the .dot file...")
    subprocess.run("dot -T" + README_PICTURE_FORMAT + " -Gdpi=" + str(DPI_DOCUMENTATION) + " " + profile_file + ".dot -o" + profile_file + "." + README_PICTURE_FORMAT)

    sc().info("Creating the .png file from the filtered .dot file...")
    subprocess.run("dot -T" + README_PICTURE_FORMAT + " -Gdpi=" + str(DPI_DOCUMENTATION) + " " + filtered_profile_file + ".dot -o" + filtered_profile_file + "." + README_PICTURE_FORMAT)

    print("")


def main(arguments):
    # Store original path variables
    path_old_value = os.environ["PATH"]
    if not("Graphviz" in os.environ["PATH"]):
        graphviz_bin_abspath = os.path.abspath(arguments.graphviz_bin_folder)
        # Add to path
        os.environ["PATH"] += (graphviz_bin_abspath + ";")

    try:
        generateCallGraph(EmmaProfileFile, EmmaExecutionString, arguments.verbose)
        generateCallGraph(EmmaVisualiserProfileFile, EmmaVisualiserExecutionString, arguments.verbose)

    except Exception as e:
        sc().error("An exception was caught:", e)

    # Get back initial path config
    os.environ["PATH"] = path_old_value


if __name__ == "__main__":
    commandLineArguments = ParseArguments()
    if not os.path.isdir(README_CALL_GRAPH_AND_UML_FOLDER_NAME):
        sc().info("The folder \"" + README_CALL_GRAPH_AND_UML_FOLDER_NAME + "\" was created because it did not exist...")
        os.makedirs(README_CALL_GRAPH_AND_UML_FOLDER_NAME)
    main(commandLineArguments)
