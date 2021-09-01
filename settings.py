import json

def ProviderSettings(provider, prefer_download=True):
    return {'provider': provider, 'prefer_download': prefer_download}

class Settings:

    def __init__(self, path):
        self.providers = dict()

    def save(self):
        pass