import subprocess as sp
from argparse import Namespace
from pathlib import Path
import tempfile

from . import logger
from . import utils
from .logger import colors
from .deps import iBootPatcher, Gaster


class palera1n:
    def __init__(self, in_package: bool, args: Namespace) -> None:
        self.in_package = in_package
        self.args = args
        
        # Binaries
        self.ibootpatcher = None
        self.img4tool = None
        self.irecovery = None
        self.kernelpatcher = None
        self.gaster = None
        
        # Directories
        self.data_dir = None
        self.tmp = None
        
        # Device info
        self.cpid = None
        self.model = None
        self.deviceid = None
        
        # Other variables
        self.os = sp.getoutput("uname")

    def main(self) -> None:
        # logger.log(f"palera1n | Version {utils.get_version()}")
        print(colors["bold"] + f"palera1n | Version 2.0.0" + colors["reset"])
        print("Written by Nebula and Mineek | Some code and ramdisk from Nathan | Loader app by Amy")
        
        if self.in_package:
            logger.debug(f"Running from package, not cloned repo.", self.args.debug)
        
        logger.debug(f"Running on {self.os}", self.args.debug)
        
        # Create data directory
        self.data_dir = utils.get_storage_dir()
        logger.debug(f"Data directory is '{self.data_dir}'", self.args.debug)
        Path(self.data_dir).mkdir(exist_ok=True, parents=True)
        
        # Dependency check
        logger.log("Checking for dependencies...")
        
        print("Checking for iBoot64Patcher")
        self.ibootpatcher = utils.cmd_in_path('iBoot64Patcher')
        if self.ibootpatcher:
            logger.debug("iBoot64Patcher found!", self.args.debug)
        else:
            logger.debug("iBoot64Patcher not found in path", self.args.debug)
            iBootPatcher(self.data_dir, self.args).download()
        
        print("Checking for gaster")
        self.gaster = utils.cmd_in_path('gaster')
        if self.gaster:
            logger.debug("gaster found!", self.args.debug)
        else:
            logger.debug("gaster not found in path", self.args.debug)
            Gaster(self.data_dir, self.args).download()
        
        logger.log("Getting device info")
        self.cpid = utils.device_info("recovery", "CPID")
        self.model = utils.device_info("recovery", "MODEL")
        self.deviceid = utils.device_info("recovery", "PRODUCT")
        
        if utils.check_pwned() is False:
            logger.log("Pwning device")
            Gaster(self.data_dir, self.args).run("pwn")
        
        # Create tmp folder
        with tempfile.TemporaryDirectory() as tmpfolder:
            self.tmp = Path(tmpfolder)
