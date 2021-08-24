
class Console():

    def __init__(self, player, backend):
        self.player = player
        self.backend = backend

    def execute(self, text):
        if text.startswith("!"):
            pass  # bang
        else:
            pass # normal search
