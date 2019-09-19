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

class SUBPARSER_STRINGS:
    ANALYSER: str = "a"
    VISUALISER: str = "v"
    DELTAS: str = "d"


VERSION_MAJOR = "3"
VERSION_MINOR = "1"
VERSION_PATCH = "1"
EMMA_VERSION = ".".join([VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH])
EMMA_VISUALISER_VERSION = EMMA_VERSION
EMMA_DELTAS_VERSION = EMMA_VERSION

PYTHON_REQ_VERSION = ">=3.6"
