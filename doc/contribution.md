
# Contribution guide
This guide will assist you in order to sucessfully submit contributions for the Emma project.  

## Obtain the current version of the source code
Assure that you are working with the latest stable version.

## Describe your changes
Absolutely describe your changes regardless of what problem you solved nor how complex your changes are. Keep the following points in mind:

### General
* What is your motivation to do to this change?
* Why it is worth fixing?
* How will it affect end-user?
* If optimisations were done - quantify them. Present trade-offs (e.g. run-time vs. memory).
* Evaluate your contribution objectively. What are pro's, con's?
* One contribution should solve only one problem. If not split it.
* Your description should be self-explanatory (avoiding external resources).

### Linking, referencing & documentation
* If you link to tickets/mailing lists etc. reference to them. Summarise what is its principal outcome.
* When referencing specific commits: state the commit ID (use the long hash) + (!) the commit massage in order to make it more readable for the reviewer.

### Implementation specific
* How you solved the problem?
* If your solution is complex: provide an introduction before going into details. 
* If your patch your solution describe what you have done and why.


## Test and review your code
Test it on a clean environment.

Review your code with regards to our [coding guidelines](#coding-guidelines).


## Check and act on the review process
You may receive comments regarding your submission. In order to be considered you must respond to those comments. 


## Sign your work
You must sign the [Developer Certificate of Origin (DCO)](https://developercertificate.org/) for any submission. We use this to keep track of who contributed what. Additionaly you certify that the contribution is your own work or you have the right to pass it on as an open-source patch.

**To do so you read the DCO and agree by adding a "sign-off" line at the end of the explanation of the patch like in the example below:**

```text
Signed-off-by: Joe Contrib <joe.contrib@somedomain.com>
```

Fill in your full name (no pseudonyms) and your email address surrounded by angle brackets.

Small or formal changes can be done in square bracket notation:

```
Signed-off-by: Joe Contrib <joe.contrib@somedomain.com>
[alice.maintain@somedomain.com: struct foo moved from foo.c to foo.h]
Signed-off-by: Alice Maintain <alice.maintain@somedomain.com>
```

## Do the pull request

```git
git request-pull master git://repo-url.git my-signed-tag
```

See also [here](https://help.github.com/en/articles/requesting-a-pull-request-review) for more information about pull requests in general on GitHub.


----------------------------------------------------------------
# Coding guidelines
Generally [PEP-8](https://github.com/python/peps/blob/master/pep-0008.txt) or the [Google style guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md) apply. However we deviate slightly from this (see the following sections). 

## Style
* Naming conventions
    * mixedCase (camelCase and PascalCase is used)
    * **Methods/functions** and **variables** start with a minuscule (**camelCase**)
    * [**Class names**](https://www.python.org/dev/peps/pep-0008/#class-names) names start with a majuscule (**PascalCase**)
    * Global variables: `CAPS_WITH_UNDER`
* Max line length rule is ignored since it decreases readability, use line-breaks where appropriate
* Imports in Python
    * The imports need to be separated from other parts of the file with 2-2 blank lines above and under
    * They need to be grouped into the following three groups:
      * Python Standard Library Imports
      * 3rd Party Imports
      * Emma Imports
    * The groups need to be in the same order as in the previous list and they need to be separated from each other with a single blank line
    * Only packages and modules shall be imported, individual classes and functions not
    * Imports shall not use renaming
    * There are some exceptions:
      * Importing from shared_libs.stringConstants shall be done in the following way: `from shared_libs.stringConstants import *`
      * Importing the `pyipiscout` library shall be done in the following way: `import pypiscout as sc`
* British English shall be used in function names and comments
    * Exceptions:
        * `map file` is always written as `mapfile`
* `TODO`, `FIXME` and similar tags should be in the format: `# TODO: This is my TODO (<author>)`
    * First letter in the comment is a majuscule
    * The comment ends with the name of the author or with an unique and consistent abbreviation/alias/username/pseudonym (preferably your initials if still available; if you are unsure check the [CONTRIBUTORS](../CONTRIBUTORS) file)

## Path handling
Use `os.path.normpath()` where appropriate. Using `/` and `\` can cause problems between OSes (even on Windows with WSL) and strange things could happen. Also prefer `joinPath()` (in `shared_libs.Emma_helper`) instetad of `os.path.join()`.
    
## Raising exceptions
* Exceptions should be avoided where possible. Instead use a descriptive error message using `SCout` and exit with `sys.exit(<err-code>)`
* the default error code is `-10`
* For the user it is hard to distinquish whether an exception was caused by a bug or wrong user input

----------------------------------------------------------------
# Colour palette
The following colour palette is used for the documentation:

| Colour       | HSL(A)        | RGB(A)        | RGBA (hex) |
| ------------ | ------------- | ------------- | ---------- |
| Yellow       | 34, 255, 192  | 255, 230, 128 | ffe680ff   |
| Light orange | 17, 255, 213  | 255, 204, 170 | ffccaaff   |
| Dark orange  | 17, 145, 204  | 233, 198, 175 | e9c6afff   |
| Light blue   | 136, 145, 204 | 175, 221, 233 | afdde9ff   |
| Green        | 68, 145, 204  | 198, 233, 175 | c6e9afff   |
| Light grey   | 0, 0, 236     | 236, 236, 236 | ecececff   |
| Grey         | 0, 0, 204     | 204, 204, 204 | ccccccff   |
