from playlist import playlist
import json

def ProviderSettings(provider, prefer_download=True):
    return {'provider': provider, 'prefer_download': prefer_download}

class Settings:

    def __init__(self, path):
        self.path = path
        self.providers = dict()
        self.global_search = []
        self.history = list()
        self.song_history = playlist('Last played')
        self.cache_timeout = 60*60
        self.collect_cache = True
        self.save_cache = True
        self.collect_history = True
        self.refresh_rate = 60
        self.background = 255 # White
        self.foreground = 0 # Black
        self.background_alt = 255 # White
        self.foreground_alt = 10
        self.volume_steps = 1
        self.titlebar = True
        self.titlebar_title = 'OpenPlayer'
        self.debug_mode = False
        self.playerd = 'http://127.0.0.1:5000'
        self.backend = 'http://127.0.0.1:5001'
        try:
            with open(self.path) as f:
                self.__dict__.update(json.load(f))
        except FileNotFoundError:
            self.save()
   
    def insert_history(self, query):
        for q in self.history:
            if q.lower() == query.lower():
                self.history.remove(q)
                self.history.insert(0, query)
                return
        self.history.insert(0, query)
        self.save()

    def insert_song(self, song):
        songs = self.song_history['songs']
        for s in songs:
            if s['title'] == song['title']:
                songs.remove(s)
                songs.insert(0, s)
                return
        songs.insert(0, song)
        self.save()

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.__dict__, f, indent=4, sort_keys=True)
