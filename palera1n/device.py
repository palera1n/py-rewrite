import time
from functools import cached_property
from pathlib import Path
from typing import Optional

import usb
import usb.backend.libusb1
from pymobiledevice3.irecv import IRecv, Mode

from .errors import DeviceNotFound


class _IRecv(IRecv):
    def _get_backend(self) -> str:
        '''Attempt to find a libusb 1.0 library to use as pyusb's backend, exit if one isn't found.'''

        search_paths = (
            Path('/usr/local/lib'),
            Path('/usr/lib'),
            Path('/opt/homebrew/lib'),
            Path('/opt/procursus/lib'),
        )

        for path in search_paths:
            for file_ in path.rglob('*libusb-1.0*'):
                if not file_.is_file():
                    continue

                if file_.suffix not in ('.so', '.dylib'):
                    continue

                return usb.backend.libusb1.get_backend(find_library=lambda _: file_)

        raise usb.core.NoBackendError('No backend available')

    def _find(self, ecid=None, timeout=0xFFFFFFFF, is_recovery=None):
        start = time.time()
        end = start + timeout
        while (self._device is None) and (time.time() < end):
            for device in usb.core.find(find_all=True, backend=self._get_backend()):
                try:
                    if device.manufacturer is None:
                        continue
                    if not device.manufacturer.startswith('Apple'):
                        continue

                    mode = Mode.get_mode_from_value(device.idProduct)
                    if mode is None:
                        # not one of Apple's special modes
                        continue

                    if is_recovery is not None and mode.is_recovery != is_recovery:
                        continue

                    if self._device is not None:
                        raise Exception(
                            'More than one connected device was found connected in recovery mode'
                        )
                    self._device = device
                    self.mode = mode
                    self._populate_device_info()

                    if ecid is not None:
                        found_ecid = int(self._device_info['ECID'], 16)
                        if found_ecid != ecid:
                            # wrong device - move on
                            self._device = None
                            continue
                except ValueError:
                    continue


# TODO: Update to remove dfu/recovery mode requirement
class Device:
    def __init__(self, device: _IRecv):
        if not isinstance(device, _IRecv):
            raise TypeError(f'Expected _IRecv, got {type(device).__name__}')

        self._device = device

        self._device.reset()

    def __del__(self) -> None:
        usb.util.release_interface(self._device._device, 1)

    @classmethod
    def find_device(cls, ecid: Optional[int] = None):
        try:
            if ecid is not None:
                return cls(_IRecv(ecid=ecid))
            else:
                return cls(_IRecv())
        except:
            raise DeviceNotFound()

    @cached_property
    def board_config(self):
        return self._device.hardware_model

    @cached_property
    def board_id(self) -> int:
        return self._device.board_id

    @cached_property
    def chip_id(self) -> int:
        return self._device.chip_id

    @cached_property
    def display_name(self) -> str:
        return self._device.display_name

    @cached_property
    def ecid(self) -> int:
        return self._device.ecid

    @cached_property
    def identifier(self) -> str:
        return self._device.product_type

    @cached_property
    def mode(self) -> str:
        return self._device.mode

    @cached_property
    def pwned(self) -> bool:
        return 'PWND' in self._device._device_info.keys()

    def send_data(self, data: bytes) -> None:
        if not isinstance(data, bytes):
            raise TypeError(f'Expected bytes, got {type(data).__name__}')

        self._device.send_buffer(data)

    def reset(self):
        self._device.reset()
