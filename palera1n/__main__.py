import argparse
import palera1n
from . import utils


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help="shows some debug info, only useful for testing")
    parser.add_argument('-i', '--ipsw', type=str,
                        help="specify IPSW url")
    parser.add_argument('-t', '--tweaks', type=float,
                        help="specify iOS version for the tethered jailbreak")
    parser.add_argument('-D', '--dfu', type=float,
                        help="specify iOS version for the rootless jailbreak")
    parser.add_argument('-v', '--version', action='version', version=f'palera1n v{utils.get_version()}',
                        help='show current version and exit')
    args = parser.parse_args()

    pr = palera1n.palera1n(args)
    pr.main()


if __name__ == "__main__":
    main()