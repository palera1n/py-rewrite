# module imports
from argparse import Namespace
from pathlib import Path
from subprocess import getoutput
from time import sleep
from pymobiledevice3.irecv import IRecv
from sys import exit
from shutil import rmtree
from requests import post

# local imports
from . import utils
from . import logger
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
        self.os = getoutput('uname')
        self.irecv = None
        self.jb = None

    def main(self) -> None:
        print(colors['bold'] + colors['lightblue'] + 'palera1n' + colors['reset'] + colors['bold'] + f' | version {utils.get_version()}' + colors['reset'])
        print('Made with ❤️ by Nebula, Mineek, Nathan, llsc12, Ploosh, Nick Chan, and the amazing developers of checkra1n')
        
        if self.in_package:
            logger.debug(f'Running from package, not cloned repo.', self.args.debug)
        
        logger.debug(f'Running on {self.os}', self.args.debug)
        
        # Create data directory
        self.data_dir = utils.get_storage_dir()
        logger.debug(f'Data directory is "{self.data_dir}"', self.args.debug)
        Path(self.data_dir).mkdir(exist_ok=True, parents=True)
        Path(self.data_dir / 'binaries').mkdir(exist_ok=True, parents=True)
        
        if self.args.safe_mode and self.args.restore_rootfs:
            logger.error('You cannot combine safe mode and restore rootfs!')
            exit(0)
        
        # Subcommands
        if self.args.subcommand == 'clean':
            logger.log('Cleaning data directory...')
            rmtree(self.data_dir)
            exit(0)
        
        # Dependency check
        if self.args.subcommand != 'dfuhelper':
            logger.log('Checking for dependencies...')
            print('Checking for checkra1n')
            checkra1n(self.data_dir, self.args).download()

        logger.log('Waiting for devices...')
            
        while utils.get_device_mode() == 'none':
            sleep(1)
        
        mode = utils.get_device_mode()
        print(f'Detected device in {"DFU" if mode == "dfu" else mode} mode')
        self.jb = Jailbreak(self.data_dir, self.args)
        
        if utils.get_device_mode() == 'pongo':
            print('Rebooting device in Pongo')
            self.jb.pongo_send_cmd('bootux')
            
            logger.log('Waiting for devices...')
            while utils.get_device_mode() == 'none':
                sleep(1)
        
        # Get device info, then debug log them
        if utils.get_device_mode() == 'normal':
            if utils.device_info('CPUArchitecture') == 'arm64e':
                logger.error('palera1n does not support arm64e devices, and never will')
                exit(1)
        
        if utils.get_device_mode() != 'dfu':
            if utils.get_device_mode() == 'recovery':
                self.irecv = IRecv()
                self.irecv._reinit(ecid=self.irecv.ecid)
            else:
                logger.log('Entering recovery mode...')
                utils.enter_recovery()
                utils.wait('recovery')
                self.irecv = IRecv()
                self.irecv._reinit(ecid=self.irecv.ecid)
                self.irecv.set_autoboot(True)
                print('Entered recovery mode.')
            utils.guide_to_dfu(str(self.irecv.chip_id), str(self.irecv.product_type), self.irecv)
        utils.wait('dfu')
        
        if self.args.subcommand == 'dfuhelper':
            exit(0)
        
        # Lets actually boot the device
        logger.log('Booting device')
        boot_args = f'{"serial=3" if self.args.serial else "-v"} rootdev=md0'
        ramdisk = utils.get_resource('ramdisk.dmg', in_package)
        overlay = utils.get_resource('binpack.dmg', in_package)
        kpf = utils.get_resource('kpf', in_package)
        pongo = utils.get_resource('Pongo.bin', in_package)
        
        sleep(3)
        self.jb.run_checkra1n(pongo_bin=pongo, exit_early=True, pongo_full=True, 
                              force_revert=True if self.args.restore_rootfs else False, safe_mode=True if self.args.safe_mode else False)
        print('Waiting for Pongo to boot')
        utils.wait('pongo', no_log=True)
        sleep(2)
        self.jb.pongo_send_file(kpf, modload=True)
        self.jb.pongo_send_file(ramdisk)
        self.jb.pongo_send_cmd('ramdisk')
        self.jb.pongo_send_file(overlay)
        self.jb.pongo_send_cmd('overlay')
        self.jb.pongo_send_cmd('fuse lock')
        self.jb.pongo_send_cmd(f'checkra1n_flags {utils.checkra1n_flags(self.args)}')
        self.jb.pongo_send_cmd(f'xargs {boot_args}')
        self.jb.pongo_send_cmd('xfb')
        self.jb.pongo_send_cmd('sep auto')
        self.jb.pongo_send_cmd('bootx')
            
        logger.log('Done!')
        logger.log('The device should now boot to jailbroken iOS', nln=False)
        logger.log('If you have any issues or questions, please ask in our Discord server: https://dsc.gg/palera1n', nln=False)
        logger.log('Also, this is free and open source software! Feel free to donate to our Patreon if you enjoy :)', nln=False)
        print(f'    {colors["yellow"]}https://patreon.com/palera1n')
        
        if not self.args.disable_analytics:
            try:
                req = post('https://ohio.itsnebula.net/hit', json={'app_name': 'palera1n_py-rewrite'})
            except:
                pass
