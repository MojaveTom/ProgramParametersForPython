
'''
Define the schema for program parameters definition dictionary.

Define function to validate program parameters definition dictionary.
Define function to read configuration information.
Define function to create program parameters dictionary from definitions dict,
    apply defaults from definitions,
    apply any configuration defined values,
    apply any command line values,
    return parameters dictionary.

Define function to put all the pieces together.

'''

import os               #   https://docs.python.org/3/library/os.html
import sys              #   https://docs.python.org/3/library/sys.html
import inspect          #   https://docs.python.org/3/library/inspect.html
import json             #   https://docs.python.org/3/library/json.html
import toml             #   https://github.com/uiri/toml    https://github.com/toml-lang/toml
# comment json strips python and "//" comments form json before applying json.load routines.
import commentjson      #   https://github.com/vaidik/commentjson       https://commentjson.readthedocs.io/en/latest/
# Lark is used by commentjson -- import commented out, but here for documentation.
# import lark             #   https://github.com/lark-parser/lark    https://lark-parser.readthedocs.io/en/latest/
import logging          #   https://docs.python.org/3/library/logging.html
                        #   https://github.com/keleshev/schema
from progparams.GetLoggingDict import setConsoleLoggingLevel, setLogFileLoggingLevel, getConsoleLoggingLevel, getLogFileLoggingLevel

from schema import Schema, And, Or, Use, Optional, SchemaError
import argparse         #   https://docs.python.org/3/library/argparse.html
import configparser     #   https://docs.python.org/3/library/configparser.html
## The following may be needed to initialize some params
# import time             #   https://docs.python.org/3/library/time.html
# import datetime         #   https://docs.python.org/3/library/datetime.html
import glob
from itertools import chain
flatten = chain.from_iterable

logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info
warning = logger.warning
critical = logger.critical

#  Defines "extend" action for argparse which was introduced in python3.8
class ExtendAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            items = getattr(namespace, self.dest) or []
        except:
            items = []
        items.extend(values)
        setattr(namespace, self.dest, items)

ProgName, ext = os.path.splitext(os.path.basename(sys.argv[0]))
ProgPath = os.path.dirname(os.path.realpath(sys.argv[0]))

validArgParserActions = ("store", "store_const", "store_true", "store_false"
                        , "append", "append_const", "count", "extend")
    # These arg parser actions are incompatible with also specifying a type keyword.
argParserActionsWithNoType = ("store_const", "store_true", "store_false", "count")
    # These arg parser keywords do not take a string as their value
nonStringParserKeyWords = ("type", "required")
validArgParserKeyWords = ('dest', 'action', 'default', 'nargs', 'const', 'type', 'choices', 'required', 'help', 'metavar')

# with open(os.path.join(MyPath, "ProgramParamsDefs.json"), 'w') as file:
#     json.dump(ppds, file, indent=2)
# Doesn't work to put schema definition in a JSON file
# since some of the keys are class objects defined in schema.
# Can't pickle ppds either.
ppds = {
        Optional('ProgramDescription', default=None): str,
        Optional('PositionalArgParserArgs', default=None): {
              'paramName': str
            , 'action': str
            , Optional('nargs'): str
            , Optional('help'): str
            },
        'Parameters': [{'paramName': str
            , 'description': str
            , Optional('intermediate'): Use(bool)       # intermediate params are for defining others and will be deleted from final dictionary.
            , Optional('configName', default=None): Use(str.casefold)       # make sure all configNames are lower case.
            , Optional('default', default=None): Use(str)
            , Optional('type'): Use(str)
            , Optional('argParserArgs', default=None):
                { Optional('short', default=None): And(str, lambda s: s != '-h', error="The short command option '-h' is reserved for help.")
                , Optional('long', default=None): And(str, lambda s: s != '--help', error="The long command option '--help' is reserved for help.")
                , Optional('dest'): str
                , Optional('action'): And(str, lambda k: k in validArgParserActions, error=f"Argparser action not one of {validArgParserActions}")
                , Optional("default"): object
                , Optional('nargs'): str
                , Optional('const'): str
                , Optional('type'): str
                , Optional('choices'): str
                , Optional('required'): And(str, lambda k: k in ('True', 'False'), error=f'Argparser "required" must be "True" or "False".')
                , Optional('help'): str
                , Optional('metavar'): str
                }
        } ]
        }

def GetFunctionId() -> str:
    return f"{os.path.splitext(os.path.basename(__file__))[0]}.{inspect.currentframe().f_back.f_code.co_name}"

