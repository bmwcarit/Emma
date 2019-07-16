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


import sys
import re

from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper
import emma_libs.memoryEntry


class Categorisation:
    def __init__(self, categoriesObjects, categoriesObjectsKeywords, categoriesSections, categoriesSectionsKeywords, noPrompt):
        self.categoriesObjects = categoriesObjects
        self.categoriesObjectsKeywords = categoriesObjectsKeywords
        self.categoriesSections = categoriesSections
        self.categoriesSectionsKeywords = categoriesSectionsKeywords
        self.categorisedByKeywords = []
        self.noPrompt = noPrompt

    def fillSectionCategories(self, consumerCollection):
        for consumer in consumerCollection:
            consumerName = consumer.section
            consumer.category = self.__evalCategory(consumerName, self.categoriesSections, self.categoriesSectionsKeywords)

    def fillOutObjectCategories(self, consumerCollection):
        for consumer in consumerCollection:
            consumerName = consumer.moduleName
            consumer.category = self.__evalCategory(consumerName, self.categoriesObjects, self.categoriesObjectsKeywords)

    def __evalCategory(self, nameString, categories, categoriesKeywords):
        """
        Returns the category of a module. This function calls __categoriseModuleByKeyword()
        and __searchCategoriesJson() to evaluate a matching category.
        :param nameString: The name string of the module/section to categorise.
        :return: Category string
        """
        foundCategory = self.__searchCategoriesJson(nameString, categories)

        if foundCategory is None:
            # If there is no match check for keyword specified in categoriesKeywordsJson
            foundCategory = self.__categoriseByKeyword(nameString, categoriesKeywords)

        if foundCategory is None:
            # If there is still no match then we will assign the default constant
            foundCategory = UNKNOWN_CATEGORY
            # Add all unmatched module names so they can be appended to categories.json under "<unspecified>"
            self.categorisedByKeywords.append((nameString, foundCategory))

        return foundCategory

    def __searchCategoriesJson(self, nameString, categories):
        if categories is not None:
            categoryEval = []
            for category in categories:  # Iterate through keys
                for i in range(len(categories[category])):  # Look through category array
                    if nameString == categories[category][i]:  # If there is a match append the category
                        categoryEval.append(category)
            if categoryEval:
                categoryEval.sort()
                return ", ".join(categoryEval)
            else:
                return None
        else:
            return None

    def __categoriseByKeyword(self, nameString, categoriesKeywords):
        """
        Categorise a nameString by a keyword specified in categoriesKeywords.json
        :param nameString: The name-string of the module to categorise
        :return: The category string, None if no matching keyword found or the categoriesKeywords.json was not loaded
        """
        if categoriesKeywords is not None:
            for category in categoriesKeywords:
                for keyword in range(len(categoriesKeywords[category])):
                    pattern = r"""\w*""" + categoriesKeywords[category][keyword] + r"""\w*"""     # Search module name for substring specified in categoriesKeywords.json
                    if re.search(pattern, nameString) is not None:                                # Check for first occurence
                        self.categorisedByKeywords.append((nameString, category))                 # Append categorised module, is list of tuples because dict doesn't support duplicate keys
                        return category
        return None

# FIXME solve this...
    def removeUnmatchedFromCategoriesJson(self):
        """
        Removes unused module names from categories.json.
        The function prompts the user to confirm the overwriting of categories.json
        :return: Bool if file has been overwritten
        """
        sc.info("Remove unmatched modules from" + self.__categoriesFilePath + "?\n" + self.__categoriesFilePath + " will be overwritten.\n`y` to accept, any other key to discard.")
        text = input("> ") if not self.args.noprompt else sys.exit(-10)
        if text == "y":
            # Make a dict of {modulename: category} from consumerCollection
            # Remember: consumerCollection is a list of memEntry objects
            rawCategorisedModulesConsumerCollection = {memEntry.moduleName: memEntry.category for memEntry in self.consumerCollection}

            # Format rawCategorisedModulesConsumerCollection to {Categ1: [Modulename1, Modulename2, ...], Categ2: [...]}
            categorisedModulesConsumerCollection = {}
            for k, v in rawCategorisedModulesConsumerCollection.items():
                categorisedModulesConsumerCollection[v] = categorisedModulesConsumerCollection.get(v, [])
                categorisedModulesConsumerCollection[v].append(k)

            for category in self.categoriesJson:  # For every category in categories.json
                if category not in categorisedModulesConsumerCollection:
                    # If category is in categories.json but has never occured in the mapfiles (hence not present in consumerCollection)
                    # Remove the not occuring category entirely
                    self.categoriesJson.pop(category)
                else:  # Category occurs in consumerCollection, hence is present in mapfiles,
                    # overwrite old category module list with the ones acutally occuring in mapfiles
                    self.categoriesJson[category] = categorisedModulesConsumerCollection[category]

            # Sort self.categories case-insensitive in alphabetical order
            for x in self.categoriesJson.keys():
                self.categoriesJson[x].sort(key=lambda s: s.lower())

            shared_libs.emma_helper.writeJson(self.__categoriesFilePath, self.categoriesJson)

            return True

        else:
            sc().warning(self.__categoriesFilePath + " not changed.")
            return False

    def createCategoriesSections(self):
        self.__createCategoriesJson(self.noPrompt, self.categoriesSections)

    def createCategoriesObjects(self):
        self.__createCategoriesJson(self.noPrompt, self.categoriesObjects)

    def __createCategoriesJson(self, noPrompt, categoriesJson):
        """
        Updates/overwrites the present categories.json
        :return Bool if CategoriesJson has been created
        """
        # FIXME: Clearer Output (FM)
        sc().info("Merge categories.json with categorised modules from categoriesKeywords.json?\ncategories.json will be overwritten.\n`y` to accept, any other key to discard.")
        text = input("> ") if not noPrompt else sys.exit(-10)

        if "y" == text:
            # Format moduleCategories to {Categ1: [Modulename1, Modulename2, ...], Categ2: [...]}
            formatted = {}
            for k, v in dict(self.categorisedByKeywords).items():
                formatted[v] = formatted.get(v, [])
                formatted[v].append(k)

            # Merge categories from keyword search with categories from categories.json
            moduleCategories = {**formatted, **categoriesJson}

            # Sort moduleCategories case-insensitive in alphabetical order
            for x in moduleCategories.keys():
                moduleCategories[x].sort(key=lambda s: s.lower())

            shared_libs.emma_helper.writeJson(self.__categoriesKeywordsPath, self.__categoriesKeywordsPath)

            return True
        else:
            sc().warning(self.__categoriesFilePath + " not changed.")
            return False
