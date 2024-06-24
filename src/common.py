from os import environ, makedirs, path
from typing import Any, Optional
import json

__storage_relpath = "./releaser/storage.json"
__work_path = environ["WORK_PATH"]
__storage_path = path.join(__work_path, __storage_relpath)

class Storage:
    input_mode: str
    input_prerelease: bool
    body: str
    old_release_url: str
    old_release_tag: str
    new_release_tag: str
    new_relese_title: str

    def __init__(self, *, input_mode: Optional[str] = None, input_prerelease: Optional[bool] = None) -> None:
        if input_mode != None:
            self.input_mode = input_mode
        if input_prerelease != None:
            self.input_prerelease = input_prerelease

    @classmethod
    def create_from_json(cls, data: dict[str, Any]):
        ins = cls()
        ins.load_from_json(data)
        return ins

    def load_from_json(self, data: dict[str, Any]):
        for k, v in data.items():
            setattr(self, k, v)
    
    def save_to_json(self) -> dict[str, Any]:
        attr = [a for a in dir(self) if not (a.startswith("__") and a.endswith("__")) and not a in ["load_from_json", "save_to_json"]]
        data: dict[str, Any] = {}
        for a in attr:
            data[a] = getattr(self, a)
        return data

def get_storage() -> Storage:
    with open(__storage_path, "r") as f:
        return Storage.create_from_json(json.load(f))

def save_storage(storage: Storage):
    if not path.exists(p := path.dirname(__storage_path)):
        makedirs(p, exist_ok=True)
    with open(__storage_path, "w") as f:
        json.dump(storage.save_to_json(), f)