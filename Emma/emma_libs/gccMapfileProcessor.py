import os
import re

from Emma.shared_libs.stringConstants import *
import Emma.emma_libs.memoryEntry

sectionStart = re.compile(r"^\.[$a-z0-9]+\s+0x[a-z0-9]*")    # regex to find the beginning of one section
subsections = re.compile(r"(\s\.[.*$a-z0-9_]+\s*0x[a-z0-9]*) | (\s*0x[a-z0-9]*\s*0x[a-z0-9]*)")  # find a subsection name
object = re.compile(r"[a-zA-Z]+[\\a-zA-Z0-9:_\-()/\[\]{}?+.]+\s?[a-zA-Z]*\n")     # find object name
size = re.compile(r"0x[a-z0-9]+\s+0x[a-z0-9]+")     # find start address and length of an object
sectionsBoundaries = []


def readMapfile(mapfilePath):
    with open(mapfilePath, "r") as mapfileFileObject:
        mapfileContent = mapfileFileObject.readlines()
    return mapfileContent


def parseMapfile(mapfileContent, mapfileName, configId):
    sections = filter(sectionStart.match, mapfileContent)   # find beginning of sections
    for section in sections:
        sectionLineIndex = mapfileContent.index(section)
        sectionsBoundaries.append(sectionLineIndex)
    for i, sectionIndex in enumerate(sectionsBoundaries):
        sectionName = mapfileContent[sectionIndex].split()[0]
        if i+1 != len(sectionsBoundaries):  # if not the last section, find the end of the section
            objects = filter(subsections.match, mapfileContent[sectionIndex:sectionsBoundaries[i+1]])   # find objects in a given section
            for objectData in objects:
                startAndLength = re.search(size, objectData).group()
                physicalAddress = startAndLength.split()[0]
                subsectionName = re.search(subsections, objectData).group()     # information about subsection is currently not used
                addressLength = startAndLength.split()[-1]
                objectName = re.search(object, objectData).group().rstrip()

                memEntry = Emma.emma_libs.memoryEntry.MemEntry(configID=configId,
                                                               mapfileName=mapfileName,
                                                               addressStart=physicalAddress,
                                                               addressLength=addressLength,
                                                               sectionName=sectionName,
                                                               objectName=objectName,
                                                               compilerSpecificData=None)


filePath = r"D:\git_projects\Emma\doc\test_project_gcc\sakura_sketch.map"
mapfile = readMapfile(filePath)
mapfileName = os.path.split(filePath)
parseMapfile(mapfile, mapfileName, None)
