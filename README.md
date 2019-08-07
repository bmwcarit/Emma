[![Codacy Badge](https://api.codacy.com/project/badge/Grade/8c6208f6f0bf4d429b13e2fa701aa780)](https://www.codacy.com/app/holzkohlengrill/Emma?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=bmwcarit/Emma&amp;utm_campaign=Badge_Grade) [![Codacy Badge](https://api.codacy.com/project/badge/Coverage/8c6208f6f0bf4d429b13e2fa701aa780)](https://www.codacy.com/app/holzkohlengrill/Emma?utm_source=github.com&utm_medium=referral&utm_content=bmwcarit/Emma&utm_campaign=Badge_Coverage) [![Build Status](https://travis-ci.org/bmwcarit/Emma.svg?branch=master)](https://travis-ci.org/bmwcarit/Emma) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)



# Emma
**Emma Memory and Mapfile Analyser (Emma)**

> Conduct static (i.e. worst case) memory consumption analyses based on arbitrary linker map files. It produces extensive `.csv` files which are easy to filter and post-process. Optionally `.html` and markdown reports as well as neat figures help you visualising your results.

Given a **map file input** (Green Hills map files are the default but others - like GCC - are supported via configuration options; examples are enclosed) Emma **map**s the addresses of sections (aka images) and/or objects (aka modules) **to memory regions**. Those memory regions are classified into two levels of granularity respectively. The first level defines arbitrary groups based on your personal taste (however using names similar to those defined by your microcontroller vendor makes most sense). Later each of those regions (second level) are assigned to one of four generalised predefined memory regions (those are: `INT_RAM`, `INT_FLASH`, `EXT_RAM`, `EXT_FLASH`). In case of **virtual memory** objects and sections lying within virtual address spaces (VASes) get **translated back into physical memory**. This is depicted in the below figure (lower part).

**Categorisation** can be used to assign consumers (a consumer would usually represent a software component) to each object or section. This is useful for subsequent steps in order to display memory consumption per consumer type. See the upper part of the figure shown below. Mechanisms are provided to batch categorise object and section names. "Objects in sections" provides ways to obtain a **finer granularity of the categorisation result**. Therefore categorised sections containing (smaller) objects of a different category got split up and result into a more accurate categorisation.

As a result you will get **output** files in form of a **`.csv` file** which sets you up to do later processing on this data easily. In this file **additional information is added** like:

* Overlaps (of sections/objects)
* Containments (e.g. sections containing objects)
* Duplicates
* All meta data about the origin of each section/object (mapfile, addess space, ...)
* ...

Holding the aforementioned **augmented data** makes it easy to **detect issues in linker scripts** and get an **in-depth understanding of** your program's **memory consumption**. Including a lot of additional and "corrected" data can cause confusion. Thus all original (unmodified) data is preserved in the output files simultaneously.

The Emma visualiser helps you to create nice plots and reports in a `.png` and `.html` and markdown file format.

The whole Emma tool suite contains command line options making it convenient to be **run on a build server** like `-Werror` (treat all warnings as errors) or `--no-prompt` (exit and fail on user prompts; user prompts can happen when ambiguous configurations appear such as multiple matches for one configured map files).

------------------------
<br>

<div align="center"> <img src="./doc/images/architecture.png" width="100%" /> </div>

------------------------
# Contents
1. [General Workflow](#general-workflow)
1. [Quick Start Guide](#quick-start-guide)
    1. [Project files are already present](#project-files-are-already-present)
    1. [Project files have to be created](#project-files-have-to-be-created)
1. [Full documentation](#full-documentation)
1. [Contribute](#contribute)
1. [Dependencies & Licences](#dependencies--licences)

Install dependencies: Python 3.6 or higher; `pip3 install Pygments Markdown matplotlib pandas pypiscout`


# General Workflow
The following figure shows a possible workflow using Emma:

<div align="center"> <img src="./doc/images/workflow.png" width="100%" /> </div>

**Emma** - as the core component - produces an intermediate `.csv` file. Inputs are mapfiles and JSON files (for configuration (memory layout, sizes, ...)). From this point you are very flexible to choose your own pipeline. You could

* use the Emma tools (**Emma Visualiser**, **Emma Deltas**, ...) for **further processing (data aggregation and analysis)**,
* simply your favourite spreadsheet software (like Microsoft Excel or LibreOffice Calc) or
* use your own tool for the data analysis.


# Quick Start Guide
At this point we want to give you a brief overview what to do in the below two scenarios. If you want to play around go to [(project files are already present)](#Project-files-are-already-present) and use our example projects in [`./doc/test_project*`](./doc/).

* if the Emma *project is already set-up* (JSON files were created) and you want to analyse your software with newly generated mapfiles proceed to [-> Project files are already present](#Project-files-are-already-present) or
* you *start* your analysis *from scratch* and need to do configure Emma before you use it then go to [-> Project files have to be created](#project-files-that-have-to-be-created).

Example projects (including Emma* outputs/results) can be found in [`./doc/test_project*`](./doc/).

------------------------

## Project files are already present
Try `python emma.py --help` to see all possible options or refer to the documentation (`./doc/*`).

1. Create intermediate `.csv` from mapfiles with Emma:

```bash
python emma.py -p .\MyProjectFolder --map .\MyProjectFolder\mapfiles --dir .\MyProjectFolder\analysis --subdir Analysis_1
```

2. Generate reports and graphs with Emma Visualiser:

```bash
python emma_vis.py -p .\MyProjectFolder --dir .\MyProjectFolder\analysis --subdir Analysis_1 -q 
```

## Project files that have to be created
To create a new project, the following files must be created:

* `globalConfig.json`
* `budgets.json`
* `categories.json`
* `categoriesKeywords.json`
* `categoriesSections.json`
* `categoriesSectionsKeywords.json`

You will find example projects in [`./doc/test_project*`](./doc/). In-depth documentation can be found in the full documentation (see [`./doc/`](./doc/)).

A basic configuration can be short per file. For complex systems you can choose from many optional keywords/options that will provide you means to adjust your analysis as fine grained as you wish.

One main concept includes the `globalConfig.json`. You can see this as meta-config. Each configuration ID (configID) is a separately conducted analysis. Per configID you state individually the configuration files you want to use for this exact analysis. Herewith you can mix and match any combination of subconfigs you prefer.

<div align="center"> <img src="./doc/images/globalConfigScheme.png" width="60%" /> </div>

A `globalConfig.json` could look like this:

```json
{
    "configID1": {
        "addressSpacesPath": "addressSpaces.json",
        "sectionsPath": "sections.json",
        "patternsPath": "patterns.json"
    }
}
```


# Full documentation
For the full documentation please refer to the [`./doc/`](./doc/) directory.


# Contribute
We are glad if you want to participate. In [`./doc/contribution.md`](doc/contribution.md) you will find a guide telling you everything you need to know including coding conventions and more.

# Dependencies & Licences

| Library (version)    | pip package name                                    | Licence                              | URL                                                                                                                                                                                          |
|----------------------|-----------------------------------------------------|--------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Pygments (v2.3.1+)   | [Pygments](https://pypi.org/project/Pygments/)      | BSD-2-Clause                         | [https://bitbucket.org/birkenfeld/pygments-main/src/default/](https://bitbucket.org/birkenfeld/pygments-main/src/default/); [http://pygments.org/download/](http://pygments.org/download/)   |
| Markdown (v3.0.1+)   | [Markdown](https://pypi.org/project/Markdown/)      | BSD-3-Clause                         | [https://github.com/Python-Markdown/markdown](https://github.com/Python-Markdown/markdown); [https://python-markdown.github.io/](https://python-markdown.github.io/)                         |
| Matplotlib (v3.0.0+) | [matplotlib](https://pypi.org/project/matplotlib/)  | Matplotlib License (BSD compatible)  | [https://matplotlib.org/users/installing.html](https://matplotlib.org/users/installing.html); [https://github.com/matplotlib/matplotlib](https://github.com/matplotlib/matplotlib)           |
| Pandas (v0.23.4+)    | [pandas](https://pypi.org/project/pandas/)          | BSD-3-Clause                         | [https://github.com/pandas-dev/pandas/](https://github.com/pandas-dev/pandas/); [http://pandas.pydata.org/getpandas.html](http://pandas.pydata.org/getpandas.html)                           |
| SCout (v1.8+)        | [pypiscout](https://pypi.org/project/pypiscout/)    | MIT                                  | [https://github.com/holzkohlengrill/SCout](https://github.com/holzkohlengrill/SCout)                                                                                                         |


**Dependencies needed to generate documentation:**

Utility scripts in [`./doc/`](doc) need additional dependencies. As a normal user you can ignore this.

| Library (version)        | pip package name                                    | Licence                              | URL                                                                                                                                                |
|--------------------------|-----------------------------------------------------|--------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| gprof2dot (v2017.9.19+)  | [gprof2dot](https://pypi.org/project/gprof2dot/)    | LGPL-3.0                             | [https://github.com/jrfonseca/gprof2dot](https://github.com/jrfonseca/gprof2dot)                                                                   |
| pylint (v2.3.1+)         | [pylint](https://pypi.org/project/pylint/)          | GPL-2.0                              | [https://github.com/PyCQA/pylint](https://github.com/PyCQA/pylint)                                                                                 |

Please refer to the [gprof2dot project site](https://github.com/jrfonseca/gprof2dot) and install its dependencies.

Note that those modules are invoked via subprocess calls within the [./genDoc/](genDoc/) scripts.


**Code snippets etc.:**

| Name (version)           | Kind                                                 | Modified?  | Licence         | URL                                                                                                                                                                                                                                                                                |
|--------------------------|------------------------------------------------------|------------|-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| pygmentize (v2.2.0+)     | Auto-generated .css file                             | Yes        | BSD-2-Clause    | [http://pygments.org/download/](http://pygments.org/download/); [https://bitbucket.org/birkenfeld/pygments-main/issues/1496/question-licence-of-auto-generated-css](https://bitbucket.org/birkenfeld/pygments-main/issues/1496/question-licence-of-auto-generated-css)   |
| toHumanReadable (--)     | Code snippet                                         | No         | MIT             | [https://github.com/TeamFlowerPower/kb/wiki/humanReadable](https://github.com/TeamFlowerPower/kb/wiki/humanReadable)                                                                                                                                                               |
| ~test_project_gcc (v1.3+)~ | ~Map files based on XMC 2Go Initial Start project~ | ~No~         | ~BSD-3-Clause~    | ~[Infineon -> Documents -> XMC 2Go Initial Start](https://www.infineon.com/cms/en/product/evaluation-boards/kit_xmc_2go_xmc1100_v1/#!documents)~                                                                                                                                     |

For the full documentation please refer to the [`./doc/`](doc) directory.
