
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
import json             #   https://docs.python.org/3/library/json.html
import toml             #   https://github.com/uiri/toml    https://github.com/toml-lang/toml
# comment json strips python and "//" comments form json before applying json.load routines.
import commentjson      #   https://github.com/vaidik/commentjson       https://commentjson.readthedocs.io/en/latest/
# Lark is used by commentjson -- import commented out, but here for documentation.
# import lark             #   https://github.com/lark-parser/lark    https://lark-parser.readthedocs.io/en/latest/
import logging
                        #   https://github.com/keleshev/schema
from schema import Schema, And, Or, Use, Optional, SchemaError
import argparse         #   https://docs.python.org/3/library/argparse.html
import configparser     #   https://docs.python.org/3/library/configparser.html
## The following may be needed to initialize some params
# import time             #   https://docs.python.org/3/library/time.html
# import datetime         #   https://docs.python.org/3/library/datetime.html

logger = logging.getLogger(__name__)
debug = logger.debug
critical = logger.critical
info = logger.info
logger.setLevel('NOTSET')
console = logging.getLogger("ConsoleLogger")

MyPath = os.path.dirname(os.path.realpath(__file__))
logger.debug(f'MyPath in ProgramParametersDefinitions is: {MyPath}')
ProgName, ext = os.path.splitext(os.path.basename(sys.argv[0]))
ProgPath = os.path.dirname(os.path.realpath(sys.argv[0]))

'''
#########################################
The class below might be replaced by one of these packages:
> pip3 install pydantic[email,typing_extensions,dotenv]
pydantic seems way overkill for what I want.
- or -
> pip3 install prodict
prodict is a worthy option; only thing is, it doesn't
keep the initialization dict up-to-date with mods to
the prodict version.  Trying prodict...

I'm not happy with my ProgramParameters class; it seems
kinda a kludge, especially in __getattribute__, but it
does keep the underlying dictionary up-to-date with mods
to dotted references to the instance.
#########################################'''
# class ProgramParameters(object):
#     """Simple object for storing attributes.
#     Provides a simple string representation.
#     setAttributesFromDict function sets attributes.
#     """

#     def __init__(self, attrDict=None):
#         # print(f"In __init__")
#         self._theDict = dict()      # empty dictionary
#         if attrDict is not None:
#             self.setAttributesFromDict(attrDict)

#     def setAttributesFromDict(self, attrDict):
#         # print(f"In setAttributesFromDict")
#         self._theDict = attrDict
#         for name, val in attrDict.items():
#             setattr(self, name, val)

#     def setattr(self, name, val):
#         '''
#         This func called when the client program calls does <ProgramParameters instance>.setattr(<name>, <val>)
#         and this in turn calls __setattr__
#         '''
#         # print(f"In setattr")
#         self._theDict[name] = val
#         # print(f"in setattr, _theDict becomes {self._theDict}")
#         setattr(self, name, val)

#     def __setattr__(self, name, val):
#         '''
#         __setattr__ is called when the client program calls does an assignment <ProgramParameters instance>.attrib = val
#          OR when the client program calls does <ProgramParameters instance>.setattr(<name>, <val>) {which calls us}
#         '''
#         myself = self           #object.__getattribute__(self, 'self')
#         # print(f"in __setattr__, args are {myself}, {name}, {val}")
#         super().__setattr__(name, val)
#         mydict = object.__getattribute__(self, '_theDict')
#         ## Don't put _theDict in _theDict; otherwise keep _theDict up to date with the attributes.
#         if (mydict is not None) and (not name == '_theDict'): mydict[name] = val
#         # print(f"in __setattr__, _theDict becomes {mydict}")

#     ######  What we want to accomplish is to return the attribute with the _theDict object of the
#     ######      same name, even it the dictionary item was assigned a value elsewhere.
#     ###  This function overrides the object.__getattribute__ but I haven't figured out how to make
#     ###   everything work with this enabled.  Calls to object.__getattribute__(self, '<name>') are
#     ###   supposed to keep down infinite recursion; I just don't know where-all to do it.
#     def __getattribute__(self, name):
#         myself = self           #object.__getattribute__(self, 'self')
#         retval =object.__getattribute__(self, name)     #  Hopefully just to super function.
#         mydict = None
#         moduleDict = object.__getattribute__(self, '__dict__')
#         # print(f"in __getattribute__, args are self, {name}; moduleDict is: {moduleDict}")

