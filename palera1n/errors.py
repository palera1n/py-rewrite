from subprocess import CalledProcessError
from typing import Any, NoReturn


class Palera1nError(Exception):
    pass

class DeviceError(Palera1nError):
    pass

class DeviceNotSupported(Palera1nError):
    pass

class DependencyError(Palera1nError):
    pass

class DependencyNotFound(DependencyError, FileNotFoundError):
    def __init__(self, binary: str) -> NoReturn:
        super().__init__(
            f"Required depdendency: '{binary}' is not installed (check your $PATH)."
        )

class ToolError(Palera1nError):
    pass

class ToolFailed(ToolError, CalledProcessError):
    def __init__(self, binary: str) -> NoReturn:
        super().__init__(
            f"Tool: '{binary}' failed to run (error code {self.__cause__.returncode}:\n{self.__cause__.stdout})"
        )

class PatchError(ToolError):
    pass

class PatchFailed(PatchError, CalledProcessError):
    def __init__(self, binary: str) -> NoReturn:
        super().__init__(
            f"Patch: '{binary}' failed to run (error code {self.__cause__.returncode}:\n{self.__cause__.stdout})"
        )