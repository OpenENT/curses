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
                    if f'{path}/Liked songs.json' in file:
                        likedplaylistfound = True
                        self.playlists.insert(0, data)
                    else:    
                        self.playlists.append(data)

        if not likedplaylistfound:
            self.playlists.append(playlist('Liked songs'))
            self.save()

    def save(self):
        for playlist in self.playlists:
            with open(f'{self.path}/{playlist["name"]}.json', 'w') as f:
                json.dump(playlist, f, indent=4)

def playlist(name: str, songs=None):
    if songs is None:
        songs = list()
    return {'type': 'playlist', 'name': name, 'songs': songs}

def playlist_to_list(playlist: dict):
    l = list()
    for song in playlist['songs']:
        l.append(song['title'])
    return l