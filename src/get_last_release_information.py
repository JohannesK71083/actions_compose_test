import json
from os import getenv
from sys import stderr
import requests

if __name__ == "__main__":
    token = getenv("GITHUB_TOKEN")
    r = requests.get('https://api.github.com/repos/JohannesK71083/actions_test/releases', headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {token}"})
    js = r.json()[0]
    print(js["body"], file=stderr)
    print(json.dumps(js), file=stderr)
    print(f'{js["html_url"]}|{js["tag_name"]}|{js["body"]}')
