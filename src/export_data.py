from sys import argv
from common import get_storage

if __name__ == "__main__":
    storage = get_storage()
    BODY_FILE = f"{storage.work_path}/releaser/old_release_body.txt"

    if len(argv) != 2:
        raise ValueError(f"invalid number of arguments: {argv[1:]}")
    
    match argv[1]:
        case "OLD_RELEASE_BODY":
            with open(BODY_FILE, "w") as f:
                f.write(storage.old_release_body)
        case "NEW_RELEASE_TAG":
            print(storage.new_release_tag)
        case "NEW_RELEASE_TITLE":
            print(storage.new_relese_title)
        case _:
            raise ValueError(f"invalid argument: {argv[1]}")