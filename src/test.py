from __future__ import annotations
import enum
from os import environ
from typing import Any, get_type_hints


class MetaClass(type):
    def __new__(cls, name: str, bases: tuple[type, ...], dct: dict[str, str]) -> MetaClass:
        x = super().__new__(cls, name, bases, dct)
        return x

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith("__") and __name.endswith("__"):
            return super().__getattribute__(__name)

        if __name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {__name}")
        
        return get_type_hints(self)[__name](environ[__name])
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {__name}")
        
        environ[__name] = str(__value)


class Test(metaclass=MetaClass):
    a: enum.Enum
    b: int

class X(enum.Enum):
    A = enum.auto()

Test.a = X.A

print(Test.a, type(Test.a))