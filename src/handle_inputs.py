from os import getenv, environ
from typing import Any
from common import Storage

class InputError(ValueError):
    def __init__(self, input_name: str, value: Any) -> None:
        super().__init__(f"input '{input_name}' has the invalid value '{value}'")

if __name__ == "__main__":
    work_path = environ["WORK_PATH"]
    prerelease = getenv(prerelease_key := "PRERELEASE")
    mode = getenv(mode_key := "MODE")

    if not (prerelease) in ["true", "false"]:
        raise InputError(prerelease_key, prerelease)
    if not (mode) in ["major", "minor", "pre"]:
        raise InputError(mode_key, mode)
    
    if mode == "pre" and prerelease != "true":
        raise ValueError("mode 'pre' requires 'prerelease' to be True.")

    Storage.WORK_PATH = work_path
    Storage.INPUT_PRERELEASE = prerelease != "false"
    Storage.INPUT_MODE = mode