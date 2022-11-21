# imports
from argparse import Namespace
from deps import irecovery
from paramiko.client import SSHClient
from pathlib import Path
from pymobiledevice3.exceptions import NoDeviceConnectedError
from pymobiledevice3.lockdown import LockdownClient
from typing import Union
import importlib
import logger
import os
import pkg_resources
import platform
import shutil
import subprocess as sp
import sys
import sys
import time


def device_info(type: str, string: str, data_dir: Path, args: Namespace) -> str:
    """Get info about the device"""
    try:
        if type == "normal":
            with LockdownClient(client_name="palera1n", usbmux_connection_type="USB") as lockdown:
                return lockdown.all_values[string]
        elif type == "recovery":
            #status, output = sp.getstatusoutput(f"{get_storage_dir() / 'irecovery'} -q | grep {string} | sed 's/{string}: //'")
            code, output = irecovery(data_dir, args).run("info")
            
            for line in output.split('\n'):
                if string in line:
                    info = line.replace(f"{string}: ", "")
                    
            return info
    except NoDeviceConnectedError:
        logger.error('No device connected.')
        exit(1)


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


def check_state(type: str) -> bool:
    """Check if the device is in a state"""
    if type == "dfu":
        if is_macos():
            if " Apple Mobile Device (DFU Mode):" in sp.getoutput("system_profiler SPUSBDataType"):
                return True
        else:
            if "DFU Mode" in sp.getoutput("lsusb"):
                return True
        return False
    elif type == "recovery":
        if is_macos():
            if " Apple Mobile Device (Recovery Mode):" in sp.getoutput("system_profiler SPUSBDataType"):
                return True
        else:
            if "Recovery Mode" in sp.getoutput("lsusb"):
                return True
        return False
    elif type == "normal":
        if is_macos():
            if (" iPhone:", " iPad:", " iPod:") in sp.getoutput("system_profiler SPUSBDataType"):
                return True
        else:
            if ("iPhone", "iPad", "iPod") in sp.getoutput("lsusb"):
                return True
        return False


def wait(type: str) -> bool:
    """Wait for device to go into a state"""
    if not check_state(type):
        logger.log(f"Waiting for device in {'DFU' if type == 'dfu' else type} mode...")
    
        while check_state(type) is not True:
            time.sleep(1)


def check_pwned(data_dir: Path, args: Namespace) -> tuple[bool, str]:
    pwned = device_info("recovery", "PWND", data_dir, args)
    if pwned == "":
        return False, None
    else:
        return True, pwned


def run(command: str, args: Namespace) -> None:
    print(f"Running {command.split()[0]}")
    logger.debug(f"Running command: {command}", args.debug)
    status, output = sp.getstatusoutput(command)
    if status != 0:
        logger.error(f"An error occurred when running {command.split()[0]}: {output}")
        sys.exit(1)


def run_ssh(client: SSHClient, command: str, args: Namespace) -> str:
    logger.debug(f"Running command (SSH): {command}", args.debug)
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    
    if stderr != "":
        logger.error(f"An error occurred while running an SSH command: {stderr}")
        sys.exit(1)
    
    return stdout


def get_path(identity: dict, item: str) -> str:
    return identity["Manifest"][item]["Info"]["Path"]
