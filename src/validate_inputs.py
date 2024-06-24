from os import getenv
from typing import Any

class InputError(ValueError):
    def __init__(self, input_name: str, value: Any) -> None:
        super().__init__(f"input '{input_name}' has the invalid value '{value}'")

if __name__ == "__main__":
    if not (v := getenv("prerelease")) in ["true", "false"]:
        raise InputError("prerelease", v)
    if not (v := getenv("mode")) in ["major", "minor", "pre"]:
        raise InputError("mode", v)