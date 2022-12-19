import os
import plistlib
import requests
import remotezip
import subprocess as sp
import sys
import tempfile
import time

from pathlib import Path
from argparse import Namespace

from . import utils
from . import logger
from .deps import iBootPatcher, Gaster, irecovery, iBootpatch2, KernelPatcher
from .img4 import IMG4
from .logger import colors
from .ramdisk import Ramdisk


class palera1n:
    def __init__(self, in_package: bool, args: Namespace) -> None:
        self.in_package = in_package
        self.args = args
        
        # Binaries
        self.ibootpatcher = None
        self.ibootpatch2 = None
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
        self.version = None
        
        # Other variables
        self.ipsw = None
        self.os = sp.getoutput("uname")

    def main(self) -> None:
        print(colors["bold"] + f"palera1n | version {utils.get_version()}" + colors["reset"])
        print("Thanks to the team: Nebula, Mineek, Nathan, Ploosh, Nick Chan")
        
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
        print("Checking for iBoot64Patcher")
        self.ibootpatcher = self.data_dir / "iBoot64Patcher"
        if utils.cmd_in_path("iBoot64Patcher"):
            logger.debug("iBoot64Patcher found in path!", self.args.debug)
        else:
            if iBootPatcher(self.data_dir, self.args).exists_in_data_dir():
                logger.debug("iBoot64Patcher found!", self.args.debug)
            else:
                logger.debug("iBoot64Patcher not found in data dir", self.args.debug)
                iBootPatcher(self.data_dir, self.args).download()
        
        print("Checking for gaster")
        self.gaster = self.data_dir / "gaster"
        if utils.cmd_in_path("gaster"):
            logger.debug("gaster found in path!", self.args.debug)
        else:
            if Gaster(self.data_dir, self.args).exists_in_data_dir():
                logger.debug("gaster found!", self.args.debug)
            else:
                logger.debug("gaster not found in data dir", self.args.debug)
                Gaster(self.data_dir, self.args).download()
        
        print("Checking for irecovery")
        self.irecovery = self.data_dir / "irecovery"
        if utils.cmd_in_path("irecovery"):
            logger.debug("irecovery found in path!", self.args.debug)
        else:
            if irecovery(self.data_dir, self.args).exists_in_data_dir():
                logger.debug("irecovery found!", self.args.debug)
            else:
                logger.debug("irecovery not found in data dir", self.args.debug)
                irecovery(self.data_dir, self.args).download()
        
        print("Checking for Kernel64Patcher")
        self.kernelpatcher = self.data_dir / "Kernel64Patcher"
        if utils.cmd_in_path("Kernel64Patcher"):
            logger.debug("Kernel64Patcher found in path!", self.args.debug)
        else:
            if KernelPatcher(self.data_dir, self.args).exists_in_data_dir():
                logger.debug("Kernel64Patcher found!", self.args.debug)
            else:
                logger.debug("Kernel64Patcher not found in data dir", self.args.debug)
                KernelPatcher(self.data_dir, self.args).download()
        
        print("Checking for iBootpatch2")
        self.iBootpatch2 = self.data_dir / "iBootpatch2"
        if utils.cmd_in_path("iBootpatch2"):
            logger.debug("iBootpatch2 found in path!", self.args.debug)
        else:
            if iBootpatch2(self.data_dir, self.args).exists_in_data_dir():
                logger.debug("iBootpatch2 found!", self.args.debug)
            else:
                logger.debug("iBootpatch2 not found in data dir", self.args.debug)
                iBootpatch2(self.data_dir, self.args).download()
        
        if utils.get_device_mode() == "none":
            logger.log("Waiting for devices...")
            
        while utils.get_device_mode() == "none":
            time.sleep(1)
        
        mode = utils.get_device_mode()
        logger.log(f"Detected device in {'DFU' if mode == 'dfu' else mode} mode")
        
        # Get device info, then debug log them
        if self.args.version:
            self.version = self.args.version
        else:
            if utils.get_device_mode() == "normal":
                self.version = utils.device_info("normal", "ProductVersion", self.data_dir, self.args)
            else:
                logger.error("You must specify an iOS version when not starting from normal mode.")
                sys.exit(1)

        if self.version.startswith("15") is not True or self.version.startswith("16") is not True:
            logger.error(f"Your device is not supported. (iOS 15.x-16.x required, currently running iOS {self.version})")
            sys.exit(1)
        
        if utils.get_device_mode() == "normal":
            if utils.device_info("normal", "CPUArchitecture", self.data_dir, self.args) == "arm64e":
                logger.error("Your device is not supported. (arm64e architecture detected)")
                sys.exit(1)
        
            logger.log(f"Hello, {utils.device_info('normal', 'ProductType', self.data_dir, self.args)} on {self.version}!")
        else:
            logger.log(f"Hello, {utils.device_info('recovery', 'PRODUCT', self.data_dir, self.args)} on {self.version}!")
        
        if utils.get_device_mode() != "dfu":
            if utils.get_device_mode() != "recovery":
                logger.log("Entering recovery mode...")
                utils.enter_recovery(utils.device_info("normal", "UniqueDeviceID", self.data_dir, self.args))
                utils.wait("recovery")
                utils.fix_autoboot(self.data_dir, self.args)
                logger.log("Entered recovery mode.")
            utils.guide_to_dfu(utils.device_info("recovery", "CPID", self.data_dir, self.args), utils.device_info("recovery", "PRODUCT", self.data_dir, self.args), self.data_dir, self.args)

        utils.wait("dfu")
        
        logger.log("Getting device info")
        self.cpid = utils.device_info("recovery", "CPID", self.data_dir, self.args)
        self.model = utils.device_info("recovery", "MODEL", self.data_dir, self.args)
        self.deviceid = utils.device_info("recovery", "PRODUCT", self.data_dir, self.args)
        logger.debug(f"CPID: {self.cpid}, MODEL: {self.model}, ID: {self.deviceid}", self.args.debug)
        
        # Check if the device is pwned already, if not, then use gaster
        if utils.check_pwned(self.data_dir, self.args) is False:
            logger.log("Pwning device")
            Gaster(self.data_dir, self.args).run("pwn")
            Gaster(self.data_dir, self.args).run("reset")
        
        # Get IPSW
        if self.args.ipsw:
            self.ipsw = self.args.ipsw
        else:
            res = requests.get(f"https://api.ipsw.me/v4/device/{self.deviceid}?type=ipsw")
            firmwares = res.json()["firmwares"]
            for firmware in firmwares:
                if firmware["version"] == self.version:
                    self.ipsw = firmware["url"]
                
            if self.ipsw is None or self.ipsw == "":
                logger.error("IPSW could not be fetched! Please supply one with --ipsw")
                sys.exit(1)
        
        # Create tmp folder for ramdisk
        if self.args.restore_rootfs or not Path(self.data_dir / f"blobs/{self.deviceid}_{self.version}.der").exists():
            Path(self.data_dir / f"blobs/{self.deviceid}_{self.version}.der").unlink(missing_ok=True)
            
            with tempfile.TemporaryDirectory() as rd_tmp:
                rd = Ramdisk(self.args, self.in_package, self.data_dir, Path(rd_tmp), self.cpid, self.model, self.deviceid)
                
                rd.create("15.6.1" if self.version.startswith("15.7") else ("16.0.3" if self.version.startswith("16") else self.version), rootless=False) #True if self.args.rootless else False)
                rd.boot()
                
                if self.args.restore_rootfs:
                    rd.restore_rootfs()
                else:
                    rd.install(self.ipsw)
        
        # tmp folder for everything else
        with tempfile.TemporaryDirectory() as tmp:
            self.tmp = Path(tmp)
            
            if self.args.semi_tethered or self.args.rootless:
                utils.wait("normal")
            else:
                utils.wait("recovery")
            time.sleep(3)
            utils.wait("dfu")
            
            # Now we check if boot files exist
            if not Path(self.data_dir / f"boot/{self.deviceid}_{self.version}/ibot.img4").exists():
                logger.log(f"Creating boot files for {self.version}")
                    
                with remotezip.RemoteZip(self.ipsw) as ipsw:
                    ipsw.extract("BuildManifest.plist", path=self.tmp)
                    with open(self.tmp / "BuildManifest.plist", "rb") as f:
                        plist = plistlib.load(f)
                    
                    for the_dict in plist["BuildIdentities"]:
                        if the_dict["ApChipID"] == self.cpid:
                            identity = the_dict
                            break
                    
                    print("Downloading files")
                    ipsw.extract(utils.get_path(identity, "iBSS"), path=self.tmp)
                    ipsw.extract(utils.get_path(identity, "iBoot"), path=self.tmp)
                
                img4 = IMG4(self.args, self.in_package, self.data_dir / f"blobs/{self.deviceid}_{self.version}.shsh2", self.data_dir, self.tmp)
                
                print("Patching iBSS")
                Gaster(self.data_dir, self.args).run("decrypt", decrypt_input=(self.tmp / utils.get_path(identity, "iBSS").replace("Firmware/dfu/", "")), decrypt_output=(self.tmp / "iBSS.dec"))
                iBootPatcher(self.data_dir, self.args).run((self.tmp / "iBSS.dec"), (self.tmp / "iBSS.patched"))
                img4.im4p_to_img4((self.tmp / "iBSS.patched"), (self.data_dir / f"boot/{self.deviceid}_{self.version}/iBSS.img4"), "ibss")
                
                print("Patching iBoot")
                Gaster(self.data_dir, self.args).run("decrypt", decrypt_input=(self.tmp / utils.get_path(identity, "iBoot").replace("Firmware/dfu/", "")), decrypt_output=(self.tmp / "ibot.dec"))
                iBootPatcher(self.data_dir, self.args).run((self.tmp / "ibot.dec"), (self.tmp / "ibot.patched"), 
                                                           nvram_unlock=True, fsboot=False if self.args.semi_tethered else True, 
                                                           local_boot=True if self.args.semi_tethered else False, 
                                                           boot_args=f"{'serial=3' if self.args.serial else '-v'}{' rd=disk0s1s8' if self.args.semi_tethered else ''}")
                with open((self.tmp / "ibot.patched"), "wb") as f:
                    content = f.read()
                    new = content.replace(b"s/kernelcache", b"s/kernelcachd")
                    f.truncate(0)
                    f.write(new)
                img4.im4p_to_img4((self.tmp / "ibot.patched"), (self.data_dir / f"boot/{self.deviceid}_{self.version}/ibot.img4"), "ibec" if any(x in self.deviceid for x in ["iPhone8", "iPad5", "iPad6"]) else "ibss")
                
            # Lets actually boot the device
            if utils.check_pwned() is False:
                print("Pwning device")
                Gaster(self.data_dir, self.args).run("pwn")
                Gaster(self.data_dir, self.args).run("reset")
            
            irec = irecovery(self.data_dir, self.args)
            
            irec.run("file", file=(self.data_dir / f"boot/{self.deviceid}_{self.version}/iBSS.img4"))
            irec.run("file", file=(self.data_dir / f"boot/{self.deviceid}_{self.version}/ibot.img4"))
            
            if not self.args.semi_tethered:
                irec.run("cmd", command="fsboot")
        
        logger.info("Done!")
        logger.info("The device should now boot to jailbroken iOS")
        logger.info("If you have any issues or questions, please ask in our Discord server: https://dsc.gg/palera1n")
        logger.info("Also, this is free and open source software! Feel free to donate to our Patreon if you enjoy :)")
        print(f"    {colors['green']}https://patreon.com/palera1n")
