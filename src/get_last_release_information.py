from os import getenv
import requests
from common import get_storage, save_storage

if __name__ == "__main__":
    storage = get_storage()
    token = getenv("GITHUB_TOKEN")

    r = requests.get('https://api.github.com/repos/JohannesK71083/actions_test/releases', headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {token}"})
    js = r.json()[0]

    storage.old_release_url = js["html_url"]
    storage.old_release_tag = js["tag_name"]
    storage.old_release_body = js["body"]

    save_storage(storage)
