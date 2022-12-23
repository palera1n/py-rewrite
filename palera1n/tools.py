import subprocess
from shutil import which

from .errors import ToolFailed, DependencyNotFound, PatchFailed
from tempfile import NamedTemporaryFile

class _Tool:
    def __init__(self, binary: str) -> None:
        self._name = self._check_path(binary)

    def _check_path(self, binary: str) -> str:
        if which(binary) is None:
            raise DependencyNotFound(binary)

        return binary

    def _run(self, *args: list[str]) -> str:
        try:
            return subprocess.check_output([self._name, *args], stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            raise ToolFailed(self._name) from e

class iBoot64Patcher(_Tool):
    def patch(self, input_: bytes) -> bytes:
        with NamedTemporaryFile(mode='wb') as input_file, NamedTemporaryFile(mode='rb') as output_file:
            input_file.write(input_)

            try:
                self._run(input_file.name, output_file.name)
                return output_file.read()
            except ToolFailed as e:
                raise PatchFailed(self._name) from e

    
    def get_version(self) -> str:
        return self._run('--version')