#         if '_theDict' in moduleDict.keys():
#             mydict = object.__getattribute__(self,'_theDict')
#             # print(f"Got _theDict: {mydict}")
#         ## get the value from _theDict.
#         if (mydict is not None) and (not name == '_theDict'):
#             if name in mydict:
#                 retval = mydict[name]
#         return retval

#     def __getattr__(self, name):
#         '''
#         __getattr__ is called when the client program calls <ProgramParameters instance>.get(...)
#         but NOT when the client program references <ProgramParameters instance>.<attrib>
#         '''
#         myself = self           #object.__getattribute__(self, 'self')
#         # print(f"in __getattr__, args are self, {name}")
#         mydict = object.__getattribute__(self,'_theDict')
#         # print(f"in __getattr__, _theDict is: {mydict}")
#         retval = None    # set the default value.
#         ## get the value from _theDict.
#         if (mydict is not None) and (not name == '_theDict'):
#             if name in mydict:
#                 retval = mydict[name]
#         # print(f"in __getattr__, returning {retval}")
#         return retval

#     def __get__(self, name):
#         ''' __get__ is not called;
#         __getattr__ is called when the client program calls <ProgramParameters instance>.get(...)
#         but NOT when the client program references <ProgramParameters instance>.<attrib>
#         '''
#         # print(f"in __get__, args are self, {name}")
#         mydict = object.__getattribute__(self,'_theDict')
#         # print(f"in __get__, _theDict is: {mydict}")
#         retval = None    # set the default value.
#         ## get the value from _theDict.
#         if (mydict is not None) and (not name == '_theDict'):
#             if name in mydict:
#                 retval = mydict[name]
#         # print(f"in __get__, returning {retval}")
#         return retval

#     def get(self, attrName, fallBack=None):
#         ''' get is not called;
#         __getattr__ is called when the client program calls <ProgramParameters instance>.get(...)
#         '''
#         retval = getattr(self, attrName, fallBack)
#         if retval is None: retval = fallBack
#         return retval

#     def __contains__(self, key):
#         if isinstance(key, str): return key in self.__dict__
#         if isinstance(key, set): return key <= set(self.__dict__)
#         if isinstance(key, frozenset): return key <= set(self.__dict__)
#         else: return False

#     def __repr__(self):
#         type_name = type(self).__name__
#         arg_strings = ['{may not agree with individual attributes}', ]
#         star_args = {}
#         for arg in self._get_args():
#             arg_strings.append(repr(arg))
#         for name, value in self._get_kwargs():
#             ## Don't put _theDict in the representation.
#             if not name == '_theDict':
#                 if name.isidentifier():
#                     arg_strings.append('%s=%r' % (name, value))
#                 else:
#                     star_args[name] = value
#         if star_args:
#             arg_strings.append('**%s' % repr(star_args))
#         return '%s(%s)' % (type_name, ', '.join(arg_strings))

#     def _get_kwargs(self):
#         d = self.__dict__
#         # d.pop('_theDict', None)
#         return d.items()

#     def _get_args(self):
#         return []

#############  GetConfig
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
    import glob
    from itertools import chain
    flatten = chain.from_iterable

    # Pick up configPaths from kwargs or default.
    if kwargs.get('configPaths') is not None:
        fns = kwargs['configPaths']
        if isinstance(fns, str): fns = (fns,)
    else:
        # Look for .jsonc and .json files with our program name in the cwd.
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
    info(f'Using configuration file(s) at: {cfgFilesUsed}')
    if len(config) == 0:        # nothing loaded into config (which looks like a dict)
        return cfgDict          # return empty dict

    for cfgSection in cfgSections:
        if cfgSection in config:
            info(f"Reading INI file section: {cfgSection}")
            cfg = config[cfgSection]        # saved as variable so could print in debugging
            cfgDict = {**cfgDict, **cfg}    # Puts both dictionaries into one, second overriding
    return cfgDict

