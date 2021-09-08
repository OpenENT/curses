from pathlib import Path
import json
import re

class PlaylistManager:

    def __init__(self, path):
        self.path = path
        self.playlists = list()
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        for file in p.rglob("*.json"):
            with open(file) as f:
                try:
                    data = json.load(f)
                    if 'type' in data and data['type'] == 'playlist':
                        self.playlists.append(data)
                except Exception:
                    pass

    def save(self):
        for playlist in self.playlists:
            with open(f'{self.path}/{playlist["name"]}.json', 'w') as f:
                json.dump(playlist, f, indent=4)

def playlist(name: str, songs=None):
    if songs is None:
        songs = list()
    return {'type': 'playlist', 'name': name, 'songs': songs}
