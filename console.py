from ui import SearchIntent
from clients import PlayerD, Backend

class Console():

    def __init__(self, instance):
        self.instance = instance

    def execute(self, text):
        if text.startswith("!"):
            split = text[1:].split(" ")
            command = split[0]
            args = text[len(command)+1:]
            if command == 'pause':
                self.instance.player.pause()
            elif command == 'resume':
                self.instance.player.resume()
            elif command == 'go':
                if len(split) > 1:
                    self.instance.player.go_at(seconds=int(split[1]))
            elif command == 'volume':
                if len(split) > 1:
                    self.instance.player.set_volume(volume=int(split[1]))
            elif command == 'prefer_download':
                if len(split) > 3:
                    if split[1] in self.instance.settings.providers:
                        self.instance.settings.providers[split[1]]['prefer_download'] = bool(split[2])
            elif command == 'set_playerd':
                if len(split) > 1:
                    self.instance.player = PlayerD(split[1])
            elif command == 'set_backend':
                if len(split) > 1:
                    self.instance.set_backend(Backend(split[1]))
            elif command in self.instance.backend.providers:
                res = self.instance.backend.search(provider=command, query=args)
                return SearchIntent(self.instance, res)
        else:
            res = self.instance.backend.search_all(query=text)
            return SearchIntent(self.instance, res)            
