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


def checkMonolithSections():
    """
    The function collects the VAS sections from the monolith files and from the global config and from the monolith mapfile
    :return: nothing
    """
    foundInConfigID = []
    foundInMonolith = []

    # Extract sections from monolith file
    monolithPattern = emma_libs.mapfileRegexes.UpperMonolithPattern()
    for configID in self.globalConfig:
        # Check if a monolith was loaded to this configID that can be checked
        if self.globalConfig[configID]["monolithLoaded"]:
            for entry in self.globalConfig[configID]["patterns"]["monoliths"]:
                with open(self.globalConfig[configID]["patterns"]["monoliths"][entry]["associatedFilename"],
                          "r") as monolithFile:
                    monolithContent = monolithFile.readlines()
                for line in monolithContent:
                    lineComponents = re.search(monolithPattern.pattern, line)
                    if lineComponents:  # if match
                        foundInMonolith.append(lineComponents.group(monolithPattern.Groups.section))

            for vas in self.globalConfig[configID]["virtualSections"]:
                foundInConfigID += self.globalConfig[configID]["virtualSections"][vas]

            # Compare sections from configID with found in monolith file
            sectionsNotInConfigID = set(foundInMonolith) - set(foundInConfigID)
            if sectionsNotInConfigID:
                sc.warning(
                    "Monolith File has the following sections. You might want to add it to the respective VAS in " +
                    self.globalConfig[configID]["virtualSectionsPath"] + "!")
                print(sectionsNotInConfigID)
                sc.warning("Still continue? (y/n)") if not self.args.Werror else sys.exit(-10)
                text = input("> ") if not self.args.noprompt else sys.exit(-10)
                if text != "y":
                    sys.exit(-10)
    return

def __addTabularisedMonoliths(self, configID):
    """
    Manages Monolith selection, parsing and converting to a list
    :param configID: configID
    :return: nothing
    """

    def loadMonolithMapfileOnce(configID):
        """
        Load monolith mapfile (only once)
        :return: Monolith file content
        """

        if not self.globalConfig[configID]["monolithLoaded"]:
            mapfileIndexChosen = 0  # Take the first monolith file in list (default case)
            numMonolithFiles = len(self.globalConfig[configID]["patterns"]["monoliths"])
            keyMonolithMapping = {}

            # Update globalConfig with all monolith filenames
            for key, monolith in enumerate(self.globalConfig[configID]["patterns"]["monoliths"]):
                keyMonolithMapping.update(
                    {str(key): self.globalConfig[configID]["patterns"]["monoliths"][monolith]["associatedFilename"]})

            if numMonolithFiles > 1:
                sc.info("More than one monolith file detected. Which to chose (1, 2, ...)?")
                # Display files
                for key, monolith in keyMonolithMapping.items():
                    print(" ", key.ljust(10), monolith)
                # Ask for index which file to chose
                mapfileIndexChosen = shared_libs.emma_helper.Prompt.idx() if not self.args.noprompt else sys.exit(-10)
                while not (0 <= mapfileIndexChosen < numMonolithFiles):
                    sc.warning("Invalid value; try again:")
                    if self.args.Werror:
                        sys.exit(-10)
                    mapfileIndexChosen = shared_libs.emma_helper.Prompt.idx() if not self.args.noprompt else sys.exit(
                        -10)
            elif numMonolithFiles < 1:
                sc.error("No monolith file found but needed for processing")
                sys.exit(-10)

            # Finally load the file
            self.globalConfig[configID]["monolithLoaded"] = True
            with open(keyMonolithMapping[str(mapfileIndexChosen)], "r") as fp:
                content = fp.readlines()
            return content

    def tabulariseAndSortOnce(monolithContent, configID):
        """
        Parses the monolith file and returns a "table" (addresses are int's) of the following structure:
        table[n-th_entry][0] = virtual(int), ...[1] = physical(int), ...[2] = offset(int), ...[3] = size(int), ...[4] = section(str)
        Offset = physical - virtual
        :param monolithContent: Content from monolith as text (all lines)
        :return: list of lists
        """
        table = []  # "headers": virtual, physical, size, section
        monolithPattern = emma_libs.mapfileRegexes.UpperMonolithPattern()
        for line in monolithContent:
            match = re.search(emma_libs.mapfileRegexes.UpperMonolithPattern().pattern, line)
            if match:
                table.append([
                    int(match.group(monolithPattern.Groups.virtualAdress), 16),
                    int(match.group(monolithPattern.Groups.physicalAdress), 16),
                    int(match.group(monolithPattern.Groups.physicalAdress), 16) - int(
                        match.group(monolithPattern.Groups.virtualAdress), 16),
                    int(match.group(monolithPattern.Groups.size), 16),
                    match.group(monolithPattern.Groups.section)
                ])
        self.globalConfig[configID]["sortMonolithTabularised"] = True
        return table

    # Load and register Monoliths
    monolithContent = loadMonolithMapfileOnce(configID)
    if not self.globalConfig[configID]["sortMonolithTabularised"]:
        self.globalConfig[configID]["sortMonolithTabularised"] = tabulariseAndSortOnce(monolithContent, configID)

def __addMonolithsToGlobalConfig(self):

    def ifAnyNonDMA(configID):
        """
        Checks if non-DMA files were found
        Do not run this before mapfiles are searched (try: `findMapfiles` and evt. `findMonolithMapfiles` before)
        :return: True if files which require address translation were found; otherwise False
        """
        entryFound = False
        for entry in self.globalConfig[configID]["patterns"]["mapfiles"]:
            if "VAS" in self.globalConfig[configID]["patterns"]["mapfiles"][entry]:
                entryFound = True
                # TODO : here, a break could improve the performance (AGK)
        return entryFound

    for configID in self.globalConfig:
        sc.info("Processing configID \"" + configID + "\" for monolith files")
        if ifAnyNonDMA(configID):
            numMonolithMapFiles = self.__addFilesPerConfigID(configID, fileType="monoliths")
            if numMonolithMapFiles > 1:
                sc.warning("More than one monolith file found; Result may be non-deterministic")
                if self.args.Werror:
                    sys.exit(-10)
            elif numMonolithMapFiles < 1:
                sc.error("No monolith files was detected but some mapfiles require address translation (VASes used)")
                sys.exit(-10)
            self.__addTabularisedMonoliths(configID)

