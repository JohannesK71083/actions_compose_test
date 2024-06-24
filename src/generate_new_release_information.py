from common import get_storage, save_storage

if __name__ == "__main__":
    storage = get_storage()

    old_tag = storage.old_release_tag

    if old_tag[0] != "V":
        raise ValueError(f"the LAST_RELEASE_TAG_NAME ({old_tag}) is invalid (format: V1.0_pre-1)")

    old_tag = old_tag.removeprefix("V")

    old_prerelease_number = "0"
    if (i := old_tag.find("_pre-")) != -1:
        old_prerelease_number = old_tag[i+4:]
        old_tag = old_tag[:i]

    trenner = old_tag.find(".")

    old_version_major = old_tag[:trenner]
    old_version_minor = old_tag[trenner+1:]

    if not (old_prerelease_number.isnumeric() and old_version_major.isnumeric() and old_version_minor.isnumeric()):
        raise ValueError(f"at least one value could not be parsed:\nold_prerelease_number={old_prerelease_number}\nold_version_major={old_version_major}\nold_version_minor={old_version_minor}")

    old_prerelease_number = int(old_prerelease_number)
    old_version_major = int(old_version_major)
    old_version_minor = int(old_version_minor)

    match(storage.input_mode):
        case "major":
            old_version_major += 1
        case "minor":
            old_version_minor += 1
        case "pre":
            if old_prerelease_number == 0:
                raise ValueError("cannot create prerelease of already released version")
        case _:
            pass

    if storage.input_prerelease:
        old_prerelease_number += 1

    new_tag = f"V{old_version_major}.{old_version_minor}" + f"_pre-{old_prerelease_number}" if storage.input_prerelease else ""
    new_title = f"Version {old_version_major}.{old_version_minor}" + f" pre-{old_prerelease_number}" if storage.input_prerelease else ""

    storage.new_release_tag = new_tag
    storage.new_relese_title = new_title

    save_storage(storage)