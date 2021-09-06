import glob
import json

class PlaylistManager:

    def __init__(self, path):
        self.path = path
        self.playlists = list()
        likedplaylistfound = False
        for file in glob.glob(f"{path}/*.json"):
            print(file)
            with open(file) as f:
                data = json.load(f)
                if 'type' in data and data['type'] == 'playlist':
                    if f'{path}/liked.json' in file:
                        likedplaylistfound = True
                    data['filename'] = file
                    self.playlists.append(data)

        if not likedplaylistfound:
            self.playlists.append(playlist('Liked songs', [], filename = f'{path}/liked.json'))
            self.save()

    def save(self):
        for playlist in self.playlists:
            with open(playlist['filename'], 'w') as f:
                json.dump(playlist, f, indent=4)

def playlist(name: str, songs: list, filename=None):
    return {'type': 'playlist', 'filename': filename, 'name': name, 'songs': songs}
