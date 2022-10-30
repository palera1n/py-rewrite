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

    def path(self) -> Union[Path, str, None]:
        # Check if iBoot64Patcher is present in the data dir
        if self.exists_in_data_dir():
            return (self.data_dir / "iBoot64Patcher")
        elif utils.cmd_in_path("iBoot64Patcher"):
            return "iBoot64Patcher"

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
    
    def run(self, input: Path, output: Path, nvram_unlock: bool = False, boot_args: str = None) -> tuple[int, str]:
        cmd = f"{self.path()} {input} {output}"
        if nvram_unlock is True:
            cmd += " -n"
        
        if boot_args is not None:
            cmd += f" {boot_args}"
        
        print("Running iBoot64Patcher...")
        logger.debug(f"Running command: {cmd}", self.args.debug)
        
        code, output = sp.getstatusoutput(f"{cmd}")

        if code != 0:
            logger.error(f'Failed to run iBoot64Patcher: {output}')
            sys.exit(1)
            
            return code, output

class Gaster:
    def __init__(self, data_dir: Path, args: Namespace) -> None:
        self.data_dir = data_dir
        self.args = args
        self.exists = False

    @property
    def remote_filename(self) -> Union[str, None]:
        # Get remote gaster name based on the platform
        if utils.is_linux() and platform.machine() == "x86_64":
            return "gaster-Linux"
        elif utils.is_macos() and platform.machine() == "x86_64":
            return "gaster-Darwin"
        elif utils.is_macos() and platform.machine() == "arm64":
            return "gaster-Darwin"

    def exists_in_data_dir(self) -> bool:
        # Check if gaster is present in the data dir
        return (self.data_dir / "gaster").exists()

    def path(self) -> Union[Path, str, None]:
        # Check if gaster is present in the data dir
        if self.exists_in_data_dir():
            return (self.data_dir / "gaster")
        elif utils.cmd_in_path("gaster"):
            return "gaster"

    def save_file(self, content: bytearray) -> None:
        # Write bytearray to a new file
        with open("gaster.zip", "wb") as f:
            f.write(content)
            
        # Unzip
        with zipfile.ZipFile("gaster.zip", 'r') as f:
            f.extractall(self.data_dir)
        Path("gaster.zip").unlink()

        # Remove outdated version of gaster it's present in the data dir
        if self.exists:
            logger.debug("Removing outdated version of gaster", self.args.debug)
            (self.data_dir / "gaster").unlink()

        # Make downloaded gaster executable
        utils.make_executable(self.data_dir / "gaster")
        logger.debug(f"Made gaster executable", self.args.debug)

    def download(self) -> None:
        # Check for gaster's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local gaster
        local_filepath = self.data_dir / "gaster"

        # Get name of a remote gaster
        remote_filename = self.remote_filename
        
        url = f"https://nightly.link/palera1n/gaster/workflows/makefile/main/{remote_filename}.zip"
        versioning = f"https://nightly.link/palera1n/gaster/workflows/makefile/main/Versioning.zip"
        
        # Download gaster zip to a bytearray
        try:
            res = requests.get(url, stream=True)
            if res.status_code == 200:
                content = bytearray()
                for data in res.iter_content(4096):
                    content += data
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"gaster download URL is not reachable. Error: {err}")
        
        # Download Versioning zip to a bytearray
        try:
            res = requests.get(versioning, stream=True)
            if res.status_code == 200:
                with open("Versioning.zip", "wb") as f:
                    f.write(res.content)
            else:
                logger.error(f"Provided URL is not reachable. Status code: {res.status_code}")
                exit(1)
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"gaster versioning download URL is not reachable. Error: {err}")
        
        # Unzip versioning zip
        with zipfile.ZipFile("Versioning.zip", 'r') as f:
            f.extractall(".")
        Path("Versioning.zip").unlink()
        
        # Check binary against SHA and num
        sha = open("latest_build_sha.txt", "r")
        num = open("latest_build_num.txt", "r")
        if exists:
            strings = sp.getoutput(f"strings {self.data_dir / 'gaster'}").splitlines()
            check = f"Version: {sha.read()}-{num.read()}"
            logger.debug(f"Checking for '{check}'", self.args.debug)

            # Check if the SHA is in the binary
            if check in strings:
                logger.debug(f"gaster SHA successfully verified.", self.args.debug)
            else:
                # If the SHA isn't in the binary, and the content is empty, fallback to existent gaster found in PATH/data dir
                if content is None:
                    if exists:
                        logger.log('Could not verify remote SHA, falling back to gaster found in path',
                                color=colors["yellow"])
                    else:
                        logger.error('gaster download url is not reachable, and no gaster found in path, exiting.')
                        sys.exit(1)
                # If SHA's do not match but the content is not empty, save it to a file
                else:
                    logger.debug(f"gaster SHA failed to verify, saving newer version", self.args.debug)
                    self.save_file(content)
        else:
            # If the SHA isn't in the binary, and the content is empty, fallback to existent gaster found in PATH/data dir
            if content is None:
                if exists:
                    logger.log('Could not verify remote SHA, falling back to gaster found in path',
                            color=colors["yellow"])
                else:
                    logger.error('gaster download url is not reachable, and no gaster found in path, exiting.')
                    sys.exit(1)
            # If SHA's do not match but the content is not empty, save it to a file
            else:
                logger.debug(f"gaster SHA failed to verify, saving newer version", self.args.debug)
                self.save_file(content)
                        
        Path("latest_build_sha.txt").unlink()
        Path("latest_build_num.txt").unlink()
    
    def run(self, type: str, decrypt_input: Path = None, decrypt_output: Path = None) -> tuple[int, str]:
        if type == "pwn":
            cmd = f"{self.path()} pwn"
            
            print("Running gaster pwn...")
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run gaster: {output}')
                sys.exit(1)
            
            return code, output
        elif type == "reset":
            cmd = f"{self.path()} reset"
            
            print("Running gaster reset...")
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run gaster: {output}')
                sys.exit(1)
            
            return code, output
        elif type == "decrypt":
            cmd = f"{self.path()} decrypt {decrypt_input} {decrypt_output}"
            
            print("Running gaster decrypt...")
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run gaster: {output}')
                sys.exit(1)
            
            return code, output

