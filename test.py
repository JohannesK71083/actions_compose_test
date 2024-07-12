from __future__ import annotations
from enum import Enum
import re
from typing import Optional

#TODO: escape []; what if old tag does not exist

class TAG_COMPONENTS(Enum):
    FILLER = "F"
    MAJ = "{Maj}"
    MIN = "{Min}"
    PRE_TEXT_PRE = "PP"
    PRE = "{Pre}"
    PRE_TEXT_SUF = "PS"

def parse_tag_format(tag_format: str) -> list[tuple[TAG_COMPONENTS, str]]:
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
            add_tag_component(TAG_COMPONENTS.PRE_TEXT_PRE, tag_format[opt_pre_text_pos[0] + 1 : pos])
            add_tag_component(key, None)
            add_tag_component(TAG_COMPONENTS.PRE_TEXT_SUF, tag_format[pos+len(key.value) : opt_pre_text_pos[1] - 1])
            begin_index = opt_pre_text_pos[1]
            continue

        add_tag_component(TAG_COMPONENTS.FILLER, tag_format[begin_index:pos])
        add_tag_component(key, None)
        begin_index = (pos + len(key.value))
    add_tag_component(TAG_COMPONENTS.FILLER, tag_format[begin_index:])

    return tag_components

def get_old_version(tag_components: list[tuple[TAG_COMPONENTS, str]], old_tag: str) -> tuple[int, int, int]:
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
        
    return major_version, minor_version, prerelease_version
                
        

if __name__ == "__main__":
    tag_components = parse_tag_format("{Min}[.{Pre}.]{Maj}")
    #print(tag_components)
    mav, miv, prv = get_old_version(tag_components, "1.15")
    print(mav, miv, prv)
