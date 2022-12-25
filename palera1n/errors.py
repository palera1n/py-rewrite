from subprocess import CalledProcessError
from typing import NoReturn

from requests import Response


class Palera1nError(Exception):
    pass


class APIError(Palera1nError):
    def __init__(self, name: str, response: Response) -> NoReturn:
        super().__init__(
            f'{name} API (URL: {response.url}) returned status code: {response.status_code}'
        )


class DeviceError(Palera1nError):
    pass


class PwnError(DeviceError):
    pass


class PwnFailed(PwnError):
    def __init__(self, binary: str) -> NoReturn:
        super().__init__(
            f"Patch: '{binary}' failed to run (error code {self.__cause__.returncode}:\n{self.__cause__.stdout})"
        )


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


class ToolOutdated(ToolError):
    def __init__(self, binary: str) -> NoReturn:
        super().__init__(f"Tool: '{binary}' is out of date.")


class PatchError(ToolError):
    pass


class PatchFailed(PatchError, CalledProcessError):
    def __init__(self, binary: str) -> NoReturn:
        super().__init__(
            f"Patch: '{binary}' failed to run (error code {self.__cause__.returncode}:\n{self.__cause__.stdout})"
        )
