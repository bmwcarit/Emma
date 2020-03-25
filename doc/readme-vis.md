# Emma Visualiser
**Emma Memory and Mapfile Analyser Visualiser**

> Data aggregation and visualisation tool for Emma.


## Requirements
* Python 3.6 or higher
* Python libraries
	* pypiscout 2.0 or higher: (`pip3 install pypiscout`)
	* Pandas 0.22 or higher: (`pip3 install pandas`)
	* Matplotlib 2.2.0 or higher: (`pip3 install matplotlib`)
	* Markdown 3.0.1 or higher: (`pip3 install Markdown`)
	* Pygments 2.3.1 or higher: (`pip3 install Pygments`)
* Tested on Windows and Linux systems



## Process
After analysing the mapfiles with the `Emma.py a` script one can visualise them using `Emma.py v`.


## Arguments in detail
### Optional Arguments
* `--inOutDir INOUTDIR, -i INOUTDIR`
* `--subDir SUBDIR`

User defined path for the folder `./memStats` holding generated statistics from Emma. If not specified the schema below will be followed:

| Argument -> | `--projectDir` | `--inOutDir` | `--subDir` | I/O path                |
| ----------- | -------------- | ------------ | ---------- | ----------------------- |
| Given?      | x              |              |            | projectDir              |
| Given?      | x              | x            |            | inOutDir                |
| Given?      | x              | x            | x          | join(inOutDir + subDir) |

I/O path denotes the path containing `memStats`. In the same path the `results` folder will be created.

By defining `SUBDIR` a folder with the given name is created in the results directory. This option makes it easier to distinguish between different development stages when batch analysing mapfiles.

* `--append`

Additional reports in .csv format will be created in the ./results directory.


* `--categorised_image_csv, -cat_img`
Save a .csv of categories found inside the image summary (default: False).


### Quiet Mode
* `--quiet, -q`

Automatically accepts last modified `.csv` file in `./memStats` folder (default: False). If not specified the program will ask you to confirm the default path if not given or ambiguous.

### Overview
* `--overview`

This creates a .md and .html output containing an overview of the memory usage.

### Append Mode
* `--append`

Appends analyses to .csv files. This can be used to visualise memory usage over different versions.


## Project Configuration
There are several configuration files needed in order to analyze your project. Most of them are described in the Emma documentation.
Here, only the ones described that are used by the Emma Visualiser exclusively.

### `budgets.json`
This config file is used to define the available memory for every memory area of every configID.
Besides this it defines a threshold value as well that will be displayed on the diagrams. This threshold can be for example
prescribed by your project requirements in order to ensure there will be available memory areas for future updates.

The config file needs to have the following format:

```json
{
    "Project Threshold in %": <THRESHOLD_VALUE>,

    "Budgets": [
        ["<CONFIG_ID>", "<MEMORY_TYPE>", <AVAILABLE_MEMORY>],
        .
        .
        .
        ["<CONFIG_ID>", "<MEMORY_TYPE>", <AVAILABLE_MEMORY>]
    ]
}
```

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

### `[supplement]`
`.md` files in this directory will be appended to the report created by the `--overview` command.
This can be used to append additional remarks to the overview.
This is completely user defined, Emma and its components are not relying on these files in any way.


## Input/Output Files
All output files will be saved to `./[PROJECT]/results`.

If not specified otherwise using the `--quiet` and `--inOutDir` commands, the visualiser will choose the last modified section and object summary .csv files in the `./[PROJECT]/memStats` directory. If there is no module summary present the visualisation of the modules will be skipped.


Output files are:

* `.png`'s of all plots
* Overview mode creates `.md` and `.html` files of the overview
* A `.csv` file showing which section contains which modules


## Examples
After the Image Summary has been created with `Emma.py a` and the memStats CSV files were saved to the directory `../[PROJECT]/results/memStats`, it can be visualised using:

```bash
python Emma.py v --project ..\<PROJECT> --dir ..\[PROJECT]\results --quiet --overview
```

### Calling Graph Emma Visualiser
<!-- We use onerror to make images visible when viewing the content using GitHub Pages etc. on the other side reading the markdown file using an editor should kept intact -->
<div align="center"> <img src="../genDoc/call_graph_uml/emma_vis_filtered.profile.png" onerror="this.onerror=null;this.src='https://github.com/bmwcarit/Emma/blob/master/genDoc/call_graph_uml/emma_vis_filtered.profile.png"';" width="1000"> </div>
