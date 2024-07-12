from enum import Enum, auto
from os import path
import re
from typing import Any, NamedTuple, Optional, TypedDict

import requests

from GithubENVManager import GithubENVManager

TEMP_BODY_PATH: str = "./temp_body.txt"


class InputError(ValueError):
    def __init__(self, input_name: str, value: Any) -> None:
        super().__init__(f"input '{input_name}' has the invalid value '{value}'")


class MODE(Enum):
    MAJOR = auto()
    MINOR = auto()
    PRE = auto()


class BODY_MODE(Enum):
    REUSE_OLD_BODY = auto()
    BODY_FROM_FILE = auto()
    BODY_FROM_INPUT = auto()


class TAG_COMPONENTS(Enum):
    FILLER = "F"
    MAJ = "{Maj}"
    MIN = "{Min}"
    PRE_TEXT_PRE = "PP"
    PRE = "{Pre}"
    PRE_TEXT_SUF = "PS"


class Inputs(TypedDict):
    github_token: str
    work_path: str
    repository: str

    mode: MODE
    prerelease: bool
    tag_format: str
    body_mode: BODY_MODE
    body_path: str
    body: str


class ReleaseInformation(TypedDict):
    tag: str
    body: str


class ENVStorage(GithubENVManager):
    GITHUB_TOKEN: str
    WORK_PATH: str
    REPOSITORY: str

    INPUT_MODE: str
    INPUT_PRERELEASE: str
    INPUT_TAG_FORMAT: str
    INPUT_REUSE_OLD_BODY: str
    INPUT_BODY_PATH: str
    INPUT_BODY: str

    s_release_tag: str
    s_release_title: str
    s_release_body_path: str

Version = NamedTuple("Version", [("major", int), ("minor", int), ("prerelease", int)])


def validate_inputs() -> Inputs:
    match ENVStorage.INPUT_MODE:
        case "major":
            mode = MODE.MAJOR
        case "minor":
            mode = MODE.MINOR
        case "pre":
            mode = MODE.PRE
        case _:
            raise InputError("INPUT_MODE", ENVStorage.INPUT_MODE)

    if ENVStorage.INPUT_PRERELEASE not in ["true", "false"]:
        raise InputError("INPUT_PRERELEASE", ENVStorage.INPUT_PRERELEASE)
    prerelease = ENVStorage.INPUT_PRERELEASE == "true"

    if ENVStorage.INPUT_REUSE_OLD_BODY not in ["true", "false"]:
        raise InputError("INPUT_REUSE_OLD_BODY", ENVStorage.INPUT_REUSE_OLD_BODY)

    github_token = ENVStorage.GITHUB_TOKEN
    work_path = ENVStorage.WORK_PATH
    repository = ENVStorage.REPOSITORY
    tag_format = ENVStorage.INPUT_TAG_FORMAT
    body_path = ENVStorage.INPUT_BODY_PATH
    body = ENVStorage.INPUT_BODY

    if ENVStorage.INPUT_REUSE_OLD_BODY == "true":
        body_mode = BODY_MODE.REUSE_OLD_BODY
    elif body_path != "":
        body_mode = BODY_MODE.BODY_FROM_FILE
    else:
        body_mode = BODY_MODE.BODY_FROM_INPUT

    if body_mode == BODY_MODE.BODY_FROM_FILE:
        if not path.exists(ENVStorage.INPUT_BODY_PATH):
            raise FileNotFoundError(ENVStorage.INPUT_BODY_PATH)

    if ENVStorage.INPUT_MODE == "pre" and ENVStorage.INPUT_PRERELEASE != "true":
        raise ValueError("mode 'pre' requires 'prerelease' to be True.")

    # TODO
    if tag_format.find("{Maj}") == -1 or tag_format.find("{Min}") == -1 or tag_format.find("{Pre}") == -1:
        raise InputError("INPUT_TAG_FORMAT", tag_format)

    return Inputs(github_token=github_token, work_path=work_path, repository=repository, mode=mode, prerelease=prerelease, tag_format=tag_format, body_mode=body_mode, body_path=body_path, body=body)


