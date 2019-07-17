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

import emma_libs.ghsConfiguration


def createSpecificConfiguration(compiler, *args):
    configuration = None
    if "GreenHills" == compiler:
        configuration = emma_libs.ghsConfiguration.GhsConfiguration(*args)
    else:
        sc().error("Unexpected compiler value: " + compiler)

    return configuration
