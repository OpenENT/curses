import requests
import json

class PlayerD:

    def __init__(self, host):
        self.host = host

    def play(self, url: str):
        return requests.get(self.host+"/action", params={'type': 'play', 'arg': url}).text

    def resume(self):
        return requests.get(self.host+"/action", params={'type': 'resume'}).text

    def pause(self):
        return requests.get(self.host+"/action", params={'type': 'pause'}).text

    def close(self):
        return requests.get(self.host+"/action", params={'type': 'close'}).text

    def set_volume(self, volume: int):
        return requests.get(self.host+"/action", params={'type': 'volume', 'arg': volume}).text

    def go_at(self, seconds: int):
        return requests.get(self.host+"/action", params={'type': 'go_at', 'arg': seconds}).text
    
    def playlist_append(self, url: str):
        return requests.get(self.host+"/action", params={'type': 'playlist_append', 'arg': url}).text

    def playlist_remove(self, index: int):
        return requests.get(self.host+"/action", params={'type': 'playlist_remove', 'arg': index}).text
    
    def playlist_clear(self):
        return requests.get(self.host+"/action", params={'type': 'playlist_clear'}).text
    
    def playlist_go(self, index: int):
        return requests.get(self.host+"/action", params={'type': 'playlist_go', 'arg': index}).text
    
    def play_playlist(self, playlist):
        self.close()
        self.playlist_clear()
        for song in playlist['songs']:
            self.playlist_append(song['stream_url'])
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
    sip = subnet.split('.')
    if len(sip) != 4:
        raise Exception("Invalid subnet")
    base = f'http://{sip[0]}.{sip[1]}.{sip[2]}.'
    for i in range(255):
        print(f'{base}{i}')
        try:
            r = requests.get(f'{base}{i}:5000').text
            if 'PlayerD' in r:
                print(f'Found PlayerD on host {base}{i}')
        except:
            continue
        try:
            r = requests.get(f'{base}{i}:5001').text
            if 'Backend' in r:
                print(f'Found Backend on host {base}{i}')
        except:
            continue
