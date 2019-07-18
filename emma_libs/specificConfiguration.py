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


import abc


class SpecificConfiguration(abc.ABC):
    @abc.abstractmethod
    def __init__(self, noPrompt):
        pass

    @abc.abstractmethod
    def readConfiguration(self, configurationPath, mapfilesPath, configId, configuration) -> None:
        pass

    @abc.abstractmethod
    def validateConfiguration(self, configId, configuration) -> bool:
        pass
