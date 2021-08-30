import curses
import time

class Intent:

    def __init__(self):
        pass

    def render(self, stdscr, x, y, w, h):
        pass

    def input(self, char): # {exit: bool, intent: intent}
        return False, None


class TitleBarIntent(Intent):

    def __init__(self, title="OpenPlayer", color_pair=1):
        super().__init__()
        self.title = title
        self.color_pair = color_pair
        
    def render(self, stdscr, x, y, w, h):
        strlen = len(self.title)
        padding = " " * int((w - strlen) / 2)
        stdscr.addstr(y, x, f"{padding}{self.title}{padding}", curses.color_pair(self.color_pair))


class PlayingStatusIntent(Intent): # TODO: Text transition when text len > width

    def __init__(self, player, color_pair=1):
        super().__init__()
        self.player = player
        self.color_pair = color_pair
        
    def render(self, stdscr, x, y, w, h):
        status = self.player.get_status()
        stdscr.addstr(y, x, " "*(w-1), curses.color_pair(self.color_pair)) # Clear line
        if status['playing']:
            current = time.strftime('%M:%S', time.gmtime(int(status['position'])))
            duration = time.strftime('%M:%S', time.gmtime(int(status['duration'])))
            stdscr.addstr(y, x, f"{current} / {duration} - {status['name']}", curses.color_pair(self.color_pair))
        else:
            stdscr.addstr(y, x, "Not playing", curses.color_pair(self.color_pair))


class ConsoleIntent(Intent):

    def __init__(self, engine, color_pair=1):
        super().__init__()
        self.color_pair = color_pair
        self.engine = engine
        self.text = str()

    def render(self, stdscr, x, y, w, h):
        render_text = self.text
        if len(self.text) == 0:
            render_text = "..."
        stdscr.addstr(y, x, " " * (x+w - 1), curses.color_pair(self.color_pair))
        stdscr.addstr(y, x, ">" + render_text, curses.color_pair(self.color_pair))
    
    def input(self, char):
        if char == 127: # delete
            if len(self.text) == 0:
                return False, None
            self.text = self.text[:-1]
        elif char == 263: # Ctrl+delete
            self.text = ""
        elif char == 10: # Return
            intent = self.engine.execute(self.text)
            self.text = ""
            return True, intent
        else: # Normal key
            self.text += chr(char)
        return False, None

class MainIntent(Intent):

    def __init__(self):
        super().__init__()

    def render(self, stdscr, x, y, w, h):
        stdscr.addstr(y, x, "Working")


class SearchIntent(Intent):

    def __init__(self, player, results):
        super().__init__()
        self.player = player
        self.results = results
        self.index = 0
        self.shittyworkaround = None
        

    def render(self, stdscr, x, y, w, h):
        ry = 0
        for res in self.results:
            if res['type'] == "song":
                if self.index == ry:
                    self.shittyworkaround = res
                    stdscr.addstr(y+ry, x, f'{res["title"]}', curses.color_pair(1))
                else:
                    stdscr.addstr(y+ry, x, f'{res["title"]}')
                ry += 1
            if ry == h:
                break

    def input(self, char):
        if char == 259:
            self.index -= 1
        elif char == 258:
            self.index += 1
        elif char == 10:
            self.player.play(url=self.shittyworkaround['stream_url'])
            
        return False, None