# module imports
from argparse import Namespace
from hashlib import md5
from pathlib import Path
from platform import machine
from requests import get
from requests.exceptions import RequestException, ConnectionError
from shutil import move
from struct import pack
from subprocess import getstatusoutput
from typing import Union
from urllib3.exceptions import NewConnectionError
from usb.core import find
from usb.util import dispose_resources
from time import sleep

# local imports
from . import utils
from . import logger
from .logger import colors


class checkra1n:
    def __init__(self, data_dir: Path, args: Namespace) -> None:
        self.data_dir = data_dir
        self.args = args
        self.exists = False

    @staticmethod
    def get_hash(filepath, url):
        """Get remote hash if a url is provided. Otherwise, get hash of a local file."""
        
        m = md5()
        if url is None:
            with open(filepath, 'rb') as fh:
                m = md5()
                while True:
                    data = fh.read(8192)
                    if not data:
                        break
                    m.update(data)
                return m.hexdigest()
        else:
            try:
                res = get(url, stream=True)
                if res.status_code == 200:
                    content = bytearray()
                    for data in res.iter_content(4096):
                        content += data
                        m.update(data)
                    return m.hexdigest(), content
                else:
                    return m.hexdigest(), None
            except (NewConnectionError, ConnectionError, RequestException) as err:
                logger.error(f'checkra1n download URL is not reachable. Error: {err}')
                return m.hexdigest(), None

    @property
    def remote_filename(self) -> Union[str, None]:
        """Get remote checkra1n name based on the platform.
        
        :return: None if unsupported, otherwise the remote filename
        :rtype: Union[str, None]
        """
        
        if utils.is_linux() and machine() == 'x86_64':
            return 'checkra1n-linux-x86_64'
        elif utils.is_linux() and machine() == 'aarch64':
            return 'checkra1n-linux-arm64'
        elif utils.is_macos():
            return 'checkra1n-macos'


    def exists_in_data_dir(self) -> bool:
        """Check if checkra1n is present in the data dir.
        
        :return: Whether or not checkra1n exists
        :rtype: bool
        """
        
        return (self.data_dir / f'binaries/checkra1n').exists()

    def save_file(self, content: bytearray) -> None:
        """Write bytearray to a new file.
        
        :param bytearray content: Content to write
        """
        
        with open('checkra1n', 'wb') as f:
            f.write(content)
            logger.debug(f'Wrote file.', self.args.debug)

        # Remove outdated version of checkra1n it's present in the data dir
        if self.exists:
            logger.debug('Removing outdated version of checkra1n', self.args.debug)
            (self.data_dir / 'checkra1n').unlink()

        # Make downloaded checkra1n executable
        utils.make_executable('checkra1n')

        # Move downloaded checkra1n to data dir
        move('checkra1n', self.data_dir / 'binaries/checkra1n')
        logger.debug(f'Moved checkra1n to {self.data_dir / "binaries/checkra1n"}', self.args.debug)

    def download(self) -> None:
        """Download the checkra1n binary."""
        
        # Check for checkra1n's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local checkra1n
        local_filepath = self.data_dir / 'binaries/checkra1n'

        # Get name of a remote checkra1n
        remote_filename = self.remote_filename

        url = f'https://assets.checkra.in/downloads/preview/0.1337.1/{remote_filename}'
        logger.debug(f'Comparing {local_filepath} hash with {url}', self.args.debug)

        # Get remote hash of checkra1n
        remote_hash, content = self.get_hash(None, url)
        local_hash = None

        # Determine checkra1n's hash if it's present in the data directory
        if exists:
            local_hash = self.get_hash(local_filepath, None)

        # Check if both hashes match, and if so proceed to the signing stage
        if remote_hash == local_hash:
            logger.debug(f'checkra1n hash successfully verified.', self.args.debug)
        else:
            # If hashes do no match, and the content is empty, fallback to existent checkra1n found in data dir
            if content is None:
                if exists:
                    logger.log('Could not verify remote hash, falling back to checkra1n found in path',
                               color=colors['yellow'])
                else:
                    logger.error('Download url is not reachable, and no checkra1n found in path, exiting.')
                    exit(1)
            # If hashes do not match but the content is not empty, save it to a file
            else:
                logger.debug(f'checkra1n hash failed to verify, saving newer version', self.args.debug)
                self.save_file(content)

class Jailbreak:
    def __init__(self, data_dir: Path, args: Namespace) -> None:
        self.data_dir = data_dir
        self.args = args

    def run_checkra1n(self, ramdisk: Path = None, overlay: Path = None, kpf: Path = None, pongo_bin: Path = None, 
                      boot_args: str = None, force_revert: bool = False, safe_mode: bool = False, 
                      exit_early: bool = False, pongo: bool = False, pongo_full: bool = False) -> None:
        """Run checkra1n."""

        cmd = f'{self.data_dir / "binaries/checkra1n"}'
        if ramdisk != None:
            cmd = f'{cmd} -r {ramdisk}'
            
        if overlay != None:
            cmd = f'{cmd} -o {overlay}'
            
        if kpf != None:
            cmd = f'{cmd} -K {kpf}'
            
        if pongo_bin != None:
            cmd = f'{cmd} -k {pongo_bin}'
            
        if boot_args != None:
            cmd = f'{cmd} -e \'{boot_args}\''
            
        if force_revert == True:
            cmd = f'{cmd} --force-revert'
            
        if safe_mode == True:
            cmd = f'{cmd} -s'
            
        if exit_early == True:
            cmd = f'{cmd} -E'
            
        if pongo == True:
            cmd = f'{cmd} -p'
            
        if pongo_full == True:
            cmd = f'{cmd} -P'

        print('Running checkra1n...')
        logger.debug(f'Running command: {cmd}', self.args.debug)

        code, output = getstatusoutput(cmd)

        if code != 0:
            logger.error(f'Failed to run checkra1n: {output}')
            exit(1)
    
    def pongo_send_cmd(self, cmd: str) -> None:
        """Run a command on device using Pongo.
        
        :param str cmd: Command to run
        """
        
        dev = find(idVendor=0x05ac, idProduct=0x4141)
        if dev is None:
            logger.error('Device not found')
            exit(1)
        
        dev.set_configuration()
        logger.debug(f'Running Pongo command: {cmd}', self.args.debug)
        sent = False
        while sent == False:
            dev.ctrl_transfer(0x21, 3, 0, 0, f'{cmd}\n')
            sent = True
            
        dispose_resources(dev)
        sleep(1)
    
    def pongo_send_file(self, file: Path, modload: bool = False) -> None:
        """Send a file to device using Pongo.
        
        :param Path file: File to send
        :param bool modload: Defaults to False
        """
        
        dev = find(idVendor=0x05ac, idProduct=0x4141)
        if dev is None:
            logger.error('Device not found')
            exit(1)
            
        with open(file, 'rb') as f:
            data = f.read()
            
            sent = False
            dev.set_configuration()
            while sent == False:
                dev.ctrl_transfer(0x21, 2, 0, 0, 0)
                dev.ctrl_transfer(0x21, 1, 0, 0, pack('I', len(data)))
                dev.write(2, data, 100000)
                
                #if len(data) % 512 == 0:
                #    dev.write(2, '')
                
                sent = True
                
            if modload:
                logger.debug('Running Pongo command: modload', self.args.debug)
                dev.ctrl_transfer(0x21, 3, 0, 0, 'modload\n')
        
        dispose_resources(dev)
        sleep(1)