import importlib
import os
import pkg_resources
import platform
import shutil
import subprocess as sp
import sys
import time
import re

from argparse import Namespace
from paramiko.client import SSHClient
from pathlib import Path
from pymobiledevice3.exceptions import NoDeviceConnectedError
from pymobiledevice3.lockdown import LockdownClient
from typing import Union

from . import logger
from .deps import irecovery


def log_stdout(tolog: str):
    sys.stdout.write(tolog)
    sys.stdout.flush()


def remove_log_stdout(toremove: str):
    for _ in range(len(toremove)):
        sys.stdout.write('\033[D \033[D')
        sys.stdout.flush()
        

def guide_to_dfu(cpid: str, product: str, data_dir: str, args: Namespace):
    """Guide the user to enter DFU mode"""
    log = "Get ready (3)"
    colorway = logger.colors["yellow"] + logger.colors["bold"] + "[*] " + logger.colors["reset"] + logger.colors["yellow"]

    logger.ask("Press enter when you're ready to enter DFU mode.")
    log_stdout(colorway + log)
    time.sleep(1)
    remove_log_stdout(colorway + log + logger.colors["reset"])

    for i in range(2):
        i = i + 1
        remove_log_stdout(colorway + log.replace("3", str(3 - i)) + logger.colors["reset"])
        log_stdout(colorway + log.replace("3", str(3 - i)) + logger.colors["reset"])
        time.sleep(1)
    
    remove_log_stdout(colorway + log + logger.colors["reset"])

    if (cpid.startswith("0x801") and product.startswith('iPad') is not True):
        log = "Hold volume down + side button (4)"
    else:
        log = "Hold home + power button (4)"

    log_stdout(colorway + log + logger.colors["reset"])
    time.sleep(1)
    remove_log_stdout(colorway + log + logger.colors["reset"])

    for i in range(3):
        i = i + 1
        remove_log_stdout(colorway + log.replace("4", str(4 - i)) + logger.colors["reset"])
        log_stdout(colorway + log.replace("4", str(4 - i)) + logger.colors["reset"])
        if (i == 3):
            irecovery(data_dir, args).run(type="cmd", command="reset")
        else:
            time.sleep(1)

    remove_log_stdout(colorway + log + logger.colors["reset"])

    if (cpid.startswith("0x801") and product.startswith('iPad') is not True):
        log = "Release side button, but keep holding volume down (10)"
    else:
        log = "Release power button, but keep holding home button (10)"
    
    log_stdout(colorway + log + logger.colors["reset"])
    time.sleep(1)
    remove_log_stdout(colorway + log + logger.colors["reset"])
    
    for i in range(9):
        i = i + 1
        remove_log_stdout(colorway + log.replace("10", str(10 - i)) + logger.colors["reset"])
        log_stdout(colorway + log.replace("10", str(10 - i)) + logger.colors["reset"])
        time.sleep(1)
    
    if utils.get_device_mode() != "dfu":
        remove_log_stdout(colorway + log + logger.colors["reset"])
        logger.log("Successfully entered DFU mode.")
    else:
        remove_log_stdout(colorway + log + logger.colors["reset"])
        logger.error("Failed to enter DFU mode. Try running the script again.")
        sys.exit(1)


def enter_recovery(udid: str) -> None:
    """Enter recovery mode"""
    executable = ""
    if is_macos():
        executable = "Darwin/ideviceenterrecovery"
    else:
        executable = "Linux/ideviceenterrecovery"

    command = os.getcwd() + "/palera1n/data/binaries/" + executable + " " + udid

    status, output = sp.getstatusoutput(command)
    if status != 0:
        logger.error(f"An error occurred when running {command.split()[0]}: {output}")
        sys.exit(1)
        

def fix_autoboot(data_dir: Path, args: Namespace) -> None:
    """Fix autoboot"""
    status, output = irecovery(data_dir, args).run("cmd", command="setenv auto-boot true")
    status, output = irecovery(data_dir, args).run("cmd", command="saveenv")
    if status != 0:
        logger.error(f"An error occurred when running saveenv: {output}")
        sys.exit(1)
    

def device_info(type: str, string: str, data_dir: Path, args: Namespace) -> str:
    """Get info about the device"""
    if type == "normal":
        with LockdownClient(client_name="palera1n", usbmux_connection_type="USB") as lockdown:
            return lockdown.all_values[string]
    elif type == "recovery":
        #status, output = sp.getstatusoutput(f"{get_storage_dir() / 'irecovery'} -q | grep {string} | sed 's/{string}: //'")
        status, output = irecovery(data_dir, args).run("info")
            
        info = None
        for line in output.split('\n'):
            if string in line:
                info = line.replace(f"{string}: ", "")
        
        if info is None:
            return ""
        else:
            return info


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
    """Get path to data directory"""

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
        return f"{pkg_resources.get_distribution(__package__).version}-{sp.getoutput('git rev-parse --abbrev-ref HEAD')}-{sp.getoutput('git rev-parse --short HEAD')}"
    else:
        return pkg_resources.get_distribution(__package__).version


def get_resources_dir(package: str) -> Path:
    if sys.version_info < (3, 9):
        with importlib.resources.path(package, '__init__.py') as r:
            res = r.parent
    else:
        res = importlib.resources.files(package)

    return res / "data"


def get_device_mode() -> str:
    """Find what state the device is in"""
    if is_macos():
        apples = sp.getoutput("system_profiler SPUSBDataType 2> /dev/null | grep -B1 'Vendor ID: 0x05ac' | grep 'Product ID:' | cut -dx -f2 | cut -d' ' -f1 | tail -r")
    else:
        apples = sp.getoutput("lsusb | cut -d' ' -f6 | grep '05ac:' | cut -d: -f2")
    
    device_count = 0
    usbserials = ""
    
    for apple in apples.splitlines():
        if any(x in apple for x in ["12a8", "12aa", "12ab"]):
            device_mode = "normal"
            device_count += 1
        elif apple == "1281":
            device_mode = "recovery"
            device_count += 1
        elif apple == "1227":
            device_mode = "dfu"
            device_count += 1
        elif apple == "1222":
            device_mode = "diag"
            device_count += 1
        elif apple == "1338":
            device_mode = "checkra1n_stage2"
            device_count += 1
        elif apple == "4141":
            device_mode = "pongo"
            device_count += 1
            
    if device_count == 0:
        device_mode = "none"
    elif device_count >= 2:
        logger.error("Please attach only one device")
        sys.exit(1)

    if is_macos():
        usbserials = sp.getoutput("system_profiler SPUSBDataType 2> /dev/null | grep 'Serial Number' | cut -d: -f2- | sed 's/ //'")
    else:
        usbserials = sp.getoutput("cat /sys/bus/usb/devices/*/serial")
    
    if re.match("(ramdisk tool|SSHRD_Script) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]{1,2} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}", usbserials):
        device_mode = "ramdisk"
    
    return device_mode


def wait(mode: str) -> bool:
    """Wait for device to go into a state"""
    if get_device_mode() != mode:
        logger.log(f"Waiting for device in {'DFU' if mode == 'dfu' else mode} mode...")
    
        while get_device_mode() != mode:
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
