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
import timeit
import datetime
import argparse
import re

from pypiscout.SCout_Logger import Logger as sc
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


import Emma.shared_libs.emma_helper
                                                            # For version number

from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import

# TODO: support conversion of lt command via argument switch (MSc)

# Consts
TIMESTAMP = "timestamp"
START = "start"
END = "end"
ATTR = "attr"
NAME = "name"


class MapGroups:
    """
    Helper class for RegEx groups
    """
    # pylint: disable=too-few-public-methods
    # Rationale: This is a special class to be used for log file processing, it does not have to have more public methods.
    timestamp = "timestamp"
    start = "start"
    end = "end"
    attr = "attr"
    name = "name"


class MapCmdPattern:
    # pylint: disable=too-few-public-methods
    # Rationale: This is a special class to be used for log file processing, it does not have to have more public methods.
    """
    Class holding regex pattern for the map command log file
    """
    pattern = re.compile(r"""
    # one-liner for testing: ^(\[.*\])\s*\(0x([0-9a-fA-F]{8,16}),0x([0-9a-fA-F]{8,16})\)\s*Attr:\s*0x([0-9a-fA-F]{8,16}),\s*Name:\s*(.*)$
    (?:^\s*)(?P<timestamp>\[.+\])                       # Log timestamp
    (?:\s*\(0x)(?P<start>[0-9a-fA-F]{8,16})             # Start address
    (?:,0x)(?P<end>[0-9a-fA-F]{8,16})                   # End address
    (?:\)\s*Attr:\s*0x)(?P<attr>[0-9a-fA-F]{8,16})      # Attribute address
    (?:,\s*Name:\s*)?(?P<name>.+)?(?:$)                 # Name
    """, re.X)


def main(arguments):
    """
    Converts a log file (GHS run-time map output) to a parsable output for Emma
    Regarding the map command refer to the GHS devguide chapter 18.
    :return: None
    """
    #sc(invVerbosity=-1, actionWarning=(lambda: sys.exit(-10) if arguments.Werror is not None else None), actionError=lambda: sys.exit(-10))
    sc(invVerbosity=arguments.verbosity, actionError=lambda: sys.exit(-10))

    sc().header("Emma Memory and Mapfile Analyser - `map` log file converter ", symbol="/")

    # Start and display time measurement
    TIME_START = timeit.default_timer()
    sc().info("Started processing at", datetime.datetime.now().strftime("%H:%M:%S"))

    verbosity, out, mapLogFilePath = processArguments(arguments)
    convertMapLogFileFile(out, mapLogFilePath)

    # Stop and display time measurement
    TIME_END = timeit.default_timer()
    sc().info("Finished job at:", datetime.datetime.now().strftime("%H:%M:%S"), "(duration: " "{0:.2f}".format(TIME_END - TIME_START) + "s)")


def initParser():
    """
    Prepare the parser for Emma
    We need this as a separate function for the top level sub commands (argparse).
    :return: Set-up parser
    """
    parser = argparse.ArgumentParser(
        prog="Emma Memory and Mapfile Analyser (Emma)",
        description="Analyser for map files from Greens Hills Linker (other files are supported via configuration options)."
                    "It creates a summary/overview about static memory usage in form of a csv file.",
        epilog=EPILOG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--version",
        help="Display the version number.",
        action="version",
        version="%(prog)s, Version: " + Emma.EMMA_VERSION
    )
    parser.add_argument(
        "--verbosity",
        "-v",
        action='count',
        default=0,
        help="Adjust verbosity of console output. DECREASE verbosity by adding more `v`s"
    )
    parser.add_argument(
        "--map_log",
        required=True,
        help="Path to the log file to be converted",
    )
    parser.add_argument(
        "--out",
        "-o",
        help="Path to the output folder holding the converted file; if not given the input folder is used",
        default=None
    )
    # parser.add_argument(
    #     "--noprompt",
    #     help="Exit program with an error if a user prompt occurs; useful for CI systems",
    #     action="store_true",
    #     default=False
    # )
    # parser.add_argument(
    #     "--Werror",
    #     help="Treat all warnings as errors.",
    #     action="store_true",
    #     default=False
    # )
    return parser


def parseArgs(arguments=""):
    """
    Parse command line arguments
    :param arguments: Optional arguments when nothing gets parsed
    :return: Parsed arguments
    """
    parser = initParser()
    parsedArguments = Emma.shared_libs.emma_helper.parseGivenArgStrOrStdIn(arguments, parser)
    return parsedArguments


