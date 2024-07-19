from __future__ import annotations
from os import environ
from typing import Any, get_type_hints


class __GithubENVManagerMeta(type):
    def __new__(cls, name: str, bases: tuple[type, ...], dct: dict[str, str]) -> __GithubENVManagerMeta:
        x = super().__new__(cls, name, bases, dct)
        return x

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            return super().__getattribute__(name)

        if name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {name}")

        st = environ[name]

        return get_type_hints(self)[name](st)

    def __setattr__(self, name: str, value: Any) -> None:
        if name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {name}")

        if type(value) == bool:
            st = "true" if value else "false"
        else:
            st = str(value)

        environ[name] = st
        with open(environ["GITHUB_ENV"], "a") as f:
            f.write(f"{name}<<EOF\n{st}\nEOF\n")


class GithubENVManager(metaclass=__GithubENVManagerMeta):
    pass


class __GithubOutputManagerMeta(type):
    _outputs: dict[str, Any]

    def __new__(cls, name: str, bases: tuple[type, ...], dct: dict[str, str]) -> __GithubOutputManagerMeta:
        x = super().__new__(cls, name, bases, dct)
        x._outputs = {}
        return x

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__") or name == "_outputs":
            return super().__getattribute__(name)

        if name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {name}")

        return self._outputs[name]

    def __setattr__(self, name: str, value: Any) -> None:
        if name not in self.__annotations__.keys():
            raise AttributeError(f"invalid attribute {name}")

        self._outputs[name] = value

        if type(value) == bool:
            st = "true" if value else "false"
        else:
            st = str(value)

        with open(environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{name}<<EOF\n{st}\nEOF\n")


class GithubOutputManager(metaclass=__GithubOutputManagerMeta):
    pass
