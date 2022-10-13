import subprocess as sp
from argparse import Namespace
from pathlib import Path
from typing import Union

import requests
import hashlib
import platform
from shutil import move
from requests.exceptions import RequestException, ConnectionError
from urllib3.exceptions import NewConnectionError
import tarfile
import zipfile
from glob import glob
import sys

from . import utils, logger
from .logger import colors


class iBootPatcher:
    def __init__(self, data_dir: Path, args: Namespace) -> None:
        self.data_dir = data_dir
        self.args = args
        self.exists = False

    @property
    def remote_filename(self) -> Union[str, None]:
        # Get remote iBoot64Patcher name based on the platform
        if utils.is_linux() and platform.machine() == "x86_64":
            return "iBoot64Patcher-Linux-x86_64-RELEASE"
        elif utils.is_macos() and platform.machine() == "x86_64":
            return "iBoot64Patcher-macOS-x86_64-RELEASE"
        elif utils.is_macos() and platform.machine() == "arm64":
            return "iBoot64Patcher-macOS-arm64-RELEASE"

    def exists_in_data_dir(self) -> bool:
        # Check if iBoot64Patcher is present in the data dir
        return (self.data_dir / "iBoot64Patcher").exists()

    def save_file(self, content: bytearray) -> None:
        # Write bytearray to a new file
        with open("iBoot64Patcher.zip", "wb") as f:
            f.write(content)
            
        # Unzip
        with zipfile.ZipFile("iBoot64Patcher.zip", 'r') as f:
            f.extractall(".")
        Path("iBoot64Patcher.zip").unlink()
                
        # Now, we unzip the tar.xz
        xz = glob('iBoot64Patcher-*.tar.xz')[0]
        with tarfile.open(xz) as f:
            with(self.data_dir) as path:
                f.extractall(path)
        Path(xz).unlink()

        # Remove outdated version of iBoot64Patcher it's present in the data dir
        if self.exists:
            logger.debug("Removing outdated version of iBoot64Patcher", self.args.debug)
            (self.data_dir / "iBoot64Patcher").unlink()

        # Make downloaded iBoot64Patcher executable
        utils.make_executable(self.data_dir / "iBoot64Patcher")
        logger.debug(f"Made iBoot64Patcher executable", self.args.debug)

    def download(self) -> None:
        # Check for iBoot64Patcher's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local iBoot64Patcher
        local_filepath = self.data_dir / "iBoot64Patcher"

        # Get name of a remote iBoot64Patcher
        remote_filename = self.remote_filename

        url = f"https://nightly.link/Cryptiiiic/iBoot64Patcher/workflows/ci/main/{remote_filename}.zip"
        versioning = f"https://nightly.link/Cryptiiiic/iBoot64Patcher/workflows/ci/main/Versioning.zip"
        
        # Download iBoot64Patcher zip to a bytearray
        try:
            res = requests.get(url, stream=True)
            if res.status_code == 200:
                content = bytearray()
                for data in res.iter_content(4096):
                    content += data
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"iBoot64Patcher download URL is not reachable. Error: {err}")
        
        # Download Versioning zip to a bytearray
        try:
            res = requests.get(versioning, stream=True)
            if res.status_code == 200:
                vers_content = bytearray()
                for data in res.iter_content(4096):
                    vers_content += data
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"iBoot64Patcher versioning download URL is not reachable. Error: {err}")
        
        with open("Versioning.zip", "wb") as f:
            f.write(vers_content)
        
        # Unzip versioning zip
        with zipfile.ZipFile("Versioning.zip", 'r') as f:
            f.extractall(".")
        Path("Versioning.zip").unlink()
        
        # Check binary against SHA and num
        sha = open("latest_build_sha.txt", "r")
        num = open("latest_build_num.txt", "r")
        if exists:
            strings = sp.getoutput(f"strings {self.data_dir / 'iBoot64Patcher'}").splitlines()
            check = f"Version: {sha.read()}-{num.read()}"
            logger.debug(f"Checking for '{check}'", self.args.debug)

            # Check if the SHA is in the binary
            if check in strings:
                logger.debug(f"iBoot64Patcher SHA successfully verified.", self.args.debug)
            else:
                # If the SHA isn't in the binary, and the content is empty, fallback to existent iBoot64Patcher found in PATH/data dir
                if content is None:
                    if exists:
                        logger.log('Could not verify remote SHA, falling back to iBoot64Patcher found in path',
                                color=colors["yellow"])
                    else:
                        logger.error('iBoot64Patcher download url is not reachable, and no iBoot64Patcher found in path, exiting.')
                        sys.exit(1)
                # If SHA's do not match but the content is not empty, save it to a file
                else:
                    logger.debug(f"iBoot64Patcher SHA failed to verify, saving newer version", self.args.debug)
                    self.save_file(content)
        else:
            # If the SHA isn't in the binary, and the content is empty, fallback to existent iBoot64Patcher found in PATH/data dir
            if content is None:
                if exists:
                    logger.log('Could not verify remote SHA, falling back to iBoot64Patcher found in path',
                            color=colors["yellow"])
                else:
                    logger.error('iBoot64Patcher download url is not reachable, and no iBoot64Patcher found in path, exiting.')
                    sys.exit(1)
            # If SHA's do not match but the content is not empty, save it to a file
            else:
                logger.debug(f"iBoot64Patcher SHA failed to verify, saving newer version", self.args.debug)
                self.save_file(content)
                        
        Path("latest_build_sha.txt").unlink()
        Path("latest_build_num.txt").unlink()
                