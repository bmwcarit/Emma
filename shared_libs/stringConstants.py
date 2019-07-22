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

# Emma Memory and Mapfile Analyser - string constants


# Version ################################################
VERSION_MAJOR = "2"
VERSION_MINOR = "0"
EMMA_VERSION = ".".join([VERSION_MAJOR, VERSION_MINOR])
EMMA_VISUALISER_VERSION = EMMA_VERSION
EMMA_DELTAS_VERSION = EMMA_VERSION
# #########################################################

ADDR_END_DEC = "addrEndDec"
ADDR_END_HEX = "addrEndHex"
ADDR_END_HEX_ORIGINAL = "addrEndHexOriginal"
ADDR_START_DEC = "addrStartDec"
ADDR_START_HEX = "addrStartHex"
ADDR_START_HEX_ORIGINAL = "addrStartHexOriginal"
ANALYSIS_FOLDER = "analysis"
AVAILABLE_PERCENT = "available [%]"
BUDGET = "budget"
CATEGORIES_OBJECTS_JSON = "categoriesObjects.json"
CATEGORIES_SECTIONS_JSON = "categoriesSections.json"
CATEGORIES_KEYWORDS_OBJECTS_JSON = "categoriesObjectsKeywords.json"
CATEGORIES_KEYWORDS_SECTIONS_JSON = "categoriesSectionsKeywords.json"
CATEGORY = "category"
CONFIG_ID = "configID"
CONTAINMENT_FLAG = "containmentFlag"
CONTAINING_OTHERS_FLAG = "containgOthers"
DELTA_CONFIG = ".delta_config.json"
DELTA_LATEST_PATH = "Latest path"
DMA = "DMA"
DPI_DOCUMENTATION = 300             # Dots per inch for visualiser figure output
DUPLICATE_FLAG = "duplicateFlag"
EPILOG =\
    """Copyright (C) 2019 The Emma authors
    License GPL-3.0: GNU GPL version 3 <https://gnu.org/licenses/gpl.html>.
    This is free software: you are free to change and redistribute it.
    There is NO WARRANTY, to the extent permitted by law."""
# TODO: This shall be changed to Object summary (AGK)
FILE_IDENTIFIER_OBJECT_SUMMARY = "Module_Summary"
# TODO: This shall be changed to Section summary (AGK)
FILE_IDENTIFIER_SECTION_SUMMARY = "Image_Summary"
FILE_IDENTIFIER_OBJECTS_IN_SECTIONS = "Objects_in_Sections"
IGNORE_CONFIG_ID = "ignoreConfigID"
IGNORE_MEMORY = "ignoreMemory"
MAPFILE = "mapfile"
OUTPUT_DIR = "memStats"
OUTPUT_DIR_VISUALISER = "results"
MEM_TYPE = "memType"
MEM_REGION_TO_EXCLUDE = "memRegionExcludes"
MODULE_NAME = "moduleName"
MODULE_SIZE_BYTE = "Module Size [Byte]"
MODULE_SIZE_PERCENT = "Module Size [%]"
OVERLAP_FLAG = "overlapFlag"
PERCENTAGE = "percentage"
SECTION_NAME = "section"
SECTION_SIZE_BYTE = "Section Size [Byte]"
SIZE_DEC = "sizeDec"
SIZE_DEC_ORIGINAL = "sizeDecOriginal"
SIZE_DEC_BY_CATEGORY = "sizeDec by category"
SIZE_HEX = "sizeHex"
SIZE_HEX_ORIGINAL = "sizeHexOriginal"
SIZE_HUMAN_READABLE = "sizeHumanReadable"
TAG = "tag"
TIMESTAMP = "timestamp"
TOTAL_USED_PERCENT = "Total used [%]"
UNIQUE_PATTERN_SECTIONS = "UniquePatternSections"
UNIQUE_PATTERN_OBJECTS = "UniquePatternObjects"
USED_BYTE = "Used [Byte]"
USED_PERCENT = "used [%]"
VAS_NAME = "vasName"
VAS_SECTION_NAME = "vasSectionName"
MEMORY_ESTIMATION_BY_PERCENTAGES_PICTURE_NAME_FIX_PART = "-Memory_Estimation_by_Percentages_generated_"
MEMORY_ESTIMATION_BY_MODULES_PICTURE_NAME_FIX_PART = "-Memory_Estimation_by_Modules_generated_"
MEMORY_ESTIMATION_PARTITION_OF_ALLOCATED_MEMORY_PICTURE_NAME_FIX_PART = "-Memory_Estimation-Partition_of_allocated_Memory"
MEMORY_ESTIMATION_CATEGORISED_IMAGE_CVS_NAME_FIX_PART = "-Memory_Estimation_categorised_Image_generated_"
MEMORY_ESTIMATION_PICTURE_FILE_EXTENSION = "png"
MEMORY_ESTIMATION_PICTURE_DPI = 500
README_CALL_GRAPH_AND_UML_FOLDER_NAME = "call_graph_uml"
README_PICTURE_FORMAT = "png"
OBJECTS_IN_SECTIONS_SECTION_ENTRY = "<Emma_SectionEntry>"
OBJECTS_IN_SECTIONS_SECTION_RESERVE = "<Emma_SectionReserve>"
UNKNOWN_MEM_REGION = "<Emma_UnknownMemRegion>"
UNKNOWN_MEM_TYPE = "<Emma_UnknownMemType>"
UNKNOWN_CATEGORY = "<Emma_UnknownCategory>"