class irecovery:
    def __init__(self, data_dir: Path, args: Namespace) -> None:
        self.data_dir = data_dir
        self.args = args
        self.exists = False

    @property
    def remote_filename(self) -> Union[str, None]:
        # Get remote irecovery name based on the platform
        if utils.is_linux() and platform.machine() == "x86_64":
            return "libirecovery-static_Linux"
        elif utils.is_macos() and platform.machine() == "x86_64":
            return "libirecovery-static_Darwin"
        elif utils.is_macos() and platform.machine() == "arm64":
            return "libirecovery-static_Darwin"

    def exists_in_data_dir(self) -> bool:
        # Check if irecovery is present in the data dir
        return (self.data_dir / "irecovery").exists()

    def path(self) -> Union[Path, str, None]:
        # Check if irecovery is present in the data dir
        if self.exists_in_data_dir():
            return (self.data_dir / "irecovery")
        elif utils.cmd_in_path("irecovery"):
            return "irecovery"

    def save_file(self, content: bytearray) -> None:
        # Write bytearray to a new file
        with open("irecovery.zip", "wb") as f:
            f.write(content)
            
        # Unzip
        with zipfile.ZipFile("irecovery.zip", 'r') as f:
            f.extractall(self.data_dir)
        Path("irecovery.zip").unlink()
        
        """# Now, we unzip the tar
        with tarfile.open("libirecovery.tar") as f:
            with(self.data_dir) as path:
                f.extractall(path)
        Path("libirecovery.tar").unlink()"""

        # Remove outdated version of irecovery it's present in the data dir
        if self.exists:
            logger.debug("Removing outdated version of irecovery", self.args.debug)
            (self.data_dir / "irecovery").unlink()

        # Make downloaded irecovery executable
        utils.make_executable(self.data_dir / "irecovery")
        logger.debug(f"Made irecovery executable", self.args.debug)

    def download(self) -> None:
        # Check for irecovery's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local irecovery
        local_filepath = self.data_dir / "irecovery"

        # Get name of a remote irecovery
        remote_filename = self.remote_filename
        
        url = f"https://nightly.link/palera1n/libirecovery/workflows/build/master/{remote_filename}.zip"
        versioning = f"https://nightly.link/palera1n/libirecovery/workflows/build/master/Versioning.zip"
        
        # Download irecovery zip to a bytearray
        try:
            res = requests.get(url, stream=True)
            if res.status_code == 200:
                content = bytearray()
                for data in res.iter_content(4096):
                    content += data
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"irecovery download URL is not reachable. Error: {err}")
        
        # Download Versioning zip to a bytearray
        try:
            res = requests.get(versioning, stream=True)
            if res.status_code == 200:
                with open("Versioning.zip", "wb") as f:
                    f.write(res.content)
            else:
                logger.error(f"Provided URL is not reachable. Status code: {res.status_code}")
                exit(1)
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"irecovery versioning download URL is not reachable. Error: {err}")
        
        # Unzip versioning zip
        with zipfile.ZipFile("Versioning.zip", 'r') as f:
            f.extractall(".")
        Path("Versioning.zip").unlink()
        
        # Check binary against SHA and num
        sha = open("latest_build_sha.txt", "r")
        num = open("latest_build_num.txt", "r")
        if exists:
            strings = sp.getoutput(f"strings {self.data_dir / 'irecovery'}").splitlines()
            check = f"Version: {sha.read()}-{num.read()}"
            logger.debug(f"Checking for '{check}'", self.args.debug)

            # Check if the SHA is in the binary
            if check in strings:
                logger.debug(f"irecovery SHA successfully verified.", self.args.debug)
            else:
                # If the SHA isn't in the binary, and the content is empty, fallback to existent irecovery found in PATH/data dir
                if content is None:
                    if exists:
                        logger.log('Could not verify remote SHA, falling back to irecovery found in path',
                                color=colors["yellow"])
                    else:
                        logger.error('irecovery download url is not reachable, and no irecovery found in path, exiting.')
                        sys.exit(1)
                # If SHA's do not match but the content is not empty, save it to a file
                else:
                    logger.debug(f"irecovery SHA failed to verify, saving newer version", self.args.debug)
                    self.save_file(content)
        else:
            # If the SHA isn't in the binary, and the content is empty, fallback to existent irecovery found in PATH/data dir
            if content is None:
                if exists:
                    logger.log('Could not verify remote SHA, falling back to irecovery found in path',
                            color=colors["yellow"])
                else:
                    logger.error('irecovery download url is not reachable, and no irecovery found in path, exiting.')
                    sys.exit(1)
            # If SHA's do not match but the content is not empty, save it to a file
            else:
                logger.debug(f"irecovery SHA failed to verify, saving newer version", self.args.debug)
                self.save_file(content)
                        
        Path("latest_build_sha.txt").unlink()
        Path("latest_build_num.txt").unlink()
    
    def run(self, type: str, file: Path = None, command: str = None) -> tuple[int, str]:
        if type == "info":
            cmd = f"{self.path()} -q"
            
            print("Running irecovery -q...")
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run irecovery: {output}')
                sys.exit(1)
            
            return code, output
        elif type == "file":
            cmd = f"{self.path()} -f {file}"
            
            print("Running irecovery -f...")
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run irecovery: {output}')
                sys.exit(1)
            
            return code, output
        elif type == "cmd":
            cmd = f"{self.path()} -c {command}"
            
            print("Running irecovery -c...")
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run irecovery: {output}')
                sys.exit(1)
            
            return code, output

