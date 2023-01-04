# imports
import argparse

from . import palera1n
from . import utils


def main(argv=None, in_package=None) -> None:
    if argv is None:
        in_package = True

    in_package = False if in_package is None else in_package
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help="shows some debug info, only useful for testing")
    parser.add_argument('-R', '--restore-rootfs', action='store_true',
                        help="forcefully restore rootfs")
    parser.add_argument('-s', '--safe-mode', action='store_true',
                        help="boot without tweaks enabled")
    parser.add_argument('-S', '--serial', action='store_true',
                        help="add serial=3 to bootargs for serial output")
    parser.add_argument('-a', '--a10-sep-test', action='store_true', # TODO: test and remove this
                        help="temporary arg for A10 sep, may or may not work correctly")
    parser.add_argument('-v', '--version', action='version', version=f'palera1n v{utils.get_version()}',
                        help='show current version and exit')
    args = parser.parse_args()

    pr = palera1n.palera1n(in_package, args)
    pr.main()


if __name__ == "__main__":
    main()