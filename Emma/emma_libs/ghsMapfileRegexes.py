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

# Mapfile Regexes:
#     This File containes classes holding the regex patterns.
#     The default patterns are specific for Green Hills mapfiles.
#     The default patterns can be overriden by adding a JSON entry in patterns*.json. Refer to the Documentation for more info


import re

from pypiscout.SCout_Logger import Logger as sc


class Groups:
    # pylint: disable=too-few-public-methods
    # Rationale: This is a special class to be used for mapfile processing, it does not have to have more public methods.

    """
    Helper class for regex groups
    """
    def __init__(self):
        self.origin = None
        self.size = None
        self.section = None
        self.name = None
        self.sectionOffset = None

        # additional Groups for monolith
        self.virtualAdress = None
        self.physicalAdress = None


class RegexPatternBase:
    # pylint: disable=too-few-public-methods
    # Rationale: This is a special class to be used for mapfile processing, it does not have to have more public methods.

    """
    Base class for module/image summary
    """
    def __init__(self):
        self.pattern = None
        self.Groups = Groups()


class ModuleSummaryPattern(RegexPatternBase):
    # pylint: disable=too-few-public-methods
    # Rationale: This is a special class to be used for mapfile processing, it does not have to have more public methods.

    """
    Class holding the regex pattern for module summary
    """
    def __init__(self):
        super().__init__()
        self.pattern = re.compile(r"""
            # one-liner for testing: ^([0-9a-f]{8})\+([0-9a-f]{6})\s+(.+)\s+(([\w.]+\.([oa]|bin)*.*)|(<.*>))$
            (?:^)(?P<origin>[0-9a-f]+)                                  # Origin
            (?:\+)(?P<size>[0-9a-f]+)                                   # Size
            (?:\s{2,})(?P<section>.+)                                   # Section (i.e.: `.text`, `.debug_abbrev`, `.rodata`, ...)
            #   ^^^^---- we need two or more spaces in order to differentiate between global symbols (only one space) and module summary
            (?:\s+)(?P<module>([\w.]+\.([oa]|bin)*.*)|(<.*>))(?:\s*$)  # Module (i.e.: `crt0.o`, ...) 
            """, re.X)

        self.Groups.origin = "origin"
        self.Groups.size = "size"
        self.Groups.section = "section"
        self.Groups.name = "module"

    def getModuleName(self, lineComponents):
        return lineComponents.group(self.Groups.name).rstrip()


class ImageSummaryPattern(RegexPatternBase):
    # pylint: disable=too-few-public-methods
    # Rationale: This is a special class to be used for mapfile processing, it does not have to have more public methods.

    """
    Class holding the regex pattern for image summary
    """
    def __init__(self):
        super().__init__()
        self.pattern = re.compile(r"""
            #one-liner for testing: ^\s+([/\-:@<>_\[\].*\w]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+)\s+([0-9a-f]+)$
            (?:^\s+)(?P<section>[/\-:@<>_\[\].*\w]+)				    # Section
            (?:\s+)(?P<baseAddr>[0-9a-f]+)							    # Base Address
            (?:\s+)(?P<sizeHex>[0-9a-f]+)						    	# Size(hex)
            (?:\s+)(?P<sizeDec>\d+)									    # Size(dec)
            (?:\s+)(?P<sectionOffset>[0-9a-f]+)(?:\s*$)				    # Sec Offs
            """, re.X)

        self.Groups.name = "section"
        self.Groups.section = "section"
        self.Groups.origin = "baseAddr"  # Origin is equvialent to base Address
        self.Groups.size = "sizeHex"
        self.Groups.sectionOffset = "sectionOffset"

    def getModuleName(self, lineComponents):    # pylint: disable=unused-argument, no-self-use
                                                # Rationale: Sections do not have object names. This function has to have the same prototype as the other subclasses of the RegexPatternBase.
        """
        :param lineComponents: A mapfile line - here not needed (image has no module names (>> thus empty string))
        :return: Empty string (because image has no module names)
        """
        return ""       # image has no module names (>> thus empty string)


class UpperMonolithPattern(RegexPatternBase):
    # pylint: disable=too-few-public-methods
    # Rationale: This is a special class to be used for mapfile processing, it does not have to have more public methods.

    """
    Class holding regex pattern for virtual <-> physical section mapping in monolith file
    """
    def __init__(self):
        super().__init__()
        self.pattern = re.compile(r"""
        # one-liner for testing: ^\s*0x[0-9a-fA-F]{8}\s+0x[0-9a-fA-F]{8}\s*0x[0-9a-fA-F]{8}\s+.+$
        (?:^\s*0x)(?P<virtual>[0-9a-fA-F]+)                   # Virtual address
        (?:\s+0x)(?P<physical>[0-9a-fA-F]+)                   # Physical address
        (?:\s+0x)(?P<size>[0-9a-fA-F]+)                       # Size address
        (?:\s+)(?P<section>.+)(?:\s*$)                        # Section
        """, re.X)

        self.Groups.section = "section"
        self.Groups.size = "size"
        self.Groups.virtualAdress = "virtual"
        self.Groups.physicalAdress = "physical"


class LowerMonolithPattern(RegexPatternBase):
    # pylint: disable=too-few-public-methods
    # Rationale: This is a special class to be used for mapfile processing, it does not have to have more public methods.

    """
    Class holding the regex pattern for the lower part of the monolith file
    """
    def __init__(self):
        super().__init__()
        self.pattern = re.compile(r"""
            # ^\s+[/\-:@<>_\[\].+*\w]+\s+0x[0-9a-f]+\s+[0x]*[0-9a-f]+\s\(\w+\s*/[\w+,\s]+\)
            (?:^\s+)(?P<section>[/\-:@<>_\[\].+*\w]+)					# Section
            (?:\s+0x)(?P<address>[0-9a-f]+)							    # Base Address
            (?:\s+[0x]*)(?P<size>[0-9a-f]+)(?:\s*$)						# Size(hex)
            """, re.X)

        self.Groups.name = "section"
        self.Groups.section = "section"
        self.Groups.origin = "address"  # address is equvialent to base Address
        self.Groups.size = "size"

        sc().info("Preparing lower monolith summary...")

    def getModuleName(self, lineComponents):    # pylint: disable=unused-argument, no-self-use
                                                # Rationale: Sections do not have object names. This function has to have the same prototype as the other subclasses of the RegexPatternBase.
        """
        :param lineComponents: A mapfile line - here not needed (image has no module names (>> thus empty string))
        :return: Empty string (because image has no module names)
        """
        return ""       # image has no module names (>> thus empty string)
