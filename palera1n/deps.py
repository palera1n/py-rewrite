import platform
import requests
import shutil
import subprocess as sp
import sys
import tarfile
import time
import zipfile

from argparse import Namespace
from glob import glob
from pathlib import Path
from requests.exceptions import RequestException, ConnectionError
from typing import Union
from urllib3.exceptions import NewConnectionError

from . import utils
from . import logger
from .logger import colors

class Dependency:
    def __init__(self, args: Namespace):
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
        logger.debug(f"Running command: {cmd}", self.args.debug)
        
        status, output = sp.getstatusoutput(f"{cmd}")
        if status != 0:
            logger.error(f'Failed to run {self.filename}: {output}')
            sys.exit(1)
        
        return status, output

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
        return (self.data_dir / "binaries/iBoot64Patcher").exists()

    def path(self) -> Union[Path, str, None]:
        # Check if iBoot64Patcher is present in the data dir
        if self.exists_in_data_dir():
            return (self.data_dir / "binaries/iBoot64Patcher")
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
            with(self.data_dir / "binaries") as path:
                f.extractall(path)
        Path(xz).unlink()

        # Remove outdated version of iBoot64Patcher it's present in the data dir
        if self.exists:
            logger.debug("Removing outdated version of iBoot64Patcher", self.args.debug)
            (self.data_dir / "binaries/iBoot64Patcher").unlink()

        # Make downloaded iBoot64Patcher executable
        utils.make_executable(self.data_dir / "binaries/iBoot64Patcher")
        logger.debug(f"Made iBoot64Patcher executable", self.args.debug)

    def download(self) -> None:
        # Check for iBoot64Patcher's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local iBoot64Patcher
        local_filepath = self.data_dir / "binaries/iBoot64Patcher"

        # Get name of a remote iBoot64Patcher
        remote_filename = self.remote_filename

        url = f"https://nightly.link/palera1n/iBoot64Patcher/workflows/ci/main/{remote_filename}.zip"
        versioning = f"https://nightly.link/palera1n/iBoot64Patcher/workflows/ci/main/Versioning.zip"
        
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
            strings = sp.getoutput(f"strings {self.data_dir / 'binaries/iBoot64Patcher'}").splitlines()
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
    
    def run(self, input: Path, output: Path, nvram_unlock: bool = False, fsboot: bool = False, local_boot: bool = False, boot_args: str = None) -> tuple[int, str]:
        cmd = f"{self.path()} {input} {output}"
        if nvram_unlock is True:
            cmd += " -n"
            
        if fsboot is True:
            cmd += " -f"
            
        if local_boot is True:
            cmd += " -l"
        
        if boot_args is not None:
            cmd += f" -b \"{boot_args}\""
        
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
        return (self.data_dir / "binaries/gaster").exists()

    def path(self) -> Union[Path, str, None]:
        # Check if gaster is present in the data dir
        if self.exists_in_data_dir():
            return (self.data_dir / "binaries/gaster")
        elif utils.cmd_in_path("gaster"):
            return "gaster"

    def save_file(self, content: bytearray) -> None:
        # Write bytearray to a new file
        with open("gaster.zip", "wb") as f:
            f.write(content)
            
        # Unzip
        with zipfile.ZipFile("gaster.zip", 'r') as f:
            f.extractall(self.data_dir / "binaries")
        Path("gaster.zip").unlink()

        # Remove outdated version of gaster it's present in the data dir
        if self.exists:
            logger.debug("Removing outdated version of gaster", self.args.debug)
            (self.data_dir / "binaries/gaster").unlink()

        # Make downloaded gaster executable
        utils.make_executable(self.data_dir / "binaries/gaster")
        logger.debug(f"Made gaster executable", self.args.debug)

    def download(self) -> None:
        # Check for gaster's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local gaster
        local_filepath = self.data_dir / "binaries/gaster"

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
            strings = sp.getoutput(f"strings {self.data_dir / 'binaries/gaster'}").splitlines()
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
            
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run gaster: {output}')
                sys.exit(1)
            
            return code, output
        elif type == "reset":
            cmd = f"{self.path()} reset"
            
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run gaster: {output}')
                sys.exit(1)
            
            return code, output
        elif type == "decrypt":
            cmd = f"{self.path()} decrypt {decrypt_input} {decrypt_output}"
            
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
        return (self.data_dir / "binaries/irecovery").exists()

    def path(self) -> Union[Path, str, None]:
        # Check if irecovery is present in the data dir
        if self.exists_in_data_dir():
            return (self.data_dir / "binaries/irecovery")
        elif utils.cmd_in_path("irecovery"):
            return "irecovery"

    def save_file(self, content: bytearray) -> None:
        # Write bytearray to a new file
        with open("irecovery.zip", "wb") as f:
            f.write(content)
            
        # Unzip
        with zipfile.ZipFile("irecovery.zip", 'r') as f:
            f.extractall(self.data_dir / "binaries")
        Path("irecovery.zip").unlink()

        # Remove outdated version of irecovery it's present in the data dir
        if self.exists:
            logger.debug("Removing outdated version of irecovery", self.args.debug)
            (self.data_dir / "binaries/irecovery").unlink()

        # Make downloaded irecovery executable
        utils.make_executable(self.data_dir / "binaries/irecovery")
        logger.debug(f"Made irecovery executable", self.args.debug)

    def download(self) -> None:
        # Check for irecovery's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local irecovery
        local_filepath = self.data_dir / "binaries/irecovery"

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
            strings = sp.getoutput(f"strings {self.data_dir / 'binaries/irecovery'}").splitlines()
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

            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run irecovery: {output}')
                sys.exit(1)
            
            return code, output
        elif type == "file":
            cmd = f"{self.path()} -f {file}"
            
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run irecovery: {output}')
                sys.exit(1)
            
            time.sleep(4)
            
            return code, output
        elif type == "cmd":
            cmd = f"{self.path()} -c {command}"
            
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = sp.getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run irecovery: {output}')
                sys.exit(1)
            
            time.sleep(4)
            
            return code, output

