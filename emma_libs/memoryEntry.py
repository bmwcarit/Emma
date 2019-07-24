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
import collections

from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper


class MemEntry:
    """
    A class representing an entry that is stored in the memory.
    """
    def __eq__(self, other):
        """
        This is not implemented because we shall compare MemEntry objects trough the subclasses of the MemEntryHandler class.
        :param other: another MemEntry object.
        :return: None
        """
        raise NotImplementedError("Operator __eq__ not defined between " + type(self).__name__ + " objects!")

    def __init__(self, configID, mapfileName, addressStart, addressLength=None, addressEnd=None, sectionName="", objectName="", memType="", memTypeTag="", category="", compilerSpecificData=None):
        """
        Constructor of the MemEntry class.
        :param configID: [string] The configId the entry belongs to.
        :param mapfileName: [string] The name of the mapfile the entry was extracted from.
        :param addressStart: [int or string] The start address of the entry in bytes. It can be an int or a hexadecimal value as string.
        :param addressLength: [int or string] The length of the entry in bytes. Either this or the addressEnd must be given. It can be an int or a hexadecimal value as string.
        :param addressEnd: [int or string] The end address of the entry in bytes. Either this or the addressLength must be given. It can be an int or a hexadecimal value as string.
        :param sectionName: [string] Section name. In case of objects this shall contain the name of the section, the object belongs to.
        :param objectName: [string] Object name, for sections shall be empty.
        :param memType: [string] The type of the memory the entry is located in. For example: INT_FLASH, EXT_FLASH, INT_RAM, EXT_RAM...
        :param memTypeTag: [string] The name of the memory area the entry is located in. This is a logical subtype of the memType value. For example: Code, DataTable...
        :param category: [string] The name of the category, the entry belongs to. This is only a logical grouping. For example: GraphicFramework, EthernetDriver, HMI
        :param compilerSpecificData: [collections.OrderedDict] Data that comes from the object of the MapfileProcessor subclasseses during the mapfile processing.
        """

        self.configID = configID
        self.mapfile = mapfileName

        # Converting the address related parameters to int
        if addressStart is not None:
            _, addressStart = shared_libs.emma_helper.unifyAddress(addressStart)
        if addressLength is not None:
            _, addressLength = shared_libs.emma_helper.unifyAddress(addressLength)
        if addressEnd is not None:
            _, addressEnd = shared_libs.emma_helper.unifyAddress(addressEnd)

        self.addressStart = addressStart

        # Initializing the length to None. This will be later overwritten, but the member has to be created in __init__()
        self.addressLength = None
        if addressLength is None and addressEnd is None:
            sc().error("Either addressLength or addressEnd must be given!")
        elif addressEnd is not None and addressLength is None:
            self.setAddressesGivenEnd(addressEnd)
        elif addressLength is not None and addressEnd is None:
            self.setAddressesGivenLength(addressLength)
        else:
            sc().warning("MemEntry: addressLength AND addressEnd were both given. The addressLength will be used.")
            self.setAddressesGivenLength(addressLength)

        self.sectionName = sectionName
        self.objectName = objectName

        self.memType = memType
        self.memTypeTag = memTypeTag
        self.category = category

        if type(compilerSpecificData) is collections.OrderedDict:
            self.compilerSpecificData = compilerSpecificData
        else:
            sc().error("The compilerSpecificData has to be of type " + type(collections.OrderedDict).__name__ + " instad of " + type(compilerSpecificData).__name__ + "!")

        # Flags for overlapping, containment and duplicate
        self.overlapFlag = None
        self.containmentFlag = None
        self.duplicateFlag = None
        self.containingOthersFlag = None
        self.overlappingOthersFlag = None

        # Original values. These are stored in case the element is changed during processing later later. Then the original values will be still visible in the report.
        self.addressStartOriginal = self.addressStart
        self.addressLengthOriginal = self.addressLength

    def addressStartHex(self):
        return hex(self.addressStart)

    def addressLengthHex(self):
        return hex(self.addressLength)

    def addressEnd(self):
        return self.__calculateAddressEnd(self.addressStart, self.addressLength)

    def addressEndHex(self):
        return hex(self.addressEnd())

    def addressStartHexOriginal(self):
        return hex(self.addressStartOriginal)

    def addressLengthHexOriginal(self):
        return hex(self.addressLengthOriginal)

    def addressEndOriginal(self):
        return self.__calculateAddressEnd(self.addressStartOriginal, self.addressLengthOriginal)

    def addressEndHexOriginal(self):
        return hex(self.addressEndOriginal())

    def equalConfigID(self, other):
        return self.configID == other.configID

    def __lt__(self, other):
        """
        We only want the `<` operator to compare the address start element (dec); nothing else
        Reimplementation of `<` due to bisect comparison (`.insort` uses this operator for insertions;
        can cause errors (TypeError: '<' not supported between instances of 'dict' and 'dict') for same addresses)
        :param other:  x<other calls x.__lt__(other)
        :return: boolean evaluation
        """
        # TODO: Do we want to compare the length (shortest first) when address ist the same? (MSc)
        return self.addressStart < other.addressStart

    def setAddressesGivenEnd(self, addressEnd):
        """
        Function to calculate the address length value from an address end value.
        :return: None
        """
        if self.addressStart < addressEnd:
            self.addressLength = addressEnd - self.addressStart + 1
        elif self.addressStart == addressEnd:
            self.addressLength = 0
        else:
            sc().error("MemEntry: The addressEnd (" + str(addressEnd) + ") is smaller than the addressStart (" + str(self.addressStart) + ")!")

    def setAddressesGivenLength(self, addressLength):
        """
        Function to set the address length value from an address length value.
        :return: None
        """
        if 0 <= addressLength:
            self.addressLength = addressLength
        else:
            sc().error("MemEntry: The addressLength (" + str(addressLength) + ") is negative!")

    @staticmethod
    def __calculateAddressEnd(addressStart, addressLength):
        """
        Function to calculate the end address from a start address and a length.
        :return: The calculated end address.
        """
        # Is this a non-zero length memEntry object?
        if 0 < addressLength:
            result = addressStart + addressLength - 1
        # Else the addressEnd is the addressStart
        else:
            result = addressStart
        return result


