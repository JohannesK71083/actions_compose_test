from enum import Enum, auto
from os import path
import re
from sys import exc_info, stderr
from traceback import format_exc
from typing import Any, NamedTuple, Optional, TypedDict
from pathvalidate import sanitize_filename

import requests

from GithubStorageManager import GithubENVManager, GithubOutputManager

TEMP_BODY_PATH: str = "./temp_body.txt"


def print_to_err(x: str):
    return print(x, file=stderr)


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
    title_format: str
    ignore_drafts: bool
    body_mode: BODY_MODE
    body_path: str
    body: str
    full_source_code_filename: str
    version_text_repo_file_path: Optional[str]
    version_text_format: str


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
    INPUT_TITLE_FORMAT: str
    IGNORE_DRAFTS: str
    INPUT_REUSE_OLD_BODY: str
    INPUT_BODY_PATH: str
    INPUT_BODY: str
    INPUT_FULL_SOURCE_CODE_FILENAME: str
    INPUT_VERSION_TEXT_REPO_FILE: str
    INPUT_VERSION_TEXT_FORMAT: str


class OutputStorage(GithubOutputManager):
    tag: str
    title: str
    body_path: str
    files: str
    full_source_code_filename: str


Version = NamedTuple("Version", [("major", int), ("minor", int), ("prerelease", int)])
TitleFormat = NamedTuple("TitleFormat", [("title_with_pre_text", str), ("title_without_pre_text", str)])


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

    if ENVStorage.IGNORE_DRAFTS not in ["true", "false"]:
        raise InputError("IGNORE_DRAFTS", ENVStorage.IGNORE_DRAFTS)
    ignore_drafts = ENVStorage.IGNORE_DRAFTS == "true"

    github_token = ENVStorage.GITHUB_TOKEN
    work_path = ENVStorage.WORK_PATH
    repository = ENVStorage.REPOSITORY
    tag_format = ENVStorage.INPUT_TAG_FORMAT
    title_format = ENVStorage.INPUT_TITLE_FORMAT
    body_path = ENVStorage.INPUT_BODY_PATH
    body = ENVStorage.INPUT_BODY
    version_text_format = ENVStorage.INPUT_VERSION_TEXT_FORMAT

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

    if tag_format.find("{Maj}") == -1 or tag_format.find("{Min}") == -1 or tag_format.find("{Pre}") == -1:
        raise InputError("INPUT_TAG_FORMAT", tag_format)

    full_source_code_filename = sanitize_filename(ENVStorage.INPUT_FULL_SOURCE_CODE_FILENAME)
    full_source_code_filename = full_source_code_filename.removesuffix(".zip")

    version_text_repo_file = sanitize_filename(ENVStorage.INPUT_VERSION_TEXT_REPO_FILE)
    if version_text_repo_file != "":
        print("HÄÄÄ:", path.relpath(version_text_repo_file, "/"))
        version_text_repo_file_path = path.normpath(path.join(f"{work_path}/checkout/", path.relpath(version_text_repo_file, "/")))
    else:
        version_text_repo_file_path = None

    return Inputs(github_token=github_token, work_path=work_path, repository=repository, mode=mode, prerelease=prerelease, tag_format=tag_format, title_format=title_format, ignore_drafts=ignore_drafts, body_mode=body_mode, body_path=body_path, body=body, full_source_code_filename=full_source_code_filename, version_text_repo_file_path=version_text_repo_file_path, version_text_format=version_text_format)


def parse_tag_format(tag_format: str) -> tuple[tuple[TAG_COMPONENTS, str], ...]:
    tag_ver_components_pos: list[tuple[TAG_COMPONENTS, int]] = [(TAG_COMPONENTS.MAJ, 0), (TAG_COMPONENTS.MIN, 0), (TAG_COMPONENTS.PRE, 0)]
    for i, (key, _) in enumerate(tag_ver_components_pos):
        pos = tag_format.find(key.value)
        tag_ver_components_pos[i] = (key, pos)
    tag_ver_components_pos.sort(key=lambda x: x[1])

    opt_pre_text_pos: tuple[int, int] | None = None
    escape = r"(?<!\\)"  # lookbehind the open/close that no \ is before that
    open = r"\["
    wildcard = r"[^\[]((?![^\\]\[).)*"  # begins with not another opening [ and does not have an unescaped [ inside.
    close = r"\]"
    full_close = "(" + wildcard + escape + close + "|" + close + ")"  # alt. path if it is empty []
    regex = escape + open + full_close
    for m in re.finditer(regex, tag_format):
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


def parse_title_format(title_format: str) -> TitleFormat:
    escape = r"(?<!\\)"  # lookbehind the open/close that no \ is before that
    open = r"\["
    wildcard = r"[^\[]((?![^\\]\[).)*?"  # begins with not another opening [ and does not have an unescaped [ inside.
    close = r"\]"
    full_close = "(" + wildcard + escape + close + "|" + close + ")"  # alt. path if it is empty []
    regex = escape + open + full_close
    for m in re.finditer(regex, title_format):
        pos = m.start(0), m.end(0)
        if title_format.find("{Pre}", pos[0], pos[1]) != -1 and title_format.find("{Maj}", pos[0], pos[1]) == -1 and title_format.find("{Min}", pos[0], pos[1]) == -1:
            return TitleFormat(title_format[:pos[0]] + title_format[pos[0]+1:pos[1]-1] + title_format[pos[1]:], title_format[:pos[0]] + title_format[pos[1]:])
    else:
        return TitleFormat(title_format, title_format)


