import glob
import json

class PlaylistManager:

    def __init__(self, path):
        self.path = path
        self.playlists = list()
        for file in glob.glob(f"{path}/*.json"):
            with open(file) as f:
                data = json.load(f)
                if 'type' in data and data['type'] == 'playlist':
                    self.playlists.append(data)

    def save(self):
        for playlist in self.playlists:
            with open(f'{self.path}/{playlist["name"]}.json', 'w') as f:
                json.dump(playlist, f, indent=4)

def playlist(name: str, songs=None):
    if songs is None:
        songs = list()
    return {'type': 'playlist', 'name': name, 'songs': songs}
