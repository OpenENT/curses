from ui import SearchIntent

class Console():

    def __init__(self, player, backend, settings):
        self.player = player
        self.backend = backend
        self.settings = settings

    def execute(self, text):
        if text.startswith("!"):
            split = text[1:].split(" ")
            command = split[0]
            args = text[len(command):]
            if command == 'pause':
                self.player.pause()
            elif command == 'resume':
                self.player.resume()
            elif command == 'go':
                if len(split) > 1:
                    self.player.go_at(seconds=int(split[1]))
            elif command == 'volume':
                if len(split) > 1:
                    self.player.set_volume(volume=int(split[1]))
            elif command == 'prefer_download':
                if len(split) > 3:
                    if split[1] in self.settings.providers:
                        self.settings.providers[split[1]]['prefer_download'] = bool(split[2])
        else:
            res = self.backend.search_all(query=text)
            return SearchIntent(self.backend, self.player, res, self.settings)            