def get_last_release_information(repository_name: str, github_token: str, ignore_drafts: bool) -> ReleaseInformation:
    r = requests.get(f'https://api.github.com/repos/{repository_name}/releases?per_page=100', headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {github_token}"})
    for js in r.json():
        if not (js["draft"] and ignore_drafts):
            break
    else:
        print_to_err("::warning title=no releases found::no existing " + ("(non-draft) " if ignore_drafts else "") + "releases found!")
        js = {"tag_name": "", "body": ""}

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


def delete_duplicates(repository_name: str, tag: str, github_token: str) -> None:
    r = requests.get(f'https://api.github.com/repos/{repository_name}/releases?per_page=100', headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {github_token}"})
    for js in r.json():
        if js["tag_name"] == tag:
            print_to_err(f"::warning title=duplicate release deleted::deleted duplicate release with same tag (id: {js['id']})")
            requests.delete(f"https://api.github.com/repos/{repository_name}/releases/{js['id']}", headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {github_token}"})


def generate_new_release_information(version: Version, tag_components: tuple[tuple[TAG_COMPONENTS, str], ...], title_format: TitleFormat, mode: MODE, prerelease: bool, body_mode: BODY_MODE, body_path: str, body: str, full_source_code_filename: str, version_text_repo_file_path: Optional[str], version_text_format: TitleFormat) -> str:
    new_version = list(version)
    match(mode):
        case MODE.MAJOR:
            new_version[0] += 1
            new_version[2] = 0
        case MODE.MINOR:
            new_version[1] += 1
            new_version[2] = 0
        case MODE.PRE:
            if new_version[2] == -1:
                raise ValueError("cannot create prerelease of already released version")
    if prerelease:
        new_version[2] += 1

    new_tag = ""
    for k, v in tag_components:
        if k == TAG_COMPONENTS.FILLER:
            new_tag += v
        elif k == TAG_COMPONENTS.PRE_TEXT_PRE:
            if prerelease:
                new_tag += v
        elif k == TAG_COMPONENTS.PRE_TEXT_SUF:
            if prerelease:
                new_tag += v
        elif k == TAG_COMPONENTS.MAJ:
            new_tag += str(new_version[0])
        elif k == TAG_COMPONENTS.MIN:
            new_tag += str(new_version[1])
        elif k == TAG_COMPONENTS.PRE:
            if prerelease:
                new_tag += str(new_version[2])

    if prerelease:
        new_title = title_format.title_with_pre_text
        new_version_text = version_text_format.title_with_pre_text
    else:
        new_title = title_format.title_without_pre_text
        new_version_text = version_text_format.title_without_pre_text

    new_title = new_title.replace("{Maj}", str(new_version[0]))
    new_title = new_title.replace("{Min}", str(new_version[1]))
    new_title = new_title.replace("{Pre}", str(new_version[2]))

    if version_text_repo_file_path != None:
        with open(version_text_repo_file_path, "w") as f:
            f.write(new_version_text.replace("{Maj}", str(new_version[0])).replace("{Min}", str(new_version[1])).replace("{Pre}", str(new_version[2])))

    OutputStorage.tag = new_tag
    OutputStorage.title = new_title

    match body_mode:
        case BODY_MODE.BODY_FROM_FILE:
            OutputStorage.body_path = body_path
        case BODY_MODE.BODY_FROM_INPUT:
            with open(TEMP_BODY_PATH, "w") as f:
                f.write(body)
            OutputStorage.body_path = TEMP_BODY_PATH
        case _:
            raise ValueError

    OutputStorage.full_source_code_filename = full_source_code_filename
    OutputStorage.files = path.join(ENVStorage.WORK_PATH, full_source_code_filename + ".zip")

    return new_tag


def main() -> None:
    inputs = validate_inputs()
    tag_components = parse_tag_format(inputs["tag_format"])
    title_format = parse_title_format(inputs["title_format"])
    version_text_format = parse_title_format(inputs["version_text_format"])
    last_release_information = get_last_release_information(inputs["repository"], inputs["github_token"], inputs["ignore_drafts"])

    try:
        version = get_old_version(tag_components, last_release_information["tag"])
    except Exception:
        exc = format_exc()
        if last_release_information["tag"] != "":
            print_to_err(f"::error title=VERSION_PARSING_ERROR::Error while parsing old version! Using Version(1, 0, 0) instead.\nError:\n{exc}")
        version = Version(1, 0, 0)

    if inputs["body_mode"] == BODY_MODE.REUSE_OLD_BODY:
        body = last_release_information["body"]
        body_mode = BODY_MODE.BODY_FROM_INPUT
    else:
        body = inputs["body"]
        body_mode = inputs["body_mode"]

    release_tag = generate_new_release_information(version, tag_components, title_format, inputs["mode"], inputs["prerelease"], body_mode, inputs["body_path"], body, inputs["full_source_code_filename"], inputs["version_text_repo_file_path"], version_text_format)
    delete_duplicates(inputs["repository"], release_tag, inputs["github_token"])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        exc = format_exc()
        exc_type, exc_obj, exc_tb = exc_info()
        ln = exc_tb.tb_lineno if exc_tb is not None else -1
        fname = path.split(exc_tb.tb_frame.f_code.co_filename)[1] if exc_tb is not None else ""
        print_to_err(f"::error title={type(e).__name__}::{type(e).__name__}: {str(e)}\n{exc}")
        exit(1)
