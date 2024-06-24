from os import environ

env_path = environ["GITHUB_ENV"]

with open(env_path, "a") as f:
    f.write("TEST=123")