def parse_tag_format(tag_format: str) -> tuple[tuple[TAG_COMPONENTS, str], ...]:
    tag_ver_components_pos: list[tuple[TAG_COMPONENTS, int]] = [(TAG_COMPONENTS.MAJ, 0), (TAG_COMPONENTS.MIN, 0), (TAG_COMPONENTS.PRE, 0)]
    for i, (key, _) in enumerate(tag_ver_components_pos):
        pos = tag_format.find(key.value)
        tag_ver_components_pos[i] = (key, pos)
    tag_ver_components_pos.sort(key=lambda x: x[1])

    opt_pre_text_pos: tuple[int, int] | None = None
    for m in re.finditer("\\[.*?\\]", tag_format):
        pos = m.start(0), m.end(0)
        if tag_format.find("{Pre}", pos[0], pos[1]) != -1 and tag_format.find("{Maj}", pos[0], pos[1]) == -1 and tag_format.find("{Min}", pos[0], pos[1]) == -1:
            opt_pre_text_pos = pos[0], pos[1]
            break

    tag_components: list[tuple[TAG_COMPONENTS, str]] = []

    def add_tag_component(key: TAG_COMPONENTS, value: Optional[str]):
        if value == "":
            return
        tag_components.append((key, value if value is not None else ""))

    begin_index = 0
    for i in range(3):
        key, pos = tag_ver_components_pos[i]

        if key == TAG_COMPONENTS.PRE and opt_pre_text_pos is not None:
            add_tag_component(TAG_COMPONENTS.FILLER, tag_format[begin_index:opt_pre_text_pos[0]])
            add_tag_component(TAG_COMPONENTS.PRE_TEXT_PRE, tag_format[opt_pre_text_pos[0] + 1: pos])
            add_tag_component(key, None)
            add_tag_component(TAG_COMPONENTS.PRE_TEXT_SUF, tag_format[pos+len(key.value): opt_pre_text_pos[1] - 1])
            begin_index = opt_pre_text_pos[1]
            continue

        add_tag_component(TAG_COMPONENTS.FILLER, tag_format[begin_index:pos])
        add_tag_component(key, None)
        begin_index = (pos + len(key.value))
    add_tag_component(TAG_COMPONENTS.FILLER, tag_format[begin_index:])

    return tuple(tag_components)


