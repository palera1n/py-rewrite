import platform
import sys
import time
from collections import namedtuple
from typing import Optional

import click

from palera1n import Device, __version__
from palera1n.errors import *

Version = namedtuple('Version', ['major', 'minor', 'patch'])


class VersionType(click.ParamType):
    name = 'version'

    def convert(self, value: str, param: click.Parameter, ctx: click.Context):
        split_values = value.split('.')
        if len(split_values) == 2:
            split_values.append(0)
        elif len(split_values) != 3:
            self.fail(f"'{value}' is not a valid version", param, ctx)

        for i, item in enumerate(split_values):
            try:
                split_values[i] = int(item)
            except ValueError:
                self.fail(f"'{value}' is not a valid version", param, ctx)

        return Version(*split_values)


@click.command()
@click.argument(
    'version',
    type=VersionType(),
    required=True,
)
@click.version_option(None, '-v', message=f'Palera1n {__version__}')
@click.option('-u', '--url', 'url', type=str, help='URL of IPSW file.')
@click.option(
    '-r',
    '--rootless',
    'rootless',
    is_flag=True,
    help='Rootless jailbreak (meant for iOS 15+).',
)
@click.option(
    '-s',
    '--semi-tethered',
    'semi_tethered',
    is_flag=True,
    help='Semi-tethered jailbreak.',
)
@click.option(
    '--restore-rootfs',
    'restore_rootfs',
    is_flag=True,
    help='Restore root filesystem (effectively unjailbreaking the device).',
)
@click.option(
    '--serial',
    'serial',
    is_flag=True,
    help='Add required boot-args for serial logging.',
)
@click.option(
    '-V',
    '--verbose',
    'verbose',
    is_flag=True,
    help='Increase verbosity.',
)
def main(
    version: Version,
    url: Optional[str],
    rootless: bool,
    semi_tethered: bool,
    restore_rootfs: bool,
    serial: bool,
    verbose: bool,
) -> None:
    '''An iOS 15.0-16.2 (semi-)tethered checkm8 jailbreak.'''

    click.secho(f'palera1n {__version__}', bold=True)
    click.secho('Made by: Nebula, Mineek, Nathan, Ploosh, and Nick Chan', italic=True)

    if not verbose:
        sys.tracebacklimit = 0

    if version.major not in (15, 16):
        click.secho('[ERROR] Only iOS 15 and 16 are supported. Exiting.', fg='red')
        return

    if version.major == 16 and version.minor > 3:
        click.secho('[ERROR] iOS 16.4 and above are not supported. Exiting.', fg='red')
        return

    if platform.system() == 'Windows':
        click.secho('[ERROR] Windows systems are not supported. Exiting.', fg='red')
        return

    # TODO: Ensure iBoot64Patcher, gaster, iBootpatch2, and Kernel64Patcher are available

    click.echo('Attempting to connect to device...')
    connection_attempts = 0
    while connection_attempts < 5:
        try:
            device = Device.find_device(ecid=1201921105576486)
            break
        except DeviceNotFound:
            connection_attempts += 1
            time.sleep(1)
    else:
        click.secho('[ERROR] No device was found in 5 seconds. Exiting.', fg='red')
        return

    click.secho(f'Connected to device, mode: {device.mode.name}', bold=True)

    # TODO: ensure device is 64-bit + checkm8 vulnerable

    # TODO: check if device is pwned, if not run gaster


'''
Rest of palera1n jb logic:
    if (
        self.args.restore_rootfs
        or not Path(
            self.data_dir / f"blobs/{self.deviceid}_{self.version}.der"
        ).exists()
    ):
        Path(self.data_dir / f"blobs/{self.deviceid}_{self.version}.der").unlink(
            missing_ok=True
        )

        with tempfile.TemporaryDirectory() as rd_tmp:
            rd = Ramdisk(
                self.args,
                self.in_package,
                self.data_dir,
                Path(rd_tmp),
                self.cpid,
                self.model,
                self.deviceid,
            )

            rd.create(
                "15.6.1"
                if self.version.startswith("15.7")
                else ("16.0.3" if self.version.startswith("16") else self.version),
                rootless=False,
            )  # True if self.args.rootless else False)
            rd.boot()
            print("rd booted, hopefully")
            sys.exit(0)

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
        if not Path(
            self.data_dir / f"boot/{self.deviceid}_{self.version}/ibot.img4"
        ).exists():
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

            img4 = IMG4(
                self.args,
                self.in_package,
                self.data_dir / f"blobs/{self.deviceid}_{self.version}.shsh2",
                self.data_dir,
                self.tmp,
            )

            print("Patching iBSS")
            Gaster(self.data_dir, self.args).run(
                "decrypt",
                decrypt_input=(
                    self.tmp
                    / utils.get_path(identity, "iBSS").replace("Firmware/dfu/", "")
                ),
                decrypt_output=(self.tmp / "iBSS.dec"),
            )
            iBootPatcher(self.data_dir, self.args).run(
                (self.tmp / "iBSS.dec"), (self.tmp / "iBSS.patched")
            )
            img4.im4p_to_img4(
                (self.tmp / "iBSS.patched"),
                (self.data_dir / f"boot/{self.deviceid}_{self.version}/iBSS.img4"),
                "ibss",
            )

            print("Patching iBoot")
            Gaster(self.data_dir, self.args).run(
                "decrypt",
                decrypt_input=(
                    self.tmp
                    / utils.get_path(identity, "iBoot").replace("Firmware/dfu/", "")
                ),
                decrypt_output=(self.tmp / "ibot.dec"),
            )
            iBootPatcher(self.data_dir, self.args).run(
                (self.tmp / "ibot.dec"),
                (self.tmp / "ibot.patched"),
                nvram_unlock=True,
                fsboot=False if self.args.semi_tethered else True,
                local_boot=True if self.args.semi_tethered else False,
                boot_args=f"{'serial=3' if self.args.serial else '-v'}{' rd=disk0s1s8' if self.args.semi_tethered else ''}",
            )
            with open((self.tmp / "ibot.patched"), "wb") as f:
                content = f.read()
                new = content.replace(b"s/kernelcache", b"s/kernelcachd")
                f.truncate(0)
                f.write(new)
            img4.im4p_to_img4(
                (self.tmp / "ibot.patched"),
                (self.data_dir / f"boot/{self.deviceid}_{self.version}/ibot.img4"),
                "ibec"
                if any(x in self.deviceid for x in ["iPhone8", "iPad5", "iPad6"])
                else "ibss",
            )

        # Lets actually boot the device
        if utils.check_pwned() is False:
            print("Pwning device")
            Gaster(self.data_dir, self.args).run("pwn")
            Gaster(self.data_dir, self.args).run("reset")

        irec = irecovery(self.data_dir, self.args)

        irec.run(
            "file",
            file=(self.data_dir / f"boot/{self.deviceid}_{self.version}/iBSS.img4"),
        )
        irec.run(
            "file",
            file=(self.data_dir / f"boot/{self.deviceid}_{self.version}/ibot.img4"),
        )

        if not self.args.semi_tethered:
            irec.run("cmd", command="fsboot")

    logger.info("Done!")
    logger.info("The device should now boot to jailbroken iOS")
    logger.info(
        "If you have any issues or questions, please ask in our Discord server: https://dsc.gg/palera1n"
    )
    logger.info(
        "Also, this is free and open source software! Feel free to donate to our Patreon if you enjoy :)"
    )
    print(f"    {colors['green']}https://patreon.com/palera1n")'''
