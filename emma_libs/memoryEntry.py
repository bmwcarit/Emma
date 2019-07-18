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

# This file contains the parser and internal data structures for holding the mapfile information.
# The memEntry class stores a mapfile-element.
# The MemoryManager class handles parsing, categorisation and overlap/containment flagging.


import abc

from pypiscout.SCout_Logger import Logger as sc

import shared_libs.emma_helper


class MemEntry:
    def __eq__(self, other):
        """
        This is not implemented because we shall compare MemEntry objects trough the SectionEntry and ObjectEntry wrappers.
        :param other: another MemEntry object.
        :return: None
        """
        raise NotImplementedError("Operator __eq__ not defined between " + type(self).__name__ + " objects!")

    def __init__(self, vasName, vasSectionName, section, moduleName, mapfileName, configID, addressStart, tag=None, memType=None, category=None, addressLength=None, addressEnd=None):
        """
        Class storing one memory entry + meta data
        Chose addressLength or addressEnd (one and only one of those two must be given)

        Meta data arguments
        :param tag: [string] Arbitrary name (f.ex. IO_RAM, CM_RAM, ...) in order to distinguish not only by memType
        :param memType: [string] {int, ext} flash, {int, ext} RAM
        :param vasName: [string] name of the corresponding virtual address space (VAS)
        :param vasSectionName [string] name of the vasSection the address translation was done for this element with
        :param section: [string] section name; i.e.: `.text`, `.debug_abbrev`, `.rodata`, ...
        :param moduleName: [string] name of the module
        :param mapfileName: [string] name of the mapfile where we found this entry
        :param configID: [class/string(=members)] defining the micro system
        :param category: [string] = classifier (/ logical grouping of known modules)
        # dma: [bool] true if we can use physical addresses directly (false for address translation i.e. via monolith file)

        Address related arguments
        :param addressStart: [string(hex) or int(dec)] start address
        :param addressLength: [string(hex) or int(dec) or nothing(default = None)] address length
        :param addressEnd: [string(hex) or int(dec) or nothing(default = None)] end address
        """

        # Check if we got hex or dec addresses and decide how to convert those
        # Start address
        _, self.addressStart = shared_libs.emma_helper.unifyAddress(addressStart)
        # Initializing the length to None. This will be later overwritten, but the member has to be created in __init__()
        self.addressLength = None

        if addressLength is None and addressEnd is None:
            sc().error("Either addressLength or addressEnd must be given!")
        elif addressLength is None:
            self.setAddressesGivenEnd(addressEnd)
        elif addressEnd is None:
            self.setAddressesGivenLength(addressLength)
        else:
            sc().warning("MemEntry: addressLength AND addressEnd were both given. The addressLength will be used.")
            self.setAddressesGivenLength(addressLength)

        self.memTypeTag = tag  # Differentiate in more detail between memory sections/types
        self.vasName = vasName
        self.vasSectionName = vasSectionName
        if vasName is None:  # Probably we can just trust that a VAS name of `None` or "" is give; Anyway this seems more safe to me
            # Direct memory access
            self.dma = True
        else:
            self.dma = False

        self.section = section  # Section type; i.e.: `.text`, `.debug_abbrev`, `.rodata`, ...
        self.moduleName = moduleName  # Module name (obj files, ...)
        self.mapfile = mapfileName  # Shows mapfile association (belongs to mapfile `self.mapfile`)
        self.configID = configID
        self.memType = memType
        self.category = category  # = classifier (/grouping)

        # Flags for overlapping, containment and duplicate
        self.overlapFlag = None
        self.containmentFlag = None
        self.duplicateFlag = None
        self.containingOthersFlag = None
        self.overlappingOthersFlag = None

        # Original values. These are stored in case the element is moved later. Then the original values will be still accessible.
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
        """
        Function to evaluate whether two sections have the same config ID
        :return:
        """
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
        if self.addressStart < addressEnd:
            self.addressLength = addressEnd - self.addressStart + 1
        elif self.addressStart == addressEnd:
            self.addressLength = 0
        else:
            sc().warning("MemEntry: The addressEnd (" + addressEnd + ") is smaller than the addressStart (" + self.addressStart + ")!")

    def setAddressesGivenLength(self, addressLength):
        _, self.addressLength = shared_libs.emma_helper.unifyAddress(addressLength)
        if 0 > self.addressLength:
            sc().warning("MemEntry: The addressLength (" + self.addressLength + ") is negative!")

    @staticmethod
    def __calculateAddressEnd(addressStart, addressLength):
        # Is this a non-zero length memEntry object?
        if 0 < addressLength:
            result = addressStart + addressLength - 1
        # Else the addressEnd is the addressStart
        else:
            result = addressStart
        return result


class MemEntryHandler(abc.ABC):
    def __eq__(self, other):
        raise NotImplementedError("This member shall not be used, use the isEqual() instead!")

    @staticmethod
    @abc.abstractmethod
    def isEqual(first, second):
        pass

    @staticmethod
    @abc.abstractmethod
    def getName(memEntry):
        pass


class SectionEntry(MemEntryHandler):
    @staticmethod
    def isEqual(first, second):
        if isinstance(first, MemEntry) and isinstance(second, MemEntry):
            return ((first.addressStart == second.addressStart) and
                    (first.addressEnd() == second.addressEnd()) and
                    (first.section == second.section)           and
                    (first.configID == second.configID)         and
                    (first.mapfile == second.mapfile)           and
                    (first.vasName == second.vasName))
        else:
            raise NotImplementedError("Function isEqual() not defined between " + type(first).__name__ + " and " + type(second).__name__)

    @staticmethod
    def getName(memEntry):
        return memEntry.section


class ObjectEntry(MemEntryHandler):
    @staticmethod
    def isEqual(first, second):
        if isinstance(first, MemEntry) and isinstance(second, MemEntry):
            return ((first.addressStart == second.addressStart)      and
                    (first.addressEnd() == second.addressEnd())      and
                    (first.section == second.section)                and
                    (first.moduleName == second.moduleName)          and
                    (first.configID == second.configID)              and
                    (first.mapfile == second.mapfile)                and
                    (first.vasName == second.vasName)                and
                    (first.vasSectionName == second.vasSectionName))
        else:
            raise NotImplementedError("Function isEqual() not defined between " + type(first).__name__ + " and " + type(second).__name__)

    @staticmethod
    def getName(memEntry):
        return memEntry.section + "::" + memEntry.moduleName
