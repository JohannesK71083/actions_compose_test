from os import makedirs, path
from common import Storage
import requests

if __name__ == "__main__":
    r = requests.get('https://api.github.com/repos/JohannesK71083/actions_test/releases', headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {Storage.GITHUB_TOKEN}"})
    js = r.json()[0]

    Storage.old_release_url = js["html_url"]
    Storage.old_release_tag = js["tag_name"]
    makedirs(path.dirname(Storage.BODY_PATH), exist_ok=True)
    with open(Storage.BODY_PATH, "w") as f:
        f.write(js["body"])