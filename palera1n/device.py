from typing import Optional

import usb
import usb.backend.libusb1
from pymobiledevice3.irecv import IRecv, Mode
import time
from pathlib import Path

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

    def _find(self, ecid=None, timeout=0xffffffff, is_recovery=None):
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
                        raise Exception('More then one connected device was found connected in recovery mode')
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
            raise TypeError(f"Expected _IRecv, got {type(device).__name__}")

        self._device = device

        self._device.reset()

    @classmethod
    def find_device(cls, ecid: Optional[int] = None):
        if isinstance(ecid, int):
            return cls(_IRecv(ecid=hex(ecid)[2:].upper()))
        else:
            return cls(_IRecv())

    @property
    def mode(self) -> str:
        return self._device.mode

    def send_data(self, data: bytes) -> None:
        if not isinstance(data, bytes):
            raise TypeError(f"Expected bytes, got {type(data).__name__}")

        self._device.send_buffer(data)
