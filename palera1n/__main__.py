# module imports
from argparse import ArgumentParser
from sys import exit

# local imports
from . import palera1n
from . import utils


def main(argv=None, in_package=None) -> None:
    if argv is None:
        in_package = True

    in_package = False if in_package is None else in_package
    
    parser = ArgumentParser()
    parser.add_argument('subcommand', nargs='?', help='subcommands: dfuhelper, clean')
    
    parser.add_argument('-d', '--debug', action='store_true',
                        help='shows debug info, useful for testing')
    parser.add_argument('-R', '--restore-rootfs', action='store_true',
                        help='restore rootfs')
    parser.add_argument('-s', '--safe-mode', action='store_true',
                        help='boot without tweaks enabled')
    parser.add_argument('-S', '--serial', action='store_true',
                        help='add serial=3 to bootargs for serial output')
    parser.add_argument('-l', '--disable-analytics', action='store_true',
                        help='disables anonymous analytics')
    # parser.add_argument('-a', '--a10-sep-test', action='store_true', # TODO: test and remove this
    #                    help='temporary arg for A10 sep, may or may not work correctly')
    parser.add_argument('-v', '--version', action='version', version=f'palera1n v{utils.get_version()}',
                        help='show current version and exit')
    args = parser.parse_args()

    pr = palera1n.palera1n(in_package, args)
    try:
        pr.main()
    except KeyboardInterrupt:
        exit(1)


if __name__ == '__main__':
    main()