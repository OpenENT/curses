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

    def __init__(self, title, color_pair=1):
        super().__init__()
        self.title = title
        self.color_pair = color_pair
        
    def render(self, stdscr, x, y, w, h):
        strlen = len(self.title)
        padding = " " * int((w - strlen) / 2)
        stdscr.addstr(y, x, f"{padding}{self.title}{padding}", curses.color_pair(self.color_pair))

class PlayingStatusIntent(Intent): # TODO: Text transition when text len > width

    def __init__(self, instance, color_pair=1):
        super().__init__()
        self.instance = instance
        self.color_pair = color_pair
        self.time = time.time()
        self.override = False
        self.status_text = ''
        try:
            self.status = self.instance.player.get_status()
        except:
            self.status = None

    def render(self, stdscr, x, y, w, h):

        try: # bruh
            stdscr.addstr(y, x, " "*(w), curses.color_pair(self.color_pair)) # Clear line
        except:
            pass
        
        if self.override:

            stdscr.addstr(y, x, self.status_text, curses.color_pair(self.color_pair))
            if time.time() - self.time > 2:
                self.time = time.time()
                self.override = False
            return
        
        if time.time() - self.time > 1:
            self.time = time.time()
            try:
                self.status = self.instance.player.get_status()
            except:
                self.status = None

        if self.status is None:
            stdscr.addstr(y, x, "Can't connect to PlayerD", curses.color_pair(self.color_pair))
        elif self.status['playing']:
            current = time.strftime('%M:%S', time.gmtime(int(self.status['position'])))
            duration = time.strftime('%M:%S', time.gmtime(int(self.status['duration'])))
            stdscr.addstr(y, x, f"{current} / {duration} - {self.status['name']}", curses.color_pair(self.color_pair))
        else:
            stdscr.addstr(y, x, "Not playing", curses.color_pair(self.color_pair))
    
    def input(self, char):
        if char == 32:
            if self.status is not None and self.status['playing']:
                if self.status['paused']:
                    self.instance.player.resume()
                else:
                    self.instance.player.pause()

        elif char == 337: # shift + up
            self.instance.player.set_volume(self.status['volume'] + 10)
        elif char == 336: # shift + down
            self.instance.player.set_volume(self.status['volume'] - 10)
        elif char == 4: # ctrl+d
            self.instance.player.close()

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
        if char == 263: # delete
            if len(self.text) == 0:
                return False, None
            self.text = self.text[:-1]
        elif char == 8: # Ctrl+delete
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

    def __init__(self, instance, results):
        super().__init__()
        self.instance = instance
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
            if self.instance.settings.providers[self.shittyworkaround['provider']]['prefer_download']:
                res = self.instance.backend.download(self.shittyworkaround)
                if 'stream_url' in res:
                    self.instance.player.play(url=res['stream_url'])
                else:
                    self.instance.player.play(url=self.shittyworkaround['stream_url'])
            else:
                self.instance.player.play(url=self.shittyworkaround['stream_url'])
            
        return False, None

