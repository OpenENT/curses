
class Intent:

    def __init__(self):
        pass

    def render(self, stdscr, x, y, w, h):
        pass

    def input(self, char): # maybe {exit: bool, intent: intent}
        return False


class MainIntent(Intent):

    def __init__(self):
        super().__init__()

    def render(self, stdscr, x, y, w, h):
        stdscr.addstr(y, x, "I need professional help")


class SearchIntent(Intent):

    def __init__(self, results):
        super().__init__()
        self.results = results
        self.index = 0

    def render(self, stdscr, x, y, w, h):
        ry = 0
        for res in self.results:
            ry += 1
            stdscr.addstr(y+ry, x, "a")

    def input(self, char):
        pass
