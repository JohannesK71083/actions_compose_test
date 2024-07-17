from __future__ import annotations
from os import environ
from typing import Any, get_type_hints


class __GithubENVManagerMeta(type):
    def __new__(cls, name: str, bases: tuple[type, ...], dct: dict[str, str]) -> __GithubENVManagerMeta:
        x = super().__new__(cls, name, bases, dct)
        return x

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith("__") and __name.endswith("__"):
            return super().__getattribute__(__name)

        if __name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {__name}")

        st = environ[__name]
        st = st.replace("\\n", "\n")

        return get_type_hints(self)[__name](st)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {__name}")

        if type(__value) == bool:
            st = "true" if __value else "false"
        else:
            st = str(__value)
        st = st.replace("\r", "").replace("\n", "\\n")

        with open(environ["GITHUB_ENV"], "a") as f:
            f.write(f"{__name}={st}\n")


class GithubENVManager(metaclass=__GithubENVManagerMeta):
    pass