class iBootpatch2:
    def __init__(self, data_dir: Path, args: Namespace) -> None:
        self.data_dir = data_dir
        self.args = args
        self.exists = False

    @property
    def remote_filename(self) -> Union[str, None]:
        # Get remote v name based on the platform
        if utils.is_linux() and platform.machine() == "x86_64":
            return "iBootpatch2-Linux"
        elif utils.is_macos() and platform.machine() == "x86_64":
            return "iBootpatch2-Darwin"
        elif utils.is_macos() and platform.machine() == "arm64":
            return "iBootpatch2-Darwin"

    def exists_in_data_dir(self) -> bool:
        # Check if iBootpatch2 is present in the data dir
        return (self.data_dir / "binaries/iBootpatch2").exists()

    def path(self) -> Union[Path, str, None]:
        # Check if iBootpatch2 is present in the data dir
        if self.exists_in_data_dir():
            return (self.data_dir / "binaries/iBootpatch2")
        elif utils.cmd_in_path("iBootpatch2"):
            return "iBootpatch2"

    def save_file(self, content: bytearray) -> None:
        # Write bytearray to a new file
        with open("iBootpatch2.zip", "wb") as f:
            f.write(content)
            
        # Unzip
        with zipfile.ZipFile("iBootpatch2.zip", 'r') as f:
            f.extractall(self.data_dir / "binaries")
        Path("iBootpatch2.zip").unlink()

        # Remove outdated version of iBootpatch2 it's present in the data dir
        if self.exists:
            logger.debug("Removing outdated version of iBootpatch2", self.args.debug)
            (self.data_dir / "binaries/iBootpatch2").unlink()

        # Make downloaded iBootpatch2 executable
        utils.make_executable(self.data_dir / "binaries/iBootpatch2")
        logger.debug(f"Made iBootpatch2 executable", self.args.debug)

    def download(self) -> None:
        # Check for iBootpatch2's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local iBootpatch2
        local_filepath = self.data_dir / "binaries/iBootpatch2"

        # Get name of a remote iBootpatch2
        remote_filename = self.remote_filename
        
        url = f"https://nightly.link/palera1n/iBootpatch2/workflows/build/main/{remote_filename}.zip"
        versioning = f"https://nightly.link/palera1n/iBootpatch2/workflows/build/main/Versioning.zip"
        
        # Download iBootpatch2 zip to a bytearray
        try:
            res = requests.get(url, stream=True)
            if res.status_code == 200:
                content = bytearray()
                for data in res.iter_content(4096):
                    content += data
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"iBootpatch2 download URL is not reachable. Error: {err}")
        
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
            logger.error(f"iBootpatch2 versioning download URL is not reachable. Error: {err}")
        
        # Unzip versioning zip
        with zipfile.ZipFile("Versioning.zip", 'r') as f:
            f.extractall(".")
        Path("Versioning.zip").unlink()
        
        # Check binary against SHA and num
        sha = open("latest_build_sha.txt", "r")
        num = open("latest_build_num.txt", "r")
        if exists:
            strings = sp.getoutput(f"strings {self.data_dir / 'binaries/iBootpatch2'}").splitlines()
            check = f"Version: {sha.read()}-{num.read()}"
            logger.debug(f"Checking for '{check}'", self.args.debug)

            # Check if the SHA is in the binary
            if check in strings:
                logger.debug(f"iBootpatch2 SHA successfully verified.", self.args.debug)
            else:
                # If the SHA isn't in the binary, and the content is empty, fallback to existent iBootpatch2 found in PATH/data dir
                if content is None:
                    if exists:
                        logger.log('Could not verify remote SHA, falling back to iBootpatch2 found in path',
                                color=colors["yellow"])
                    else:
                        logger.error('iBootpatch2 download url is not reachable, and no iBootpatch2 found in path, exiting.')
                        sys.exit(1)
                # If SHA's do not match but the content is not empty, save it to a file
                else:
                    logger.debug(f"iBootpatch2 SHA failed to verify, saving newer version", self.args.debug)
                    self.save_file(content)
        else:
            # If the SHA isn't in the binary, and the content is empty, fallback to existent iBootpatch2 found in PATH/data dir
            if content is None:
                if exists:
                    logger.log('Could not verify remote SHA, falling back to iBootpatch2 found in path',
                            color=colors["yellow"])
                else:
                    logger.error('iBootpatch2 download url is not reachable, and no iBootpatch2 found in path, exiting.')
                    sys.exit(1)
            # If SHA's do not match but the content is not empty, save it to a file
            else:
                logger.debug(f"iBootpatch2 SHA failed to verify, saving newer version", self.args.debug)
                self.save_file(content)
                        
        Path("latest_build_sha.txt").unlink()
        Path("latest_build_num.txt").unlink()
    
    def run(self, soc: str, input: str, output: str) -> tuple[int, str]:
        cmd = f"{self.path()} --{soc} {input} {output}"

        logger.debug(f"Running command: {cmd}", self.args.debug)
        
        code, output = sp.getstatusoutput(f"{cmd}")

        if code != 0:
            logger.error(f'Failed to run iBootpatch2: {output}')
            sys.exit(1)
        
        return code, output