# The HTML Template that will be used during the conversion of .md files to .html
# The CSS in the header has two parts:
#       /* Emma CSS part */
#           There is also a part in it that was completely written by us (see in /**/
#       /* Generated CSS Part*/:
#           This was created with the following command "$ pygmentize -S default -f html > style.css" and then edited after (see CSS comments).
"""
Licence discussion on Bitbucket: https://bitbucket.org/birkenfeld/pygments-main/issues/1496/question-licence-of-auto-generated-css
Change-set: https://bitbucket.org/birkenfeld/pygments-main/commits/38d35093ce1e
----------------------
https://bitbucket.org/birkenfeld/pygments-main/src/default/
https://bitbucket.org/birkenfeld/pygments-main/src/default/LICENSE
https://bitbucket.org/birkenfeld/pygments-main/src/default/AUTHORS

Copyright (c) 2006-2017 by the respective authors (see AUTHORS file).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
"""
# The body placeholder is placed into the template and then later it can be searched for and replaced by the actual body content.
HTML_TEMPLATE_BODY_PLACEHOLDER = "__BODY__"
HTML_TEMPLATE = "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n\n<style>" + \
                """
/*
generated by Pygments <http://pygments.org>
Copyright 2006-2019 by the Pygments team.
Licensed under the BSD license, see LICENSE for details.
*/

/* Emma CSS part */

body
{
    max-width: 1000px;
    font-family: Calibri, Carlito, Arial, Helvetica, sans-serif;
}
h1 { text-align: center; }
div.codehilite { background-color: #F6F8FA; }
code { background-color: #F6F8FA; }


/* Generated CSS Part*/
.hll { background-color: #ffffcc }
.c { color: #408080; font-style: italic } /* Comment */
/*.err { border: 1px solid #FF0000 } /* Error */ --- This was removed because it puts a red frame around code parts that are not recognised by CodeHilite. */
.k { color: #008000; font-weight: bold } /* Keyword */
.o { color: #666666 } /* Operator */
.ch { color: #408080; font-style: italic } /* Comment.Hashbang */
.cm { color: #408080; font-style: italic } /* Comment.Multiline */
.cp { color: #BC7A00 } /* Comment.Preproc */
.cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
.c1 { color: #408080; font-style: italic } /* Comment.Single */
.cs { color: #408080; font-style: italic } /* Comment.Special */
.gd { color: #A00000 } /* Generic.Deleted */
.ge { font-style: italic } /* Generic.Emph */
.gr { color: #FF0000 } /* Generic.Error */
.gh { color: #000080; font-weight: bold } /* Generic.Heading */
.gi { color: #00A000 } /* Generic.Inserted */
.go { color: #888888 } /* Generic.Output */
.gp { color: #000080; font-weight: bold } /* Generic.Prompt */
.gs { font-weight: bold } /* Generic.Strong */
.gu { color: #800080; font-weight: bold } /* Generic.Subheading */
.gt { color: #0044DD } /* Generic.Traceback */
.kc { color: #008000; font-weight: bold } /* Keyword.Constant */
.kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
.kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
.kp { color: #008000 } /* Keyword.Pseudo */
.kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
.kt { color: #B00040 } /* Keyword.Type */
.m { color: #666666 } /* Literal.Number */
.s { color: #BA2121 } /* Literal.String */
.na { color: #7D9029 } /* Name.Attribute */
/* .nb { color: #008000 } /* Name.Builtin */ --- This was removed because it highlights some keyword in the help text. */
.nc { color: #0000FF; font-weight: bold } /* Name.Class */
.no { color: #880000 } /* Name.Constant */
.nd { color: #AA22FF } /* Name.Decorator */
.ni { color: #999999; font-weight: bold } /* Name.Entity */
.ne { color: #D2413A; font-weight: bold } /* Name.Exception */
.nf { color: #0000FF } /* Name.Function */
.nl { color: #A0A000 } /* Name.Label */
.nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
.nt { color: #008000; font-weight: bold } /* Name.Tag */
.nv { color: #19177C } /* Name.Variable */
.ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
.w { color: #bbbbbb } /* Text.Whitespace */
.mb { color: #666666 } /* Literal.Number.Bin */
.mf { color: #666666 } /* Literal.Number.Float */
.mh { color: #666666 } /* Literal.Number.Hex */
.mi { color: #666666 } /* Literal.Number.Integer */
.mo { color: #666666 } /* Literal.Number.Oct */
.sa { color: #BA2121 } /* Literal.String.Affix */
.sb { color: #BA2121 } /* Literal.String.Backtick */
.sc { color: #BA2121 } /* Literal.String.Char */
.dl { color: #BA2121 } /* Literal.String.Delimiter */
.sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
.s2 { color: #BA2121 } /* Literal.String.Double */
/*.se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */ --- This was removed because it highlites escape characters in Bash. */
.sh { color: #BA2121 } /* Literal.String.Heredoc */
.si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
.sx { color: #008000 } /* Literal.String.Other */
.sr { color: #BB6688 } /* Literal.String.Regex */
.s1 { color: #BA2121 } /* Literal.String.Single */
.ss { color: #19177C } /* Literal.String.Symbol */
.bp { color: #008000 } /* Name.Builtin.Pseudo */
.fm { color: #0000FF } /* Name.Function.Magic */
.vc { color: #19177C } /* Name.Variable.Class */
.vg { color: #19177C } /* Name.Variable.Global */
.vi { color: #19177C } /* Name.Variable.Instance */
.vm { color: #19177C } /* Name.Variable.Magic */
.il { color: #666666 } /* Literal.Number.Integer.Long */
""" + "</style>\n</head>\n<body>\n\n" + HTML_TEMPLATE_BODY_PLACEHOLDER + "\n\n</body>\n\n</html>"

