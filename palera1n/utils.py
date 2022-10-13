import importlib
import os
import platform
import plistlib
import shutil
import subprocess as sp
import sys
from argparse import Namespace
from pathlib import Path
from typing import Union
import string
import sys
import pkg_resources

from pymobiledevice3.lockdown import LockdownClient

from . import logger


def is_macos() -> bool:
    """Determine if current OS is macOS"""
    if platform.machine().startswith("i"):
        return False

    return sys.platform == "darwin"


def is_linux() -> bool:
    """Determine if current OS is Linux"""
    return sys.platform == "linux"


def make_executable(path: Path) -> None:
    """Set chmod +x on a given path"""
    file = Path(path)
    mode = file.stat().st_mode
    mode |= (mode & 0o444) >> 2
    file.chmod(mode)


def cmd_in_path(cmd: str) -> Union[None, str]:
    """Check if command is in PATH"""
    path = shutil.which(cmd)

    if path is None:
        return None

    return path


def get_storage_dir() -> Path:
    """ Get path to data directory"""

    # Get the value of PALERA1N_HOME variable and if it's exported use it as data directory
    pr_home = os.environ.get("PALERA1N_HOME")
    if pr_home:
        return Path(pr_home)

    # Get path to user's $HOME
    home = Path.home()

    # Check if OS is Linux
    # then, use $XDG_DATA_HOME as data directory
    # otherwise, default to $HOME/.local/share
    if is_linux():
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data).joinpath("palera1n")
        return home / ".local/share/palera1n"
    # Check if OS is macOS
    # then, use $HOME/.palera1n as data directory
    elif is_macos():
        return home / ".palera1n"
    # Check if OS is Windows
    # then, use %APPDATA%/palera1n as data directory
    #elif is_windows():
    #    return home / "AppData/Roaming/palera1n"


def get_version() -> str:
    # Check if running from a git repository,
    # then, construct version in the following format: version-branch-hash
    if Path('.git').exists():
        return f"{sp.getoutput('git rev-parse --abbrev-ref HEAD')}_{sp.getoutput('git rev-parse --short HEAD')}"
    else:
        return pkg_resources.get_distribution(__package__).version


def get_resources_dir(package: str) -> Path:
    if sys.version_info < (3, 9):
        with importlib.resources.path(package, '__init__.py') as r:
            res = r.parent
    else:
        res = importlib.resources.files(package)

    return res / "data"


def check_state(type: str) -> None:
    """Check if the device is in a state"""
    if type == "dfu":
        if is_macos():
            if " Apple Mobile Device (DFU Mode):" in sp.getoutput("system_profiler SPUSBDataType"):
                logger.log("Device connected in DFU mode!")
            else:
                logger.error("Device isn't in DFU mode, please rerun the script and try again")
                sys.exit(1)
        else:
            if "DFU Mode" in sp.getoutput("lsusb"):
                logger.log("Device connected in DFU mode!")
            else:
                logger.error("Device isn't in DFU mode, please rerun the script and try again")
                sys.exit(1)

def device_info(type: str, string: str) -> str:
    """Get info about the device"""
    if type == "normal":
        lockdown = LockdownClient(client_name="palera1n", usbmux_connection_type="USB")
        return lockdown.all_values[string]
    elif type == "recovery":
        get_storage_dir() / "irecovery"
