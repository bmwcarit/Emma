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

# Emma Memory and Mapfile Analyser - helpers


import sys
import os
import re
import json
import hashlib
import base64

from pypiscout.SCout_Logger import Logger as sc

import markdown
import markdown.extensions.codehilite
import markdown.extensions.fenced_code
import markdown.extensions.toc
import markdown.extensions.tables

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import


def checkIfFolderExists(folderName):
    """
    Check whether a folder exists in current directory; If not exit with error message
    :param folderName: Project to check
    """
    if not os.path.isdir(folderName):
        sc().error("Given directory (" + os.path.abspath(folderName) + ") does not exist; exiting...")


def checkForFile(filePath):
    """
    Check whether a file exists; If not exit with error message
    :param filePath: File path to check
    """
    if not os.path.exists(filePath):
        sc().error("Given file (" + filePath + ") does not exist; exiting...")


def mkDirIfNeeded(path):
    """
    Creates path and all intermediate directories until there
    :param path: Path to create
    """
    if not os.path.isdir(path):
        os.makedirs(path)
        sc().info("Directory " + path + " created since not present")


def readJson(jsonInFilePath):
    """
    Function to read a JSON file
    :return: dict of JSON
    """
    checkForFile(os.path.abspath(jsonInFilePath))     # Absolute path for more readable error message
    with open(jsonInFilePath, "r") as fp:
        dictFromJson = json.load(fp)
    return dictFromJson


def writeJson(jsonOutFilePath, dictToWrite):
    """
    Function to write a JSON file
    :return: dict of JSON
    """
    with open(jsonOutFilePath, "w") as fp:
        json.dump(dictToWrite, fp, indent='\t')


def unifyAddress(address):
    """
    Convert hex or dec address and returns both (in this order)
    :param address: hex or dec address
    :return: [addressHex, addressDec)
    """
    if type(address) == str and address is not None:
        address = int(address, 16)
        addressHex = hex(address)
    elif type(address) == int and address is not None:
        addressHex = hex(address)
    else:
        sc().error("unifyAddress(): Address must be either of type int or str!")
        raise TypeError
    return addressHex, address


def getTimestampFromFilename(filename):
    """
    Get the timestamp from the summary
    :param filename: summary filename in ./memstats
    :return: The timestamp in string form
    """
    pattern = re.compile(r"\d{4}-\d{2}-\d{2}-\d{2}h\d{2}s\d{2}")  # Matches timestamps of the following format: `2017-11-06-14h56s52`
    match = re.search(pattern, filename)
    if match:
        return match.group()
    else:
        sc().error("Could not match the given filename:", filename)


def getColourValFromString(inputString):
    """
    Hashes an input string and returns an 6 digit hex string from it
    :param inputString: an arbitrary string to convert
    :return: 6 digit hex string
    """
    # FIXME: this will crash anyway since we do not import hashlib (MSc)
    hashedString = hashlib.sha256(inputString.encode())
    return hashedString.hexdigest()[len(hashedString.hexdigest())-6:]                         # FIXME: stripping anything except the first 6 characters might fail in some cases >> investigate this further (MSc)


def lastModifiedFilesInDir(path, extension):
    """
    :param path: Directory the files are in
    :param extension: Only files with a specified extension are included
    :return: Sorted list of modified files
    """
    directory = os.listdir(path)
    fileTimestamps = []

    for file in directory:
        file = joinPath(path, file)
        if os.path.isfile(file) and file.endswith(extension):
            time = os.path.getmtime(file)
            fileTimestamps.append([time, file])

    return [item[1] for item in sorted(fileTimestamps)]       # python sorts always by first element for nested lists; we only need the last element (last change) and only its filename (>> [1])


def evalSummary(filename):
    """
    Function to check whether current memStats file is image or module summary
    :param filename: Filename to check
    :return: "Image_Summary" or "Module_Summary"
    """
    if FILE_IDENTIFIER_SECTION_SUMMARY in filename:
        return FILE_IDENTIFIER_SECTION_SUMMARY
    elif FILE_IDENTIFIER_OBJECT_SUMMARY in filename:
        return FILE_IDENTIFIER_OBJECT_SUMMARY


def projectNameFromPath(path):
    """
    Derives the project name from path
    :param path:
    :return:
    """
    return os.path.split(os.path.normpath(path))[-1]


def joinPath(*paths):
    # Removing the elements that are None because these can be optional path elements and they would cause an exception
    listOfReceivedPaths = [i for i in paths if i is not None]
    # FIXME : Docstring or comment pls, and what about the commented out code?
    return os.path.normpath(os.path.join(*listOfReceivedPaths))  # .replace("\\", "/")


