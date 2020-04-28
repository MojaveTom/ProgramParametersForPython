
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
    Find the root logger and set the logging level of the first handler to the loggingLevel.
    '''
    if LGR is None:
        LGR = logging.getLogger(__name__)
    #  We know about all the loggers defined for this module;
    #  so we can set the level for all of them here in one place.
    ####  Alright, I know this is flakey.  The right way to do this
    ####  is to analyze config_dict and find out which logger handler
    ####  is for the console.
    ####   logger.handlers is a list that must be indexed by a number.
    ####  You can make a dictionary of logger.handler names to indexes:
    ####  for i, n in enumerate(config_dict['loggers']['Debug  Logger']['handlers']): d[n]=i
    ####  "d" then looks like:  {'console': 0, 'debug_file_handler': 1}
    ####   But then you still have to know the name of the handler you want!!
    #>>> logger.handlers
    ##[<StreamHandler <stdout> (NOTSET)>, <RotatingFileHandler /Volumes/UsersData/tom/Logs/HomeGraphing.log (NOTSET)>]
    #######   ARGH  Too much for my tired brain.
    lgr = LGR
    while (lgr is not None) and (lgr.name is not None) and (lgr.name != 'root'): lgr = lgr.parent
    if len(lgr.handlers) > 0:
        lgr.handlers[0].setLevel(loggingLevel)
    pass

def setLogFileLoggingLevel(loggingLevel, LGR=None):
    '''
    Find the root logger and set the logging level of the second handler to the loggingLevel.
    '''
    if LGR is None:
        LGR = logging.getLogger(__name__)
    lgr = LGR
    while (lgr is not None) and (lgr.name is not None) and (lgr.name != 'root'): lgr = lgr.parent
    if len(lgr.handlers) > 1:
        lgr.handlers[1].setLevel(loggingLevel)
    pass

def getConsoleLoggingLevel(loggingLevel, LGR=None):
    '''
    Find the root logger and get the logging level of the first handler.
    '''
    if LGR is None:
        LGR = logging.getLogger(__name__)
    lgr = LGR
    while (lgr is not None) and (lgr.name is not None) and (lgr.name != 'root'): lgr = lgr.parent
    if len(lgr.handlers) > 0:
        return lgr.handlers[0].getEffectiveLevel()
    return 0

def getLogFileLoggingLevel(loggingLevel, LGR=None):
    '''
    Find the root logger and get the logging level of the second handler.
    '''
    if LGR is None:
        LGR = logging.getLogger(__name__)
    lgr = LGR
    while (lgr is not None) and (lgr.name is not None) and (lgr.name != 'root'): lgr = lgr.parent
    if len(lgr.handlers) > 1:
        return lgr.handlers[1].getEffectiveLevel()
    return 0
