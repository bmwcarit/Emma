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

from shared_libs.stringConstants import *   # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper


class MemEntry:
    # pylint: disable=too-many-instance-attributes
    # Rationale: This class needs to store all the attributes of an entry.
    """
    A class to represent an entry in the memory. This is a generic class, it can represent both sections and objects.
    To handle objects of this class according to their type, please use one of the subclasses of the @ref:MemEntryHandler.
    """
    def __init__(self, configID, mapfileName, addressStart, addressLength=None, addressEnd=None, sectionName="", objectName="", memType="", memTypeTag="", category="", compilerSpecificData=None):
        # pylint: disable=too-many-arguments
        # Rationale: The constructor needs to be able to fully setup during construction.

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

        self.compilerSpecificData = None
        if isinstance(compilerSpecificData, collections.OrderedDict):
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

    def __eq__(self, other):
        """
        This is not implemented because we shall compare MemEntry objects trough the subclasses of the MemEntryHandler class.
        :param other: another MemEntry object.
        :return: None
        """
        raise NotImplementedError("Operator __eq__ not defined between " + type(self).__name__ + " objects!")

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

    def addressStartHex(self):
        """
        Function to get the addressStart in hex.
        """
        return hex(self.addressStart)

    def addressLengthHex(self):
        """
        Function to get the addressLength in hex.
        """
        return hex(self.addressLength)

    def addressEnd(self):
        """
        Function to get the addressEnd. This is the end address of the MemEntry object.
        By definition the end address is the addressStart + addressLength - 1.
        Objects that have 0 addressLength do not have end addresses by definition.
        :return: The addressEnd if addressLength is not 0, None otherwise.
        """
        return self.__calculateAddressEnd(self.addressStart, self.addressLength)

    def addressEndHex(self):
        """
        Function to get the addressEnd in hex.
        :return: The addressEnd in hex if addressLength is not 0, None otherwise.
        """
        return hex(self.addressEnd())

    def addressStartHexOriginal(self):
        """
        Function to get the original addressStart in hex.
        This means the addressStart value that was given to the object at construction.
        """
        return hex(self.addressStartOriginal)

    def addressLengthHexOriginal(self):
        """
        Function to get the original addressLength in hex.
        This means the addressLength value that was given to (or calculated) the object at construction.
        """
        return hex(self.addressLengthOriginal)

    def addressEndOriginal(self):
        """
        Function to get the original addressEnd.
        This means the addressEnd value calculated from the addressStart and addressLength that was given to (or calculated) the object at construction.
        """
        return self.__calculateAddressEnd(self.addressStartOriginal, self.addressLengthOriginal)

    def addressEndHexOriginal(self):
        return hex(self.addressEndOriginal())

    def equalConfigID(self, other):
        """
        Function to decide whether two MemEntry objects have the same configIDs.
        :param other: Another MemEntry object.
        :return: True if the two MemEntry objects have the same configID, False otherwise.
        """
        return self.configID == other.configID

    def setAddressesGivenEnd(self, addressEnd):
        """
        Function to set the address length value from an address end value.
        :return: None
        """
        if self.addressStart <= addressEnd:
            self.addressLength = addressEnd - self.addressStart + 1
        else:
            sc().error("MemEntry: The addressEnd (" + str(addressEnd) + ") is smaller than the addressStart (" + str(self.addressStart) + ")!")

    def setAddressesGivenLength(self, addressLength):
        """
        Function to set the address length value from an address length value.
        :return: None
        """
        if addressLength >= 0:
            self.addressLength = addressLength
        else:
            sc().error("MemEntry: The addressLength (" + str(addressLength) + ") is negative!")

    @staticmethod
    def __calculateAddressEnd(addressStart, addressLength):
        """
        Function to calculate the end address from a start address and a length.
        :return: The calculated end address if that exists (the object has addressLenght > 0), None otherwise.
        """
        result = None
        # Is this a non-zero length memEntry object?
        if addressLength > 0:
            result = addressStart + addressLength - 1

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

    @staticmethod
    @abc.abstractmethod
    def getName(memEntry):
        """
        A name getter for MemEntry objects.
        :param memEntry: The MemEntry object that´s name want to be get.
        :return: A string representing the name created from the MemEntry object.
        """


class SectionEntry(MemEntryHandler):
    """
    A MemEntryHandler for handling MemEntries that represents sections.
    """
    def __eq__(self, other):
        raise NotImplementedError("This member shall not be used, use the isEqual() instead!")

    @staticmethod
    def isEqual(first, second):
        """
        Function to decide whether two sections are equal.
        :param first: MemEntry object representing a section.
        :param second: MemEntry object representing a section.
        :return: True if the object first and second are equal, False otherwise.
        """
        if not isinstance(first, MemEntry) or not isinstance(second, MemEntry):
            raise TypeError("The argument needs to be of a type MemEntry.")

        return ((first.addressStart == second.addressStart)                     and
                (first.addressLength == second.addressLength)                   and
                (first.sectionName == second.sectionName)                       and
                (first.configID == second.configID)                             and
                (first.mapfile == second.mapfile)                               and
                (first.compilerSpecificData == second.compilerSpecificData))

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
    def __eq__(self, other):
        raise NotImplementedError("This member shall not be used, use the isEqual() instead!")

    @staticmethod
    def isEqual(first, second):
        """
        Function to decide whether two object are equal.
        :param first: MemEntry object representing an object.
        :param second: MemEntry object representing an object.
        :return: True if the object first and second are equal, False otherwise.
        """
        if not isinstance(first, MemEntry) or not isinstance(second, MemEntry):
            raise TypeError("The argument needs to be of a type MemEntry.")

        return ((first.addressStart == second.addressStart)                     and
                (first.addressLength == second.addressLength)                   and
                (first.sectionName == second.sectionName)                       and
                (first.objectName == second.objectName)                         and
                (first.configID == second.configID)                             and
                (first.mapfile == second.mapfile)                               and
                (first.compilerSpecificData == second.compilerSpecificData))

    @staticmethod
    def getName(memEntry):
        """
        A name getter for MemEntry object representing an object.
        :param memEntry: The MemEntry object that´s name want to be get.
        :return: A string representing the name created from the MemEntry object.
        """
        return memEntry.sectionName + "::" + memEntry.objectName
