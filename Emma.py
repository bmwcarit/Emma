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
import sys
import os

sys.path.append(os.path.abspath("Emma"))

import emma
import emma_vis
import emma_deltas
import shared_libs.emma_helper
from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import


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
        version="%(prog)s, Version: " + EMMA_VERSION
    )
    subparser = topLevelParser.add_subparsers(dest="_invoked_emma_module")       # Use `dest` to introduce a variable in order to check which sub parser was invoked
    subparser.add_parser(
        SUBPARSER_STRINGS.ANALYSER,                                         # Sub parser name which will be written in `invoked_emma_module`
        parents=[emma.initParser()],
        add_help=False,
    )
    subparser.add_parser(
        SUBPARSER_STRINGS.VISUALISER,
        parents=[emma_vis.initParser()],
        add_help=False,
    )
    subparser.add_parser(
        SUBPARSER_STRINGS.DELTAS,
        parents=[emma_deltas.initParser()],
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
    parsedArguments = shared_libs.emma_helper.parseGivenArgStrOrStdIn(arguments, parser)

    emmaModuleLUT = {
        SUBPARSER_STRINGS.ANALYSER: emma.main,
        SUBPARSER_STRINGS.VISUALISER: emma_vis.main,
        SUBPARSER_STRINGS.DELTAS: emma_deltas.main
    }

    # Dispatch emma modules
    emmaModuleLUT[parsedArguments._invoked_emma_module](parsedArguments)                    # pylint: disable=protected-access
                                                                                            # We do not have to check if the LUT entry exists since argparse does that already for us


if __name__ == "__main__":
    main()
