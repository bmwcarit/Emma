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


from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *   # pylint: disable=unused-wildcard-import,wildcard-import
import emma_libs.ghsConfiguration


def createSpecificConfiguration(compiler, **kwargs):
    """
    A factory for creating an object of one of the subclasses of the SpecificConfiguration class.
    The concrete subclass is selected based on the received compiler name.
    :param compiler: The compiler name.
    :param kwargs: The arguments that will be forwarded to the constructor during the object creation.
    :return: An object of the selected subclass of the SpecificConfiguration.
    """

    configuration = None
    if COMPILER_NAME_GHS == compiler:
        configuration = emma_libs.ghsConfiguration.GhsConfiguration(**kwargs)
    else:
        sc().error("Unexpected compiler value: " + compiler)

    return configuration
