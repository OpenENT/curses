import requests
import json

from playlist import playlist

class PlayerD:

    def __init__(self, instance, host):
        self.current_playlist = None
        self.instance = instance
        self.host = host

    def play(self, url: str):
        try:
            return requests.get(self.host+"/action", params={'type': 'play', 'arg': url}).text
        except:
            return None

    def resume(self):
        try:
            return requests.get(self.host+"/action", params={'type': 'resume'}).text
        except:
            return None
        
    def pause(self):
        try:
            return requests.get(self.host+"/action", params={'type': 'pause'}).text
        except:
            return None

    def close(self):
        try:
            return requests.get(self.host+"/action", params={'type': 'close'}).text
        except:
            return None

    def set_volume(self, volume: int):
        try:
            return requests.get(self.host+"/action", params={'type': 'volume', 'arg': volume}).text
        except:
            return None

    def go_at(self, seconds: int):
        try:
            return requests.get(self.host+"/action", params={'type': 'go_at', 'arg': seconds}).text
        except:
            return None

    def playlist_append(self, song):
        if self.current_playlist is None:
            self.current_playlist = playlist('Queue')
        try:
            r = requests.get(self.host+"/action", params={'type': 'playlist_append', 'arg': self.check_download(song)}).text
            self.current_playlist['songs'].append(song)
            return r
        except Exception as e:
            raise e
    
    def playlist_remove(self, index: int):
        if self.current_playlist is not None:
            del self.current_playlist[[*self.current_playlist.keys()][index]] # ? needs testing
        try:
            return requests.get(self.host+"/action", params={'type': 'playlist_remove', 'arg': index}).text
        except:
            return None

    def playlist_clear(self):
        self.current_playlist = None
        try:
            return requests.get(self.host+"/action", params={'type': 'playlist_clear'}).text
        except:
            return None

    def playlist_go(self, index: int):
        try:
            return requests.get(self.host+"/action", params={'type': 'playlist_go', 'arg': index}).text
        except:
            return None

    def check_download(self, song) -> str:
        try:
            if self.instance.settings.providers[song['provider']]['prefer_download']:
                res = self.instance.backend.download(song)
                if 'stream_url' in res:
                    return res['stream_url']
            return song['stream_url']
        except:
            return None

    def play_song(self, song, history=True):
        if history and self.instance.settings.collect_history:
            self.instance.settings.insert_song(song)
        self.current_playlist = playlist('Queue')
        self.current_playlist['songs'].append(song)
        self.play(self.check_download(song))

    def play_playlist(self, playlist):
        self.close()
        self.playlist_clear()
        self.current_playlist = playlist
        for song in playlist['songs']:
            self.playlist_append(self.check_download(song))
        self.playlist_go(0)

    def get_status(self):
        t = requests.get(self.host+"/status").text
        return json.loads(t)

class Backend:

    def __init__(self, host):
        self.host = host
        self.providers = list()
        
    def connect(self):
        self.providers = json.loads(requests.get(self.host+"/info").text)['providers']

    def search(self, provider, query):
        return json.loads(requests.get(self.host+"/search", params={'provider': provider, 'query': query}).text)['result']

    def search_all(self, query, providers=None):
        if providers is None:
            providers = self.providers
        results = list()
        for provider in providers:
            results.extend(json.loads(requests.get(self.host+"/search", params={'provider': provider, 'query': query}).text)['result'])
        return results

    def download(self, song):
        return json.loads(requests.get(self.host+"/download", params={'provider': song['provider'], 'stream_url': song['stream_url']}).text)

def discovery(subnet): # Bad shit ngl
    hosts = list()
    sip = subnet.split('.')
    if len(sip) != 4:
        raise Exception("Invalid subnet")
    base = f'http://{sip[0]}.{sip[1]}.{sip[2]}.'
    for i in range(255):
        print(f'{base}{i}')
        try:
            r = requests.get(f'{base}{i}:5000').text
            if 'PlayerD' in r:
                hosts.append(f"{base}{i}:5000")
        except:
            continue
    return hosts