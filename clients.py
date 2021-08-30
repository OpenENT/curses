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

    def go_at(self, seconds: int):
        return requests.get(self.host+"/action", params={'type': 'go_at', 'arg': seconds}).text
    
    def get_status(self):
        t = requests.get(self.host+"/status").text
        return json.loads(t)

class Backend:

    def __init__(self, host):
        self.host = host
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