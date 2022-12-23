import platform
import sys
from typing import Optional

import click

from palera1n import __version__, Device


@click.command()
@click.argument(
    'version',
    type=str,
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
    version: str,
    url: Optional[str],
    rootless: bool,
    semi_tethered: bool,
    restore_rootfs: bool,
    serial: bool,
    verbose: bool,
) -> None:
    '''An iOS 15.0-16.2 (semi-)tethered checkm8 jailbreak.'''

    if not verbose:
        sys.tracebacklimit = 0

    if platform.system() == 'Windows':
        click.echo('[ERROR] Windows systems are not supported. Exiting.')
        return

    click.echo('Attempting to connect to device...')
    device = Device.find_device()
    click.echo(f'Device found! Mode: {device.mode}')


if __name__ == "__main__":
    main()
