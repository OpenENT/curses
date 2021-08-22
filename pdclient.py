import requests
import json

class PDClient:

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
