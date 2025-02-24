import pprint

_colors = {"BLACK": '\033[30m',
"RED": '\033[31m',
"GREEN": '\033[32m',
"YELLOW": '\033[33m', # orange on some systems
"BLUE": '\033[34m',
"MAGENTA": '\033[35m',
"CYAN": '\033[36m',
"LIGHT_GRAY": '\033[37m',
"DARK_GRAY": '\033[90m',
"BRIGHT_RED": '\033[91m',
"BRIGHT_GREEN": '\033[92m',
"BRIGHT_YELLOW": '\033[93m',
"BRIGHT_BLUE": '\033[94m',
"BRIGHT_MAGENTA": '\033[95m',
"BRIGHT_CYAN": '\033[96m',
"WHITE": '\033[97m'}

RESET = '\033[0m' # called to return to standard terminal text color

BACKGROUND_BLACK = '\033[40m'
BACKGROUND_RED = '\033[41m'
BACKGROUND_GREEN = '\033[42m'
BACKGROUND_YELLOW = '\033[43m' # orange on some systems
BACKGROUND_BLUE = '\033[44m'
BACKGROUND_MAGENTA = '\033[45m'
BACKGROUND_CYAN = '\033[46m'
BACKGROUND_LIGHT_GRAY = '\third-party033[47m'
BACKGROUND_DARK_GRAY = '\033[100m'
BACKGROUND_BRIGHT_RED = '\033[101m'
BACKGROUND_BRIGHT_GREEN = '\033[102m'
BACKGROUND_BRIGHT_YELLOW = '\033[103m'
BACKGROUND_BRIGHT_BLUE = '\033[104m'
BACKGROUND_BRIGHT_MAGENTA = '\033[105m'
BACKGROUND_BRIGHT_CYAN = '\033[106m'
BACKGROUND_WHITE = '\033[107m'

def cprint(color, *args, **kw):
    color = _colors[color.upper()]
    if kw.pop("pretty", False):
        print(color, end="")
        pprint.pprint(args[0])
        print(RESET, **kw)
    else:
        print(color, end="")
        print(*args, end="")
        print(RESET, **kw)
        
def header(text, color="WHITE"):
    cprint(color, "\n####{}####".format("#"*len(text)))
    cprint(color, "### {} ###".format(text))
    cprint(color, "####{}####".format("#"*len(text)))

def subheader(text, color="WHITE"):
    cprint(color, "###", text, "###")

def deep_merge_dicts(dict1, dict2):
    """
    Recursively merge two dictionaries.
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
