import json

def ProviderSettings(provider, prefer_download=True):
    return {'provider': provider, 'prefer_download': prefer_download}

class Settings:

    def __init__(self, path):
        self.path = path
        self.providers = dict()
        self.global_search = []
        self.history = list()
        self.collect_history = True
        self.refresh_rate = 60
        self.background = 255 # White
        self.foreground = 0 # Black
        self.titlebar = True
        self.titlebar_title = 'OpenPlayer'
        self.playerd = 'http://127.0.0.1:5000'
        self.backend = 'http://127.0.0.1:5001'
        try:
            with open(self.path) as f:
                self.__dict__.update(json.load(f))
        except FileNotFoundError:
            self.save()

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.__dict__, f, indent=4, sort_keys=True)
