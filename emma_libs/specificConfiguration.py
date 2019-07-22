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
    """
    Abstract parent class for classes that represent the compiler specific configuration.
    """
    @abc.abstractmethod
    def __init__(self, noPrompt):
        """
        Constructor of the SpecificConfiguration class. The functionality that is required to be implemented is the
        storage of settings that are the parameters of the constructor.
        :param noPrompt: False if during the calls to the methods can contain user prompts.
                         If True, then no user prompts shall be made. It is suggested that the programs fails in case
                         they can not decide the necessary action.
        """
        pass

    @abc.abstractmethod
    def readConfiguration(self, configurationPath, mapfilesPath, configId, configuration) -> None:
        """
        This function will be called to read in and process the compiler specific parts of the configuration.
        These parts of the configuration will be used during the compiler specific mapfile processing.
        :param configurationPath: Path of the directory that contains the configuration files.
        :param mapfilesPath: Path of the directory that contains the mapfiles.
        :param configId: The configId to which the configuration belongs.
        :param configuration: The configuration dictionary to which the configuration elements need to be added.
        :return: None
        """
        pass

    @abc.abstractmethod
    def checkConfiguration(self, configId, configuration) -> bool:
        """
        This function will be called after the readconfiguration() to check whether the configuration is correct.
        The checks are fully compiler specific, there are no requirements for them. Based on the result of this function,
        the configuration may be not analysed if it was marked incorrect.
        :param configId: The configId to which the configuration belongs.
        :param configuration: The configuration that needs to be checked.
        :return: True if the configuration is correct, False otherwise.
        """
        pass
