# ProgramParametersForPython
Functions to create program parameters from .toml, .json and .ini files, and to define and use command line options.

## MakeParams(*args, **kwargs)
MakeParams is a top level function to create a dictionary of parameters from a `.toml` or `.json` formatted parameter definition file and `.ini` default values files.

Get a couple command line arguments before proceeding:
We are almost always called with NO parameters, but we
want to allow a couple command line arguments to modify
how we process param files and config files.

*--ParamPath* defines a list of paths to glob looking for .toml or .json
 (// comments allowed) formatted files to define and initialize program parameters.  First valid file
    found is used, all others ignored.

*--configPaths* defines a list of paths to glob looking for .ini files to provide
    optional values for the parameters defined in the TOML or JSON param file.
    All .ini files found are processed; later ones overriding repeated options.
    Missing or ill-formatted files are ignored.

*--configSections* defines a list of "sections" in the .ini files to process.

A dictionary with contents of `.ini` file(s) using sections related to
the calling program is used to load values into options that may be overridden
by command line arguments.

Keyword args to the main program as well as the command line options
referenced above affect this behavior:
* configPaths = a list of "glob" paths to files that will be read.
                    Any files that do not exist or don't parse ok will
                    be ignored.  Defaults as below.
* configSections = a list of sections in the `.ini` file(s) from which
                    to load values.  Last section with an option in it
                    overrides previous definitions.  Defaults as below.

DEFAULT CONFIG PATHS:
* Look for `ProgName+'*.ini'` in our directory *(not including file extension, typically `.py`)*
* Path as defined in the `PrivateConfig` environment variable.

DEFAULT CONFIG SECTIONS (in order; later sections overriding earlier ones):
*    [DEFAULT]
*    [\<"LOCATION" evnironment variable>]
*    [\<"HOST" evnironment variable>]
*    [\<program name>] *(including extension, typically `.py`)*
*    [\<program name>/\<"LOCATION" environment variable>]
*    [\<program name>/\<"HOST" environment variable>]
