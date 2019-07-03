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
import sys
import subprocess
import datetime

import pypiscout as sc


def main():
    """
    Script to create code coverage reports for the unit tests of Emma.

    Output folder of the report (relative):
        reports/<TIMESTAMP>

    In this folder the "source" sub-folder contains the .coverage file from which the .html report can be generated.

    If the report folder (or its sub-folder) exists then script will break with an error, in order not to overwrite the previous report.
    """

    sc.header("Generating Unit Test Coverage Report")

    # Setting up the variables (folder and file names...etc.)
    reports_folder = os.path.join(sys.path[0], "reports")
    unit_test_folder = os.path.join(sys.path[0], "..", "..", "unit_tests")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Ms%S")
    actual_report_folder = os.path.join(reports_folder, timestamp)
    actual_report_source_folder = os.path.join(reports_folder, timestamp, "source")
    source_file_name = ".coverage"

    # Checking whether the output folders exist
    if not os.path.isdir(actual_report_folder):
        os.mkdir(actual_report_folder)
        if not os.path.isdir(actual_report_source_folder):
            os.mkdir(actual_report_source_folder)
        else:
            sc.error("Error! The folder " + actual_report_source_folder + " already exists!")
            sys.exit(-10)
    else:
        sc.error("Error! The folder " + actual_report_folder + " already exists!")
        sys.exit(-10)

    # Switching to the unit tests folder and running the tests
    os.chdir(unit_test_folder)
    sc.info("Running the unit tests...")
    subprocess.run(["coverage", "run", "-m", "unittest", "discover", "-v"])

    # Moving the .coverage file to the source folder of the report and switching to that folder
    os.rename(os.path.join(unit_test_folder, source_file_name), os.path.join(actual_report_source_folder, source_file_name))
    os.chdir(actual_report_source_folder)

    sc.info("Creating the .html report...")
    subprocess.run(["coverage", "html", str("--directory=" + actual_report_folder)])


if __name__ == '__main__':
    main()
