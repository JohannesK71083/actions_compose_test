from common import Storage
from os import getenv
import requests

if __name__ == "__main__":
    token = getenv("GITHUB_TOKEN")

    r = requests.get('https://api.github.com/repos/JohannesK71083/actions_test/releases', headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {token}"})
    js = r.json()[0]

    Storage.old_release_url = js["html_url"]
    Storage.old_release_tag = js["tag_name"]
    Storage.old_release_body = js["body"]