def processArguments(arguments):
    """
    Function to extract the settings values from the command line arguments.
    :param arguments: The command line arguments, that is the result of the parser.parse_args().
    :return: The setting values.
    """
    # Get paths straight (only forward slashes) or set it to empty if it was empty
    # and assign to variables
    mapLogFilePath = Emma.shared_libs.emma_helper.joinPath(arguments.map_log)
    if arguments.out is None:
        out = os.path.dirname(os.path.abspath(mapLogFilePath))
        arguments.out = mapLogFilePath
    else:
        out = Emma.shared_libs.emma_helper.joinPath(arguments.out)
    verbosity = arguments.verbosity

    # Check path/file existence
    Emma.shared_libs.emma_helper.mkDirIfNeeded(out)
    Emma.shared_libs.emma_helper.checkIfFileExists(mapLogFilePath)

    # TODO: It would be more convenient if arguments which are not modified are passed without manually modifying the code (MSc)
    return verbosity, out, mapLogFilePath


def convertMapLogFileFile(outFolder, mapLogFilePath):
    """
    Convert map run-time output to GHS map file format
    :param outFolder: Path to the output directory
    :param mapLogFilePath: Path to the input log file containing the map run-time log
    :return: None
    """
    # Load file
    with open(mapLogFilePath) as fp:
        logFileContent = fp.readlines()
    parsedEntries = parseContent(logFileContent)


    outFile = os.path.join(outFolder, os.path.splitext(os.path.basename(mapLogFilePath))[0] + "-converted.map")
    writeToFile(outFile, parsedEntries)


def writeToFile(outFile, parsedEntries):
    """
    Writes the converted data to the given output directory in the GHS map file format
    :param outFile: Path to the output file
    :param parsedEntries: [list({timestamp, start, end, attr, name}, ...)] List of entries to be written
    :return: None
    """
    def end2Size(startAddr, endAddr):
        """
        Convert size from start and end address (all in hex)
        :param startAddr: start address (hex)
        :param endAddr: end address (hex)
        :return: size (hex)
        """
        if startAddr == endAddr:
            return hex(1)
        if int(startAddr, 16) > int(endAddr, 16):
            sc().error(f"End address ({endAddr}) is bigger than start address ({startAddr})!")
        return format(int(endAddr, 16) - int(startAddr, 16), "x")

    with open(outFile, "w") as fp:
        # Write header
        fp.write(
            """// Emma - Emma Memory and Mapfile Analyser
// Copyright (C) 2019 The Emma authors
//
// Auto-generated by Emma map converter

""")
        # Write table header
        name = "Name"
        start = "Base"
        sizeHex = "Size(hex)"
        sizeDec = "Size(dec)"
        secOffs = "SecOffs"
        padding = 8

        fp.write(f"  {name:<50}{start:<20}{sizeHex:<20}{sizeDec:<20}{secOffs:<20}\n")
        # Write data
        for line in parsedEntries:
            size = end2Size(line[START], line[END])
            origin = line[START].zfill(padding)
            size = size.zfill(padding)
            secOffs = f"{0:0{padding}}"
            fp.write(f"  {line[NAME]:<50}{origin:<20}{size:<20}{int(size, 16):<20}{secOffs:<20}\n")


def parseContent(logFileContent):
    """
    Parses the log file and returns a list of entries (= dict)
    :param logFileContent: plain text log file containing the line of the debug command
    :return: list({timestamp, start, end, attr, name}, ...)
    """
    cmdStartFlag = "DEBUG> map"
    cmdBegun = False
    entries = []
    for line in logFileContent:
        line = line.strip()
        # Skip all files until the actual command was executed in the log file
        if not cmdBegun:
            if line.endswith(cmdStartFlag):
                cmdBegun = True
                continue
        # Command was found; parsing all following lines
        lineComponents = re.search(MapCmdPattern.pattern, line)
        if lineComponents:
            entries.append({
                TIMESTAMP: lineComponents.group(MapGroups.timestamp),
                START: lineComponents.group(MapGroups.start),
                END: lineComponents.group(MapGroups.end),
                ATTR: lineComponents.group(MapGroups.attr),
                NAME: lineComponents.group(MapGroups.name) if lineComponents.group(MapGroups.name) is not None else UNKNOWN_ENTRY_NAME
            })
    return entries


def runMapCmdConverter():
    """
    Runs Emma map command converter application
    :return: None
    """
    # Parsing the command line arguments
    parsedArguments = parseArgs()
    # Execute Emma
    main(parsedArguments)


if __name__ == "__main__":
    runMapCmdConverter()

