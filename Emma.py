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

import argparse

import Emma
import Emma.emma
import Emma.emma_vis
import Emma.emma_deltas
import Emma.shared_libs.emma_helper
from Emma.shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import


def initParser():
    """
    Prepare the parser for Emma
    We need this as a separate function for the top level sub commands (argparse).
    :return: Set-up parser
    """
    topLevelParser = argparse.ArgumentParser(
            prog="Emma Memory and Mapfile Analyser (Emma)",
            description=DESCRIPTION_EMMA,
            epilog=EPILOG,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    topLevelParser.add_argument(
        "--version",
        help="Display the version number.",
        action="version",
        version="%(prog)s, Version: " + Emma.EMMA_VERSION
    )
    subparser = topLevelParser.add_subparsers(dest="_invoked_emma_module")       # Use `dest` to introduce a variable in order to check which sub parser was invoked
    subparser.add_parser(
        Emma.SUBPARSER_STRINGS.ANALYSER,                                         # Sub parser name which will be written in `invoked_emma_module`
        parents=[Emma.emma.initParser()],
        add_help=False,
    )
    subparser.add_parser(
        Emma.SUBPARSER_STRINGS.VISUALISER,
        parents=[Emma.emma_vis.initParser()],
        add_help=False,
    )
    subparser.add_parser(
        Emma.SUBPARSER_STRINGS.DELTAS,
        parents=[Emma.emma_deltas.initParser()],
        add_help=False,
    )
    return topLevelParser


def main(arguments=""):
    """
    Top level Emma script calling all Emma sub-scripts
    :param arguments: Pass arguments manually (may be used for testing)
    :return: None
    """
    parser = initParser()
    parsedArguments = Emma.shared_libs.emma_helper.parseGivenArgStrOrStdIn(arguments, parser)

    emmaModuleLUT = {
        Emma.SUBPARSER_STRINGS.ANALYSER: Emma.emma.main,
        Emma.SUBPARSER_STRINGS.VISUALISER: Emma.emma_vis.main,
        Emma.SUBPARSER_STRINGS.DELTAS: Emma.emma_deltas.main
    }

    # Dispatch emma modules
    emmaModuleLUT[parsedArguments._invoked_emma_module](parsedArguments)                    # pylint: disable=W0212
                                                                                            # We do not have to check if the LUT entry exists since argparse does that already for us


if __name__ == "__main__":
    main()
