from os import getenv
from typing import Any

class InputError(ValueError):
    def __init__(self, input_name: str, value: Any) -> None:
        super().__init__(f"input '{input_name}' has the invalid value '{value}'")

if __name__ == "__main__":
    if not (v := getenv(i := "PRERELEASE")) in ["true", "false"]:
        raise InputError(i, v)
    if not (v := getenv(i := "MODE")) in ["major", "minor", "pre"]:
        raise InputError(i, v)