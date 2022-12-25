from pathlib import Path
from typing import Optional, Union
from urllib import urlparse

import remotezip
import requests

from ._types import Version
from .manifest import Manifest


class Firmware:
    def __init__(self, data: dict):
        self._manifest = None

        required_keys = ('version', 'buildid', 'url')
        if any(key not in data.keys() for key in required_keys):
            raise ValueError(
                f'One or more of the following keys are missing from the provided data: {required_keys}'
            )

        for key, value in data.items():
            if key == 'url':
                if requests.head(value).status_code != 200:
                    raise ValueError(f'Invalid IPSW URL: {value}')

                try:
                    with remotezip.RemoteZip(value) as ipsw:
                        if 'BuildManifest.plist' not in ipsw.namelist():
                            raise ValueError(f'Invalid IPSW URL: {value}')

                except remotezip.RemoteIOError as e:
                    raise ValueError(f'Invalid IPSW URL: {value}') from e

                self._url = value

            elif key == 'version':
                try:
                    self._version = Version(map(int, value.split('.')))
                except:
                    raise ValueError(f'Invalid IPSW version: {value}')

            elif key == 'buildid':
                self._buildid = value

    @property
    def buildid(self) -> str:
        return self._buildid

    @property
    def manifest(self) -> Manifest:
        if self._manifest is None:
            url = urlparse(self.url)
            manifest_url = url._replace(
                path=str(Path(url.path).parents[0] / 'BuildManifest.plist')
            ).geturl()

            manifest = requests.get(manifest_url)

            if manifest.status_code == 200:
                self._manifest = Manifest(manifest.content)
            else:
                self._manifest = Manifest(self.read_file('BuildManifest.plist'))

        return self._manifest

    @property
    def url(self) -> str:
        return self._url

    @property
    def version(self) -> tuple:
        return self._version

    def read_file(self, path: Union[str, Path]) -> Optional[bytes]:
        with remotezip.RemoteZip(self.url) as ipsw:
            return ipsw.read(str(path))
