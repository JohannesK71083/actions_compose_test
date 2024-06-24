from os import environ, path
from typing import Any
from common import Storage

class InputError(ValueError):
    def __init__(self, input_name: str, value: Any) -> None:
        super().__init__(f"input '{input_name}' has the invalid value '{value}'")

if __name__ == "__main__":
    prerelease = environ[prerelease_key := "RAW_INPUT_PRERELEASE"]
    mode = environ[mode_key := "RAW_INPUT_MODE"]
    reuse_old_body = environ[reuse_old_body_key := "RAW_INPUT_REUSE_OLD_BODY"]
    body_path = environ[body_path_key := "RAW_INPUT_BODY_PATH"]
    body = environ[body_key := "RAW_INPUT_BODY"]

    if prerelease not in ["true", "false"]:
        raise InputError(prerelease_key, prerelease)
    if mode not in ["major", "minor", "pre"]:
        raise InputError(mode_key, mode)
    if reuse_old_body not in ["true", "false"]:
        raise InputError(reuse_old_body_key, reuse_old_body)
    if reuse_old_body == "false" and body_path == "":
        if not path.exists(body_path):
            raise FileNotFoundError(body_path)
    
    if mode == "pre" and prerelease != "true":
        raise ValueError("mode 'pre' requires 'prerelease' to be True.")

    Storage.input_prerelease = prerelease != "false"
    Storage.input_mode = mode
    Storage.input_reuse_old_body = reuse_old_body != "false"
    Storage.input_body_path = body_path
    Storage.input_body = body