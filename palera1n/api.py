import requests

from .device import Device
from .errors import APIError
from .firmware import Firmware


def get_firmware(device: Device, buildid: str) -> Firmware:
    resp = requests.get(
        f'https://api.ipsw.me/v4/device/{device.identifier}',
        params={'type': 'ipsw'},
    )
    if resp.status_code != 200:
        raise APIError('IPSW.me', resp)

    data = resp.json()
    firmwares = data.get('firmwares', None)
    if firmwares is None:
        pass  # TODO: raise error

    resp = requests.get(
        f'https://api.m1sta.xyz/betas/{device.identifier}',
    )
    if resp.status_code != 200:
        raise APIError('Beta API', resp)

    firmwares += resp.json()

    for firmware in firmwares:
        if firmware['buildid'].casefold() == buildid.casefold():
            return Firmware(firmware)

    raise ValueError(
        f'No firmware with buildid: {buildid} found for device: {device.identifier}.'
    )
