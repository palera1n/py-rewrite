import os
import plistlib
import requests
import shutil
import string
import subprocess as sp
import sys
import tarfile
import time
import zipfile

from paramiko.client import AutoAddPolicy, SSHClient
from paramiko.ssh_exception import AuthenticationException, SSHException
from pathlib import Path
from pymobiledevice3 import usbmux
from remotezip import RemoteZip
from argparse import Namespace

from . import utils
from . import logger
from .deps import Gaster, iBootPatcher, irecovery, KernelPatcher
from .img4 import IMG4


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
        self.os = sp.getoutput("uname")

    def create(self, version: string, rootless: bool = False) -> None:
        logger.log("Creating ramdisk...")
        
        if self.in_package:
            rd_tar = utils.get_resources_dir("palera1n") / "ramdisk.tar.gz"
            rd_logo = utils.get_resources_dir("palera1n") / "ramdisklogo.im4p"
            rd_shsh = utils.get_resources_dir("palera1n") / f"shsh/{self.cpid}.shsh2"
        else:
            rd_tar = Path("palera1n/data/ramdisk.tar.gz")
            rd_logo = Path("palera1n/data/ramdisklogo.im4p")
            rd_shsh = Path("palera1n/data/shsh") / f"{self.cpid}.shsh2"
        
        if self.args.ipsw:
            self.ipsw = self.args.ipsw
        else:
            res = requests.get(f"https://api.ipsw.me/v4/device/{self.deviceid}?type=ipsw")
            firmwares = res.json()["firmwares"]
            for firmware in firmwares:
                if firmware["version"] == version:
                    self.ipsw = firmware["url"]
                
            if self.ipsw is None or self.ipsw == "":
                logger.error("IPSW could not be fetched! Please supply one with --ipsw")
                sys.exit(1)
            
        if utils.check_pwned(self.data_dir, self.args) is False:
            print("Pwning device")
            Gaster(self.data_dir, self.args).run("pwn")
        
        with RemoteZip(self.ipsw) as ipsw:
            ipsw.extract("BuildManifest.plist", path=self.tmp)
            with open(self.tmp / "BuildManifest.plist", "rb") as f:
                plist = plistlib.load(f)
            
            for the_dict in plist["BuildIdentities"]:
                if the_dict["ApChipID"] == self.cpid:
                    identity = the_dict
                    break
            
            print("Downloading files")
            ipsw.extract(utils.get_path(identity, "iBSS"), path=self.tmp)
            ipsw.extract(utils.get_path(identity, "iBEC"), path=self.tmp)
            ipsw.extract(utils.get_path(identity, "DeviceTree"), path=self.tmp)
            ipsw.extract(utils.get_path(identity, "RestoreKernelCache"), path=self.tmp)
            ipsw.extract(utils.get_path(identity, "RestoreRamDisk"), path=self.tmp)
            ipsw.extract(utils.get_path(identity, "RestoreRamDisk") + ".trustcache", path=self.tmp)
            
        img4 = IMG4(self.args, self.in_package, rd_shsh, self.data_dir, self.tmp)
            
        print("Patching iBSS and iBEC")
        Gaster(self.data_dir, self.args).run("decrypt", decrypt_input=(self.tmp / utils.get_path(identity, "iBSS").replace("Firmware/dfu/", "")), decrypt_output=(self.tmp / "iBSS.dec"))
        iBootPatcher(self.data_dir, self.args).run((self.tmp / "iBSS.dec"), (self.tmp / "iBSS.patched"))
        img4.im4p_to_img4((self.tmp / "iBSS.patched"), (self.tmp / "iBSS.img4"), "ibss")
        
        Gaster(self.data_dir, self.args).run("decrypt", decrypt_input=(self.tmp / utils.get_path(identity, "iBEC").replace("Firmware/dfu/", "")), decrypt_output=(self.tmp / "iBEC.dec"))
        iBootPatcher(self.data_dir, self.args).run((self.tmp / "iBEC.dec"), (self.tmp / "iBEC.patched"), nvram_unlock=True, boot_args=f"rd=md0 wdt=-1{' -restore' if self.cpid in ('0x8960', '0x7000', '0x7001') else ''}")
        img4.im4p_to_img4((self.tmp / "iBEC.patched"), (self.tmp / "iBEC.img4"), "ibec")

        print("Packing DeviceTree")
        img4.im4p_to_img4((self.tmp / utils.get_path(identity, "DeviceTree")), (self.tmp / "devicetree.img4"), "rdtr")

        print("Patching kernel")
        img4.im4p_to_raw((self.tmp / utils.get_path(identity, "RestoreKernelCache")), (self.tmp / "kcache.raw"))
        KernelPatcher(self.data_dir, self.args).run((self.tmp / "kcache.raw"), (self.tmp / "kcache.patched"), amfi=True)
        img4.im4p_to_img4((self.tmp / "kcache.patched"), (self.tmp / "kernelcache.img4"), "rkrn")
        
        print("Packing trustcache")
        img4.im4p_to_img4((self.tmp / utils.get_path(identity, "RestoreRamDisk") + ".trustcache"), (self.tmp / "trustcache.img4"), "rtsc")

        print("Creating ramdisk dmg")
        img4.im4p_to_raw((self.tmp / utils.get_path(identity, "RestoreRamDisk")), (self.tmp / "ramdisk.dmg"))
        
        # Download kpf zip
        try:
            res = requests.get("https://nightly.link/palera1n/PongoOS/workflows/ci/iOS15/Kernel15Patcher.zip", stream=True)
            if res.status_code == 200:
                with open("kpf.zip", "wb") as f:
                    f.write(res.content)
            else:
                logger.error(f"Provided URL is not reachable. Status code: {res.status_code}")
                exit(1)
        except (requests.exceptions.NewConnectionError, ConnectionError, requests.exceptionsRequestException) as err:
            logger.error(f"Kernel15Patcher versioning download URL is not reachable. Error: {err}")
        
        # Unzip kpf zip
        with zipfile.ZipFile("kpf.zip", 'r') as f:
            f.extractall(".")
        Path("kpf.zip").unlink()
        
        if self.os == "Darwin":
            # Computer is macOS, we can use hdiutil and other stuff
            utils.run(f"hdiutil resize -size 256MB {self.tmp / 'ramdisk.dmg'}", self.args)
            utils.run(f"hdiutil attach -mountpoint /tmp/palera1n-ramdisk {self.tmp / 'ramdisk.dmg'}", self.args)
            
            with tarfile.open(rd_tar) as f:
                f.extractall("/tmp/palera1n-ramdisk/")
            
            shutil.move("Kernel15Patcher.ios", "/tmp/palera1n-ramdisk/sbin/kpf")
            Path("/tmp/palera1n-ramdisk/sbin/kpf").chmod(755)
            os.chown("/tmp/palera1n-ramdisk/sbin/kpf", 0, 0)
            
            utils.run("hdiutil detach -force /tmp/palera1n-ramdisk", self.args)
            utils.run(f"hdiutil resize -sectors min {self.tmp / 'ramdisk.dmg'}", self.args)
        else:
            # Computer is on something else (probably Linux), we'll have to use hfsplus
            # todo: finish linux rd build
            pass
        
        img4.im4p_to_img4((self.tmp / "ramdisk.dmg"), (self.tmp / "ramdisk.img4"), "rdsk")
        
        print("Packing bootlogo")
        img4.im4p_to_img4(rd_logo, (self.tmp / "bootlogo.img4"), "rlgo")
        
    def boot(self) -> None:
        logger.log("Booting ramdisk")
        
        irec = irecovery(self.data_dir, self.args)
        
        irec.run("file", file=(self.tmp / "iBSS.img4"))
        irec.run("file", file=(self.tmp / "iBEC.img4"))
        if self.cpid in ('0x8010', '0x8011', '0x8012', '0x8015'):
            irec.run("cmd", command="go")
        
        irec.run("file", file=(self.tmp / "bootlogo.img4"))
        irec.run("cmd", command="setpicture 0x0")
        irec.run("file", file=(self.tmp / "ramdisk.img4"))
        irec.run("cmd", command="ramdisk")
        irec.run("file", file=(self.tmp / "devicetree.img4"))
        irec.run("cmd", command="devicetree")
        irec.run("file", file=(self.tmp / "trustcache.img4"))
        irec.run("cmd", command="firmware")
        irec.run("file", file=(self.tmp / "kernelcache.img4"))
        irec.run("cmd", command="bootx")

    def install(self, ipsw: str) -> None:
        logger.log("Waiting for SSH to start")
        device = None
        while device is None:
            device = usbmux.select_device()
        
        port = None
        while port is None:
            port = device.connect(80)
    
        with SSHClient() as ssh:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            try:
                ssh.connect('localhost',
                            sock=port,
                            username="root",
                            password="alpine",
                            timeout=20,
                            allow_agent=False,
                            look_for_keys=False,
                            compress=True)
            except (SSHException, AuthenticationException) as e:
                logger.error(f"An error has occurred while trying to connect with SSH: {e}")
                sys.exit(1)

            logger.log("Connected to device, running commands")

            print("Mounting filesystems")
            out = utils.run_ssh(ssh, "/usr/bin/mount_filesystems", self.args)
            
            if self.args.semi_tethered:
                has_fakefs = utils.run_ssh(ssh, "ls /dev/disk0s1s8", self.args)
                if has_fakefs != "/dev/disk0s1s8":
                    print("Creating fakefs (this could take up to 10 minutes)")
                    out = utils.run_ssh(ssh, "/sbin/newfs_apfs -A -D -o role=r -v System /dev/disk0s1", self.args)
                    time.sleep(3)
                    out = utils.run_ssh(ssh, "/sbin/mount_apfs /dev/disk0s1s8 /mnt8", self.args)
                    time.sleep(2)
                    out = utils.run_ssh(ssh, "cp -a /mnt1/. /mnt8/", self.args)
                
                print("Setting nvram args...")
            else:
                print("Setting nvram args...")
                out = utils.run_ssh(ssh, "/usr/sbin/nvram auto-boot=false", self.args)
                
            out = utils.run_ssh(ssh, "/usr/sbin/nvram allow-root-hash-mismatch=1", self.args)
            out = utils.run_ssh(ssh, "/usr/sbin/nvram root-live-fs=1", self.args)

            # Now we put the kernelcache on the device for fsbooting
            # Path(self.tmp / "fsboot").mkdir()
            has_active = utils.run_ssh(ssh, "ls /mnt6/active", self.args)
            if has_active != "/mnt6/active":
                logger.error("Active file does not exist! Please use SSH to create it")
                print("    /mnt6/active should contain the name of the UUID in /mnt6")
                print("    When done, type reboot in the SSH session, then rerun the script")
                print("    ssh root@localhost -p 2222")
                sys.exit(1)
            
            active = utils.run_ssh(ssh, "cat /mnt6/active", self.args)
            
            print("Creating patched kernelcache")
            kcaches = f"/mnt6/{active}/System/Library/Caches/com.apple.kernelcaches"
            out = utils.run_ssh(ssh, f"rm -f {kcaches}/kcache.raw {kcaches}/kcache.patched {kcaches}/kcache.im4p {kcaches}/kernelcachd", self.args)
            out = utils.run_ssh(ssh, f"cp {kcaches}/kernelcache {kcaches}/kernelcache.bak", self.args)
            
            Path(self.tmp / "install").mkdir()
            with RemoteZip(ipsw) as the_ipsw:
                the_ipsw.extract("BuildManifest.plist", path=self.tmp / "install")
                with open(self.tmp / "BuildManifest.plist", "rb") as f:
                    plist = plistlib.load(f)
                
                for the_dict in plist["BuildIdentities"]:
                    if the_dict["ApChipID"] == self.cpid:
                        identity = the_dict
                        break
                
                print("Downloading kernelcache")
                the_ipsw.extract(utils.get_path(identity, "kernelcache.release"), path=self.tmp / "install")
            
            img4 = IMG4(self.args, self.in_package, self.data_dir / f"blobs/{self.deviceid}_{self.version}.shsh2", self.data_dir, self.tmp)
            img4.im4p_to_raw(self.tmp / "install" / utils.get_path(identity, "RestoreRamDisk"), self.tmp / "install/kcache.raw")
            
            #with ssh.open_sftp() as sftp:
            #    sftp.get()
            
            out = utils.run_ssh(ssh, f"img4 -i {kcaches}/kernelcache -o {kcaches}/kcache.raw", self.args)
            out = utils.run_ssh(ssh, f"kpf {kcaches}/kcache.raw {kcaches}/kcache.patched", self.args)
            out = utils.run_ssh(ssh, f"img4 -i {kcaches}/kcache.patched -o {kcaches}/kernelcachd" +
                                f"-M /mnt6/{active}/System/Library/Caches/apticket.der -J", self.args)
            
            out = utils.run_ssh(ssh, f"rm {kcaches}/kcache.raw {kcaches}/kcache.patched", self.args)
            
            print("Rebooting the device")
            out = utils.run_ssh(ssh, "/sbin/reboot", self.args)

    def restore_rootfs(self) -> None:
        logger.log("Waiting for SSH to start")
        device = None
        while device is None:
            device = usbmux.select_device()
        
        port = None
        while port is None:
            port = device.connect(80)
    
        with SSHClient() as ssh:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            try:
                ssh.connect('localhost',
                            sock=port,
                            username="root",
                            password="alpine",
                            timeout=20,
                            allow_agent=False,
                            look_for_keys=False,
                            compress=True)
            except (SSHException, AuthenticationException) as e:
                logger.error(f"An error has occurred while trying to connect with SSH: {e}")
                sys.exit(1)

            logger.log("Connected to device, running commands")
            
            has_fakefs = utils.run_ssh(ssh, "ls /dev/disk0s1s8", self.args)
            if has_fakefs == "/dev/disk0s1s8":
                print("Deleting fakefs")
                out = utils.run_ssh(ssh, "apfs_deletefs disk0s1s8", self.args)
            
            print("Removing custom kernel")
            has_active = utils.run_ssh(ssh, "ls /mnt6/active", self.args)
            if has_active != "/mnt6/active":
                logger.error("Active file does not exist! Please use SSH to create it")
                print("    /mnt6/active should contain the name of the UUID in /mnt6")
                print("    When done, type reboot in the SSH session, then rerun the script")
                print("    ssh root@localhost -p 2222")
                sys.exit(1)
            
            active = utils.run_ssh(ssh, "cat /mnt6/active", self.args)
            out = utils.run_ssh(ssh, f"rm /mnt6/{active}/System/Library/Caches/com.apple.kernelcaches/kernelcachd", self.args)
            
            print("Resetting nvram variables")
            out = utils.run_ssh(ssh, "/usr/sbin/nvram auto-boot=true", self.args)
            out = utils.run_ssh(ssh, "/usr/sbin/nvram -d allow-root-hash-mismatch", self.args)
            out = utils.run_ssh(ssh, "/usr/sbin/nvram -d root-live-fs", self.args)
            out = utils.run_ssh(ssh, "/usr/sbin/nvram -d boot-args", self.args)
            
            print("Rebooting the device")
            out = utils.run_ssh(ssh, "/sbin/reboot", self.args)
