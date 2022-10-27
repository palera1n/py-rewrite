import pkgutil
from pathlib import Path
from argparse import Namespace
from remotezip import RemoteZip
import requests
import sys
import plistlib

from . import logger
from . import utils
from .logger import colors
from .deps import Gaster, iBootPatcher


class Ramdisk:
    def __init__(self, args: Namespace, in_package: bool, data_dir: Path, tmp: Path, cpid: str, model: str, deviceid: str) -> None:
        self.in_package = in_package
        self.args = args
        
        # Device info
        self.cpid = cpid
        self.model = model
        self.deviceid = deviceid
        
        # Directories
        self.data_dir = data_dir
        self.tmp = tmp
        
        self.ipsw = None

    def create(self, version: string) -> None:
        if self.in_package:
            rd_tar = utils.get_resources_dir("palera1n") / "ramdisk.tar.gz"
            rd_logo = utils.get_resources_dir("palera1n") / "ramdisklogo.im4p"
        else:
            rd_tar = Path("palera1n/data/ramdisk.tar.gz")
            rd_logo = Path("palera1n/data/ramdisklogo.im4p")
        
        res = requests.get(f"https://api.ipsw.me/v4/device/{self.deviceid}?type=ipsw")
        firmwares = res.json()["firmwares"]
        for firmware in firmwares:
            if firmware["version"] == version:
                self.ipsw = firmware["url"]
        
        if utils.check_pwned() is False:
            logger.log("Pwning device")
            Gaster(self.data_dir, self.args).run("pwn")
            
        if self.ipsw is None or self.ipsw == "":
            logger.error("IPSW could not be fetched! Please supply one with --ipsw")
            sys.exit(1)
        
        with RemoteZip(self.ipsw) as ipsw:
            ipsw.extract("BuildManifest.plist", path=self.tmp)
            with open(self.tmp / "BuildManifest.plist", "rb") as f:
                plist = plistlib.load(f)
            
            for dict in plist["BuildIdentities"]:
                if dict["ApChipID"] == self.cpid:
                    identity = dict
                    break
            
            logger.log("Downloading files")
            ipsw.extract(identity["Manifest"]["iBSS"]["Info"]["Path"], path=self.tmp)
            ipsw.extract(identity["Manifest"]["iBEC"]["Info"]["Path"], path=self.tmp)
            ipsw.extract(identity["Manifest"]["DeviceTree"]["Info"]["Path"], path=self.tmp)
            ipsw.extract(identity["Manifest"]["RestoreRamDisk"]["Info"]["Path"], path=self.tmp)
            ipsw.extract(identity["Manifest"]["RestoreRamDisk"]["Info"]["Path"] + ".trustcache", path=self.tmp)
            
        logger.log("Decrypting iBSS and iBEC")
        Gaster(self.data_dir, self.args).run("decrypt", decrypt_input=(self.tmp / str(identity["Manifest"]["iBSS"]["Info"]["Path"]).replace("Firmware/dfu/", "")), decrypt_output=(self.tmp / "iBSS.dec"))
        Gaster(self.data_dir, self.args).run("decrypt", decrypt_input=(self.tmp / str(identity["Manifest"]["iBEC"]["Info"]["Path"]).replace("Firmware/dfu/", "")), decrypt_output=(self.tmp / "iBEC.dec"))
        
        logger.log("Patching iBSS and iBEC")
        iBootPatcher(self.data_dir, self.args).run((self.tmp / "iBSS.dec"), (self.tmp / "iBSS.patched"))
        iBootPatcher(self.data_dir, self.args).run((self.tmp / "iBEC.dec"), (self.tmp / "iBEC.patched"), nvram_unlock=True, boot_args=f"rd=md0 debug=0x2014e -v wdt=-1{' -restore' if self.cpid == '0x8960' or self.cpid == '0x8960' or self.cpid == '0x7001' else ''}")
            
