# module imports
from argparse import Namespace
from importlib import resources
from pathlib import Path
from pkg_resources import get_distribution
from platform import machine
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.irecv import IRecv
from os import environ
from re import match
from shutil import which
from subprocess import getoutput, getstatusoutput
from sys import platform, stdout, version_info
from time import sleep
from typing import Union

# local imports
from . import logger
from .logger import colors


def log_stdout(tolog: str):
    stdout.write(tolog)
    stdout.flush()


def remove_log_stdout(toremove: str):
    for _ in range(len(toremove)):
        stdout.write('\033[D \033[D')
        stdout.flush()


def guide_to_dfu(cpid: str, product: str, irecv: IRecv):
    '''Guide the user to enter DFU mode
    
    Arguments:
        cpid (str): CPID of the device
        product (str): Device product number
        irecv (IRecv): IRecv object to send the device into recovery.
    '''
    
    log = 'Get ready (3)'
    colorway = colors['yellow'] + colors['bold'] + '[*] ' + colors['reset'] + colors['yellow']

    logger.ask('Press enter when you\'re ready to enter DFU mode.')
    log_stdout(colorway + log)
    sleep(1)
    remove_log_stdout(colorway + log + colors['reset'])

    for i in range(2):
        i = i + 1
        remove_log_stdout(colorway + log.replace('3', str(3 - i)) + colors['reset'])
        log_stdout(colorway + log.replace('3', str(3 - i)) + colors['reset'])
        sleep(1)
    
    remove_log_stdout(colorway + log + logger.colors['reset'])

    if (cpid.startswith('0x801') and product.startswith('iPad') is not True):
        log = 'Hold volume down + side button (4)'
    else:
        log = 'Hold home + power button (4)'

    log_stdout(colorway + log + colors['reset'])
    sleep(1)
    remove_log_stdout(colorway + log + colors['reset'])

    for i in range(3):
        i = i + 1
        remove_log_stdout(colorway + log.replace('4', str(4 - i)) + colors['reset'])
        log_stdout(colorway + log.replace('4', str(4 - i)) + colors['reset'])
        if (i == 3):
            try:
                irecv.send_command('reset')
            except:
                pass
        else:
            sleep(1)

    remove_log_stdout(colorway + log + colors['reset'])

    if (cpid.startswith('0x801') and product.startswith('iPad') is not True):
        log = 'Release side button, but keep holding volume down (10)'
    else:
        log = 'Release power button, but keep holding home button (10)'
    
    log_stdout(colorway + log + colors['reset'])
    sleep(1)
    remove_log_stdout(colorway + log + colors['reset'])
    
    for i in range(9):
        i = i + 1
        if get_device_mode() == 'dfu':
            remove_log_stdout(colorway + log + colors['reset'])
            logger.log('Successfully entered DFU mode.')
            return
        
        remove_log_stdout(colorway + log.replace('10', str(10 - i)) + colors['reset'])
        log_stdout(colorway + log.replace('10', str(10 - i)) + colors['reset'])
        sleep(1)
    
    if get_device_mode() == 'dfu':
        remove_log_stdout(colorway + log + colors['reset'])
        logger.log('Successfully entered DFU mode.')
    else:
        remove_log_stdout(colorway + log + colors['reset'])
        logger.error('Failed to enter DFU mode. Try running the script again.')
        exit(1)


def enter_recovery() -> None:
    '''Enter recovery mode'''
    with LockdownClient(client_name='palera1n', usbmux_connection_type='USB') as lockdown:
        lockdown.enter_recovery()
    

def device_info(string: str) -> str:
    '''Get info about the device
    
    Arguments:
        string (str): Information to retrieve from the device
    
    Returns:
        (str) Found data
    '''
    
    with LockdownClient(client_name='palera1n', usbmux_connection_type='USB') as lockdown:
        return lockdown.all_values[string]


def is_macos() -> bool:
    '''Determine if current OS is macOS
    Returns:
        (bool)
    '''
    if machine().startswith('i'):
        return False

    return platform == 'darwin'


def is_linux() -> bool:
    '''Determine if current OS is Linux
    
    Returns:
        (bool)
    '''
    
    return platform == 'linux'


def make_executable(path: Path) -> None:
    '''Set chmod +x on a given path
    
    Arguments:
        path (Path): Path to change permissions of
    '''
    
    file = Path(path)
    mode = file.stat().st_mode
    mode |= (mode & 0o444) >> 2
    file.chmod(mode)


def cmd_in_path(cmd: str) -> Union[None, str]:
    '''Check if command is in PATH
    
    Arguments:
        cmd (str): Command to find in path
    
    Returns:
        (Union[None, str]) None if not in path, otherwise the path to the command binary.
    '''
    
    path = which(cmd)

    if path is None:
        return None

    return path


