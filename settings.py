import json

def ProviderSettings(provider, prefer_download=True):
    return {'provider': provider, 'prefer_download': prefer_download}

class Settings:

    def __init__(self, path):
        self.path = path
        self.providers = dict()
        with open(self.path) as f:
            self.__dict__.update(json.load(f))

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.__dict__, f)