# generic dependency class
class Dependency:
    def __init__(self, args: argparse.Namespace):
        self.args = args

    def path(self) -> Path:
        return self.data_dir / self.filename

    def exists_in_data_dir(self) -> bool:
        return self.path().exists()

    def save_file(self, content: bytearray) -> None:
        with open(self.path(), "wb") as f:
            f.write(content)

    def download(self) -> None:
        # Check for dependency's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local dependency
        local_filepath = self.data_dir / self.filename

        # Get name of a remote dependency
        remote_filename = self.remote_filename

        # Download dependency zip to a bytearray
        try:
            res = requests.get(self.download_url, stream=True)
            if res.status_code == 200:
                content = bytearray()
                for data in res.iter_content(4096):
                    content += data
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"{self.filename} download URL is not reachable. Error: {err}")

        # save dependency to a file
        if content is None:
            if exists:
                logger.log(f'Could not download {self.filename}, falling back to {self.filename} found in path',
                        color=colors["yellow"])
            else:
                sys.exit(1)
        else:
            logger.debug(f"Saving {self.filename} to {self.data_dir}", self.args.debug)
            self.save_file(content)

    def run(self, args: list[str]) -> tuple[int, str]:
        cmd = f"{self.path()} {' '.join(args)}"
        print(f"Running {self.filename}...")
        logger.debug(f"Running command: {cmd}", self.args.debug)
        code, output = sp.getstatusoutput(f"{cmd}")
        if code != 0:
            logger.error(f'Failed to run {self.filename}: {output}')
            sys.exit(1)
        return code, output