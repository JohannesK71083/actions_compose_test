from os import getenv

if __name__ == "__main__":
    print(getenv("prerelease"), type(getenv("prerelease")))
    print(getenv("mode"))