def changePictureLinksToEmbeddingInHtmlData(htmlData, sourceDataPath=""):
    """
    The function looks for linked pictures in a html formatted string.
    Then it tries to open every picture file that was linked, encodes their content with base64.encodebytes and replaces the picture links with the encoded data.
    This function should be used whenever a portable .html file needs to be created that has all the pictures embedded into it.
    :param htmlData: Path of the .html file.
    :param sourceDataPath: This is the path of the file from which the htmlData comes from. It is needed during the search for the picture files.
    :return: The modified htmlData.
    """
    list_of_linked_pictures = re.findall(r"<img src=\"([^\"]*)", htmlData)
    for linked_picture in list_of_linked_pictures:
        # If the linked_picture is not an absolute path it needs to be prepended with the sourceDataPath
        if os.path.isabs(linked_picture):
            linked_picture_path = linked_picture
        else:
            linked_picture_path = os.path.join(os.path.dirname(sourceDataPath), linked_picture)

        if not os.path.exists(linked_picture_path):
            sc().warning("The file " + linked_picture_path + " does not exist!")
            continue

        with open(linked_picture_path, "rb") as file_object:
            encoded_picture_data = base64.encodebytes(file_object.read())
        linked_picture_file_extension = os.path.splitext(linked_picture)[1][1:]
        replacement_string = "data:image/" + linked_picture_file_extension + ";base64," + encoded_picture_data.decode() + "\" alt=\"" + linked_picture
        htmlData = htmlData.replace(linked_picture, replacement_string)
    return htmlData


def convertMarkdownDataToHtmlData(markdownData):
    """
    Function to convert markdown formatted data to html formatted data.
    :param markdownData: The markdown formatted data that will be converted.
    :return: The created html formatted data.
    """
    # For available extensions see here: https://github.com/Python-Markdown/markdown/blob/master/docs/extensions/index.md
    htmlData = markdown.markdown(markdownData, extensions=[markdown.extensions.codehilite.CodeHiliteExtension(),
                                                           markdown.extensions.toc.TocExtension(),
                                                           markdown.extensions.fenced_code.FencedCodeExtension(),
                                                           markdown.extensions.tables.TableExtension()])
    return htmlData


def convertMarkdownFileToHtmlFile(markdownFilePath, htmlFilePath):
    """
    Function to convert a .md file to a .html file.
    :param markdownFilePath: Path to the .md file.
    :param htmlFilePath: Path to the .html file.
    :return: nothing
    """
    with open(markdownFilePath, "r") as file_object:
        markdownData = file_object.read()

    htmlData = convertMarkdownDataToHtmlData(markdownData)
    htmlData = changePictureLinksToEmbeddingInHtmlData(htmlData, markdownFilePath)
    htmlData = HTML_TEMPLATE.replace(HTML_TEMPLATE_BODY_PLACEHOLDER, htmlData)

    with open(htmlFilePath, "w") as file_object:
        file_object.write(htmlData)


def findFilesInDir(search_directory, regex_pattern=r".*", including_root=True):
    """
    It looks recursively for files in the search_directory that are matching the regex_pattern.
    :param search_directory: The directory in which the search will be done.
    :param regex_pattern: The regex patterns that the files will be matched against.
    :param including_root: If true, the search directory will be added to the path of the search results as well.
    :return: The paths of the files found.
    :rtype: list of str
    """
    result = []
    for (root, directories, files) in os.walk(search_directory):
        for file in files:
            if re.search(regex_pattern, file) is not None:
                if including_root:
                    result.append(joinPath(root, file))
                else:
                    result.append(file)
    return result


def saveMatplotlibPicture(picture_data, path_to_save, savefig_format, savefig_dpi, savefig_transparent):
    """
    Function to save a matplotlib figure to disk. It ensures that the picture file is properly flushed.
    :param picture_data: A matplotlib Figure object that has a savefig method.
    :param path_to_save: The path where the picture will be saved to.
    :param savefig_format: This value will be forwarded to the savefig method of the Figure object. (See savefig´s description for details)
    :param savefig_dpi: This value will be forwarded to the savefig method of the Figure object. (See savefig´s description for details)
    :param savefig_transparent: This value will be forwarded to the savefig method of the Figure object. (See savefig´s description for details)
    :return: nothing
    """
    with open(path_to_save, "wb") as file_object:
        picture_data.savefig(file_object, format=savefig_format, dpi=savefig_dpi, transparent=savefig_transparent)
        file_object.flush()


"""
MIT License toHumanReadable
Copyright (c) 2019 Marcel Schmalzl, Steve Göring
https://github.com/TeamFlowerPower/kb/wiki/humanReadable
"""


def toHumanReadable(num, suffix='B'):
    """
    Converts a number into a human readable format: humanReadableSize(168963795964) -> ' 157.36 GiB'
    Note: we use binary prefixes (-> 1kiB = 1024 Byte)
    :param num: Number to convert
    :param suffix: The suffix that will be added to the quantifier
    :return: Formatted string
    """
    count = 0
    bit_10 = 10
    num_tmp = num
    for prefix in UNIT_PREFIXES:
        if num_tmp > 1024:
            num_tmp = num_tmp >> bit_10
            count += 1
        else:
            return "{: .2f} {}{}".format(num/2**(count*bit_10), prefix, suffix)


class Prompt:
    @staticmethod
    def idx():
        """
        Prompt for an index [0,inf[ and return it if in this range otherwise return `None`
        :return:
        """
        text = input("> ")
        if text is None or text == "":
            return -1
        else:
            return int(text)

    @staticmethod
    def txt():
        # TODO: implement this method (Msc)
        raise NotImplementedError


def checkIfHelpWasCalled():
    """
    Checks if --help or -h is within the command line argument list
    This is an argparse limitation
    :return: False if it is inside; else True
    """
    if "--help" in sys.argv or "-h" in sys.argv:
        return False
    else:
        return True
