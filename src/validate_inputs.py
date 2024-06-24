from os import getenv

if __name__ == "__main__":
    if not (v := getenv("prerelease")) in ["true", "false"]:
        raise ValueError(f"input 'prerelease' has an invalid value: {v}")
    if not (v := getenv("mode")) in ["major", "minor", "pre"]:
        raise ValueError(f"input 'mode' has an invalid value: {v}")