def SetLogLevelsFromKwargs(myFunctionId, **kwargs):
    ############# Trouble is, setting console log level from here affects file logging too.
    #  Set logging level according to kwargs & cmd line options.
    newLogLevel = kwargs.get('BiolerPlateLoggingLevel')
    debug(f"Computed new log level from parsed boiler plate parameters as {newLogLevel}.")
    lls = (kwargs.get(f"{myFunctionId}.ConsoleLoggingLevel", None), kwargs.get(f"{myFunctionId}.FileLoggingLevel", None))
    debug(f"Function ID logging levels are: {lls!r}")
    llvi = int(kwargs.get('LogLevelInterval', 10))      # convenience assignment
    if (lls is not None) and (len(lls) > 0) and (lls[0] is not None):
        ll = round(int(lls[0])/llvi)*llvi        #  round to nearest multiple of LogLevelInterval
        if ll != int(lls[0]):
            logger.warning(f"Log level given: {lls[0]} is not a multiple of {llvi}, it is rounded to nearest multiple: {ll}")
        setConsoleLoggingLevel(ll)
        debug(f'Console logging level set to {ll} from cmd line "KeyWordParams"')
    elif newLogLevel is not None:
        debug(f'Console logging {newLogLevel} from -v,-q cmd line options.')
        setConsoleLoggingLevel(newLogLevel)
    if (lls is not None) and (len(lls) > 1) and (lls[1] is not None):
        ll = round(int(lls[1])/llvi)*llvi        #  round to nearest multiple of LogLevelInterval
        if ll != int(lls[1]):
            warning(f"Log level given: {lls[1]} is not a multiple of {llvi}, it is rounded to nearest multiple: {ll}")
        setLogFileLoggingLevel(ll)
        debug(f"File logging level set to {ll}")

# ppds = [{'paramName': str
#         , 'description': str
#         , Optional('configName', default=None): str
#         , Optional('default', default=None): Use(str)
#         , Optional('type'): Use(str)
#         , Optional('argParserArgs', default=None): { Or(Or('short', 'long'), 'cmdArg'):
#                         (And(str, lambda s: s not in ('-h', '--help'), error="The command options cannot be '-h' or '--help"))
#                     , 'dest': str
#                     , 'action': str
#                     }
#         } ]

BoilerPlateArgs = toml.loads('''##  These argparser args are evaluated before the Parameters
##  since they may affect relavent paths and verbosity.
#  These are added the the primary arg parser only to document
#    them in the help message.
[[BoilerPlateArgParserArgs]]
paramName = "ParamPath"
long = "--ParamPath"
dest = "ParamPath"
action = "extend"
nargs = "+"
type = "str"
help = "Give multiple times to make a list of paths to .toml or .jsonc or .json parameter definition files.  The first successful load wins."

[[BoilerPlateArgParserArgs]]
paramName = "configPaths"
dest = "configPaths"
long = "--configPaths"
action = "extend"
nargs = "+"
type = "str"
help = "Give multiple times to make a list of paths to configuration .ini files."

[[BoilerPlateArgParserArgs]]
paramName = "configSections"
dest = "configSections"
long = "--configSections"
action = "extend"
nargs = "+"
type = "str"
help = "Give multiple times to make a list of configuration sections to load from .ini files."

[[BoilerPlateArgParserArgs]]
paramName = "KeyWordParams"
dest = "KeyWordParams"
long = "--KeyWordParams"
action = "extend"
nargs = "*"
type = "str"
help = "Give multiple times to make a list of key word arguments to pass to functions in the program."

# logger.setLevel(DefaultLoggingLevel - Verbosity*LogLevelInterval + Quietude*LogLevelInterval)
[[BoilerPlateArgParserArgs]]
paramName = "DefaultLoggingLevel"
long = "--DefaultLoggingLevel"
type = "int"
help = "Verbosity level starting point for Verbosity."
default = 20                #  "logging.INFO"
dest = "DefaultLoggingLevel"
action = "store"

[[BoilerPlateArgParserArgs]]
paramName = "Verbosity"
type = "int"
help = "Increase verbosity, higher is more."
default = 0
short = "-v"
long = "--verbosity"
dest = "Verbosity"
action = "count"

[[BoilerPlateArgParserArgs]]
paramName = "Quietude"
type = "int"
help = "Decrease verbosity; more times given, the less verbosity."
default = 0
short = "-q"
long = "--quiet"
dest = "Quietude"
action = "count"

# [[BoilerPlateArgParserArgs]]
# # Value determined by examining https://docs.python.org/3/library/logging.html#logging-levels
# paramName = "LogLevelInterval"
# type = "int"
# help = "The difference in various logging levels. (Modify at your own risk.)"
# default = 10
# dest = "LogLevelInterval"
# action = "store"
# long = "--LogLevelInterval"
''')['BoilerPlateArgParserArgs']

##  After all this, BoilerPlateArgs is a list of things to put in our arg parser.

#  setParamFromOption defined here to protect multiline string from source
# formatting problems. Used in createParams.
setParamFromOption = """if args.{optDest} is not None: {paramName} = args.{optDest}
else: debug("There is no cmd option given for {paramName}")"""

