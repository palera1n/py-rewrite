import subprocess
from shutil import which
from tempfile import NamedTemporaryFile
from typing import Optional

from pyimg4 import Keybag

from .errors import DependencyNotFound, PatchFailed, PwnFailed, ToolFailed, ToolOutdated


# TODO: Write _Tool subclasses for Kernel64Patcher and iBootpatch2
class _Tool:
    def __init__(self, binary: str) -> None:
        self._name = binary
        self._path = self._check_path(binary)

    def _check_path(self, binary: str) -> str:
        path = which(binary)
        if path is None:
            raise DependencyNotFound(binary)

        return path

    def _run(
        self,
        *args: list[Optional[str]],
        timeout: Optional[int] = None,
        env: Optional[dict[str, str]] = None
    ) -> str:
        try:
            return subprocess.check_output(
                executable=self._path,
                args=[self._name, *args],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=timeout,
                env=env,
            )
        except subprocess.CalledProcessError as e:
            raise ToolFailed(self._name) from e


class iBoot64Patcher(_Tool):
    def __init__(self) -> None:
        super().__init__('iBoot64Patcher')

    def patch(self, input_: bytes) -> bytes:
        with NamedTemporaryFile(mode='wb') as input_file, NamedTemporaryFile(
            mode='rb'
        ) as output_file:
            input_file.write(input_)

            try:
                self._run(input_file.name, output_file.name)
                return output_file.read()
            except ToolFailed as e:
                raise PatchFailed(self._name) from e

    def get_version(self) -> str:
        return self._run('--version')


class Gaster(_Tool):
    def __init__(self) -> None:
        super().__init__('gaster')

    def pwn(self) -> None:
        try:
            self._run('pwn', timeout=3)
        except subprocess.TimeoutExpired as e:
            raise PwnFailed(self._name) from e

    def decrypt_keybag(self, keybag: Keybag) -> Keybag:
        try:
            self._run()
        except subprocess.CalledProcessError as e:
            if 'decrypt_kbag' not in e.output:
                raise ToolOutdated(self._name)

        gaster_kbag = self.run[
            'gaster', 'decrypt_kbag', (keybag.iv + keybag.key).hex()
        ].splitlines()[-1]

        return Keybag(
            iv=bytes.fromhex(gaster_kbag.split('IV: ')[1].split(',')[0]),
            key=bytes.fromhex(gaster_kbag.split('key: ')[1]),
        )
