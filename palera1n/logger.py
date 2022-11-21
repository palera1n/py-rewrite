#imports
import os

# fix windows up
if os.name == 'nt':
    from ctypes import windll
    k = windll.kernel32
    k.SetConsoleMode(k.GetStdHandle(-11), 7)


colors = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "orange": "\033[33m",
    "blue": "\033[34m",
    "purple": "\033[35m",
    "cyan": "\033[36m",
    "lightgrey": "\033[37m",
    "darkgrey": "\033[90m",
    "lightred": "\033[91m",
    "lightgreen": "\033[92m",
    "yellow": "\033[93m",
    "lightblue": "\033[94m",
    "pink": "\033[95m",
    "lightcyan": "\033[96m",

    "reset": "\033[0m",
    "bold": "\033[01m",
    "disable": "\033[02m",
    "underline": "\033[04m",
    "reverse": "\033[07m",
    "strikethrough": "\033[09m",
    "invisible": "\033[08m"
}


def log(message, color=colors["green"]):
    print(colors["darkgrey"] + colors["bold"] + "[" + colors["reset"] + color + colors["bold"] + "*" + colors["reset"] + colors["darkgrey"] + colors["bold"] + "]" + colors["reset"] + f" {message}")


def debug(message, dbg):
    if dbg:
        print(colors["darkgrey"] + colors["bold"] + "[" + colors["reset"] + colors["lightcyan"] + colors["bold"] + "^" + colors["reset"] + colors["darkgrey"] + colors["bold"] + "]" + colors["reset"] + f" {message}")


def error(message):
    print(colors["darkgrey"] + colors["bold"] + "[" + colors["reset"] + colors["lightred"] + colors["bold"] + "!" + colors["reset"] + colors["darkgrey"] + colors["bold"] + "]" + colors["reset"] + f" {message}")


def ask(message):
    return input(colors["darkgrey"] + colors["bold"] + "[" + colors["reset"] + colors["orange"] + colors["bold"] + "?" + colors["reset"] + colors["darkgrey"] + colors["bold"] + "]" + colors["reset"] + f" {message}")
    