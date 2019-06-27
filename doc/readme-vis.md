# Emma Visualiser
**Emma Memory and Mapfile Analyser Visualiser**

> Data aggregation and visualisation tool for Emma.

------------------------
# Contents
1. [Requirements](#requirements)
1. [Process](#process)
1. [Usage](#usage)
1. [Arguments](#arguments)
    1. [Required Arguments:](#required-arguments)
    1. [Optional Arguments:](#optional-arguments)
    1. [Quiet Mode](#quiet-mode)
    1. [Overview](#overview)
    1. [Append Mode](#append-mode)
1. [Project Configuration](#project-configuration)
    1. [budgets.json](#budgets.json)
    1. [[supplement]](#supplement)
1. [Input Files](#input-files)
1. [Output Folder and Files](#output-folder-and-files)
1. [Examples](#examples)
    1. [Calling Graph Emma Visualiser](#calling-graph-emma-visualiser)

------------------------

# Requirements
* Python 3.6 or higher
	* Tested with 3.6.1rc1; 3.7.0
* Python libraries
	* pypiscout 1.7 or higher: (`pip3 install pypiscout`)
	* Pandas 0.22 or higher: (`pip3 install pandas`)
	* Matplotlib 2.2.0 or higher: (`pip3 install matplotlib`)
	* Markdown 3.0.1 or higher: (`pip3 install Markdown`)
	* Pygments 2.3.1 or higher: (`pip3 install Pygments`)
* Tested on Windows but should also work on Linux systems



# Process

After analysing the mapfiles with the `emma.py` script, one can visualise them using `emma_vis.py`.


# Usage

    $ python emma_vis.py --help
    usage: Emma Visualiser [-h] [--version] --project PROJECT [--quiet] [--append]
                           [--dir DIR] [--subdir SUBDIR] [--overview]
                           [--categorised_image_csv] [--noprompt]

    Data aggregation and visualisation tool for Emma Memory and Mapfile Analyser (Emma).

    optional arguments:
      -h, --help            show this help message and exit
      --version             Display the version number.
      --project PROJECT, -p PROJECT
                            Path of directory holding the configs files. The
                            project name will be derived from the root folder
                            (default: None)
      --quiet, -q           Automatically accepts last modified .csv file in
                            ./memStats folder (default: False)
      --append, -a          Append reports to file in ./results folder (default:
                            False)
      --dir DIR, -d DIR     User defined path to the statistics root directory.
                            (default: None)
      --subdir SUBDIR       User defined subdirectory in results folder. (default:
                            )
      --overview, -ovw      Create a .html overview. (default: False)
      --categorised_image_csv, -cat_img
                            Save a .csv of categories found inside the image
                            summary (default: False)
      --noprompt            Exit fail on user prompt. (default: False)

    ********* Marcel Schmalzl, Felix Mueller, Gergo Kocsis - 2017-2019 *********



# Arguments

## Required Arguments: 

* ``` --project PROJECT, -p PROJECT ```

Specify the project root directory (the folder holding the .json files). The project name will be derived from the root folder.


## Optional Arguments:

* ```--help, -h```

Show the help message.

* ```--append, -a ```

Additional reports in .csv format will be created in the ./results directory.

* ```--directory DIRECTORY, --dir DIRECTORY, -d DIRECTORY```

User defined path for the folder ./memStats holding generated statistics from Emma (default: ./memStats). If not specified the program will ask you to confirm the default path.

* ```--res_subdir RES_SUBDIR```

User defined subdirectory in results folder. By defining `RES_SUBDIR` a folder with the given name is created in the results directory. This option makes it easier to distinguish between different development stages when batch analysing mapfiles.

* ```--categorised_image_csv, -cat_img```
Save a .csv of categories found inside the image summary (default: False).


## Quiet Mode

* ```--quiet, -q```

Automatically accepts last modified .csv file in ./memStats folder (default: False). If not specified the program will ask you to confirm the default path.

## Overview

* ```--overview, -ovw```

This creates a .md and .html output containing an overview of the memory usage.

## Append Mode

* ```--append, -a```

Appends analyses to .csv files. This can be used to visualise memory usage over different versions.


# Project Configuration

There are several configuration files needed in order to analyze your project. Most of them are described in the Emma documentation.
Here, only the ones described that are used by the Emma Visualiser exclusively.

## ```budgets.json```

This config file is used to define the available memory for every memory area of every configID.
Besides this it defines a threshold value as well that will be displayed on the diagrams. This threshold can be for example
prescribed by your project requirements in order to ensure there will be available memory areas for future updates.

The config file needs to have the following format:

{
    "Project Threshold in %": <THRESHOLD_VALUE>,

    "Budgets": [
        [<CONFIG_ID>, <MEMORY_TYPE>, <AVAILABLE_MEMORY>],
        .
        .
        .
        [<CONFIG_ID>, <MEMORY_TYPE>, <AVAILABLE_MEMORY>]
    ]
}

The following rules apply:

* The file contains a single unnamed JSON object
* The types used in the description:
    * `<THRESHOLD_VALUE>` is an integer
    * `<CONFIG_ID>` is a string
    * `<MEMORY_TYPE>` is a string containing one of the following values:
        * "INT_RAM" - internal RAM
        * "EXT_RAM" - external RAM
        * "INT_FLASH" - internal Flash
        * "EXT_FLASH" - external Flash
    * `<AVAILABLE_MEMORY>` is an integer
* The `<THRESHOLD_VALUE>` defines the project in percents
* The `"Budgets"` array has to contain a line for every `<MEMORY_TYPE>` of every `<CONFIG_ID>`
* The `<CONFIG_ID>`s are the ones defined in the globalConfig.json (See the Emma documentation for details)
* The `<AVAILABLE_MEMORY>`s are defining the available memory for a `<MEMORY_TYPE>` of a `<CONFIG_ID>` in bytes

## `[supplement]`

.md files in this directory will be appended to the report created by the ```--overview``` command.
This can be used to append additional remarks to the overview.
This is completely user defined, Emma and it´s components are not relying on these files in any way.


# Input Files

If not specified otherwise with the ```--quiet``` and ```--directory``` commands, the visualiser will choose the last modified image and module summary .csv files in the ./[PROJECT]/memStats directory. If there is no module summary present the visualisation of the modules will be skipped.


# Output Folder and Files

All output files will be saved to `./[PROJECT]/results`.

Output files are:

* .png's of all plots
* Overview mode creates .md and .html files of the overview
* A .csv file showing which section contains which modules.


# Examples

After the Image Summary has been created with emma.py and the memStats CSV files were saved to the directory `../[PROJECT]/results/memStats`, it can be visualised using:

    :::bash
    python emma_vis.py \
    --project ..\[PROJECT] \
    --dir ..\[PROJECT]\results \
    --quiet \
    --overview

## Calling Graph Emma Visualiser
<div align="center"> <img src="../genDoc/call_graph_uml/emma_vis_filtered.profile.png" width="1000" /> </div>
