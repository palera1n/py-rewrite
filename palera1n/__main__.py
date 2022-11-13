import argparse
import palera1n
from . import utils


def main(argv=None, in_package=None) -> None:
    if argv is None:
        in_package = True

    in_package = False if in_package is None else in_package
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help="shows some debug info, only useful for testing")
    parser.add_argument('-i', '--ipsw', type=str,
                        help="specify IPSW url")
    parser.add_argument('-D', '--dfu', type=str,
                        help="use DFU mode")
    parser.add_argument('-r', '--rootless', action='warning', version=f'Rootless is not implemented yet.', #type=str,
                        help="use rootless mode")
    parser.add_argument('-s', '--semi-tethered', action='store_true',
                        help="semi-tether a tethered install")
    parser.add_argument('-R', '--restore-rootfs', action='store_true',
                        help="restore rootfs on (semi-)tethered")
    parser.add_argument('-S', '--serial', action='store_true',
                        help="add serial=3 to bootargs for serial output")
    parser.add_argument('-v', '--version', action='version', version=f'palera1n v{utils.get_version()}',
                        help='show current version and exit')
    args = parser.parse_args()

    pr = palera1n.palera1n(in_package, args)
    pr.main()


if __name__ == "__main__":
    main()