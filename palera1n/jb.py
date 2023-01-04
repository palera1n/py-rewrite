import platform
import requests
import shutil
import subprocess as sp
import sys
import tarfile
import time
import zipfile
import hashlib

from argparse import Namespace
from glob import glob
from pathlib import Path
from requests.exceptions import RequestException, ConnectionError
from typing import Union
from urllib3.exceptions import NewConnectionError

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
        # Get remote hash if a url is provided
        # otherwise, get hash of a local file
        m = hashlib.md5()
        if url is None:
            with open(filepath, 'rb') as fh:
                m = hashlib.md5()
                while True:
                    data = fh.read(8192)
                    if not data:
                        break
                    m.update(data)
                return m.hexdigest()
        else:
            try:
                res = requests.get(url, stream=True)
                if res.status_code == 200:
                    content = bytearray()
                    for data in res.iter_content(4096):
                        content += data
                        m.update(data)
                    return m.hexdigest(), content
                else:
                    return m.hexdigest(), None
            except (NewConnectionError, ConnectionError, RequestException) as err:
                logger.error(f"checkra1n download URL is not reachable. Error: {err}")
                return m.hexdigest(), None

    @property
    def remote_filename(self) -> Union[str, None]:
        # Get remote checkra1n name based on the platform
        if utils.is_linux() and platform.machine() == "x86_64":
            return "checkra1n-linux-x86_64"
        elif utils.is_linux() and platform.machine() == "aarch64":
            return "checkra1n-linux-arm64"
        elif utils.is_macos():
            return "checkra1n-macos"

    def exists_in_data_dir(self) -> bool:
        # Check if checkra1n is present in the data dir
        return (self.data_dir / f"binaries/checkra1n").exists()

    def save_file(self, content: bytearray) -> None:
        # Write bytearray to a new file
        with open("checkra1n", "wb") as f:
            f.write(content)
            logger.debug(f"Wrote file.", self.args.debug)

        # Remove outdated version of checkra1n it's present in the data dir
        if self.exists:
            logger.debug("Removing outdated version of checkra1n", self.args.debug)
            (self.data_dir / "checkra1n").unlink()

        # Make downloaded checkra1n executable
        utils.make_executable("checkra1n")

        # Move downloaded checkra1n to data dir
        shutil.move("checkra1n", self.data_dir / "binaries/checkra1n")
        logger.debug(f"Moved checkra1n to {self.data_dir / 'binaries/checkra1n'}", self.args.debug)

    def download(self) -> None:
        # Check for checkra1n's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local checkra1n
        local_filepath = self.data_dir / "binaries/checkra1n"

        # Get name of a remote checkra1n
        remote_filename = self.remote_filename

        url = f"https://assets.checkra.in/downloads/preview/0.1337.0/{remote_filename}"
        logger.debug(f"Comparing {local_filepath} hash with {url}", self.args.debug)

        # Get remote hash of checkra1n
        remote_hash, content = self.get_hash(None, url)
        local_hash = None

        # Determine checkra1n's hash if it's present in the data directory
        if exists:
            local_hash = self.get_hash(local_filepath, None)

        # Check if both hashes match, and if so proceed to the signing stage
        if remote_hash == local_hash:
            logger.debug(f"checkra1n hash successfully verified.", self.args.debug)
        else:
            # If hashes do no match, and the content is empty, fallback to existent checkra1n found in data dir
            if content is None:
                if exists:
                    logger.log('Could not verify remote hash, falling back to checkra1n found in path',
                               color=colors["yellow"])
                else:
                    logger.error('Download url is not reachable, and no checkra1n found in path, exiting.')
                    sys.exit(1)
            # If hashes do not match but the content is not empty, save it to a file
            else:
                logger.debug(f"checkra1n hash failed to verify, saving newer version", self.args.debug)
                self.save_file(content)

class Jailbreak:
    def __init__(self, data_dir: Path, args: Namespace) -> None:
        self.data_dir = data_dir
        self.args = args

    def run_checkra1n(self, ramdisk: Path = None, overlay: Path = None, kpf: Path = None, pongo: Path = None, 
                      boot_args: str = None, force_revert: bool = False, safe_mode: bool = False) -> None:
        """Run checkra1n"""

        cmd = f"{self.data_dir / 'binaries/checkra1n'}"
        if ramdisk != None:
            cmd = f"{cmd} -r {ramdisk}"
            
        if overlay != None:
            cmd = f"{cmd} -o {overlay}"
            
        if kpf != None:
            cmd = f"{cmd} -K {kpf}"
            
        if pongo != None:
            cmd = f"{cmd} -k {pongo}"
            
        if boot_args != None:
            cmd = f"{cmd} -e {boot_args}"
            
        if force_revert != None:
            cmd = f"{cmd} --force-revert"
            
        if safe_mode != None:
            cmd = f"{cmd} -s"

        logger.log("Running checkra1n...", color=colors["yellow"])
        logger.debug(
            f"Running command: {cmd}",
            self.args.debug)

        code, output = subprocess.getstatusoutput(cmd)

        if code != 0:
            logger.error(f'Failed to run checkra1n: {output}')
            sys.exit(1)
