
'''
A function to load a logging configuration dictionary from:
    A keyword specifiec list of paths (paths=str or list)
    -- or  --
    A list of default configruation file locations.

Parameters:
    ProgName        required first argument: is the name of the program.
    ProgPath        required second argument: is the path to the program.
Keyword parameters:
    paths           optional: is a file name or list of file names from
                    which to attempt to load a configuration dictionary.
The first file from the list that loads successfully is used; all
others are ignored.
File types: '.toml', '.jsonc', and '.json' are recognized and loaded.

To define logging: the calling program needs to:

from progparams.GetLoggingDict import GetLoggingDict
config_dict = GetLoggingDict(ProgName, ProgPath)
logging.config.dictConfig(config_dict)

then create loggers like:

errLogger = logging.getLogger("Debug  Logger")
console = logging.getLogger("ConsoleLogger")
'''

# __all__ = (
#       GetLoggingDict
#     , setConsoleLoggingLevel
#     , getConsoleLoggingLevel
#     , setLogFileLoggingLevel
#     , getLogFileLoggingLevel
# )

import os               #   https://docs.python.org/3/library/os.html
import toml             #   https://github.com/uiri/toml    https://github.com/toml-lang/toml
# comment json strips python and "//" comments form json before applying json.load routines.
import commentjson      #   https://github.com/vaidik/commentjson       https://commentjson.readthedocs.io/en/latest/
# Lark is used by commentjson -- import commented out, but here for documentation.
# import lark             #   https://github.com/lark-parser/lark    https://lark-parser.readthedocs.io/en/latest/
import logging          #   https://docs.python.org/3/library/logging.html

def GetLoggingDict(ProgName: str, ProgPath: str, *args, **kwargs) -> dict :
    ##############Logging Settings##############
    #####  Setup logging; first try for file specific, and if it doesn't exist, use a folder setup file.
    #
    #   See https://docs.python.org/3/howto/logging-cookbook.html#formatting-styles for interesting ideas.
    #
    def updateLoggingDict(config_dict: dict) -> dict :
        if 'log_file_path' in config_dict:
            logPath = os.path.expandvars(config_dict['log_file_path'])
            os.makedirs(logPath, exist_ok=True)
        else:
            logPath=""
        for p in config_dict['handlers'].keys():
            if 'filename' in config_dict['handlers'][p]:
                fn = os.path.join(logPath, config_dict['handlers'][p]['filename'].replace('<replaceMe>', ProgName))
                config_dict['handlers'][p]['filename'] = fn
        return config_dict


    if kwargs.get('paths') is not None:
        paths = kwargs['paths']
        if isinstance(paths, str): paths = list(paths)
    else:
        paths = (     os.path.join(ProgPath, ProgName + '_loggingconf.toml')        # in order to be checked
                    , os.path.join(ProgPath, 'Loggingconf.toml')
                    , os.path.join(ProgPath, ProgName + '_loggingconf.jsonc')
                    , os.path.join(ProgPath, 'Loggingconf.jsonc')
                    , os.path.join(ProgPath, ProgName + '_loggingconf.json')
                    , os.path.join(ProgPath, 'Loggingconf.json')
                )
    for path in paths:
        if not os.path.isfile(path): continue   # ignore paths entries that are not files.
        _, ext = os.path.splitext(path)
        try:
            if ext == '.toml':
                config_dict = toml.load(path)
            elif (ext == '.json') or (ext == '.jsonc'):
                config_dict = commentjson.load(open(path))
            else:
                continue
            return updateLoggingDict(config_dict)
        except Exception:
            print(f"Attempt to read existing file: {path} failed.  Trying another file.")
            pass
    print("Logging configuration file not found.")
    return {}

def setConsoleLoggingLevel(loggingLevel, LGR=None):
    '''
    Find the root logger and set the logging level of each StreamHandler to the loggingLevel.
    '''
    if LGR is None:
        LGR = logging.getLogger(__name__)
    lgr = LGR
    while (lgr is not None) and (lgr.propagate) and (lgr.parent is not None): lgr = lgr.parent
    for h in lgr.handlers:
        if isinstance(h, logging.StreamHandler):  h.setLevel(loggingLevel)
    pass

def setLogFileLoggingLevel(loggingLevel, LGR=None):
    '''
    Find the root logger and set the logging level of each FileHandler to the loggingLevel.
    '''
    if LGR is None:
        LGR = logging.getLogger(__name__)
    lgr = LGR
    while (lgr is not None) and (lgr.propagate) and (lgr.parent is not None): lgr = lgr.parent
    for h in lgr.handlers:
        if isinstance(h, logging.FileHandler):  h.setLevel(loggingLevel)
    pass

def getConsoleLoggingLevel(LGR=None):
    '''
    Find the root logger and get the logging level of the first StreamHandler.
    '''
    if LGR is None:
        LGR = logging.getLogger(__name__)
    lgr = LGR
    while (lgr is not None) and (lgr.propagate) and (lgr.parent is not None): lgr = lgr.parent
    for h in lgr.handlers:
        if isinstance(h, logging.StreamHandler):  return lgr.getEffectiveLevel()
    return None

def getLogFileLoggingLevel(LGR=None):
    '''
    Find the root logger and get the logging level of the first FileHandler.
    '''
    if LGR is None:
        LGR = logging.getLogger(__name__)
    lgr = LGR
    while (lgr is not None) and (lgr.propagate) and (lgr.parent is not None): lgr = lgr.parent
    for h in lgr.handlers:
        if isinstance(h, logging.FileHandler):  return lgr.getEffectiveLevel()
    return None
