from __future__ import annotations
from os import environ
from typing import Any, get_type_hints

class __StorageManager(type):
    def __new__(cls, name: str, bases: tuple[type, ...], dct: dict[str, str]) -> __StorageManager:
        x = super().__new__(cls, name, bases, dct)
        return x

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith("__") and __name.endswith("__"):
            return super().__getattribute__(__name)

        if __name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {__name}")
        
        st = environ[__name.upper()]
        st = st.replace("\\n", "\n")

        return get_type_hints(self)[__name](st)
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {__name}")
        
        st = str(__value)
        st = st.replace("\r", "").replace("\n", "\\n")

        with open(environ["GITHUB_ENV"], "a") as f:
            f.write(f"{__name.upper()}={st}\n")


class Storage(metaclass=__StorageManager):
    GITHUB_TOKEN: str
    WORK_PATH: str
    BODY_PATH: str
    input_mode: str
    input_prerelease: bool
    old_release_url: str
    old_release_tag: str
    new_release_tag: str
    new_release_title: str