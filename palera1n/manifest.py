import plistlib

from ._types import Version
from .device import Device


class ManifestImage:
    def __init__(self, name: str, data: dict):
        self._data = data
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._data['Info']['Path']

    @property
    def personalize(self) -> bool:
        return self._data['Info']['Personalize']


class ManifestIdentity:
    def __init__(self, data: dict):
        self._data = data
        self._images = [
            ManifestImage(name, data) for name, data in self._data['Manifest'].items()
        ]

    @property
    def board_config(self) -> str:
        return self._data['Info']['DeviceClass']

    @property
    def board_id(self) -> int:
        return int(self._data['ApBoardID'], 16)

    @property
    def chip_id(self) -> int:
        return int(self._data['ApChipID'], 16)

    @property
    def images(self) -> list[ManfiestImage]:
        return self._images

    @property
    def restore_type(self) -> str:
        return self._data['Info']['RestoreBehavior']


class Manifest:
    def __init__(self, data: bytes):
        self._data = plistlib.loads(data)

        self.version = Version(map(int, self._data['ProductVersion'].split('.')))
        self.buildid = self._data['ProductBuildVersion']
        self.supported_devices = self._data['SupportedProductTypes']

        self.identities = [ManifestIdentity(i) for i in self._data['BuildIdentities']]

    def get_identity(self, device: Device, erase: bool) -> ManifestIdentity:
        try:
            return next(
                i
                for i in self.identities
                if i.boardconfig.casefold() == device.board_config.casefold()
                and i.restore_type == ('Erase' if erase == True else 'Update')
            )
        except StopIteration:
            raise ValueError(f'Failed to find identity for device: {device.identifier}')
