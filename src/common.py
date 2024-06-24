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
        
        return get_type_hints(self)[__name](environ[__name.upper()])
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {__name}")
        
        environ[__name.upper()] = str(__value)


class Storage(metaclass=__StorageManager):
    work_path: str
    input_mode: str
    input_prerelease: bool
    old_release_url: str
    old_release_tag: str
    old_release_body: str
    new_release_tag: str
    new_release_title: str