def get_storage_dir() -> Path:
    '''Get path to data directory
    
    Returns:
        (Path) Path to storage
    '''

    # Get the value of PALERA1N_HOME variable and if it's exported use it as data directory
    pr_home = environ.get('PALERA1N_HOME')
    if pr_home:
        return Path(pr_home)

    # Get path to user's $HOME
    home = Path.home()

    # Check if OS is Linux
    # then, use $XDG_DATA_HOME as data directory
    # otherwise, default to $HOME/.local/share
    if is_linux():
        xdg_data = environ.get('XDG_DATA_HOME')
        if xdg_data:
            return Path(xdg_data).joinpath('palera1n')
        return home / '.local/share/palera1n'
    # Check if OS is macOS
    # then, use $HOME/.palera1n as data directory
    elif is_macos():
        return home / '.palera1n'
    # Check if OS is Windows
    # then, use %APPDATA%/palera1n as data directory
    #elif is_windows():
    #    return home / 'AppData/Roaming/palera1n'


def get_version() -> str:
    '''
    Get current version of running script.
    
    Returns:
        (str) Version
    '''
    
    # Check if running from a git repository,
    # then, construct version in the following format: version-branch-hash
    if Path('.git').exists():
        return f'{get_distribution(__package__).version}-{getoutput("git rev-parse --abbrev-ref HEAD")}-{getoutput("git rev-parse --short HEAD")}'
    else:
        return get_distribution(__package__).version


def get_resources_dir(package: str) -> Path:
    '''
    Gets the directory that the resources are stored in.
    
    Arguments:
        package (str): Path to palera1n package
    
    Returns:
        (Path) Path to resources
    '''
    
    if version_info < (3, 9):
        with resources.path(package, '__init__.py') as r:
            res = r.parent
    else:
        res = resources.files(package)

    return res / 'data'


def get_device_mode() -> str:
    '''
    Find what state the device is in
    
    Returns:
        (str) Device state
    '''
    
    if is_macos():
        apples = getoutput('''system_profiler SPUSBDataType 2> /dev/null | grep -B1 'Vendor ID: 0x05ac' | grep 'Product ID:' | cut -dx -f2 | cut -d' ' -f1 | tail -r''')
    else:
        apples = getoutput('''lsusb | cut -d' ' -f6 | grep \'05ac:\' | cut -d: -f2''')
    
    device_count = 0
    usbserials = ''
    
    for apple in apples.splitlines():
        if apple in ('12a8', '12aa', '12ab'):
            device_mode = 'normal'
            device_count += 1
        elif apple == '1281':
            device_mode = 'recovery'
            device_count += 1
        elif apple == '1227':
            device_mode = 'dfu'
            device_count += 1
        elif apple == '1222':
            device_mode = 'diag'
            device_count += 1
        elif apple == '1338':
            device_mode = 'checkra1n_stage2'
            device_count += 1
        elif apple == '4141':
            device_mode = 'pongo'
            device_count += 1
            
    if device_count == 0:
        device_mode = 'none'
    elif device_count >= 2:
        logger.error('Please attach only one device')
        exit(1)

    if is_macos():
        usbserials = getoutput('''system_profiler SPUSBDataType 2> /dev/null | grep 'Serial Number' | cut -d: -f2- | sed 's/ //\'''')
    else:
        usbserials = getoutput('cat /sys/bus/usb/devices/*/serial')
    
    if match('(ramdisk tool|SSHRD_Script) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]{1,2} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}', usbserials):
        device_mode = 'ramdisk'
    
    return device_mode


def wait(mode: str, no_log: bool = False) -> bool:
    '''Wait for device to go into a state.
    
    Arguments:
        mode (str): State we are waiting for
        no_log (str): Whether or not we should log
    '''
    
    if get_device_mode() != mode:
        if not no_log:
            logger.log(f'Waiting for device in {"DFU" if mode == "dfu" else mode} mode...')
    
        while get_device_mode() != mode:
            sleep(1)


def run(command: str, args: Namespace) -> None:
    '''Run a command.
    
    Arguments:
        command (str): Command to run
        args (Namespace): Args object
    '''
    
    print(f'Running {command.split()[0]}')
    logger.debug(f'Running command: {command}', args.debug)
    status, output = getstatusoutput(command)
    if status != 0:
        logger.error(f'An error occurred when running {command.split()[0]}: {output}')
        exit(1)


def get_path(identity: dict, item: str) -> str:
    return identity['Manifest'][item]['Info']['Path']


def checkra1n_flags(args: Namespace) -> hex:
    '''Generate checkra1n flags.
    
    Arguments:
        args (Namespace): args object
        
    Returns:
        (hex) arguments in hex
    '''
    
    if args.safe_mode:
        return hex(1<<0)
    elif args.restore_rootfs:
        return hex(1<<7)

def get_resource(name: str, in_package: bool) -> Path:
    '''Get a resource from the directory.
    
    Arguments:
        name (str): Name of the resource to retrieve
        in_package (bool): If we are in a package
    
    Returns:
        (Path) Path to the resources
    '''
    
    if in_package:
        return get_resources_dir('palera1n') / name
    else:
        return Path('palera1n/data') / name
