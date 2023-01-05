import os
import plistlib
import requests
import subprocess as sp
import sys
import tempfile
import time

from pathlib import Path
from argparse import Namespace

from . import utils
from . import logger
from .deps import irecovery
from .jb import checkra1n, Jailbreak
from .logger import colors


class palera1n:
    def __init__(self, in_package: bool, args: Namespace) -> None:
        self.in_package = in_package
        self.args = args
        
        # Directories
        self.data_dir = None
        self.tmp = None
        
        # Other variables
        self.os = sp.getoutput("uname")

    def main(self) -> None:
        print(colors["bold"] + colors["lightblue"] + "palera1n" + colors["reset"] + colors["bold"] + f" | version {utils.get_version()}" + colors["reset"])
        print("Thanks to the team: Nebula, Mineek, Nathan, Ploosh, Nick Chan, and the amazing developers of checkra1n")
        
        if self.in_package:
            logger.debug(f"Running from package, not cloned repo.", self.args.debug)
        
        logger.debug(f"Running on {self.os}", self.args.debug)
        
        # Create data directory
        self.data_dir = utils.get_storage_dir()
        logger.debug(f"Data directory is '{self.data_dir}'", self.args.debug)
        Path(self.data_dir).mkdir(exist_ok=True, parents=True)
        Path(self.data_dir / "binaries").mkdir(exist_ok=True, parents=True)
        
        # Dependency check
        logger.log("Checking for dependencies...")
        checkra1n(self.data_dir, self.args).download()   
             
        self.irecovery = self.data_dir / "irecovery"
        if utils.cmd_in_path("irecovery"):
            logger.debug("irecovery found in path!", self.args.debug)
        else:
            if irecovery(self.data_dir, self.args).exists_in_data_dir():
                logger.debug("irecovery found in data dir!", self.args.debug)
            else:
                logger.debug("irecovery not found in data dir", self.args.debug)
                irecovery(self.data_dir, self.args).download()

        if utils.get_device_mode() == "none":
            logger.log("Waiting for devices...", nln=False)
            
        while utils.get_device_mode() == "none":
            time.sleep(1)
        
        mode = utils.get_device_mode()
        logger.log(f"Detected device in {'DFU' if mode == 'dfu' else mode} mode", nln=False)
        
        # Get device info, then debug log them
        if utils.get_device_mode() == "normal":
            if utils.device_info("normal", "CPUArchitecture", self.data_dir, self.args) == "arm64e":
                logger.error("Your device is not supported. (arm64e architecture detected)")
                sys.exit(1)
        
        if utils.get_device_mode() != "dfu":
            if utils.get_device_mode() != "recovery":
                logger.log("Entering recovery mode...")
                utils.enter_recovery()
                utils.wait("recovery")
                utils.fix_autoboot(self.data_dir, self.args)
                logger.log("Entered recovery mode.")
            utils.guide_to_dfu(utils.device_info("recovery", "CPID", self.data_dir, self.args), utils.device_info("recovery", "PRODUCT", self.data_dir, self.args), self.data_dir, self.args)

        utils.wait("dfu")
        
        # Lets actually boot the device
        logger.log("Booting device")
        if self.in_package:
            ramdisk = utils.get_resources_dir("palera1n") / "ramdisk.dmg"
            overlay = utils.get_resources_dir("palera1n") / "binpack.dmg"
            kpf = utils.get_resources_dir("palera1n") / f"kpf"
            pongo = utils.get_resources_dir("palera1n") / f"pongo.bin"
        else:
            ramdisk = Path("palera1n/data/ramdisk.dmg")
            overlay = Path("palera1n/data/binpack.dmg")
            kpf = Path("palera1n/data/kpf")
            pongo = Path("palera1n/data/pongo.bin")
            
        jb = Jailbreak(self.data_dir, self.args)
        if self.args.a10_sep_test:
            jb.run_checkra1n(ramdisk=ramdisk, overlay=overlay, kpf=kpf, pongo_bin=pongo, exit_early=True, pongo=True, 
                             force_revert=True if self.args.restore_rootfs else False, safe_mode=True if self.args.safe_mode else False)
            utils.wait("pongo")
            time.sleep(2)
            jb.pongo_send_file(kpf, modload=True)
            jb.pongo_send_cmd("kpf")
            jb.pongo_send_file(ramdisk)
            jb.pongo_send_cmd("ramdisk")
            jb.pongo_send_file(overlay)
            jb.pongo_send_cmd("overlay")
            jb.pongo_send_cmd("fuse lock")
            jb.pongo_send_cmd(f"xargs {'serial=3' if self.args.serial else '-v'}")
            jb.pongo_send_cmd("xfb")
            jb.pongo_send_cmd("sep auto")
            jb.pongo_send_cmd("bootux")
        else:
            jb.run_checkra1n(ramdisk=ramdisk, overlay=overlay, kpf=kpf, pongo_bin=pongo, boot_args=f"{'serial=3' if self.args.serial else '-v'}", 
                             force_revert=True if self.args.restore_rootfs else False, safe_mode=True if self.args.safe_mode else False)
        
        logger.log("Done!")
        logger.log("The device should now boot to jailbroken iOS", nln=False)
        logger.log("If you have any issues or questions, please ask in our Discord server: https://dsc.gg/palera1n", nln=False)
        logger.log("Also, this is free and open source software! Feel free to donate to our Patreon if you enjoy :)", nln=False)
        print(f"    {colors['yellow']}https://patreon.com/palera1n")
