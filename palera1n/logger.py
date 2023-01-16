# module imports
from os import name

# fix logging if we are running on Windows
if name == 'nt':
    from ctypes import windll
    k = windll.kernel32
    k.SetConsoleMode(k.GetStdHandle(-11), 7)


colors = {
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'orange': '\033[33m',
    'blue': '\033[34m',
    'purple': '\033[35m',
    'cyan': '\033[36m',
    'lightgrey': '\033[37m',
    'darkgrey': '\033[90m',
    'lightred': '\033[91m',
    'lightgreen': '\033[92m',
    'yellow': '\033[93m',
    'lightblue': '\033[94m',
    'pink': '\033[95m',
    'lightcyan': '\033[96m',

    'reset': '\033[0m',
    'bold': '\033[01m',
    'disable': '\033[02m',
    'underline': '\033[04m',
    'reverse': '\033[07m',
    'strikethrough': '\033[09m',
    'invisible': '\033[08m'
}


def log(message, color=colors['yellow'], nln=True):
    '''Log a message.
    
    Arguments:
        message: Message to log
        color (str): Color to log (defaults to 'yellow')
        nln (bool): Whether or not to make a new line (defaults to True)
    '''
    
    n = '\n'
    if color is None:
        print(f'{n if nln else ""}' + colors['bold'] + '[*] ' + colors['reset'] + f'{message}' + colors['reset'])
    else:
        print(f'{n if nln else ""}' + color + colors['bold'] + '[*] ' + colors['reset'] + color + f'{message}' + colors['reset'])


def debug(message, dbg: bool):
    '''Log a debug message.
    
    Arguments:
        message: Message to log
        dbg (bool): Whether or not we are in debug mode
    '''
    
    if dbg:
        print(colors['lightcyan'] + colors['bold'] + '[DEBUG] ' + colors['reset'] + colors['lightcyan'] + f'{message}' + colors['reset'])


def error(message):
    '''Log an error.
    
    Arguments:
        message: Error to log
    '''
    
    print(colors['lightred'] + colors['bold'] + '[!] ' + colors['reset'] + colors['lightred'] + f'{message}' + colors['reset'])


def ask(message):
    '''Ask a question.
    
    Arguments:
        message: Message to ask
    '''
    
    return input(colors['orange'] + colors['bold'] + '[?] ' + colors['reset'] + colors['orange'] + f'{message}' + colors['reset'])
