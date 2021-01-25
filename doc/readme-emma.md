# Emma
**Emma Memory and Mapfile Analyser**

> Conduct static (i.e. worst case) memory consumption analyses based on linker map files (currently only Green Hills map files are supported).
This tool creates a summary/overview about static memory usage in form of a comma separated values (CSV) file.


## Requirements
* Python 3.6 or higher
* Python libraries
    * pypiscout 2.0 or higher: (`pip3 install pypiscout`)
* Tested on Windows and Linux systems

<details closed>
<summary>Optional: Cython</summary>
For bigger projects escpecially the number of objects will grow. We provide an optional Cython implementation which can speed-up your analysis (you will gain typically about **30 % speed-up**).

For now we do not provide the binaries with Emma, hence you have to compile (make sure a suitable compiler is installed) it yourself (don't worry it is quick and easy):

Install the `Cython` package (`pip install Cython`) and (in the Emma top level folder) execute (MSVC is recommended on Windows):

```
python setup.py build_ext --inplace --compiler=msvc
```
</details>


## Process
Using the Mapfile Analyser is a two step process. The first step is to extract the required information from the mapfiles and save it to .csv files.
This is done with the `Emma.py a` script. The second step is to visualise the data. This document explains the first part only, the visualisation is documented in the Emma visualiser readme document.

## Limitations
The devices must have a single linear physical address space:

* Devices that use for example an Intel 8051 architecture have separate code and data address spaces that both start at address `0x0000`. Devices based on architectures like this can not entirely analysed with Emma.
* Devices that use for example the ARMv6M architecture have a single linear address space.
    Devices based on architectures like this can be analysed with Emma.


## Arguments
### Required Arguments

    --project PROJECT, -p PROJECT

    --mapfiles MAPFILES, --map MAPFILES

### Some Optional Arguments
This section will provide a more in-depth description about selected command line arguments when a short description (like in `--help`) might be to short, the behaviour is too complex or background knowledge might assist you to understand the whole picture. For the full list execute Emma with `--help`.

* `--dir`
    * User defined path for the top folder holding the `memStats`/output files. Per default it uses the same directory as the configuration files.
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
* `--memVis`
    * This is a visualisation based on data you actually see in the map files (i.e. the data *before* the containment/duplicate/overlap resolution)
    * Prompts for a start and end address (and x/y scaling) for which memory region a visualisation should be created (as `.svg`)
    * This visualisation allows to better see complex overlaps/alignments of objects/sections (e.g. check your linker configuration, ...)
    * Note that huge address ranges containing many objects/sections may cause your viewer to get slow/unresponsive due to the high amount of objects/sections; it is recommended to keep your viewing area small
    * For huge `.svg`s the authors made good experiences with Inkscape and Google Chrome
    * Usually you detect an interesting scenario in the `.csv` reports. It might be hard to see what is actually happening (e.g. many overlaps/containments, ...). That is where a visualisation is helpful
    * If `--noPrompt` is active you will get a weak warning that no `.svg` reports will be generated
        <div align="left"> <img src="./images/memVis.png" width="50%"> </div>
* `--memVisResolved`
    * Basically the same as `--memVis` but plots the *resolved* view (i.e. after Emma resolved the containment/duplicate overlap -> basically you will see what stands in `Objects_in_Sections`)
    * Skipped if `--noResolveOverlap` is active


## Project Configuration

The memory analysis will be executed based on the project configuration. In order to be able to use Emma with your project, you need to create a configuration matching your project's hardware and software. **Configure Emma with high diligence since errors may lead to incorrect results of your analysis**. During the analysis Emma performs some sanity checks which helps you detecting misconfiguration.

This chapter explains the role and functionality of each part of the configuration and illustrates all the settings that can be used.
Based on this description the user will have to create his/her own configuration.

Creating a configuration is done by writing several JSON files (if you are not familiar with JSON, please visit [https://www.json.org](https://www.json.org)).
This chapter will go trough the topic by formally defining the format, rules and the functionality of the configuration files.
There are practical example projects available in the **`doc`** folder. These projects will lead you step by step trough the process of
creating a configuration and they also contain map files that can be analysed.

Currently the following example projects are available:

* **`doc/test_project`** - A project that illustrates a system with a hardware that consists of two devices: an MCU and an SOC.
Both of the devices have a GHS compiler specific configuration and mapfiles.

An Emma project configuration consists of two parts: the generic configuration and the compiler specific configuration.

### Formal definition of the generic configuration
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

#### `PROJECT`
The configuration has to be contained by a folder. The name of the folder will be the name of the configuration.
From the files ending with a * symbol, the configuration can contain more than one but maximum up to the number of configIDs defined in globalConfig.json.

#### `supplement`
You can add .md files into this folder with Markdown syntax to add information regarding your project that will be contained by the .html overview.
For more information please refer to the Emma Visualiser's documentation.

#### `globalConfig.json`
The globalConfig.json is the starting point of a configuration, this file defines the **configId**-s.
The configId-s are the hardware units of the system that have memory associated to them, for example an MCU, MPU or an SOC.
During the analysis, it will be examined to which extent these memory resources are used.

For each configId, globalConfig.json assigns a compiler. This means that the mapfiles belonging to the configId were created by the selected compiler.
This is important, since the format of these files are specific to the compiler. For each configId an addressSpaces*.json configuration file will be assigned.
Furthermore the globalConfig.json assigns compiler specific configuration files to each configId, that need to be consistent with the selected compiler.
For example if a GHS compiler was selected to the configId, then the compiler specific configuration part of this configId have to fulfill the requirements
described in the [Formal Definition of the GHS compiler specific configuration](#formal-definition-of-the-GHS-compiler-specific-configuration) chapter.

The globalConfig.json has to have the following format:

```json
{
    "<CONFIG_ID>": {
        "compiler": "<COMPILER_NAME>",
        "addressSpacesPath": "<CONFIG_FILE>",
        "mapfiles": "<MAPFILES_REL_PATH>",
        "ignoreConfigID": "<BOOL>",
        <COMPILER_SPECIFIC_KEY_VALUE_PAIRS>
    },
    .
    .
    .
    "<CONFIG_ID>": {
        "compiler": "<COMPILER_NAME>",
        "addressSpacesPath": "<CONFIG_FILE>",
        "mapfiles": "<MAPFILES_REL_PATH>",
        "ignoreConfigID": "<BOOL>",
        <COMPILER_SPECIFIC_KEY_VALUE_PAIRS>
    }
}
```

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
* You must assign the following configuration files for each configID by defining the following key, value pairs:
    * by defining **addressSpacesPath**, the configuration file that defines the address spaces is assigned
    * The configuration files have to be in the same folder as the globalConfig.json
    * The configuration files don't need to be different for each configID (for example you can use the same address spaces configuration file for all the configIDs)
* The mapfiles:
    * specifies a folder **relative** to the one given via **--mapfiles** command line argument
    * is optional, if is defined for a configID, then the map files belonging to this configId will be searched for within this folder
    * Otherwise the mapfiles will be searched for in the **--mapfiles** root map file path
* The ignoreConfigID:
    * can be used to mark a configID as ignored, which means that this will not be processed during the analysis
    * is optional, it does not need to be included in every configID, leaving it has the same effect as including it with false

#### `addressSpaces*.json`
The address spaces configuration files define the existing memory areas for the configIDs they were assigned to in the globalConfigs.json.

These configuration files have to have the following format:

```json
{
    "offset": "<ADDRESS>",
    "memory": {
        "<MEMORY_AREA>": {
            "start": "<ADDRESS>",
            "end": "<ADDRESS>",
            "type": "<MEMORY_TYPE>"
        },
        .
        .
        .
        "<MEMORY_AREA>": {
            "start": "<ADDRESS>",
            "end": "<ADDRESS>",
            "type": "<MEMORY_TYPE>"
        }
    },
    "ignoreMemory": [
        "<MEMORY_AREA>", ... "<MEMORY_AREA>"
    ]
}
```

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
* **offset**: a global address offset applied to addresses of all memories. If the address is non-virtual (=> DMA) the offset is subtracted from it otherwise normal address translation (virtual -> physical) is applied.
* **memory** is a JSON object that defines the memory areas
* Each memory area is a JSON object that has three elements:
    * start - start address
    * end - end address
    * type - memory type
* The **ignoreMemory** is a JSON array used to mark one or more `<MEMORY_AREA>` to be ignored during the analysis:
    * The the elements of this array can be selected from the ones defined in the "memory" object
    * It is optional, not including it or including it as an empty array means none of the `<MEMORY_AREA>`s are ignored

#### `budgets.json`
The budgets configuration file belongs to the Emma Visualiser. For a description, please see: **`doc/readme-vis.md`**.

#### `categoriesObjects.json` and `categoriesSections.json`
The categories configuration files are used to categorise objects and sections to user defined categories by using their *full names*.
These files are optional. If no categorisation is needed, these configuration files do not need to be created.
This function can be used for example to group the software components together which will make the results easier to understand and aggregate.

The `categoriesObjects.json` is used for the objects and the `categoriesSections.json` is  used for the section categorisation.

1. The objects and sections will be first tried to be categorised by these files.
2. If they could not be categorised, their categorie will be marked as unknown.

These configuration files have to have the following format:

```json
{
    "<CATEGORY>": [
        "<NAME>",
        .
        .
        .
        "<NAME>"
    ],
    .
    .
    .
    "<CATEGORY>": [
        "<NAME>",
        .
        .
        .
        "<NAME>"
    ]
}
```

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<CATEGORY>` is a string containing a unique category name
    * `<NAME>` is a string
* The categorisation can be done either by hand or with the **--create_categories** command line argument (for usage see there)
* The `<NAME>` has to contain full names of the sections or objects

#### `categoriesObjectsKeywords.json` and `categoriesSectionsKeywords.json`
The categories keywords configuration files are used to categorise objects and sections to user defined categories by using *substrings* of their names.
These files are *optional*. If no categorisation is needed, these configuration files do not need to be created.

The `categoriesObjectsKeywords.json` is used for the objects and the `categoriesSectionsKeywords.json` is  used for the section categorisation.
If no matching category keywords was found the software will assign them to a category called `<Emma_UnknownCategory>`.

These configuration files have to have the following format:

```json
{
    "<CATEGORY>": [
        "<KEYWORD>",
        .
        .
        .
        "<KEYWORD>"
    ],
    "<CATEGORY>": [
        "<KEYWORD>",
        .
        .
        .
        "<KEYWORD>"
    ]
}
```

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<CATEGORY>` is a string containing a unique category name
    * `<KEYWORD>` is a string
* The categorisation has to be done by hand
* The `<KEYWORD>` contains a regex pattern for the names of the sections or objects

### Formal Definition of the GHS compiler specific configuration
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

If you have virtual address spaces (VASes) defined. You need a "monolith file" pattern defined in `patterns*.json` in order to be able to translate virtual addresses back to physical addresses. In the same file you give each VAS a name. This name is later used to identify which section belongs to which VAS (defined in `virtualSections*.json`). *The VAS names must match between those two files.* This is needed in order to avoid name clashes of sections names between different VASes.

If you are unsure what VASes you have check out the `.int` ("integrate") files (the `.ael` files might also be of your interest).


#### Extensions to the `globalConfig.json`

The globalConfig.json has to have the following format **for configId-s that have selected "GHS" as compiler**:

```json
{
    "<CONFIG_ID>": {
        <GENERIC_KEY_VALUE_PAIRS>,
        "patternsPath": "<CONFIG_FILE>",
        "virtualSectionsPath": "<CONFIG_FILE>"
    },
    .
    .
    .
    "<CONFIG_ID>": {
        <GENERIC_KEY_VALUE_PAIRS>,
        "patternsPath": "<CONFIG_FILE>",
        "virtualSectionsPath": "<CONFIG_FILE>"
    }
}
```

The following rules apply:

* The types used in the description:
    * `<GENERIC_KEY_VALUE_PAIRS>` are the key-value pairs discussed in the [Formal definition of the generic configuration](#formal-definition-of-the-generic-configuration) chapter
    * `<CONFIG_FILE>` is a string
* You must assign a patterns configuration file for each configID by defining the **patternsPath** key
* If the configId contains virtual address spaces, you must assign a configuration file describing them by defining **virtualSectionsPath** key
* The assigned configuration files have to be in the same folder as the globalConfig.json
* The configuration files don't need to be different for each configID (for example you can use the same virtual sections configuration file for all the configIDs)

#### `patterns*.json`
The patterns configuration files define regex patterns for finding the mapfiles, monolith files and processing their content.
They belong to the `configID` they were assigned to in the `globalConfigs.json`.

These configuration files have to have the following format:

```json
{
    "mapfiles": {
        "<SW_NAME>": {
            "regex": ["<REGEX_PATTERN>", ... "<REGEX_PATTERN>"],
            "VAS": "<VAS_NAME>",
            "UniquePatternSections": "<REGEX_PATTERN>",
            "UniquePatternObjects": "<REGEX_PATTERN>",
            "memRegionExcludes": ["<MEMORY_AREA>", ... "<MEMORY_AREA>"]
        },
        .
        .
        .
        "<SW_NAME>": {
            "regex": ["<REGEX_PATTERN>", ... "<REGEX_PATTERN>"],
            "VAS": "<VAS_NAME>",
            "UniquePatternSections": "<REGEX_PATTERN>",
            "UniquePatternObjects": "<REGEX_PATTERN>",
            "memRegionExcludes": ["<MEMORY_AREA>", ... "<MEMORY_AREA>"]
        },
    },
    "monoliths": {
        "<MONILITH_NAME>": {
            "regex": ["<REGEX_PATTERN>", ... "<REGEX_PATTERN>"]
        }
    }
}
```

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
            * The memory areas can be selected from the <MEMORY_AREA> elements defined in the "memory" object of address spaces configuration file
* The **monoliths** object is optional, it is only needed if the configId has virtual address spaces
    * If one the of the mapfiles object has a VAS key, then a monolith is needed
    * It is possible to give more than one regex patterns in case of non-uniform monolith file names
    * If more than one monolith file will be found for the SW unit, a warning will be thrown
    * The search will be done in the mapfile folder defined by the command line arguments

#### `virtualSections*.json`
The virtual sections configuration files are used to assign the sections of the virtual address spaces to
a virtual address spaces defined in the `patterns*.json`file. This is needed because the mapfiles can contain physical
and virtual sections as well and Emma needs to identify the virtual ones and assign them to a specific virtual address space.
If your configuration does not use virtual address spaces, the `virtualSections*.json` file is not needed.

This configuration file have to have the following format:

```json
{
    "<VAS_NAME>": [
        "<SECTION_NAME>",
        .
        .
        .
        "<SECTION_NAME>"
    ],
    ...
    "<VAS_NAME>": [
        "<SECTION_NAME>",
        .
        .
        .
        "<SECTION_NAME>"
    ]
}
```

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<VAS_NAME>` is a string
    * `<SECTION_NAME>` is a string
* The `<VAS_NAME>` keys are the ones that were defined in the `patterns*.json`
* Every `<VAS_NAME>` key has an array as value that lists the sections that belong to the virtual address space 
* There are no rules for the assignment, this needs to be done intuitively based on the project being analysed

## Output Files
The output Files will be saved to the memStats folder of the respective project. The filename will have this form: 

```bash
<PROJECT_NAME>_Section_Summary_TIMESTAMP.csv
<PROJECT_NAME>_Object_Summary_TIMESTAMP.csv
<PROJECT_NAME>_Objects_in_Sections_TIMESTAMP.csv
```

### Section Summary
The file `<PROJECT_NAME>_Section_Summary_<TIMESTAMP>.csv` contains the sections from the mapfiles.

### Object Summary
The file `<PROJECT_NAME>_Object_Summary_<TIMESTAMP>.csv` contains the objects from the mapfiles.

### Overlap resolution
Generally all overlaps will get resolved by Emma with default settings. However Objects in Sections can be disabled via command line argument. The general process works as follows:

Objects/sections that are "touching" or overlapping each other in some way (see the above figure) are resolved in all three reports (object summary, section summary and "Objects in Sections"). Therefore the "weaker" section/object is split (and has therefore a reduced by size after each step). A section/object is considered "weaker" if its *start* address is higher.

<div align="center"> <img src="images/objectsInSectionsResolution.png" width="800"> </div>

1. All overlaps between sections and sections are resolved and between objects and objects. This will be the results of two reports.
2. Then they will be merged together which will result in "Objects in Sections". This results in the third report created by Emma. Here some "virtual" sections are introduced and overlaps between sections and objects are considered.

As a result you will get output files in form of a `.csv` file which sets you up to do later processing on this data easily.

#### Objects in Sections
"Objects in sections" provides ways to obtain a finer granularity of the categorisation result. Therefore categorised sections containing (smaller) objects of a different category got split up and result into a more accurate categorisation. In this `.csv` file additional information is added like:

* Overlaps (of sections/objects)
* Containments (e.g. sections containing objects)
* Duplicates
* All meta data about the origin of each section/object (mapfile, addess space, ...)
* ...

<div align="center"> <img src="./images/objectsInSections.png" width="90%"> </div>

The file `<PROJECT_NAME>_Objects_in_Sections_<TIMESTAMP>.csv` is the result of the "merge" of the objects and the sections file.

The information on such occurrences can be observed in columns of the Emma report:

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
2. **Section reserves (`<Emma_SectionReserve>`):** Resolved sections minus resolved objects. A section that describes the unused part of a section that was not filled up with objects. This is what remains when you resolve all "touching" occurrences and subtract objects from sections that we obtain (multiple) smaller sections
3. **Section entry (`<Emma_SectionEntry>`):** The original section size (without any modification); this is a pure virtual entry and has a size of `0` bytes; these are the only `0` byte sections which are a result of the Emma processing. Note that section-section overlaps might (depending on the chosen Emma command line flags) already be resolved at this stage and are considered as original section size.

Section names for section reserves and entries are `<Emma_SectionReserve>` and `<Emma_SectionEntry>` respectively. The `<Emma_xxxx>` pattern shows you names introduced by Emma.

### CSV header
The CSV file has the following columns:

* The address start, end and sizes: `addrStartHex; addrEndHex; sizeHex; addrStartDec; addrEndDec; sizeDec; sizeHumanReadable`
* The section and object name: `sectionName; moduleName` Note: If the image summary contains only sections, the column moduleName will be left empty.
* `configID`, `memType` and `tag` are from the configuration files.
* `vasName` is the virtual address space name defined in sections.json. The `DMA` field indicates whether a section/object is in a VAS. 
* `category`: The category evaluated from categories*.json
* `mapfile`: The mapfile, the entry originates from.
* `overlapFlag`: Indicates whether one section overlaps with another.
* `containmentFlag`: Indicates whether a section is contained in another.
* `duplicateFlag`: Indicates whether a section has duplicates.

## Terminology
In places there is some specific terminology used which is explained in the following chapter:

* DMA: Direct Memory Addressing; addresses which do not have to be translated (from virtual to physical); this has nothing to do with direct access to memory on the target (by bypassing the CPU core(s))
* Emma was formerly known as MAdZ

## Examples
Create a Mapfile Summary for <PROJECT>:

```bash
Emma.py a --project ..\<PROJECT> \
--mapfiles ..\MyMapfiles \
--dir ..\MyMapfiles\results
```

### Matching object name and category using `categoriesKeywords.json`
`categoriesObjectsKeywords.json` can be used to match object names with catgories by user defined keywords.

* Arguments required:  ```--create_categories```
* This step will append the newly categorised modules to `categories.json`. The program will ask you to confirm to overwrite the file.

### Removing not needed object names from `categoriesObjects.json`
Not needed object names can be removed from `categoriesObjects.json`, for example when `categoriesObjects.json` from another project is used.

* Arguments required:  ```--remove_unmatched```
* This step will remove never matching object names from `categoriesObjects.json`. Some modules never match because e.g. the object got removed or is not present in the current release. The program will ask you to confirm to overwrite the file.


## General Information About Map Files and Build Chains
* [COMPILER, ASSEMBLER, LINKER AND LOADER: A BRIEF STORY](http://www.tenouk.com/ModuleW.html)
* [Hello World: C, Assembly, Object File and Executable](http://resources.infosecinstitute.com/hello-world-c-assembly-object-file-and-executable)
* [Analyzing the Linker Map file with a little help from the ELF and the DWARF](https://www.embeddedrelated.com/showarticle/900.php)
* [Anatomy of a Program in Memory](http://duartes.org/gustavo/blog/post/anatomy-of-a-program-in-memory)
* [Memory Management: Paging](https://www.cs.rutgers.edu/~pxk/416/notes/10-paging.html)
* [Beginner's Guide to Linkers](http://www.lurklurk.org/linkers/linkers.html)
* [Linker Scripts](http://www.scoberlin.de/content/media/http/informatik/gcc_docs/ld_3.html)


## Technical Details
### GHS
#### Monolith files
##### Generation
Execute this to generate the monolith files (you need to have the ELF file for this step).

```bash
gdump.exe -virtual_mapping -no_trunc_sec_names Application.elf >> monolith.map
gdump.exe -map             -no_trunc_sec_names Application.elf >> monolith.map
```

By default long names will be truncated. This can lead to inaccurate results. In order to prevent this use `-no_trunc_sec_names`. If you get very high physical addresses it is probable that device trees are used in your project (see below).

##### Device Trees
Device Trees are present since Integrity version 11.7.6 (sometimes this can be found in older versions too if it was back ported). Those are similar to those known from the Linux world (e.g. `.dtb`s and `.dts` files). Only the bootloader process is done a lot less complex than in Linux.

Usually an offset of `0xffffffa000000000` (to be sure check a line like `ram_memory : ORIGIN = 0xffffffa000000000,` in the `default.ld` linker file) is added. You can see that in the `gdump` output.
In order to get the device tree - and therefore the real physical addresses of your hardware - it is helpful to decompile the correct `.dtb` (depending on your hardware variant) file:

```bash
dtc -I dtb -O dts dev-tree.dtb > decompiled-dev-tree.dts
```

### GHS map command converter
If you allocate memory dynamically during runtime you would like to analyse that state and a strict static analysis is not very useful since you miss out a lot of memory which is indeed allocated but you cannot see it in the static view.

To solve this problem you can do the following:

1. Run the GHS `map` command on the target during a debug session
2. Save the output
3. Convert it via the Emma `tools/ghs-map-converter` to a GHS mapfile alike format
4. and add it as a map file in the Emma config
    1. The addresses of the map command are physical - no address translation / VAS needs to be configured
    2. Note: In combination with device trees you will loose information (and potentialy you have to add a pseudo memory region like stated below) since it cannot be mapped to the physical hardware anymore since you get only virtual dummy addresses from `gdump.exe -virtual_mapping` command.

The dummy entry of `addressSpaces*.json` may look like this:

```json
"memory": {
    "Pseudo_Memory": {
        "start": "0x0000000000000000",
        "end": "0xffffffffffffffff",
        "type": "EXT_RAM"
    }
}
```

### Class diagram Emma
<div align="center"> <img src="images/emmaClassDiagram.png" width="1000"> </div>

### Calling Graph Emma
<div align="center"> <img src="images/call_graph_uml/emma_filtered.profile.png" onerror="this.onerror=null;this.src='https://github.com/bmwcarit/Emma/blob/master/doc/images/call_graph_uml/emma_filtered.profile.png';" width="1000"> </div>