def get_last_release_information(repository_name: str, github_token: str) -> ReleaseInformation:
    r = requests.get(f'https://api.github.com/repos/{repository_name}/releases', headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {github_token}"})
    js = r.json()[0]

    return ReleaseInformation(tag=js["tag_name"], body=js["body"])


def get_old_version(tag_components: tuple[tuple[TAG_COMPONENTS, str], ...], old_tag: str) -> Version:
    major_version = -1
    minor_version = -1
    prerelease_version = -1

    for i, (key, value) in enumerate(tag_components):
        if key in [TAG_COMPONENTS.PRE_TEXT_PRE, TAG_COMPONENTS.PRE_TEXT_SUF]:
            if i + 1 < len(tag_components):
                next_component_value = tag_components[i+1][1]
                if next_component_value.startswith(value):
                    if not old_tag.removeprefix(value).startswith(next_component_value):
                        continue

        if key in [TAG_COMPONENTS.FILLER, TAG_COMPONENTS.PRE_TEXT_PRE, TAG_COMPONENTS.PRE_TEXT_SUF]:
            old_tag = old_tag.removeprefix(value)
        elif key in [TAG_COMPONENTS.MAJ, TAG_COMPONENTS.MIN, TAG_COMPONENTS.PRE]:
            for key2, value2 in tag_components[i+1:]:
                if key2 == TAG_COMPONENTS.PRE:
                    continue
                end = old_tag.find(value2)
                if end != -1 or key2 not in [TAG_COMPONENTS.PRE_TEXT_PRE, TAG_COMPONENTS.PRE_TEXT_SUF]:
                    break
            else:
                end = None

            match key:
                case TAG_COMPONENTS.MAJ:
                    major_version = int(old_tag[:end])
                case TAG_COMPONENTS.MIN:
                    minor_version = int(old_tag[:end])
                case TAG_COMPONENTS.PRE:
                    if old_tag[:end] != "":
                        prerelease_version = int(old_tag[:end])
                case _:
                    raise ValueError

            if end is not None:
                old_tag = old_tag[end:]
            else:
                old_tag = ""
                break

    if major_version == -1 or minor_version == -1:
        raise RuntimeError

    return Version(major_version, minor_version, prerelease_version)


def generate_new_release_information(old_tag: str, mode: MODE, prerelease: bool, body_mode: BODY_MODE, body_path: str, body: str):
    if old_tag[0] != "V":
        raise ValueError(f"the LAST_RELEASE_TAG_NAME ({old_tag}) is invalid (format: V1.0_pre-1)")

    old_tag = old_tag.removeprefix("V")

    old_prerelease_number = "0"
    if (i := old_tag.find(st := "_pre-")) != -1:
        old_prerelease_number = old_tag[i+len(st):]
        old_tag = old_tag[:i]

    trenner = old_tag.find(".")

    old_version_major = old_tag[:trenner]
    old_version_minor = old_tag[trenner+1:]

    if not (old_prerelease_number.isnumeric() and old_version_major.isnumeric() and old_version_minor.isnumeric()):
        raise ValueError(f"at least one value could not be parsed:\nold_prerelease_number={old_prerelease_number}\nold_version_major={old_version_major}\nold_version_minor={old_version_minor}")

    old_prerelease_number = int(old_prerelease_number)
    old_version_major = int(old_version_major)
    old_version_minor = int(old_version_minor)

    match(mode):
        case MODE.MAJOR:
            old_version_major += 1
            old_prerelease_number = 0
        case MODE.MINOR:
            old_version_minor += 1
            old_prerelease_number = 0
        case MODE.PRE:
            if old_prerelease_number == 0:
                raise ValueError("cannot create prerelease of already released version")

    if prerelease:
        old_prerelease_number += 1

    new_tag = f"V{old_version_major}.{old_version_minor}" + f"_pre-{old_prerelease_number}" if GithubENVManager.input_prerelease else ""
    new_title = f"Version {old_version_major}.{old_version_minor}" + f" pre-{old_prerelease_number}" if GithubENVManager.input_prerelease else ""

    GithubENVManager.s_release_tag = new_tag
    GithubENVManager.s_release_title = new_title

    match body_mode:
        case BODY_MODE.BODY_FROM_FILE:
            GithubENVManager.s_release_body_path = body_path
        case BODY_MODE.BODY_FROM_INPUT:
            with open(TEMP_BODY_PATH, "w") as f:
                f.write(body)
            GithubENVManager.s_release_body_path = TEMP_BODY_PATH
        case _:
            raise ValueError


if __name__ == "__main__":
    inputs = validate_inputs()
    tag_components = parse_tag_format(inputs["tag_format"])
    last_release_information = get_last_release_information(inputs["repository"], inputs["github_token"])
    version = get_old_version(tag_components, last_release_information["tag"])
    if inputs["body_mode"] == BODY_MODE.REUSE_OLD_BODY:
        body = last_release_information["body"]
        body_mode = BODY_MODE.BODY_FROM_INPUT
    else:
        body = inputs["body"]
        body_mode = inputs["body_mode"]
    generate_new_release_information(last_release_information["tag"], inputs["mode"], inputs["prerelease"], body_mode, inputs["body_path"], body)