class KernelPatcher:
    def __init__(self, data_dir: Path, args: Namespace) -> None:
        self.data_dir = data_dir
        self.args = args
        self.exists = False

    @property
    def remote_filename(self) -> Union[str, None]:
        # Get remote v name based on the platform
        if utils.is_linux() and platform.machine() == "x86_64":
            return "Kernel64Patcher-Linux"
        elif utils.is_macos() and platform.machine() == "x86_64":
            return "Kernel64Patcher-Darwin"
        elif utils.is_macos() and platform.machine() == "arm64":
            return "Kernel64Patcher-Darwin"

    def exists_in_data_dir(self) -> bool:
        # Check if Kernel64Patcher is present in the data dir
        return (self.data_dir / "binaries/Kernel64Patcher").exists()

    def path(self) -> Union[Path, str, None]:
        # Check if Kernel64Patcher is present in the data dir
        if self.exists_in_data_dir():
            return (self.data_dir / "binaries/Kernel64Patcher")
        elif utils.cmd_in_path("Kernel64Patcher"):
            return "Kernel64Patcher"

    def save_file(self, content: bytearray) -> None:
        # Write bytearray to a new file
        with open("Kernel64Patcher.zip", "wb") as f:
            f.write(content)
            
        # Unzip
        with zipfile.ZipFile("Kernel64Patcher.zip", 'r') as f:
            f.extractall(self.data_dir / "binaries")
        Path("Kernel64Patcher.zip").unlink()

        # Remove outdated version of Kernel64Patcher it's present in the data dir
        if self.exists:
            logger.debug("Removing outdated version of Kernel64Patcher", self.args.debug)
            (self.data_dir / "binaries/Kernel64Patcher").unlink()

        # Make downloaded Kernel64Patcher executable
        utils.make_executable(self.data_dir / "binaries/Kernel64Patcher")
        logger.debug(f"Made Kernel64Patcher executable", self.args.debug)

    def download(self) -> None:
        # Check for Kernel64Patcher's presence in data directory
        exists = self.exists_in_data_dir()

        # Get name and extension of a local Kernel64Patcher
        local_filepath = self.data_dir / "binaries/Kernel64Patcher"

        # Get name of a remote Kernel64Patcher
        remote_filename = self.remote_filename
        
        url = f"https://nightly.link/palera1n/Kernel64Patcher/workflows/build/master/{remote_filename}.zip"
        versioning = f"https://nightly.link/palera1n/Kernel64Patcher/workflows/build/master/Versioning.zip"
        
        # Download Kernel64Patcher zip to a bytearray
        try:
            res = requests.get(url, stream=True)
            if res.status_code == 200:
                content = bytearray()
                for data in res.iter_content(4096):
                    content += data
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"Kernel64Patcher download URL is not reachable. Error: {err}")
        
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
            logger.error(f"Kernel64Patcher versioning download URL is not reachable. Error: {err}")
        
        # Unzip versioning zip
        with zipfile.ZipFile("Versioning.zip", 'r') as f:
            f.extractall(".")
        Path("Versioning.zip").unlink()
        
        # Check binary against SHA and num
        sha = open("latest_build_sha.txt", "r")
        num = open("latest_build_num.txt", "r")
        if exists:
            strings = sp.getoutput(f"strings {self.data_dir / 'binaries/Kernel64Patcher'}").splitlines()
            check = f"Version: {sha.read()}-{num.read()}"
            logger.debug(f"Checking for '{check}'", self.args.debug)

            # Check if the SHA is in the binary
            if check in strings:
                logger.debug(f"Kernel64Patcher SHA successfully verified.", self.args.debug)
            else:
                # If the SHA isn't in the binary, and the content is empty, fallback to existent Kernel64Patcher found in PATH/data dir
                if content is None:
                    if exists:
                        logger.log('Could not verify remote SHA, falling back to Kernel64Patcher found in path',
                                color=colors["yellow"])
                    else:
                        logger.error('Kernel64Patcher download url is not reachable, and no Kernel64Patcher found in path, exiting.')
                        sys.exit(1)
                # If SHA's do not match but the content is not empty, save it to a file
                else:
                    logger.debug(f"Kernel64Patcher SHA failed to verify, saving newer version", self.args.debug)
                    self.save_file(content)
        else:
            # If the SHA isn't in the binary, and the content is empty, fallback to existent Kernel64Patcher found in PATH/data dir
            if content is None:
                if exists:
                    logger.log('Could not verify remote SHA, falling back to Kernel64Patcher found in path',
                            color=colors["yellow"])
                else:
                    logger.error('Kernel64Patcher download url is not reachable, and no Kernel64Patcher found in path, exiting.')
                    sys.exit(1)
            # If SHA's do not match but the content is not empty, save it to a file
            else:
                logger.debug(f"Kernel64Patcher SHA failed to verify, saving newer version", self.args.debug)
                self.save_file(content)
                        
        Path("latest_build_sha.txt").unlink()
        Path("latest_build_num.txt").unlink()
    
    def run(self, input: Path, output: Path, amfi: bool = False, afu_sigcheck: bool = False, spu_fw_validation: bool = False, 
            rootvp_not_authenticated: bool = False, could_not_authenticate_prh: bool = False, rootfs_seal_broken: bool = False, 
            update_rootfs_rw: bool = False, amfi_init_local_signing_pubkey: bool = False, is_root_hash_auth_required: bool = False, 
            launchd_path: bool = False, tfp0: bool = False, developer_mode: bool = False) -> tuple[int, str]:
        cmd = f"{self.path()} {input} {output}"
        if amfi is True:
            cmd += " -a"
            
        if afu_sigcheck is True:
            cmd += " -f"
            
        if spu_fw_validation is True:
            cmd += " -s"
            
        if could_not_authenticate_prh is True:
            cmd += " -o"
            
        if rootfs_seal_broken is True:
            cmd += " -e"
            
        if update_rootfs_rw is True:
            cmd += " -u"
            
        if amfi_init_local_signing_pubkey is True:
            cmd += " -p"
            
        if is_root_hash_auth_required is True:
            cmd += " -h"
            
        if launchd_path is True:
            cmd += " -l"
            
        if tfp0 is True:
            cmd += " -t"
            
        if developer_mode is True:
            cmd += " -d"
        
        logger.debug(f"Running command: {cmd}", self.args.debug)
        
        code, output = sp.getstatusoutput(f"{cmd}")

        if code != 0:
            logger.error(f'Failed to run Kernel64Patcher: {output}')
            sys.exit(1)
            
            return code, output