## This is a multi-line string into which data is stuffed before being "exec"uted .
## A multi-line string is the only way a try: clause can be executed in an exec function.
addArg = '''try:
    parser.add_argument({cmdArg})
except:
    logger.warning('Parser options for parameter "{paramName}" could not be added; Ignored.')
    raise
pass
'''

##########################  addBoilerPlateArgs  ##############################
def addBoilerPlateArgs(parser, **kwargs):
    consoleLogLevel = getConsoleLoggingLevel()
    fileLogLevel = getLogFileLoggingLevel()
########## Put this whole function in a try ... finally block so we can restore log levels on exit.
    try:

        myFunctionId = GetFunctionId()
        debug(f'In GetParams, my "ID" is {myFunctionId}')
        SetLogLevelsFromKwargs(myFunctionId, **kwargs)

        for a in BoilerPlateArgs:
            paramName = a.get('paramName')
            debug(f"Adding '{paramName}' to argparse")
            #  Guarantee at least one of these.
            if (a.get('short') is None) and (a.get('long')  is None):
                critical(f'One of argParserArgs options in "short" or "long" form must be present and not None: {a!r}')
                logger.warning(f"This command line option will not be processed.")
                continue
            cmdArg = list()
            # Special add_argument key processing ...
            if a.get('short') is not None:          # This is not a keyword argument, just put it in as is.
                cmdArg.append(f"{a.get('short')!r}")       # put in short option
            if a.get('long') is not None:           # This is not a keyword argument, just put it in as is.
                cmdArg.append(f"{a.get('long')!r}")        # put in long option
            #  For some reason add_argument barfs if a type is specified and one of these store kinds is used.
            if (a.get('action') is not None) and (a['action'] in argParserActionsWithNoType) and (a.get('type') is not None):
                a.pop('type')               # In this case, remove the "type" keyword
            #  Add keyword arguments to the list of add_argument args
            for (k, v) in a.items():                # add other keyword arguments to arg list.
                if (k not in validArgParserKeyWords) or (v is None): continue   # filter out "short", "long", and any other bad words.
                if k in nonStringParserKeyWords: cmdArg.append(f"{k}={v}")
                else:  cmdArg.append(f"{k}={v!r}")
            ## put together the whole add_argument call
            cmdArg = ', '.join(cmdArg)
            arg = addArg.format(cmdArg=cmdArg, paramName=paramName)
            debug(f'exec({arg})')
            try:
                exec(arg)
                logger.debug(f'Successfully added command line argument option for "{paramName}""')
            except Exception as e:
                logger.warning(f"Trying to add arg had an exception: {e}")
                pass
    finally:        # Restore logging levels to what they were when we began.
        # setConsoleLoggingLevel(consoleLogLevel)
        # setLogFileLoggingLevel(fileLogLevel)
        pass

##########################  GetConfig  ##############################
def GetConfig(**kwargs):
    '''A dictionary with contents of ".ini" file(s) using sections related to
the calling program is used to load values into options that may be overridden
by command line arguments.

Keyword args to the main program as well as the command line options
referenced above affect this behavior:
    configPaths = a list of "glob" paths to files that will be read.
                    Any files that do not exist or don't parse ok will
                    be ignored.  Defaults as below.
    configSections = a list of sections in the .ini file(s) from which
                    to load values.  Last section with an option in it
                    overrides previous definitions.  Defaults as below.
DEFAULT CONFIG PATHS:
    Look for ProgName+'*.ini' in our directory, then in the
    path as defined in the "PrivateConfig" environment variable.
DEFAULT CONFIG SECTIONS (in order; later sections overriding earlier ones):
    [DEFAULT]
    [<"LOCATION" evnironment variable>]
    [<"HOST" evnironment variable>]
    [<program name>]     including extension, typically ".py"
    [<program name>/<"LOCATION" environment variable>]
    [<program name>/<"HOST" environment variable>]
'''
    consoleLogLevel = getConsoleLoggingLevel()
    fileLogLevel = getLogFileLoggingLevel()