"""
MIT License toHumanReadable
Copyright (c) 2019 Marcel Schmalzl, Steve Göring
https://github.com/TeamFlowerPower/kb/wiki/humanReadable
"""
UNIT_PREFIXES = [
        '',    # '' for smallest postfix (-> Byte, ...)
        'Ki',  # Kibibyte      = 2^10 Bytes
        'Mi',  # Mebibyte      = 2^20 Bytes
        'Gi',  # Gibibyte      = 2^30 Bytes
        'Ti',  # Tebibyte      = 2^40 Bytes
        'Pi',  # Pebibyte      = 2^50 Bytes
        'Ei',  # Exbibyte      = 2^60 Bytes
        'Zi',  # Zebibyte      = 2^70 Bytes
        'Yi',  # Yobibyte      = 2*80 Butes
        'Bi',  # Brobibyte     = 2^90 Bytes (from Brontobyte (BB); not yet official SI prefix)
        'GPi'  # Geopibyte (?) = 2^100 Bytes (from Geopbyte (GPB); not yet official SI prefix)
]
DWARF_SECTIONS = frozenset(
    {
        # See as a reference:
        #     * https://www.ibm.com/developerworks/aix/library/au-dwarf-debug-format/index.html
        #     * http://dwarfstd.org/doc/DWARF5.pdf
        # Excluded sections from mapfiles because not relevant for analysing
        # We use a set to be sure that we have unique sections
        ".debug_abbrev",
        ".debug_addr",  # References to loadable sections
        ".debug_aranges",  # LUT: address to compilation unit mapping
        ".debug_cu_index",
        ".debug_frame",  # Frame tables
        ".debug_info",  # DWARF information section
        ".debug_line",  # Line number tables
        ".debug_line_str",  # Stings for file names in .debug_info
        ".debug_loc",  # Location lists used in DW_AT_location
        ".debug_loclists",
        ".debug_macinfo",  # Macro descriptions
        ".debug_names",  # Names for index section
        ".debug_pubnames",  # LUT for global objects & functions
        ".debug_pubtypes",  # LUT global types
        ".debug_ranges",  # Address ranges in DW_AT_ranges
        ".debug_rnglists",
        ".debug_str",  # String references in .debug_info
        ".debug_str_offsets",  # String offsets for .debug_str
        ".debug_tu_index"
        ".debug_types"  # Type descriptions
    }
)
SECTIONS_TO_EXCLUDE = DWARF_SECTIONS.union(frozenset(
    {
        ".unused_ram",
        ".mr_rw_NandFlashDataBuffer"
    }
))

COMPILER_NAME_GHS = "GreenHillsCompiler"
