# Emma
**Emma Memory and Mapfile Analyser**

> Conduct static (i.e. worst case) memory consumption analyses based on linker map files (currently only Green Hills map files are supported).
This tool creates a summary/overview about static memory usage in form of a comma separated values (CSV) file.

------------------------
# Contents
- [Emma](#emma)
- [Contents](#contents)
- [Requirements](#requirements)
- [Process](#process)
- [Limitations](#limitations)
- [Usage](#usage)
- [Arguments](#arguments)
  - [Required Arguments](#required-arguments)
  - [Optional Arguments](#optional-arguments)
- [Project Configuration](#project-configuration)
  - [Formal definition of the generic configuration](#formal-definition-of-the-generic-configuration)
    - [`PROJECT`](#project)
    - [`supplement`](#supplement)
    - [`globalConfig.json`](#globalconfigjson)
    - [`addressSpaces*.json`](#addressspacesjson)
    - [`budgets.json`](#budgetsjson)
    - [`categoriesObjects.json` and `categoriesSections.json`](#categoriesobjectsjson-and-categoriessectionsjson)
    - [`categoriesObjectsKeywords.json` and `categoriesSectionsKeywords.json`](#categoriesobjectskeywordsjson-and-categoriessectionskeywordsjson)
  - [Formal Definition of the GHS compiler specific configuration](#formal-definition-of-the-ghs-compiler-specific-configuration)
    - [Extensions to the `globalConfig.json`](#extensions-to-the-globalconfigjson)
    - [`patterns*.json`](#patternsjson)
    - [`virtualSections*.json`](#virtualsectionsjson)
- [Output Files](#output-files)
  - [Section Summary](#section-summary)
  - [Object Summary](#object-summary)
  - [Objects in Sections](#objects-in-sections)
  - [CSV header](#csv-header)
- [Terminology](#terminology)
- [Examples](#examples)
  - [Matching object name and category using `categoriesKeywords.json`](#matching-object-name-and-category-using-categorieskeywordsjson)
  - [Removing not needed object names from `categoriesObjects.json`](#removing-not-needed-object-names-from-categoriesobjectsjson)
- [General Information About Map Files and Build Chains](#general-information-about-map-files-and-build-chains)
- [Technical Details](#technical-details)
  - [GHS Monolith file generation](#ghs-monolith-file-generation)
  - [Class diagram Emma](#class-diagram-emma)
  - [Calling Graph Emma](#calling-graph-emma)

------------------------

# Requirements
* Python 3.6 or higher
    * Tested with 3.6.1rc1; 3.7.0
* Python libraries
    * pypiscout 2.0 or higher: (`pip3 install pypiscout`)
* Tested on Windows and Linux systems


# Process
Using the Mapfile Analyser is a two step process. The first step is to extract the required information from the mapfiles and save it to .csv files.
This is done with the `emma.py` script. The second step is to visualise the data. This document explains the first part only, the visualisation is documented in the Emma visualiser readme document.

# Limitations
The Emma is only suitable for analyzing projects where the devices have a single linear physical address space:

* Devices that use for example the Intel 8051 architecture have separate code and data address spaces that both
    start at address 0x0000. Devices based on architectures like this can not be analyzed with Emma.
* Devices that use for example the ARMv6M architecture have a single linear address space.
    Devices based on architectures like this can be analyzed with Emma.

# Usage
Section and object summaries of the specified mapfiles will be created.

    $ python emma.py --help
    usage: Emma Memory and Mapfile Analyser (Emma) [-h] [--version] --project PROJECT
                                               --mapfiles MAPFILES [--dir DIR]
                                               [--subdir SUBDIR] [--analyse_debug]
                                               [--create_categories]
                                               [--remove_unmatched] [--noprompt]
                                               [--Werror]

    Analyser for mapfiles from Greens Hills Linker (other files are supported via
    configuration options).It creates a summary/overview about static memory usage
    in form of a comma separated values file.

    optional arguments:
      -h, --help           show this help message and exit
      --version            Display the version number.
      --project PROJECT    Path of directory holding the configuration.The project
                           name will be derived from the the name of this folder.
                           (default: None)
      --mapfiles MAPFILES  The folder containing the map files that need to be
                           analysed. (default: None)
      --dir DIR            Output folder holding the statistics. (default: None)
      --subdir SUBDIR      User defined subdirectory name in the --dir folder.
                           (default: None)
      --analyse_debug      Include DWARF debug sections in analysis (default:
                           False)
      --create_categories  Create categories.json from keywords. (default: False)
      --remove_unmatched   Remove unmatched modules from categories.json.
                           (default: False)
      --noprompt           Exit fail on user prompt. (default: False)
      --Werror             Treat all warnings as errors. (default: False)

    ********* Marcel Schmalzl, Felix Mueller, Gergo Kocsis - 2017-2019 *********


# Arguments
## Required Arguments

    --project PROJECT, -p PROJECT

    --mapfiles MAPFILES, --map MAPFILES

## Optional Arguments

* `--dir`
    * User defined path for the top folder holding the `memStats`/output files. Per default it uses the same directory as the config files.
* `--stats_dir`
  * User defined path inside the folder given in the `--dir` argument. This is usefull when batch analysing mapfiles from various development stages. Every analysis output gets it's own directory.
* `--create_categories`
  * Create `categories*.json` from `categories*Keywords.json` for easier categorisation.
* `--remove_unmatched`,
  * Remove unmatched entries from `categories*.json`. This is useful when a `categories*.json` from another project is used.
* `--analyse_debug`, `--dbg`
  * Normally we remove DWARF debug sections from the analysis to show the relevant information for a possible release software. This can be prevented if this argument is set. DWARF section names are defined in `stringConstants.py`. `.unused_ram` is always excluded (regardless of this flag)
* `--noprompt`
  * Exit and fail on user prompt. Normally this happens when some files or configurations are ambiguous. This is useful when running Emma on CI systems.


# Project Configuration

The memory analysis will be executed based on the project configuration. In order to be able to use Emma with your project, you need to create a configuration matching your project's hardware and software. **Configure Emma with high diligence since errors may lead to incorrect results of your analysis**. During the analysis Emma performs some sanity checks which helps you detecting misconfiguration.

This chapter explains the role and functionality of each part of the configuration and illustrates all the settings that can be used.
Based on this description the user will have to create his/her own configuration.

Creating a configuration is done by writing several JSON files (if you are not familiar with JSON, please visit https://www.json.org).
This chapter will go trough the topic by formally defining the format, rules and the functionality of the config files.
There are practical example projects available in the **doc** folder. These projects will lead you step by step trough the process of
creating a configuration and they also contain map files that can be analyzed.

Currently the following example projects are available:

* **doc/test_project** - A Test Project that illustrates a system with a hardware that consists of two devices: an MCU and an SOC.
Both of the devices have a GHS compiler specific configuration and mapfiles.

An Emma project configuration consists of two parts: the generic configuration and the compiler specific configuration.

## Formal definition of the generic configuration
The generic part of the configuration contains the following files:

    +-- [<PROJECT>]
    |   +-- [supplement]
    |   +-- globalConfig.json
    |   +-- addressSpaces*.json
    |   +-- budgets.json
    |   +-- categoriesObjects.json
    |   +-- categoriesObjectsKeywords.json
    |   +-- categoriesSections.json
    |   +-- categoriesSectionsKeywords.json
    |   +-- <COMPILER_SPECIFIC_CONFIGURATION_FILES>

The files containing the asterisk symbol can be freely named by the user because the actual file names will have to be
listed in the globalConfig.json.

### `PROJECT`
The configuration has to be contained by a folder. The name of the folder will be the name of the configuration.
From the files ending with a * symbol, the configuration can contain more than one but maximum up to the number of configIDs defined in globalConfig.json.

### `supplement`
You can add .md files into this folder with Markdown syntax to add information regarding your project that will be contained by the .html overview.
For more information please refer to the Emma Visualiser's documentation.

### `globalConfig.json`
The globalConfig.json is the starting point of a configuration, this file defines the **configId**-s.
The configId-s are the hardware units of the system that have memory associated to them, for example an MCU, MPU or an SOC.
During the analysis, it will be examined to which extent these memory resources are used.

For each configId, globalConfig.json assigns a compiler. This means that the mapfiles belonging to the configId were created by the selected compiler.
This is important, since the format of these files are specific to the compiler. For each configId an addressSpaces*.json config file will be assigned.
Furthermore the globalConfig.json assigns compiler specific config files to each configId, that need to be consistent with the selected compiler.
For example if a GHS compiler was selected to the configId, then the compiler specific configuration part of this configId have to fulfill the requirements
described in the [Formal Definition of the GHS compiler specific configuration](#formal-definition-of-the-GHS-compiler-specific-configuration) chapter.

The globalConfig.json has to have the following format:

    :::json
    {
        <CONFIG_ID>: {
            "compiler": <COMPILER_NAME>,
            "addressSpacesPath": <CONFIG_FILE>,
            "mapfiles": <MAPFILES_REL_PATH>,
            "ignoreConfigID": <BOOL>,
            <COMPILER_SPECIFIC_KEY_VALUE_PAIRS>
        },
        .
        .
        .
        <CONFIG_ID>: {
            "compiler": <COMPILER_NAME>,
            "addressSpacesPath": <CONFIG_FILE>,
            "mapfiles": <MAPFILES_REL_PATH>,
            "ignoreConfigID": <BOOL>,
            <COMPILER_SPECIFIC_KEY_VALUE_PAIRS>
        }
    }

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<CONFIG_ID>` is a string
    * `<COMPILER_NAME>` is a string
    * `<CONFIG_FILE>` is a string 
    * `<MAPFILES_REL_PATH>` is a string, with the special characters escaped in it
    * `<BOOL>` is a boolean value containing either **true** or **false**  
    * `<COMPILER_SPECIFIC_KEY_VALUE_PAIRS>` are the key-value pairs that are required by the selected compiler
* There has to be at least one **configID** defined
* You must select a compiler for every configID, by defining the **compiler** key. The possible values are:
    * "GHS" - Green Hills Compiler
* You must assign the following config files for each configID by defining the following key, value pairs:
    * by defining **addressSpacesPath**, the config file that defines the address spaces is assigned
    * The config files have to be in the same folder as the globalConfig.json
    * The config files don't need to be different for each configID (for example you can use the same address spaces config file for all the configIDs)
* The mapfiles:
    * specifies a folder **relative** to the one given via **--mapfiles** command line argument
    * is optional, if is defined for a configID, then the map files belonging to this configId will be searched for within this folder
    * Otherwise the mapfiles will be searched for in the **--mapfiles** root map file path
* The ignoreConfigID:
    * can be used to mark a configID as ignored, which means that this will not be processed during the analysis
    * is optional, it does not need to be included in every configID, leaving it has the same effect as including it with false

### `addressSpaces*.json`
The address spaces config files define the existing memory areas for the configIDs they were assigned to in the globalConfigs.json.

These config files have to have the following format:

    :::json
    {
        "offset": <ADDRESS>,
        "memory": {
            <MEMORY_AREA>: {
                "start": <ADDRESS>,
                "end": <ADDRESS>,
                "type": <MEMORY_TYPE>
            },
            .
            .
            .
            <MEMORY_AREA>: {
                "start": <ADDRESS>,
                "end": <ADDRESS>,
                "type": <MEMORY_TYPE>
            }
        },
        "ignoreMemory": [
            <MEMORY_AREA>, ... <MEMORY_AREA>
        ]
    }

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<ADDRESS>` is a string containing a 64bit hexadecimal value, for example "0x1FFFFFFF" 
    * `<MEMORY_AREA>` is a string containing a unique name
    * `<MEMORY_TYPE>` is a string containing one of the following values:
        * "INT_RAM" - internal RAM
        * "EXT_RAM" - external RAM
        * "INT_FLASH" - internal Flash
        * "EXT_FLASH" - external Flash     
* The **offset** is a global address offset applied to all addresses in the file
* **memory** is a JSON object that defines the memory areas
* Each memory area is a JSON object that has three elements:
    * start - start address
    * end - end address
    * type - memory type
* The **ignoreMemory** is a JSON array used to mark one or more `<MEMORY_AREA>` to be ignored during the analysis:
    * The the elements of this array can be selected from the ones defined in the "memory" object
    * It is optional, not including it or including it as an empty array means none of the `<MEMORY_AREA>`s are ignored

### `budgets.json`
The budgets config file belongs to the Emma Visualiser. For a description, please see: **doc/readme-vis.md**.

### `categoriesObjects.json` and `categoriesSections.json`
The categories config files are used to categorize objects and sections to user defined categories by using their full names.
These files are optional, if no categorization needed, these config files do not need to be created.
This function can be used for example to group the software components of one company together which will make the results easier to understand.

The `categoriesObjects.json` is used for the objects and the `categoriesSections.json` is  used for the section categorization.
The objects and sections will be first tried to be categorized by these files. If they could not be categorized, then the software will try
to categorize them based on the `categoriesObjectsKeywords.json` and `categoriesSectionsKeywords.json` files.

These config files have to have the following format:

    :::json
    {
        <CATEGORY>: [
            <NAME>,
            .
            .
            .
            <NAME>
        ],
        .
        .
        .
        <CATEGORY>: [
            <NAME>,
            .
            .
            .
            <NAME>
        ]
    }

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<CATEGORY>` is a string containing a unique category name
    * `<NAME>` is a string
* The categorisation can be done either by hand or with the **--create_categories** command line argument (for usage see there)
* The `<NAME>` has to contain full names of the sections or objects

### `categoriesObjectsKeywords.json` and `categoriesSectionsKeywords.json`
The categories keywords config files are used to categorize objects and sections to user defined categories by using only substrings of their names.
These files are optional, if no categorization needed, these config files do not need to be created.
This function can be used for example to group the software components of one company together which will make the results easier to understand.

The `categoriesObjectsKeywords.json` is used for the objects and the `categoriesSectionsKeywords.json` is  used for the section categorization.
The objects and sections will only tried to be categorized by these files if the categorization by the `categoriesObjects.json` and `categoriesSections.json` files failed.
If they could not be categorized, then the software will assign them to a category called `<Emma_UnknownCategory>` so they will be more visible in the results.

These config files have to have the following format:

    :::json
    {
        <CATEGORY>: [
            <KEYWORD>,
            .
            .
            .
            <KEYWORD>
        ],
        <CATEGORY>: [
            <KEYWORD>,
            .
            .
            .
            <KEYWORD>
        ]
    }

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<CATEGORY>` is a string containing a unique category name
    * `<KEYWORD>` is a string
* The categorisation has to be done by hand
* The `<KEYWORD>` contains a regex pattern for the names of the sections or objects

## Formal Definition of the GHS compiler specific configuration
The GHS compiler specific part of the configuration contains the following files:

    +-- [<PROJECT>]
    |   +-- <GENERIC_CONFIGURATION_FILES>
    |   +-- patterns*.json
    |   +-- virtualSections*.json

The following dependencies exist within this type of a configuration:

<div align="center"> <img src="./images/configDependencies.png" width="100%"> </div>

In `globalConfig.json`, you need to reference (ref relations on the picture):

1. `addressSpaces*.json`
2. `patterns*.json`
3. `sections*.json`

`memRegionExcludes`: You can exclude certain memory regions with this keyword in `patterns*.json`. In order to do this the memory regions/tags must match with those defined in `addressSpaces*.json`.

If you have virtual address spaces (VASes) defined. You need a `"monolith file"` pattern defined in `patterns*.json` in order to be able to translate virtual addresses back to physical addresses. In the same file you give each VAS a name. This name is later used to identify which section belongs to which VAS (defined in `virtualSections*.json`). The VAS names must match between those two files. This is needed in order to avoid name clashes of sections names between different VASes.

### Extensions to the `globalConfig.json`

The globalConfig.json has to have the following format **for configId-s that have selected "GHS" as compiler**:

    :::json
    {
        <CONFIG_ID>: {
            <GENERIC_KEY_VALUE_PAIRS>,
            "patternsPath": <CONFIG_FILE>,
            "virtualSectionsPath": <CONFIG_FILE>
        },
        .
        .
        .
        <CONFIG_ID>: {
            <GENERIC_KEY_VALUE_PAIRS>,
            "patternsPath": <CONFIG_FILE>,
            "virtualSectionsPath": <CONFIG_FILE>
        }
    }

The following rules apply:

* The types used in the description:
    * `<GENERIC_KEY_VALUE_PAIRS>` are the key-value pairs discussed in the [Formal definition of the generic configuration](#formal-definition-of-the-generic-configuration) chapter
    * `<CONFIG_FILE>` is a string
* You must assign a patterns config file for each configID by defining the **patternsPath** key
* If the configId contains virtual address spaces, you must assign a config file describing them by defining **virtualSectionsPath** key
* The assigned config files have to be in the same folder as the globalConfig.json
* The config files don't need to be different for each configID (for example you can use the same virtual sections config file for all the configIDs)

### `patterns*.json`
The patterns config files define regex patterns for finding the mapfiles, monolith files and processing their content.
They belong to the `configID` they were assigned to in the `globalConfigs.json`.

These config files have to have the following format:

    :::json
    {
        "mapfiles": {
            <SW_NAME>: {
                "regex": [<REGEX_PATTERN>, ... <REGEX_PATTERN>],
                "VAS": <VAS_NAME>,
                "UniquePatternSections": <REGEX_PATTERN>,
                "UniquePatternObjects": <REGEX_PATTERN>,
                "memRegionExcludes": [<MEMORY_AREA>, ... <MEMORY_AREA>]
            },
            .
            .
            .
            <SW_NAME>: {
                "regex": [<REGEX_PATTERN>, ... <REGEX_PATTERN>],
                "VAS": <VAS_NAME>,
                "UniquePatternSections": <REGEX_PATTERN>,
                "UniquePatternObjects": <REGEX_PATTERN>,
                "memRegionExcludes": [<MEMORY_AREA>, ... <MEMORY_AREA>]
            },
        },
        "monoliths": {
            "<MONILITH_NAME>": {
                "regex": [<REGEX_PATTERN>, ... <REGEX_PATTERN>]
            }
        }
    }

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<SW_NAME>` is a string containing a unique name
    * `<REGEX_PATTERN>` is a string containing a regex pattern following the format used by the "re" Python library
    * `<VAS_NAME>` is a string
    * `<MONOLITH_NAME>` is a string containing a unique name
* The **mapfiles** object must be present in the file with at least one entry:
    * Each entry describes a SW unit of the configId (eg. a bootloader or application if an MCU is used or a process if an OS, like Linux is used):
        * The **regex** defines one ore more regex pattern to find the mapfile that contains the data for this SW unit:
            * It is possible to give more than one regex patterns in case of non-uniform mapfile names
            * If more than one map file will be found for the SW unit, a warning will be thrown
            * The search will be done in the mapfile folder defined by the command line arguments
        * The **VAS** is optional element, defining the name of the virtual address space of this SW unit
            * It is only required if the SW unit has entries that belong to virtual address spaces
            * More than one mapfiles can contain data belonging to one virtual address space, so the VAS name does not need to be unique
        * The **UniquePatternSections** is an optional element defining a regex pattern for collecting the sections from the mapfile
            * It only needs to be defined if the default regex pattern has to be overridden
            * This can be necessary if the toolchain where the mapfile coming from, produces another format
        * The **UniquePatternObjects** is an optional element defining a regex pattern for collecting the objects from the mapfile
            * It only needs to be defined if the default regex pattern has to be overridden
            * This can be necessary if the toolchain where the mapfile coming from, produces another format
        * The **memRegionExcludes** lists the memory areas that needs to be ignored during the analysis of the mapfile
            * The sections and objects of the mapfile that belong to the memory areas listed here will be ignored
            * The memory areas can be selected from the <MEMORY_AREA> elements defined in the "memory" object of address spaces config file
* The **monoliths** object is optional, it is only needed if the configId has virtual address spaces
    * If one the of the mapfiles object has a VAS key, then a monolith is needed
    * It is possible to give more than one regex patterns in case of non-uniform monolith file names
    * If more than one monolith file will be found for the SW unit, a warning will be thrown
    * The search will be done in the mapfile folder defined by the command line arguments

### `virtualSections*.json`
The virtual sections config files are used to assign the sections of the virtual address spaces to
a virtual address spaces defined in the `patterns*.json`file. This is needed because the mapfiles can contain physical
and virtual sections as well and Emma needs to identify the virtual ones and assign them to a specific virtual address space.
If your configuration does not use virtual address spaces, the `virtualSections*.json` file is not needed.

This config file have to have the following format:

    :::json
    {
        <VAS_NAME>: [
            <SECTION_NAME>,
            .
            .
            .
            <SECTION_NAME>
        ],
        ...
        <VAS_NAME>: [
            <SECTION_NAME>,
            .
            .
            .
            <SECTION_NAME>
        ]
    }

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<VAS_NAME>` is a string
    * `<SECTION_NAME>` is a string
* The `<VAS_NAME>` keys are the ones that were defined in the `patterns*.json`
* Every `<VAS_NAME>` key has an array as value that lists the sections that belong to the virtual address space 
* There are no rules for the assignment, this needs to be done intuitively based on the project being analyzed

# Output Files
The output Files will be saved to the memStats folder of the respective project. The filename will have this form: 

    :::bash
    <PROJECT_NAME>_Section_Summary_TIMESTAMP.csv
    <PROJECT_NAME>_Object_Summary_TIMESTAMP.csv
    <PROJECT_NAME>_Objects_in_Sections_TIMESTAMP.csv

## Section Summary

The file `<PROJECT_NAME>_Section_Summary_<TIMESTAMP>.csv` contains the sections from the mapfiles.

## Object Summary

The file `<PROJECT_NAME>_Object_Summary_<TIMESTAMP>.csv` contains the objects from the mapfiles.

## Objects in Sections
"Objects in sections" provides ways to obtain a finer granularity of the categorisation result. Therefore categorised sections containing (smaller) objects of a different category got split up and result into a more accurate categorisation. As a result you will get output files in form of a `.csv` file which sets you up to do later processing on this data easily. In this file additional information is added like:

* Overlaps (of sections/objects)
* Containments (e.g. sections containing objects)
* Duplicates
* All meta data about the origin of each section/object (mapfile, addess space, ...)
* ...

<div align="center"> <img src="./images/objectsInSections.png" width="90%"> </div>

The file `<PROJECT_NAME>_Objects_in_Sections_<TIMESTAMP>.csv` is the result of the "merge" of the objects and the sections file.

Objects/sections that are "touching" or overlapping each other in some way (see the above figure) are resolved in this step. Therefore the "weaker" section/object is split (and has therefore a reduced by size after each step).

This is done so that the file represents a continuous and refined memory mapping. Furthermore it is checked whether sections/objects overlap, contain or duplicate each other.

The information on such occurrences can be observed in the rightmost columns:

* `overlapFlag`: Overlaps with the stated section ("overlapped by X" means X is an object/section which has a lower start address and therefore overlaps the current element)
* `containmentFlag`: Is contained by the stated section
* `duplicateFlag`: Duplicate entry
* `containgOthers`: Contains stated sections/objects
* `addrStartHexOriginal`: Address before correction (in contrast to the "new" addresses due to the above actions)
* `addrEndHexOriginal`: Address before correction (in contrast to the "new" addresses due to the above actions)

The above figure also shows how sizes of objects/sections are calculated correctly (-> namely: `start - end + 1`). Besides this a specific case of an overlap is shown above. A section/object having the same end address like the start address of another section/object. This happens to be already an overlap of one byte.

As a result you see the `+ 1` addition for the size calculation.
This might sound counter-intuitive at the first spot. However we can see memory addresses as memory blocks itself rather than infinitesimal barriers (what the term start and end address would intuitively suggest by its name).

At the end you will find three remaining "types":

1. **Real objects:** (Un)modified objects due to the above actions
2. **Section reserves:** Resolved sections minus resolved objects; this is what remains when you resolve all "touching" occurrences and subtract objects from sections that we obtain (multiple) smaller sections
3. **Section entry:** The original section size (without any modification); this is a pure virtual entry and has a size of `0` bytes; these are the only `0` byte sections which are a result of the Emma processing

Section names for section reserves and entries are `<Emma_SectionReserve>` and `<Emma_SectionEntry>` respectively. The `<Emma_xxxx>` pattern shows you names introduced by Emma.

## CSV header
The CSV file has the following columns:

* The address start, end and sizes: `addrStartHex; addrEndHex; sizeHex; addrStartDec; addrEndDec; sizeDec; sizeHumanReadable`
* The section and object name: `sectionName; moduleName` Note: If the image summary contains only sections, the column moduleName will be left empty.
* `configID`, `memType` and `tag` are from the config files.
* `vasName` is the virtual address space name defined in sections.json. The `DMA` field indicates whether a section/object is in a VAS. 
* `category`: The category evaluated from categories*.json
* `mapfile`: The mapfile, the entry originates from.
* `overlapFlag`: Indicates whether one section overlaps with another.
* `containmentFlag`: Indicates whether a section is contained in another.
* `duplicateFlag`: Indicates whether a section has duplicates.

# Terminology
In places there is some specific terminology used which is explained in the following chapter:

* DMA: Direct Memory Addressing; addresses which do not have to be translated (from virtual to physical); this has nothing to do with direct access to memory on the target (by bypassing the CPU core(s))
* Emma was formerly known as MAdZ

# Examples
Create a Mapfile Summary for <PROJECT>:

    :::bash
    emma.py --project ..\<PROJECT> \
    --mapfiles ..\MyMapfiles \
    --dir ..\MyMapfiles\results

## Matching object name and category using `categoriesKeywords.json`
`categoriesObjectsKeywords.json` can be used to match object names with catgories by user defined keywords.

* Arguments required:  ```--create_categories```
* This step will append the newly categorised modules to `categories.json`. The program will ask you to confirm to overwrite the file.

## Removing not needed object names from `categoriesObjects.json`
Not needed object names can be removed from `categoriesObjects.json`, for example when `categoriesObjects.json` from another project is used.

* Arguments required:  ```--remove_unmatched```
* This step will remove never matching object names from `categoriesObjects.json`. Some modules never match because e.g. the object got removed or is not present in the current release. The program will ask you to confirm to overwrite the file.


# General Information About Map Files and Build Chains
* [COMPILER, ASSEMBLER, LINKER AND LOADER: A BRIEF STORY](http://www.tenouk.com/ModuleW.html)
* [Hello World: C, Assembly, Object File and Executable](http://resources.infosecinstitute.com/hello-world-c-assembly-object-file-and-executable)
* [Analyzing the Linker Map file with a little help from the ELF and the DWARF](https://www.embeddedrelated.com/showarticle/900.php)
* [Anatomy of a Program in Memory](http://duartes.org/gustavo/blog/post/anatomy-of-a-program-in-memory)
* [Memory Management: Paging](https://www.cs.rutgers.edu/~pxk/416/notes/10-paging.html)
* [Beginner's Guide to Linkers](http://www.lurklurk.org/linkers/linkers.html)
* [Linker Scripts](http://www.scoberlin.de/content/media/http/informatik/gcc_docs/ld_3.html)


# Technical Details
## GHS Monolith file generation
Execute this to generate the monolith files (you need to have the ELF file for this step).

    :::bash
    gdump.exe -virtual_mapping -no_trunc_sec_names Application.elf >> monolith.map
    gdump.exe -map             -no_trunc_sec_names Application.elf >> monolith.map

By default long names will be truncated. This can lead to inaccurate results. In order to prevent this use `-no_trunc_sec_names`.

## Class diagram Emma
<div align="center"> <img src="images/emmaClassDiagram.png" width="1000"> </div>

## Calling Graph Emma
<div align="center"> <img src="../genDoc/call_graph_uml/emma_filtered.profile.png" width="1000"> </div>
