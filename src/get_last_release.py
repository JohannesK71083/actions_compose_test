import json
from os import getenv
import requests

token = getenv("")
r = requests.get('https://api.github.com/repos/JohannesK71083/actions_test/releases', headers={'Accept': 'application/vnd.github+json', 'Authorization': f"Bearer {token}"})
print(json.dumps(r.json()[0]))