########## Put this whole function in a try ... finally block so we can restore log levels on exit.
    try:

        myFunctionId = GetFunctionId()
        debug(f'In GetParams, my "ID" is {myFunctionId}')
        SetLogLevelsFromKwargs(myFunctionId, **kwargs)

        # Pick up configPaths from kwargs or default.
        if kwargs.get('configPaths') is not None:
            fns = kwargs['configPaths']
            if isinstance(fns, str): fns = (fns,)
        else:
            # Look for .ini files with our program name in the program dir, then in location given by environment variable.
            fns = (os.path.join(ProgPath, ProgName+'*.ini'), os.environ.get('PrivateConfig'))
        # Make a list of actual files to read.
        configPaths = list(flatten([glob.glob(x) for x in fns if x is not None]))

        # Pick up cfgSections from kwargs or default.
        if kwargs.get('configSections') is not None:
            cfgSections = kwargs['configSections']
            if isinstance(cfgSections, str): cfgSections = (cfgSections,)
        else:
            host = os.environ.get('HOST', 'Unknown')    # DON'T want None
                #  location is usually the same as first two of host
            loc = os.environ.get('LOCATION', host[0:2])
            progName = os.path.basename(sys.argv[0])
                #  os.path.join is too smart; my .ini file sections happen to
                #  have "/" separators, not necessarily file path separators.
            cfgSections =   ( loc                # LOCATION
                            , host               # HOST
                            , progName           # program name
                            , progName+"/"+loc   # prog name & LOCATION
                            , progName+"/"+host  # prog name & HOST
                            )

        #  This configparser lower cases all option names.  For consistency sake,
        #  only use lower case option names in .ini file.
        config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        cfgDict = dict()        # empty dict

        cfgFilesUsed = config.read(configPaths) # reads all configPaths, returns ones used.
        debug(f'Used configuration file(s) at: {cfgFilesUsed}')
        if len(cfgFilesUsed) == 0: warning(f"\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n!!    NO configuration files read     !!\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        if len(config) == 0:        # nothing loaded into config (which looks like a dict)
            warning(f"EMPTY config info dict read from .ini files.")
            return cfgDict          # return empty dict

        for cfgSection in cfgSections:
            if cfgSection in config:
                debug(f"Reading INI file section: {cfgSection}")
                cfg = config[cfgSection]        # saved as variable so could print in debugging
                cfgDict = {**cfgDict, **cfg}    # Puts both dictionaries into one, second overriding
        return cfgDict
    finally:        # Restore logging levels to what they were when we began.
        # setConsoleLoggingLevel(consoleLogLevel)
        # setLogFileLoggingLevel(fileLogLevel)
        pass

##########################  GetParams  ##############################
def GetParams(*args, **kwargs):
    consoleLogLevel = getConsoleLoggingLevel()
    fileLogLevel = getLogFileLoggingLevel()
    debug(f"Saved log levels are console: {consoleLogLevel}, file: {fileLogLevel}")
########## Put this whole function in a try ... finally block so we can restore log levels on exit.
    try:

        myFunctionId = GetFunctionId()
        debug(f'In GetParams, my "ID" is {myFunctionId}')
        SetLogLevelsFromKwargs(myFunctionId, **kwargs)

        if kwargs.get('ParamPath') is not None:
            fns = kwargs['ParamPath']
            if isinstance(fns, str): fns = (fns,)
        else:
            # Look for .jsonc and .json files with our program name in the main program's dir then in cwd.
            fns = [   os.path.join(ProgPath, ProgName+'*Params.toml')
                    , os.path.join(ProgPath, ProgName+'*Params.jsonc')
                    , os.path.join(ProgPath, ProgName+'*Params.json')
                    , f"{ProgName}*Params.toml"
                    , f"{ProgName}*Params.jsonc"
                    , f"{ProgName}*Params.json"
                ]
            debug(f"Looking for parameter definition file in default locations:  {fns}")
        # glob process param paths
        # Make a list of actual files to read.
        fns = list(flatten([glob.glob(x) for x in fns]))
        # debug(f"Looking for parameter definition file in GLOBBED locations:  {fns}")

        debug(f"Looking for first good JSON or TOML parameters file in GLOBBED locations: {fns!r}")
        if fns is None: return None, None     # no paramDefs, and no files to read it from.
        for fn in fns:
            try:
                debug(f"Trying to load parameters from file: {fn}")
                fnExt = os.path.splitext(fn)[1]
                if fnExt == ".json" or fnExt == ".jsonc":
                    paramDefs = commentjson.load(open(fn))
                elif fnExt == ".toml":
                    paramDefs = toml.load(fn)
                else:
                    critical(f"Unrecognized file type from which to load parameters: {fnExt}")
                    return None, fn
                debug(f"Successfully loaded paramDefs: {paramDefs}\n\nFrom file {fn}")
                break       #  exit the for loop without doing the else clause.
            except json.JSONDecodeError as e:
                info(f"Json file: {fn} did not load successfully: {e}")
            except FileNotFoundError as f:
                info(f"Param file: {fn} does not exist. {f}")
            except IsADirectoryError as d:
                info(f"Param file: {fn} is a directory! {d}")
            except toml.TomlDecodeError as t:
                info(f"Toml file: {fn} did not load successfully: {t}")
        else: return None, None
        return paramDefs, fn
    finally:        # Restore logging levels to what they were when we began.
        # setConsoleLoggingLevel(consoleLogLevel)
        # setLogFileLoggingLevel(fileLogLevel)
        debug(f"Restored log levels are console: {consoleLogLevel}, file: {fileLogLevel}")
        pass

'''
We see this code several times below.
        for (k, v) in a.items():                # add other keyword arguments to arg list.
            if (k not in validArgParserKeyWords) or (v is None): continue

The equivalent code in one for statement is:
        for (k,v) in filter(lambda x: (x[0] in validArgParserKeyWords) and (x[1] is not None), a.items()):

So what's happening in the fancy for construct is that the "x" in the lambda function gets
the list items returned by a.items().  x[0] is the key part, and x[1] is the value part.
I think the first form is much more understandable.
'''

##########################  MakeParams  ##############################
def MakeParams(*args, **kwargs):        # args is a list of non-keyword arguments; kwargs is a dict of keyword args.
    '''Top level function to create a dictionary of parameters from a JSON params file and .ini files.

Get a couple command line arguments before proceeding:
    We are almost always called with NO parameters, but we want to allow a couple
    command line arguments to modify how we process param files, config files,
    logging, and to allow the knowledgable user to set key-word parameters.

--ParamPath defines a list of paths to glob looking for JSON (// comments allowed)
    formatted files to define and initialize program parameters.  First valid file
    found is used, all others ignored.

--configPaths defines a list of paths to glob looking for .ini files to provide
    optional values for the parameters defined in the JSON param file.
    All .ini files found are processed; later ones overriding repeated options.
    Missing or ill-formatted files are ignored.

--configSections defines a list of "sections" in the .ini files to process.

--KeyWordParams  defines a list of key-word parameters to pass to others.  Each
    list item should be a string with "<keyword>='<value>'", with NO whitespace
    around the "=", and if whitespace in the value, single quote it.  Functions
    are expected to look for key-word arguments that start with the function name.
    I anticipate using this capability to have fine-grained control over the
    logging output.

--DefaultLoggingLevel is an integer logging level to set as the default; should be
    one of the values from https://docs.python.org/3/library/logging.html#logging-levels .

--verbosity or -v       increments a counter that increases the amount of output by
    LOWERING the logging level.

--quiet or -q           increments a counter that decreases the amount of output by
    RAISING the logging level.

--LogLevelInterval is the amount to change the logging level for each count
    of verbosity or quietude.  Determined as the difference between successive logging
    levels in https://docs.python.org/3/library/logging.html#logging-levels .
'''

    '''
    keyword arguments recognized:
    loggingLevel        => set logger to this level
    ParamPath           => alternate to setting ParamPath from command line option
    configPaths         => alternate to setting configPaths from command line option
    configSections      => alternate to setting configSections from command line option
    paramDefs           => Use this dictionary for parameter definitions instead of reading from a file.
    KeyWordParams       => A list of keyword arguments to pass to functions in this program.
                            These will be "evaluated" in this function and passed to any functions called.
                            They will be returned to the calling function as a configuration dictionary item
                            under the key "KeyWordParams" with the expectation that the calling function
                            will evaluate them and pass them as key word parameters to any other functions called.
    ProgramDocString    => Additional documentation to include in the help message.
'''
    consoleLogLevel = getConsoleLoggingLevel()
    fileLogLevel = getLogFileLoggingLevel()
########## Put this whole function in a try ... finally block so we can restore log levels on exit.
    try:
        if kwargs.get('loggingLevel') is not None:
            debug(f"In MakeParams, setting log level to {kwargs.get('loggingLevel')} from kwargs.")
            setConsoleLoggingLevel(kwargs.get('loggingLevel'))

        myFunctionId = GetFunctionId()
        debug(f'In MakeParams, my "ID" is {myFunctionId}')

        debug(f"kwargs is {kwargs}; add them to sys.argv: {sys.argv}")
        for k,v in kwargs.items():
            found = False
            for a in sys.argv:
                found |= a.startswith(f"--{k}")
            if not found:
                sys.argv.extend((f'--{k}={v}',))
        debug(f"After adding kwargs to sys.argv: {sys.argv}")

        parser = argparse.ArgumentParser(add_help=False)

        if sys.version_info < (3,8):
            parser.register('action', 'extend', ExtendAction)

        '''
        When using these optional command line args, if you use the <option>=<value> form,
        you can have only one value for that option (you can have multipel of these options however).
        If you use the <option> <value> form, you can have multiple values for the option, like:
        <option> <value> <value> ... <value> <next option>.
        Note that the shell removes quotes around values so argv gets a list of quoted strings;
        argparse processes the "=" form such that all the string past the "=" is the value including
        any spaces that were quoted on the command line.
        '''

        addBoilerPlateArgs(parser)
        # Done again because addBoilerPlateArgs may have changed logging levels
        if kwargs.get('loggingLevel') is not None:
            setConsoleLoggingLevel(kwargs.get('loggingLevel'))


        cmdArgs, leftOverArgs = parser.parse_known_args()      # get these config options
        argVars = vars(cmdArgs)        #  This gives dictionary access to cmdArgs which is a Namespace.
        debug(f"The BoilerPlateArgs options are: {cmdArgs}")
        kwargs['LogLevelInterval'] = 10            # Not modifiable but eventually passed thru kwargs
        debug(f"The (so far) unprocessed command line options are: {leftOverArgs}")
        ## Re-create sys.argv without the options that we have already processed.
        ## This will prevent errors if later command line processing doesn't recognize them.
        ## It is a good idea to include these options in whichever command line processor gives help
        ## so the help text will describe them.
        TempPath = [sys.argv[0], ]      # get the first argument to program, the program path
        TempPath.extend(leftOverArgs)   # put all the left overs on the end.
        sys.argv = TempPath             # Recreate sys.argv, without the ones we may have captured.

#####---------   Put boiler plate KeyWordParams into kwargs dictionary
        kwp = argVars.get('KeyWordParams')
        debug(f"KeyWordParams from command line are: {kwp}")
        if kwp is not None:
            for kwDef in kwp:
                # debug(f"key word def is {kwDef}")
                kwDefParts = kwDef.split("=", maxsplit=1)
                # debug(f"Key word parts are {kwDefParts!r}")
                if len(kwDefParts) < 2: continue    # don't try to do anything if it doesn't have an "="".
                kwargs[f"{kwDefParts[0]}"]= kwDefParts[1]
                debug(f"Created new kwarg: kwargs[{kwDefParts[0]!r}] = {kwDefParts[1]}")


        # Set logging levels for this function from command line KeyWordParams:
        #   ProgramParametersDefinitions.MakeParams.ConsoleLoggingLevel     and
        #   ProgramParametersDefinitions.MakeParams.FileLoggingLevel
        #           ---   or   ---
        # from boiler plate verbosity options -v and -q
        if (int(argVars['Quietude']) != 0) or (int(argVars['Verbosity']) != 0):
            newLogLevel = int(argVars['DefaultLoggingLevel']) + (int(argVars['Quietude']) - int(argVars['Verbosity'])) * kwargs['LogLevelInterval']
            kwargs['BiolerPlateLoggingLevel'] = newLogLevel
        SetLogLevelsFromKwargs(myFunctionId, **kwargs)  # Trouble is, setting console log level from here affects file logging too.

        paramFile = "from kwargs['paramDefs']"      # A string describing the source, in this case, not a file name.
        paramDefs = kwargs.get('paramDefs')
        if paramDefs is None:   # Only go read the file if we didn't get paramDefs as a keyword argument
            paramDefs, paramFile = GetParams(*args, **kwargs)   # GetParams returns a dictionary and the file from which it was read.
            SetLogLevelsFromKwargs(myFunctionId, **kwargs)
            debug(f'Read parameter definitions from file "{paramFile}" and got\n{paramDefs}')
        if (paramDefs is None) or (len(paramDefs) == 0):
            critical(f"We have no parameter definitions; just quit now.")
            return None

        paramDefs = ValidateParamDefs(paramDefs, *args, **kwargs)    # returns None if invalid
        SetLogLevelsFromKwargs(myFunctionId, **kwargs)
        debug(f'Validated paramDefs is {paramDefs!r}\n')
        paramDefs = createParams(paramDefs, *args, **kwargs)  #  CreateParams returns None if given None
        SetLogLevelsFromKwargs(myFunctionId, **kwargs)
        paramDefs['paramFile'] = paramFile

        ## If any of these options exist, include them in paramDefs so callers will get them too.
        for a in BoilerPlateArgs:
            paramName = a['paramName']
            if (argVars[a.get('dest')] is not None):        # Use command line args if they exist
                paramDefs[paramName] = argVars[a['dest']]   # overriding any params from params file.
            debug(f"paramDefs['{paramName}'] is {paramDefs.get(f'{paramName}')}")

        return paramDefs
    finally:        # Restore logging levels to what they were when we began.
        # setConsoleLoggingLevel(consoleLogLevel)
        # setLogFileLoggingLevel(fileLogLevel)
        pass

##########################  ValidateParamDefs  ##############################
def ValidateParamDefs(paramDefs=None, *args, **kwargs):
    consoleLogLevel = getConsoleLoggingLevel()
    fileLogLevel = getLogFileLoggingLevel()
    debug(f"Saved log levels are console: {consoleLogLevel}, file: {fileLogLevel}")
########## Put this whole function in a try ... finally block so we can restore log levels on exit.
    try:
        myFunctionId = GetFunctionId()
        SetLogLevelsFromKwargs(myFunctionId, **kwargs)
        logger.debug(f'In ValidateParamDefs, my "ID" is {myFunctionId}')

        if paramDefs is None:
            if kwargs.get('paramDefs')is not None:
                paramDefs = kwargs['paramDefs']
            else:
                return None
        ParamDefsSchema = Schema(ppds, name = 'Parameter Schema')
        try:
            ParamDefs = ParamDefsSchema.validate(paramDefs)
            logger.debug('Parameter definitions dict is valid.')
        except SchemaError as e:
            logger.critical('Parameter definition dictionary is not valid.  %s', e)
            logger.debug('%s' % e.autos)
            return None
        return ParamDefs
    finally:        # Restore logging levels to what they were when we began.
        # setConsoleLoggingLevel(consoleLogLevel)
        # setLogFileLoggingLevel(fileLogLevel)
        pass

##########################  createParams  ##############################
def createParams(paramDefs=None, *args, **kwargs):
    '''Create a dictionary of parameters and values from a validated param definitions dictionary.

    Parameters:
        paramDefs       A validated parameter definitions dictionary, or None.
                        If None, and kwargs['paramDefs'] is not None, use that
                        as a validated parameter definition dictionary.
    Calls GetConfig with kwargs argument to load a dictionary of configuration options.
    '''
    consoleLogLevel = getConsoleLoggingLevel()
    fileLogLevel = getLogFileLoggingLevel()
    debug(f"Saved log levels are console: {consoleLogLevel}, file: {fileLogLevel}")
########## Put this whole function in a try ... finally block so we can restore log levels on exit.
    try:
        myFunctionId = GetFunctionId()
        SetLogLevelsFromKwargs(myFunctionId, **kwargs)
        logger.debug(f'In createParams, my "ID" is {myFunctionId}')

        if kwargs.get('loggingLevel') is not None:
            # setConsoleLoggingLevel(kwargs.get('loggingLevel'))
            pass

        if paramDefs is None:
            if kwargs.get('paramDefs')is not None:
                paramDefs = kwargs['paramDefs']
            else:
                return None

        progDescription = paramDefs.get('ProgramDescription') or ""   #  Used for help text only.

        progEpilog = ""
        if GetConfig.__doc__ is not None:
            # debug.info(GetConfig.__doc__)   # shows what it really looks like
            progEpilog += f'{GetConfig.__doc__}'
        if kwargs.get("ProgramDocString") is not None:
            progEpilog += kwargs.get('ProgramDocString')

        #  Define some variables that will be in the local scope of the exec statements below (along with the created variables).
        parser = argparse.ArgumentParser(
            description = progDescription
            , usage='%(prog)s [options]'
            , formatter_class=argparse.RawDescriptionHelpFormatter
            , epilog = progEpilog
            )

        if sys.version_info < (3,8):
            parser.register('action', 'extend', ExtendAction)

        debug(f"Adding any PositionalArgParserArgs to parser.")
        if paramDefs.get('PositionalArgParserArgs') is not None:
            debug(f"There is a PositionalArgParserArgs section of the parameters.")
            p = paramDefs.get('PositionalArgParserArgs')
            paramName = p.get('paramName')
            # Make sure paramName is first argument to add_argument.
            cmdArg = [f"{paramName!r}", ]     # get param name which is guaranteed to exist by validation
            for (k, v) in p.items():
                if (k not in validArgParserKeyWords) or (v is None): continue
                if k in nonStringParserKeyWords: cmdArg.append(f"{k}={v}")
                else:  cmdArg.append(f"{k}={v!r}")
            cmdArg = addArg.format(cmdArg=", ".join(cmdArg), paramName=paramName)
            debug(f"Executing {cmdArg}")
            exec(cmdArg)

        createdParams = { 'parser': parser
                , 'cfg': GetConfig(**kwargs)}   # configPaths passed as keyword arg if not default.
        SetLogLevelsFromKwargs(myFunctionId, **kwargs)
        debug(f'Initial created Params is {createdParams!r}')
        ##  keep track of keys that we do not want to return to caller.
        localOnlyKeys = ['parser', 'cfg']

        ## Go through the list of parameter definitions, creating entries in the "createdParams" dict
        ## and creating program command line options for them (if so specified in the paramDef).
        #### "createdParams" is used as the "local" variables in the exec statements below; this
        #### allows us to create parameters in the exec statement and give them values.
        for p in paramDefs.get('Parameters'):
                ## The rest of the function deals with the list of parameters under the key 'Parameters'
            paramName = p['paramName']
            if p.get('intermediate') is not None:
                if p['intermediate']:
                    localOnlyKeys.append(paramName)
                    debug(f"Intermediate param {paramName} will be removed from final dictionary.")
            debug(f"\nInitial definition of parameter {paramName}, setting default value.")
            if p.get('default') is not None:
                if p.get('type') is not None:
                    arg = f'''{paramName} = {p['type']}({p['default']!r})'''
                else:
                    arg = f'''{paramName} = {p['default']}'''
                debug(f'exec({arg})')
                exec(arg, globals(), createdParams)
            else:
                createdParams[paramName] = None
            debug(f"Created param {paramName} as {createdParams[paramName]}.")

            ## Now that the parameter is created with its default value, see if we need a command line option for it.
            a = p.get('argParserArgs')
            if a is not None:
                debug(f"Adding '{paramName}' to argparse")
                #  schema validation does not guarantee at least one of these, so we do it here.
                if (a.get('short') is None) and (a.get('long')  is None):
                    critical(f'One of argParserArgs options in "short" or "long" form must be present and not None: {p!r}')
                    logger.warning(f"This command line option will not be processed.")
                    continue
                cmdArg = list()
                # Special add_argument key processing ...
                if a.get('short') is not None:          # This is not a keyword argument, just put it in as is.
                    cmdArg.append(f"{a.get('short')!r}")       # put in short option and remove from {a}
                if a.get('long') is not None:           # This is not a keyword argument, just put it in as is.
                    cmdArg.append(f"{a.get('long')!r}")        # put in long option and remove from {a}
                #  For some reason add_argument barfs if a type is specified and one of these store kinds is used.
                if (a.get('action') is not None) and (a['action'] in argParserActionsWithNoType) and (a.get('type') is not None):
                    a.pop('type')               # In this case, remove the "type" keyword

                if (a.get('help') is None) and (p.get('description') is not None):
                    a['help'] = f"{p['description']!r}"        # Default the help string from parameter description
                #  Add keyword arguments to the list of add_argument args
                for (k, v) in a.items():                # add other keyword arguments to arg list.
                    if (k not in validArgParserKeyWords) or (v is None): continue
                    if k in nonStringParserKeyWords: cmdArg.append(f"{k}={v}")
                    else:  cmdArg.append(f"{k}={v!r}")
                ## put together the whole add_argument call
                cmdArg = ', '.join(cmdArg)
                arg = addArg.format(cmdArg=cmdArg, a=a, paramName=paramName)
                debug(f'exec({arg})')
                try:
                    exec(arg, globals(), createdParams)
                    logger.debug(f'Successfully added command line argument option for "{paramName}""')
                except Exception as e:
                    logger.warning(f"Trying to add arg had an exception: {e}")
                    pass

        addBoilerPlateArgs(parser, **kwargs)

        debug(f"Argument parser help is:\n\n{createdParams['parser'].format_help()}")
        createdParams['args'], leftOverArgs = createdParams['parser'].parse_known_args()
        localOnlyKeys.append('args')
        if len(leftOverArgs) > 0:
            logger.warning(f"These command line args were ignored: {leftOverArgs!r}")
        debug(createdParams['args'])


        debug(f"CreatedParams before applying the config params and command line options: {createdParams!r}")
        #### if there is no configuration option for the item, it won't be set from the config file; it will be left as its default.

        debug(f"\n\nApplying values from config file, then from program arguments.")
        try:
            for p in paramDefs.get('Parameters'):
                paramName = p['paramName']
                debug(f"Looking for config & option for: {paramName} ({createdParams[paramName]})")
                a = p.get('argParserArgs')
                # get the type of the parameter
                t = p.get('type', '')
                # get the config file value for the parameter
                if p.get('configName') is not None:
                    configName = p['configName']
                    cfgVal = createdParams['cfg'].get(configName)
                    if cfgVal is not None:
                        debug(f"Config file setting {paramName} to {cfgVal!r}")
                        arg = f'''{paramName} = {t}({cfgVal!r})'''
                        debug(f'exec({arg})')
                        exec(arg, globals(), createdParams)
                        debug(f"{paramName} is %s"%eval(f"{paramName}", globals(), createdParams))
                    else: debug(f"Config file has no option for {configName}")
                else: debug(f"There is no configName option for parameter {paramName}, don't look in config file.")
                # if the parameter is specified on the command line, it overrides the config file
                if a is not None:
                    optDest = a['dest']
                    debug(f"Trying for command line arg............ {optDest}")
                    ## Multi-line exec string must obey indenting rules too.
                    arg = setParamFromOption.format(optDest=optDest, paramName=paramName)
                    debug(f'exec({arg})')
                    exec(arg, globals(), createdParams)
                    debug(f"{paramName} is %s"%eval(f"{paramName}", globals(), createdParams))
                else: debug(f"No command line option defined for {paramName}")
        except UserWarning as w:
            logger.warning(w)

        # Remove items that we don't want to return to caller.
        for k in localOnlyKeys:
            if k in createdParams:
                del createdParams[k]        # Removes key & value
        # Return the final product.
        return createdParams
    finally:        # Restore logging levels to what they were when we began.
        # setConsoleLoggingLevel(consoleLogLevel)
        # setLogFileLoggingLevel(fileLogLevel)
        pass