class MemEntryHandler(abc.ABC):
    """
    Abstract class describing an interface that a class that´s purpose is the handling of MemEntry objects shall have.
    """
    def __eq__(self, other):
        raise NotImplementedError("This member shall not be used, use the isEqual() instead!")

    @staticmethod
    @abc.abstractmethod
    def isEqual(first, second):
        """
        Function to check whether two MemEntry objects are equal.
        :param first: MemEntry object.
        :param second: MemEntry object.
        :return: True if the first and second objects are equal, false otherwise.
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def getName(memEntry):
        """
        A name getter for MemEntry objects.
        :param memEntry: The MemEntry object that´s name want to be get.
        :return: A string representing the name created from the MemEntry object.
        """
        pass


class SectionEntry(MemEntryHandler):
    """
    A MemEntryHandler for handling MemEntries that represents sections.
    """
    @staticmethod
    def isEqual(first, second):
        """
        Function to decide whether two sections are equal.
        :param first: MemEntry object representing a section.
        :param second: MemEntry object representing a section.
        :return: True if the object first and second are equal, False otherwise.
        """
        if isinstance(first, MemEntry) and isinstance(second, MemEntry):
            return ((first.addressStart == second.addressStart)                     and
                    (first.addressLength == second.addressLength)                   and
                    (first.sectionName == second.sectionName)                       and
                    (first.configID == second.configID)                             and
                    (first.mapfile == second.mapfile)                               and
                    (first.compilerSpecificData == second.compilerSpecificData))
        else:
            raise NotImplementedError("Function isEqual() not defined between " + type(first).__name__ + " and " + type(second).__name__)

    @staticmethod
    def getName(memEntry):
        """
        A name getter for MemEntry object representing a section.
        :param memEntry: The MemEntry object that´s name want to be get.
        :return: A string representing the name created from the MemEntry object.
        """
        return memEntry.sectionName


class ObjectEntry(MemEntryHandler):
    """
    A MemEntryHandler for handling MemEntries that represents objects.
    """
    @staticmethod
    def isEqual(first, second):
        """
        Function to decide whether two object are equal.
        :param first: MemEntry object representing an object.
        :param second: MemEntry object representing an object.
        :return: True if the object first and second are equal, False otherwise.
        """
        if isinstance(first, MemEntry) and isinstance(second, MemEntry):
            return ((first.addressStart == second.addressStart)                     and
                    (first.addressLength == second.addressLength)                   and
                    (first.sectionName == second.sectionName)                       and
                    (first.objectName == second.objectName)                         and
                    (first.configID == second.configID)                             and
                    (first.mapfile == second.mapfile)                               and
                    (first.compilerSpecificData == second.compilerSpecificData))
        else:
            raise NotImplementedError("Function isEqual() not defined between " + type(first).__name__ + " and " + type(second).__name__)

    @staticmethod
    def getName(memEntry):
        """
        A name getter for MemEntry object representing an object.
        :param memEntry: The MemEntry object that´s name want to be get.
        :return: A string representing the name created from the MemEntry object.
        """
        return memEntry.sectionName + "::" + memEntry.objectName
