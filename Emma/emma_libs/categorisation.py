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
import re
import copy

from pypiscout.SCout_Logger import Logger as sc

from shared_libs.stringConstants import *                           # pylint: disable=unused-wildcard-import,wildcard-import
import shared_libs.emma_helper
import emma_libs.memoryEntry


class Categorisation:
    # pylint: disable=too-many-instance-attributes
    # Rationale: The class needs to store the paths for the categorisation files, this leads to the amount of class members.

    """
    Class to implement functionality that are related to categorisation of MemEntry objects.
    """
    def __init__(self, categoriesObjectsPath, categoriesObjectsKeywordsPath, categoriesSectionsPath, categoriesSectionsKeywordsPath, noPrompt):
        # pylint: disable=too-many-arguments
        # Rationale: The categorisation paths and the settings needs to be set-up by this function.

        self.noprompt = noPrompt
        # These are list of sections and objects that are categorised by keywords (these will be used for updating the categories*.json files)
        self.keywordCategorisedSections = []
        self.keywordCategorisedObjects = []
        # Storing the paths to the categories files.
        self.categoriesObjectsPath = categoriesObjectsPath
        self.categoriesObjectsKeywordsPath = categoriesObjectsKeywordsPath
        self.categoriesSectionsPath = categoriesSectionsPath
        self.categoriesSectionsKeywordsPath = categoriesSectionsKeywordsPath
        # Loading the categories files. These files are optional, if they are not present we will store None instead.
        self.categoriesObjects = Categorisation.__readCategoriesJson(self.categoriesObjectsPath)
        self.categoriesSections = Categorisation.__readCategoriesJson(self.categoriesSectionsPath)
        self.categoriesObjectsKeywords = Categorisation.__readCategoriesJson(self.categoriesObjectsKeywordsPath)
        self.categoriesSectionsKeywords = Categorisation.__readCategoriesJson(self.categoriesSectionsKeywordsPath)

    def fillOutCategories(self, sectionCollection, objectCollection):
        """
        Organisational function to call sub-functions that fill out categories in a sectionCollection and objectCollection.
        :param sectionCollection: List of MemEntry objects that represent sections. The categories will be filled out in these.
        :param objectCollection: List of MemEntry objects that represent objects. The categories will be filled out in these.
        :return: None
        """
        self.__fillOutSectionCategories(sectionCollection)
        self.__fillOutObjectCategories(objectCollection)

    def manageCategoriesFiles(self, updateCategoriesFromKeywordMatches, removeUnmatchedCategories, sectionCollection, objectCollection):
        """
        Organisational function to call sub-functions that updates the categoriesSections and categoriesObjects files.
        This function needs to be called after running the collections with the fillOutCategories().
        :param updateCategoriesFromKeywordMatches: True if the categoriesSections and categoriesObjects needs to be updated,
                                                   from the matches found during categorisation with the categoriesSectionsKeywords
                                                   and categoriesObjectsKeywords respectively, False otherwise.
        :param removeUnmatchedCategories: True if the categories that did not match needs to be removed from
                                          categoriesSections and categoriesObjects, False otherwise.
        :param sectionCollection: List of MemEntry objects that represent sections. The categories needs to be already filled out in these by the fillOutCategories().
        :param objectCollection: List of MemEntry objects that represent objects. The categories needs to be already filled out in these by the fillOutCategories().
        :return: None
        """
        self.__manageSectionCategoriesFiles(updateCategoriesFromKeywordMatches, removeUnmatchedCategories, sectionCollection)
        self.__manageObjectCategoriesFiles(updateCategoriesFromKeywordMatches, removeUnmatchedCategories, objectCollection)

    @staticmethod
    def __readCategoriesJson(path):
        """
        Function to load a categorisation json file.
        :param path: The path of the file that needs to be read.
        :return: Content of the json file.
        """
        if os.path.exists(path):
            categoriesJson = shared_libs.emma_helper.readJson(path)
        else:
            categoriesJson = None
            sc().warning("There was no " + os.path.basename(path) + " file found, the categorization based on this will be skipped.")
        return categoriesJson

    def __fillOutSectionCategories(self, sectionCollection):
        """
        Function to fill out the categories in a section collection.
        :param sectionCollection: List of MemEntry objects representing sections.
        :return: None
        """
        # Filling out sections
        for consumer in sectionCollection:
            consumerName = consumer.sectionName
            consumer.category = Categorisation.__evalCategoryOfAnElement(consumerName, self.categoriesSections, self.categoriesSectionsKeywords, self.keywordCategorisedSections)

    def __fillOutObjectCategories(self, objectCollection):
        """
        Function to fill out the categories in an object collection.
        :param objectCollection: List of MemEntry objects representing objects.
        :return: None
        """
        # Filling out objects
        for consumer in objectCollection:
            consumerName = consumer.objectName
            consumer.category = Categorisation.__evalCategoryOfAnElement(consumerName, self.categoriesObjects, self.categoriesObjectsKeywords, self.keywordCategorisedObjects)

    def __manageSectionCategoriesFiles(self, updateCategoriesFromKeywordMatches, removeUnmatchedCategories, sectionCollection):
        """
        Function that updates the categoriesSections file based on an already categorised section collection.
        :param updateCategoriesFromKeywordMatches: True if the categoriesSections needs to be updated, from the matches
                                                   found during categorisation with the categoriesSectionsKeywords,
                                                   False otherwise.
        :param removeUnmatchedCategories: True if the categories that did not match needs to be removed from
                                          categoriesSections, False otherwise.
        :param sectionCollection: List of MemEntry objects that represent sections.
        :return: None
        """
        # Updating the section categorisation file
        if updateCategoriesFromKeywordMatches:
            # Asking the user whether a file shall be updated. If no prompt is on we will overwrite by default.
            sc().info("Merge categoriesSections.json with categorised modules from " + CATEGORIES_KEYWORDS_SECTIONS_JSON + "?\nIt will be overwritten.\n`y` to accept, any other key to discard.")
            if self.noprompt:
                sc().wwarning("No prompt is active. Chose to overwrite file.")
                text = "y"
            else:
                text = input("> ")
            # If an update is allowed
            if text == "y":
                Categorisation.__updateCategoriesJson(self.categoriesSections, self.keywordCategorisedSections, self.categoriesSectionsPath)
                # Re-categorize sections if the categorisation file have been changed
                self.__fillOutSectionCategories(sectionCollection)
                sc().info("The " + self.categoriesSectionsPath + " was updated.")
            else:
                sc().info(text + " was entered, aborting the update. The " + self.categoriesSectionsPath + " was not changed.")
        # Do we need to remove the unmatched categories?
        if removeUnmatchedCategories:
            if self.noprompt:
                sc().wwarning("No prompt is active. Chose `y` to remove unmatched categories.")
                text = "y"
            else:
                text = input("> ")
            if text == "y":
                sc().info("Remove unmatched modules from " + CATEGORIES_SECTIONS_JSON + "?\nIt will be overwritten.\n `y` to accept, any other key to discard.")
                Categorisation.__removeUnmatchedFromCategoriesJson(self.categoriesSections, sectionCollection, emma_libs.memoryEntry.SectionEntry, self.categoriesSectionsPath)
            else:
                sc().info(text + " was entered, aborting the removal. The " + self.categoriesSectionsPath + " was not changed.")

    def __manageObjectCategoriesFiles(self, updateCategoriesFromKeywordMatches, removeUnmatchedCategories, objectCollection):
        """
        Function that updates the categoriesObjects file based on an already categorised object collection.
        :param updateCategoriesFromKeywordMatches: True if the categoriesObjects needs to be updated, from the matches
                                                   found during categorisation with the categoriesObjectsKeywords,
                                                   False otherwise.
        :param removeUnmatchedCategories: True if the categories that did not match needs to be removed from
                                          categoriesObjects, False otherwise.
        :param objectCollection: List of MemEntry objects that represent objects.
        :return: None
        """
        if updateCategoriesFromKeywordMatches:
            # Updating the object categorisation file
            sc().info("Merge categoriesObjects.json with categorised modules from " + CATEGORIES_KEYWORDS_OBJECTS_JSON + "?\nIt will be overwritten.\n`y` to accept, any other key to discard.")
            if self.noprompt:
                sc().wwarning("No prompt is active. Chose `y` to overwrite.")
                text = "y"
            else:
                text = input("> ")
            # If an update is allowed
            if text == "y":
                Categorisation.__updateCategoriesJson(self.categoriesObjects, self.keywordCategorisedObjects, self.categoriesObjectsPath)
                sc().info("The " + self.categoriesObjectsPath + " was updated.")
                # Re-categorize objects if the categorisation file have been changed
                self.__fillOutObjectCategories(objectCollection)
            else:
                sc().info(text + " was entered, aborting the update. The file " + self.categoriesObjectsPath + " was not changed.")
        # Do we need to remove the unmatched categories?
        if removeUnmatchedCategories:
            if self.noprompt:
                sc().wwarning("No prompt is active. Chose `y` to remove unmatched.")
                text = "y"
            else:
                text = input("> ")
            if text == "y":
                sc().info("Remove unmatched modules from " + CATEGORIES_OBJECTS_JSON + "?\nIt will be overwritten.\n `y` to accept, any other key to discard.")
                Categorisation.__removeUnmatchedFromCategoriesJson(self.categoriesObjects, objectCollection, emma_libs.memoryEntry.ObjectEntry, self.categoriesObjectsPath)
            else:
                sc().info(text + " was entered, aborting the removal. The " + self.categoriesObjectsPath + " was not changed.")

    @staticmethod
    def __evalCategoryOfAnElement(nameString, categories, categoriesKeywords, keywordCategorisedElements):
        """
        Function to find the category of an element. First the categorisation will be tried with the categories file,
        and if that fails with the categoriesKeywords file. If this still fails a default value will be set for the category.
        If the element was categorised by a keyword then the element will be added to the keywordCategorisedElements list.
        :param nameString: The name string of the element that needs to be categorised.
        :param categories: Content of the categories file.
        :param categoriesKeywords: Content of the categoriesKeywords file.
        :param keywordCategorisedElements: List of elements that were categorised by keywords.
        :return: Category string
        """
        foundCategory = Categorisation.__searchCategoriesJson(nameString, categories)
        if foundCategory is None:
            # If there is no match check for keyword specified in categoriesKeywordsJson
            foundCategory = Categorisation.__categoriseByKeyword(nameString, categoriesKeywords, keywordCategorisedElements)
        if foundCategory is None:
            # If there is still no match then we will assign the default constant
            foundCategory = UNKNOWN_CATEGORY
        return foundCategory

    @staticmethod
    def __searchCategoriesJson(nameString, categories):
        """
        Function to search categories for a name in a categories file.
        :param nameString: String that categories needs to be searched for.
        :param categories: File the categories needs to be searched in.
        :return: String that contains the categories comma separated that were found for the nameString, else None.
        """
        result = None

        # Did we get a file?
        if categories is not None:
            categoriesFoundForTheName = []
            # Iterating trough the categories
            for category in categories:
                # Look through elements that shall be ordered to this category
                for categoryElementName in categories[category]:
                    # If the element name matches the nameString then we will add this category as found
                    if nameString == categoryElementName:
                        categoriesFoundForTheName.append(category)
            # If we have found categories then we will sort them and return them comma separated
            if categoriesFoundForTheName:
                categoriesFoundForTheName.sort()
                result = ", ".join(categoriesFoundForTheName)
        return result

    @staticmethod
    def __categoriseByKeyword(nameString, categoriesKeywords, keywordCategorisedElements):
        """
        Function to search a category for a name in a categoriesKeywords file.
        :param nameString: String that categories needs to be searched for.
        :param categoriesKeywords: File the categories needs to be searched in.
        :param keywordCategorisedElements: List of pairs that contains elements that were categorised by keywords as (name, category).
        :return: String that contains the category that was found for the nameString, else None.
        """
        result = None

        # If a categoriesKeywords file was received
        if categoriesKeywords is not None:
            # For all the categories
            for category in categoriesKeywords:
                # For all the keywords belonging to this category
                for keyword in categoriesKeywords[category]:
                    # Creating a regex pattern from the keyword
                    pattern = r"""\w*""" + keyword + r"""\w*"""
                    # Finding the first occurrence of the pattern in the nameString
                    if re.search(pattern, nameString) is not None:
                        # Adding the element to the list of elements that were keyword categorised as a pair of (name, category)
                        keywordCategorisedElements.append((nameString, category))
                        result = category
        return result

    @staticmethod
    def __updateCategoriesJson(categoriesToUpdate, newCategories, outputPath):
        """
        Updates a categories file with new categories.
        :param categoriesToUpdate: This is the categories file that needs to be updated.
        :param newCategories: These are the new categories that will be added to the categories file.
        :param outputPath: This is the path where the updated file will be written.
        :return: None.
        """
        # Format newCategories to {Categ1: [ObjectName1, ObjectName2, ...], Categ2: [...]}
        formattedNewCategories = {}
        for key, value in dict(newCategories).items():
            formattedNewCategories[value] = formattedNewCategories.get(value, [])
            formattedNewCategories[value].append(key)

        # Merge categories from keyword search with categories from categories.json
        mergedCategories = {**formattedNewCategories, **categoriesToUpdate}

        # Sort moduleCategories case-insensitive in alphabetical order
        for key in mergedCategories.keys():
            mergedCategories[key].sort(key=lambda s: s.lower())

        # Write the data to the outputPath
        shared_libs.emma_helper.writeJson(outputPath, mergedCategories)

    @staticmethod
    def __removeUnmatchedFromCategoriesJson(categoriesToRemoveFrom, consumerCollection, memEntryHandler, outputPath):
        """
        Removes categories from the categories files for those where no matches were found
        :param categoriesToRemoveFrom: This is the categories file from which we remove the unmatched categories.
        :param consumerCollection: This is the consumer collection based on we will decide which category has matched.
        :param memEntryHandler: This is a subclass of the MemEntryHandler.
        :param outputPath: This is the path where the categories file will be written to.
        """

        # Make a dict of {name : category} from consumerCollection
        rawCategorisedConsumerCollection = {memEntryHandler.getName(memEntry): memEntry.category for memEntry in consumerCollection}

        # Format rawCategorisedModulesConsumerCollection to {Categ1: [ObjectName1, ObjectName2, ...], Categ2: [...]}
        categorisedElements = {}
        for key, value in rawCategorisedConsumerCollection.items():
            categorisedElements[value] = categorisedElements.get(value, [])
            categorisedElements[value].append(key)
        # FIXME: dict changes during iteration (MSc)

        for category in copy.copy(categoriesToRemoveFrom):  # For every category in categories.json
            if category not in categorisedElements:
                # If category is in categories.json but has never occurred in the mapfiles (hence not present in consumerCollection)
                # Remove the not occuring category entirely
                categoriesToRemoveFrom.pop(category)
            else:
                # Category occurs in consumerCollection, hence is present in mapfiles,
                # overwrite old category object list with the ones actually occurring in mapfiles
                categoriesToRemoveFrom[category] = categorisedElements[category]

        # Sort self.categories case-insensitive in alphabetical order
        for key in categoriesToRemoveFrom.keys():
            categoriesToRemoveFrom[key].sort(key=lambda s: s.lower())

        # Write the data to the outputPath
        shared_libs.emma_helper.writeJson(outputPath, categoriesToRemoveFrom)
