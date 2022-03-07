import os


class FileCache:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir if cache_dir.endswith("/") else cache_dir + "/"

    def get(self, filename: str):
        try:
            with open(self.cache_dir + filename, "r") as f:
                return f.read()
        except IOError:
            return None

    def add(self, filename: str, contents: str):
        with open(self.cache_dir + filename, "w") as f:
            f.write(contents)

    def remove(self, filename: str):
        if os.path.exists(self.cache_dir + filename):
            os.remove(self.cache_dir + filename)
