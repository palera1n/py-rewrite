# module imports
from argparse import Namespace
from pathlib import Path
from platform import machine
from requests import get
from requests.exceptions import RequestException, ConnectionError
from subprocess import getstatusoutput
from time import sleep
from typing import Union
from urllib3.exceptions import NewConnectionError
from zipfile import ZipFile

# local imports
from . import utils
from . import logger
from .logger import colors

class irecovery:
    def __init__(self, data_dir: Path, args: Namespace) -> None:
        self.data_dir = data_dir
        self.args = args
        self.exists = False

    @property
    def remote_filename(self) -> Union[str, None]:
        # Get remote irecovery name based on the platform
        if utils.is_linux() and machine() == "x86_64":
            return "libirecovery-static_Linux"
        elif utils.is_macos() and machine() == "x86_64":
            return "libirecovery-static_Darwin"
        elif utils.is_macos() and machine() == "arm64":
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
        with ZipFile("irecovery.zip", 'r') as f:
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
            res = get(url, stream=True)
            if res.status_code == 200:
                content = bytearray()
                for data in res.iter_content(4096):
                    content += data
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"irecovery download URL is not reachable. Error: {err}")
        
        # Download Versioning zip to a bytearray
        try:
            res = get(versioning, stream=True)
            if res.status_code == 200:
                with open("Versioning.zip", "wb") as f:
                    f.write(res.content)
            else:
                logger.error(f"Provided URL is not reachable. Status code: {res.status_code}")
                exit(1)
        except (NewConnectionError, ConnectionError, RequestException) as err:
            logger.error(f"irecovery versioning download URL is not reachable. Error: {err}")
        
        # Unzip versioning zip
        with ZipFile("Versioning.zip", 'r') as f:
            f.extractall(".")
        Path("Versioning.zip").unlink()
        
        # Check binary against SHA and num
        sha = open("latest_build_sha.txt", "r")
        num = open("latest_build_num.txt", "r")
        if exists:
            strings = getoutput(f"strings {self.data_dir / 'binaries/irecovery'}").splitlines()
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
                        exit(1)
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
                    exit(1)
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
            
            code, output = getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run irecovery: {output}')
                exit(1)
            
            return code, output
        elif type == "file":
            cmd = f"{self.path()} -f {file}"
            
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run irecovery: {output}')
                exit(1)
            
            sleep(4)
            
            return code, output
        elif type == "cmd":
            cmd = f"{self.path()} -c {command}"
            
            logger.debug(f"Running command: {cmd}", self.args.debug)
            
            code, output = getstatusoutput(f"{cmd}")

            if code != 0:
                logger.error(f'Failed to run irecovery: {output}')
                exit(1)
            
            sleep(4)
            
            return code, output
