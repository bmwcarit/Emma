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


import os
import sys
import re

from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *
import shared_libs.emma_helper
import emma_libs.memoryEntry


class Categorisation:
    def __init__(self, categoriesObjectsPath, categoriesObjectsKeywordsPath, categoriesSectionsPath, categoriesSectionsKeywordsPath, noPrompt):
        self.noPrompt = noPrompt
        # These are list of sections and objects that are categorised by keywords (these will be used for updating the categories*.json files)
        self.keywordCategorisedSections = []
        self.keywordCategorisedObjects = []
        # Storing the paths to the categories files.
        self.categoriesObjectsPath = categoriesObjectsPath
        self.categoriesObjectsKeywordsPath = categoriesObjectsKeywordsPath
        self.categoriesSectionsPath = categoriesSectionsPath
        self.categoriesSectionsKeywordsPath = categoriesSectionsKeywordsPath
        # Loading the categories files. These files are optional, if they are not present we will store None instead.
        self.categoriesObjects = self.__readCategoriesJson(self.categoriesObjectsPath)
        self.categoriesObjectsKeywords = self.__readCategoriesJson(self.categoriesObjectsKeywordsPath)
        self.categoriesSections = self.__readCategoriesJson(self.categoriesSectionsPath)
        self.categoriesSectionsKeywords = self.__readCategoriesJson(self.categoriesSectionsKeywordsPath)

    def fillOutCategories(self, sectionCollection, objectCollection):
        self.__fillOutSectionCategories(sectionCollection)
        self.__fillOutObjectCategories(objectCollection)

    def manageCategoriesFiles(self, updateCategoriesFromKeywordMatches, removeUnmatchedCategories, sectionCollection, objectCollection):
        self.__manageSectionCategoriesFiles(updateCategoriesFromKeywordMatches, removeUnmatchedCategories, sectionCollection)
        self.__manageObjectCategoriesFiles(updateCategoriesFromKeywordMatches, removeUnmatchedCategories, objectCollection)

    def __manageSectionCategoriesFiles(self, updateCategoriesFromKeywordMatches, removeUnmatchedCategories, sectionCollection):
        if updateCategoriesFromKeywordMatches:
            # Updating the section categorisation file
            sc().info("Merge categoriesSections.json with categorised modules from categoriesSectionsKeywords.json?\ncategoriesSections.json will be overwritten.\n`y` to accept, any other key to discard.")
            sectionCategoriesWereUpdated = self.__updateCategoriesJson(self.noPrompt, self.categoriesSections, self.keywordCategorisedSections, self.categoriesSectionsPath)
            # Re-categorize sections if the categorisation file have been changed
            if sectionCategoriesWereUpdated:
                self.__fillOutSectionCategories(sectionCollection)
        # Do we need to remove the unmatched categories?
        if removeUnmatchedCategories:
            sc().info("Remove unmatched modules from categoriesSections.json?\ncategoriesSections.json will be overwritten.\n `y` to accept, any other key to discard.")
            self.__removeUnmatchedFromCategoriesJson(self.noPrompt, self.categoriesSections, sectionCollection, emma_libs.memoryEntry.SectionEntry, self.categoriesSectionsPath)

    def __manageObjectCategoriesFiles(self, updateCategoriesFromKeywordMatches, removeUnmatchedCategories, objectCollection):
        if updateCategoriesFromKeywordMatches:
            # Updating the object categorisation file
            sc().info("Merge categoriesObjects.json with categorised modules from categoriesObjectsKeywords.json?\ncategoriesObjects.json will be overwritten.\n`y` to accept, any other key to discard.")
            objectCategoriesWereUpdated = self.__updateCategoriesJson(self.noPrompt, self.categoriesObjects, self.keywordCategorisedObjects, self.categoriesObjectsPath)
            # Re-categorize objects if the categorisation file have been changed
            if objectCategoriesWereUpdated:
                self.__fillOutObjectCategories(objectCollection)
        # Do we need to remove the unmatched categories?
        if removeUnmatchedCategories:
            sc().info("Remove unmatched modules from categoriesObjects.json?\ncategoriesObjects.json will be overwritten.\n `y` to accept, any other key to discard.")
            self.__removeUnmatchedFromCategoriesJson(self.noPrompt, self.categoriesObjects, objectCollection, emma_libs.memoryEntry.ObjectEntry, self.categoriesObjectsPath)

    def __fillOutSectionCategories(self, sectionCollection):
        # Filling out sections
        for consumer in sectionCollection:
            consumerName = consumer.section
            consumer.category = self.__evalCategoryOfAnElement(consumerName, self.categoriesSections, self.categoriesSectionsKeywords, self.keywordCategorisedSections)

    def __fillOutObjectCategories(self, objectCollection):
        # Filling out objects
        for consumer in objectCollection:
            consumerName = consumer.moduleName
            consumer.category = self.__evalCategoryOfAnElement(consumerName, self.categoriesObjects, self.categoriesObjectsKeywords, self.keywordCategorisedObjects)

    def __readCategoriesJson(self, path):
        if os.path.exists(path):
            categoriesJson = shared_libs.emma_helper.readJson(path)
        else:
            categoriesJson = None
            sc().warning("There was no " + os.path.basename(path) + " file found, the categorization based on this will be skipped.")
        return categoriesJson

    def __evalCategoryOfAnElement(self, nameString, categories, categoriesKeywords, keywordCategorisedElements):
        """
        Returns the category of a module. This function calls __categoriseModuleByKeyword()
        and __searchCategoriesJson() to evaluate a matching category.
        :param nameString: The name string of the module/section to categorise.
        :return: Category string
        """
        foundCategory = self.__searchCategoriesJson(nameString, categories)
        if foundCategory is None:
            # If there is no match check for keyword specified in categoriesKeywordsJson
            foundCategory = self.__categoriseByKeyword(nameString, categoriesKeywords, keywordCategorisedElements)
        if foundCategory is None:
            # If there is still no match then we will assign the default constant
            foundCategory = UNKNOWN_CATEGORY
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

    def __categoriseByKeyword(self, nameString, categoriesKeywords, keywordCategorisedElements):
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
                        keywordCategorisedElements.append((nameString, category))                 # Append categorised module, is list of tuples because dict doesn't support duplicate keys
                        return category
        return None

    def __updateCategoriesJson(self, noPrompt, categoriesToUpdate, newCategories, outputPath):
        """
        Updates/overwrites the present categories.json
        :return Bool if CategoriesJson has been created
        """
        result = False
        text = input("> ") if not noPrompt else sys.exit(-10)

        if "y" == text:
            # Format newCategories to {Categ1: [Modulename1, Modulename2, ...], Categ2: [...]}
            formattedNewCategories = {}
            for key, value in dict(newCategories).items():
                formattedNewCategories[value] = formattedNewCategories.get(value, [])
                formattedNewCategories[value].append(key)

            # Merge categories from keyword search with categories from categories.json
            mergedCategories = {**formattedNewCategories, **categoriesToUpdate}

            # Sort moduleCategories case-insensitive in alphabetical order
            for key in mergedCategories.keys():
                mergedCategories[key].sort(key=lambda s: s.lower())

            shared_libs.emma_helper.writeJson(outputPath, mergedCategories)
            sc().info("The " + outputPath + " was updated.")

            result = True
        else:
            sc().info(text + " was entered, aborting the update. The " + outputPath + " was not changed.")
        return result

    def __removeUnmatchedFromCategoriesJson(self, noPrompt, categoriesToRemoveFrom, consumerCollection, memEntryHandler, outputPath):
        """
        Removes unused module names from categories.json.
        The function prompts the user to confirm the overwriting of categories.json
        :return: Bool if file has been overwritten
        """
        text = input("> ") if not noPrompt else sys.exit(-10)
        if text == "y":
            # Make a dict of {name : category} from consumerCollection
            rawCategorisedConsumerCollection = {memEntryHandler.getName(memEntry): memEntry.category for memEntry in consumerCollection}

            # Format rawCategorisedModulesConsumerCollection to {Categ1: [Modulename1, Modulename2, ...], Categ2: [...]}
            categorisedElements = {}
            for key, value in rawCategorisedConsumerCollection.items():
                categorisedElements[value] = categorisedElements.get(value, [])
                categorisedElements[value].append(key)

            for category in categoriesToRemoveFrom:  # For every category in categories.json
                if category not in categorisedElements:
                    # If category is in categories.json but has never occured in the mapfiles (hence not present in consumerCollection)
                    # Remove the not occuring category entirely
                    categoriesToRemoveFrom.pop(category)
                else:
                    # Category occurs in consumerCollection, hence is present in mapfiles,
                    # overwrite old category module list with the ones acutally occuring in mapfiles
                    categoriesToRemoveFrom[category] = categorisedElements[category]

            # Sort self.categories case-insensitive in alphabetical order
            for key in categoriesToRemoveFrom.keys():
                categoriesToRemoveFrom[key].sort(key=lambda s: s.lower())

            shared_libs.emma_helper.writeJson(outputPath, categoriesToRemoveFrom)
        else:
            sc().info(text + " was entered, aborting the removal. The " + outputPath + " was not changed.")