# with open(os.path.join(MyPath, "ProgramParamsDefs.json"), 'w') as file:
#     json.dump(ppds, file, indent=2)
# Doesn't work to put schema definition in a JSON file
# since some of the keys are class objects defined in schema.
# Can't pickle ppds either.

ppds = {
        Optional('ProgramDescription', default=None): str,
            'Parameters': [{'paramName': str
            , 'description': str
            , Optional('configName', default=None): Use(str.casefold)       # make sure all configNames are lower case.
            , Optional('default', default=None): Use(str)
            , Optional('type'): Use(str)
            , Optional('argParserArgs', default=None): { Optional('short', default=None): And(str, lambda s: s != '-h', error="The short command option '-h' is reserved for help.")
                        , Optional('long', default=None): And(str, lambda s: s != '--help', error="The long command option '--help' is reserved for help.")
                        , 'dest': str
                        , 'action': str
                        }
            } ]
        }

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

def MakeParams(*args, **kwargs):        # args is a list of non-keyword arguments; kwargs is a dict of keyword args.
    '''Top level function to create a dictionary of parameters from a JSON params file and .ini files.

Get a couple command line arguments before proceeding:
    We are almost always called with NO parameters, but we
    want to allow a couple command line arguments to modify
    how we process param files and config files.

--ParamPath defines a list of paths to glob looking for JSON (// comments allowed)
    formatted files to define and initialize program parameters.  First valid file
    found is used, all others ignored.

--configPaths defines a list of paths to glob looking for .ini files to provide
    optional values for the parameters defined in the JSON param file.
    All .ini files found are processed; later ones overriding repeated options.
    Missing or ill-formatted files are ignored.

--configSections defines a list of "sections" in the .ini files to process.
'''

    TempParser = argparse.ArgumentParser(add_help=False)

    if sys.version_info < (3,8):
        #  Defines "extend" action for argparse which was introduced in python3.8
        class ExtendAction(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                items = getattr(namespace, self.dest) or []
                items.extend(values)
                setattr(namespace, self.dest, items)

        TempParser.register('action', 'extend', ExtendAction)

    '''
    When using these optional command line args, if you use the <option>=<value> form,
    you can have only one value for that option (you can have multipel of these options however).
    If you use the <option> <value> form, you can have multiple values for the option, like:
    <option> <value> <value> ... <value> <next option>.
    Note that the shell removes quotes around values so argv gets a list of quoted strings;
    argparse processes the "=" form such that all the string past the "=" is the value including
    any spaces that were quoted on the command line.
    '''
    TempParser.add_argument("--configPaths", action="extend", nargs="+", type=str)
    TempParser.add_argument("--configSections", action="extend", nargs="+", type=str)
    TempParser.add_argument("--ParamPath", action="extend", nargs="+", type=str)
    cmdArgs, leftOverArgs = TempParser.parse_known_args()      # get these config options
    debug(f"The configPaths and ParamPath options are: {cmdArgs}")
    debug(f"The (so far) unprocessed command line options are: {leftOverArgs}")
    ## Re-create sys.argv without the options that we have already processed.
    ## This will prevent errors if later command line processing doesn't recognize them.
    ## It is a good idea to include these options in whichever command line processor gives help
    ## so the help text will describe them.
    TempPath = [sys.argv[0], ]      # get the first argument to program, the program path
    TempPath.extend(leftOverArgs)   # put all the others on the end.
    sys.argv = TempPath             # Recreate sys.argv, without the ones we may have captured.
    ## If any of these options exist, include them in kwargs so others will get them too.
    if cmdArgs.configPaths is not None: kwargs['configPaths'] = cmdArgs.configPaths
    if cmdArgs.configSections is not None: kwargs['configSections'] = cmdArgs.configSections
    if cmdArgs.ParamPath is not None: kwargs['ParamPath'] = cmdArgs.ParamPath
    debug(f"kwargs['configPaths'] is {kwargs.get('configPaths')}")
    debug(f"kwargs['configSections'] is {kwargs.get('configSections')}")
    debug(f"kwargs['ParamPath'] is {kwargs.get('ParamPath')}")

    paramDefs = kwargs.get('paramDefs')
    if paramDefs is None:   # Only go read the file is we didn't get paramDefs as a keyword argument
        if kwargs.get('ParamPath') is not None:
            fns = kwargs['ParamPath']
            if isinstance(fns, str): fns = (fns,)
        else:
            # Look for .jsonc and .json files with our program name in the cwd.
            fns = (f"{ProgName}*Params.toml", f"{ProgName}*Params.jsonc", f"{ProgName}*Params.json")
        # glob process param paths
        import glob
        from itertools import chain
        flatten = chain.from_iterable
        # Make a list of actual files to read.
        fns = list(flatten([glob.glob(x) for x in fns]))

        debug(f"Looking for first good JSON or TOML parameters file in {fns!r}")
        if fns is None: return None     # no paramDefs, and no files to read it from.
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
                    return None
                debug(f"Successfully loaded paramDefs: {paramDefs}")
                break       #  exit the for loop without doing the else clause.
            except json.JSONDecodeError as e:
                info(f"Json file: {fn} did not load successfully: {e}")
            except FileNotFoundError as f:
                info(f"Param file: {fn} does not exist. {f}")
            except IsADirectoryError as d:
                info(f"Param file: {fn} is a directory! {d}")
            except toml.TomlDecodeError as t:
                info(f"Toml file: {fn} did not load successfully: {t}")
        else: return None

    paramDefs = ValidateParamDefs(paramDefs, *args, **kwargs)    # returns None if invalid
    debug(f'Validated paramDefs is {paramDefs!r}\n')
    return createParams(paramDefs, *args, **kwargs)  #  CreateParams returns None if given None

def ValidateParamDefs(paramDefs=None, *args, **kwargs):
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

def createParams(paramDefs=None, *args, **kwargs):
    '''Create a dictionary of parameters and values from a validated param definitions dictionary.

    Parameters:
        paramDefs       A validated parameter definitions dictionary, or None.
                        If None, and kwargs['paramDefs'] is not None, use that
                        as a validated parameter definition dictionary.
    Calls GetConfig with kwargs argument to load a dictionary of configuration options.
    '''
    if paramDefs is None:
        if kwargs.get('paramDefs')is not None:
            paramDefs = kwargs['paramDefs']
        else:
            return None

    class BlankLinesHelpFormatter (argparse.HelpFormatter):
        # # add empty line if help ends with \n
        # def _split_lines(self, text, width):
        #     lines = super()._split_lines(text, width)
        #     if text.endswith('\n'):
        #         lines += ['']
        #     return lines
        def _split_lines(self, text, width):
            return text.splitlines()

    progDescription = paramDefs.get('ProgramDescription') or ""   #  Used for help text only.

    ## The rest of the function deals with the list of parameters under the key 'Parameters'
    paramDefs = paramDefs.get('Parameters')

    progEpilog = ""
    ## Was hoping to use ArgumentParser(epilog=str) to give more information from
    ## GetConfig using its __doc__ string, but ArgumentParser strips formatting from
    ## epilog string, so the additional info is useless.
    if GetConfig.__doc__ is not None:
        # console.info(GetConfig.__doc__)   # shows what it really looks like
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
    parser.add_argument("--ParamPath", action="append", nargs="+", type=str
        , help='Give multiple times to make a list of paths to .toml or .jsonc or .json parameter definition files.  The first successful load wins.\n')
    parser.add_argument("--configPaths", action="append", nargs="+", type=str
        , help='Give multiple times to make a list of paths to configuration ".ini" files.\n')
    parser.add_argument("--configSections", action="append", nargs="+", type=str
        , help='Give multiple times to make a list of configuration sections to load from .ini files.\n')

    createdParams = { 'parser': parser
            , 'cfg': GetConfig(**kwargs)}   # configPaths passed as keyword arg if not default.
    debug(f'Initial created Params is {createdParams!r}')
    ##  keep track of keys that we do not want to return to caller.
    localOnlyKeys = ['parser', 'cfg']

    ## Go through the list of parameter definitions, creating entries in the "createdParams" dict
    ## and creating program command line options for them (if so specified in the paramDef).
    #### "createdParams" is used as the "local" variables in the exec statements below; this
    #### allows us to create parameters in the exec statement and give them values.
    for p in paramDefs:
        debug(f"\nInitial definition of parameter {p['paramName']}, setting default value.")
        if p.get('default') is not None:
            if p.get('type') is not None:
                arg = f'''{p['paramName']} = {p['type']}({p['default']!r})'''
            else:
                arg = f'''{p['paramName']} = {p['default']}'''
            debug(f'exec({arg})')
            exec(arg, globals(), createdParams)
        else:
            createdParams[p['paramName']] = None
        debug(f"Created param {p['paramName']} as {createdParams[p['paramName']]}.")

        ## Now that the parameter is created with its default value, see if we need a command line option for it.
        a = p.get('argParserArgs')
        if a is not None:
            debug(f"Adding '{p['paramName']}' to argparse")
            cmdArg = list()
            #  schema validation does not guarantee at least one of these, so we do it here.
            if a.get('short') is not None: cmdArg.append(f"'{a['short']}'")
            if a.get('long')  is not None: cmdArg.append(f"'{a['long']}'")
            ## This next is for non-optional command line args, but it is too ambiguous to use (order is important, etc.).
            # if a.get('cmdArg') is not None: cmdArg.append(f"'{a['cmdArg']}'")
            if len(cmdArg) == 0:
                critical(f'One of argParserArgs options in "short" or "long" form must be present and not None: {p!r}')
                return None
            cmdArg = ', '.join(cmdArg)
            #  If there is no description, leave it out of add_argument.
            descrip = p.get('description')
            des = ''
            if descrip is not None:
                des = f', help={descrip!r}'
            #  For some reason add_argument barfs if a type is specified and one of these store kinds is used.
            typ = ''
            if a['action'] not in ('store_const', 'store_true', 'store_false'):
                typ = f', type={p["type"]}'
            ## put together the whole add_argument call
            arg = f'''parser.add_argument({cmdArg}, dest={a['dest']!r}, action={a['action']!r}{typ}{des})'''
            debug(f'exec({arg})')
            exec(arg, globals(), createdParams)

    createdParams['args'] = createdParams['parser'].parse_args()
    localOnlyKeys.append('args')
    # debug(createdParams['args'])

    # debug(f"Argument parser help is:  {createdParams['parser'].format_help()}")

    debug(f"CreatedParams before applying the config params and command line options: {createdParams!r}")
    #### if there is no configuration option for the item, it won't be set from the config file; it will be left as its default.

    debug(f"\n\nApplying values from config file, then from program arguments.")
    try:
        for p in paramDefs:
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
                    debug(f"{p['paramName']} is %s"%eval(f"{p['paramName']}", globals(), createdParams))
                else: debug(f"Config file has no option for {configName}")
            else: debug(f"There is no configName option for parameter {paramName}, don't look in config file.")
            # if the parameter is specified on the command line, it overrides the config file
            if a is not None:
                debug(f"Trying for command line arg............")
                optDest = a['dest']
                ## Multi-line exec string must obey indenting rules too.
                arg = f"""if args.{optDest} is not None: {paramName} = args.{optDest}
else: debug("There is no cmd option given for {paramName}")"""
                debug(f'exec({arg})')
                exec(arg, globals(), createdParams)
                debug(f"{p['paramName']} is %s"%eval(f"{p['paramName']}", globals(), createdParams))
            else: debug(f"No command line option defined for {paramName}")
    except UserWarning as w:
        logger.warning(w)

    # Remove items that we don't want to return to caller.
    for k in localOnlyKeys:
        if k in createdParams:
            del createdParams[k]        # Removes key & value
    # Return the final product.
    return createdParams
