from ui import SearchIntent

class Console():

    def __init__(self, player, backend):
        self.player = player
        self.backend = backend

    def execute(self, text):
        if text.startswith("!"):
            pass  # bang
        else:
            res = self.backend.search_all(query=text)
            return SearchIntent(self.player, res)            
