from ui import SearchIntent

class Console():

    def __init__(self, player, backend):
        self.player = player
        self.backend = backend

    def execute(self, text):
        if text.startswith("!"):
            split = text[1:].split(" ")
            command = split[0]
            args = text[len(command):]
            if command == 'pause':
                self.player.pause()
            elif command == 'resume':
                self.player.resume()
        else:
            res = self.backend.search_all(query=text)
            return SearchIntent(self.player, res)            
