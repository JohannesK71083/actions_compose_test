import json
from os import getenv
import requests

if __name__ == "__main__":
    token = getenv("GITHUB_TOKEN")
    r = requests.get('https://api.github.com/repos/JohannesK71083/actions_test/releases', headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {token}"})
    print(json.dumps(r.json()[0]))
