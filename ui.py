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
        elif char == 27:
            self.text = ''
            return True, None
        else: # Normal key
            self.text += chr(char)
        return False, None

class MainIntent(Intent):

    def __init__(self):
        super().__init__()

    def render(self, stdscr, x, y, w, h):
        stdscr.addstr(y, x, "Working")

class Submenu(Intent):

    def __init__(self, choices):
        super().__init__()
        self.choices = choices
        self.index = 0
    
    def render(self, stdscr, x, y, w, h):
        i = 0
        for k, v in self.choices.items():
            padding = " " * int((w - len(v)) / 2)
            formatted = f'{padding}{v}{padding}'
            if len(formatted) >= w:
                formatted = formatted[:w-1]
            stdscr.addstr(y+i, x, formatted, curses.color_pair(2 if i == self.index else 1))
            i += 1

    def input(self, char):
        if char == 259:
            if self.index > 0:
                self.index -= 1
        elif char == 258:
            if self.index < len(self.choices) - 1:
                self.index += 1
        elif char == 10:
            return [*self.choices][self.index]
        elif char == 27:
            return 'exit'
        return None

class PlaylistSubmenu(Submenu):

    def __init__(self, instance, global_mode=False):
        self.global_mode = global_mode
        self.instance = instance
        self.choices = dict()
        self.index = 0
        index = 0
        for playlist in self.instance.playlist.playlists:
            self.choices[index] = playlist['name']
            index += 1
        self.choices['new'] = 'New playlist'

    def input(self, char):
        ret = super().input(char)
        
        if ret is not None:
            if ret == 'exit':
                return True, None if self.global_mode else None
            if ret == 'new':
                self.instance.console_override = True
                self.instance.console.text = '!playlist add '
                return True, None if self.global_mode else None
            else:
                if self.global_mode:
                    self.instance.player.play_playlist(self.instance.playlist.playlists[ret])
                    return True, None
                else:
                    return self.instance.playlist.playlists[ret]
        elif self.global_mode:
            if char == 118:
                return True, PlaylistIntent(self.instance, self.instance.playlist.playlists[[*self.choices][self.index]])
            return False, None
        return ret

class SearchIntent(Intent):

    def __init__(self, instance, results):
        super().__init__()
        self.instance = instance
        self.results = results
        self.index = 0
        self.shittyworkaround = None
        self.on_submenu = False
        self.submenu = None

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
        if self.on_submenu:
            self.submenu.render(stdscr, x+w-16, y+self.index, 16, 4)

    def input(self, char):

        if self.on_submenu:
            ret = self.submenu.input(char)
            if ret is not None:
                if ret == 'playlist':
                    self.submenu = PlaylistSubmenu(self.instance)
                    self.instance.refresh = True
                    return False, None
                elif ret == 'queue':
                    pass
                elif type(ret) is dict:
                    ret['songs'].append(self.shittyworkaround)
                    self.instance.playlist.save()
                self.submenu = None
                self.on_submenu = False 
                self.instance.refresh = True
            return False, None

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
        elif char == 109:
            self.submenu = Submenu({'playlist': 'Add to playlist', 'queue': 'Add to queue'})
            self.on_submenu = True
        elif char == 27:
            return True, None
        
        return False, None

class PlaylistIntent(Intent):

    def __init__(self, instance, playlist):
        super().__init__()
        self.instance = instance
        self.playlist = playlist
        self.on_submenu = False
        self.submenu = None
        self.index = 0

    def render(self, stdscr, x, y, w, h):
        i = 0
        for song in self.playlist['songs']:
            stdscr.addstr(y+i, x, f'{song["title"]}', curses.color_pair(1 if i == self.index else 0))
            i += 1
        if self.on_submenu:
            self.submenu.render(stdscr, x+w-16, y+self.index, 16, 4)

    def input(self, char):
        if self.on_submenu:
            ret = self.submenu.input(char)
            if ret is not None:
                if ret == 'delete':
                    self.playlist['songs'].pop(self.index)
                    self.index -= 1
                self.submenu = None
                self.on_submenu = False 
                self.instance.refresh = True
            return False, None
        if char == 259:
            if self.index > 0:
                self.index -= 1
        elif char == 258:
            if self.index < len(self.playlist['songs']) - 1:
                self.index += 1
        elif char == 109:
            self.submenu = Submenu({'delete': 'Delete'})
            self.on_submenu = True
        elif char == 10:
            return False, None
        elif char == 27:
            return True, None
        return False, None

class EditorIntent(Intent):

    def __init__(self, instance, object=None):
        super().__init__()
        self.instance = instance
        self.instance.override_global_keys = True
        if object is None:
            self.object = instance.settings.__dict__
        else:
            self.object = object
        self.index = 0
        self.editing = False
        self.editing_field = ''

    def render(self, stdscr, x, y, w, h):
        i = 0
        if type(self.object) is dict:
            for k, v in self.object.items():
                if self.index == i:
                    if self.editing:
                        stdscr.addstr(y+i, x, f'{k}: {self.editing_field}', curses.color_pair(1))
                    else:
                        self.item = (k, v)
                        stdscr.addstr(y+i, x, f'{k}: {v}', curses.color_pair(1))
                else:
                    stdscr.addstr(y+i, x, f'{k}: {v}')
                i += 1
        elif type(self.object) is list:
            for k in self.object:
                if self.index == i:
                    if self.editing:
                        stdscr.addstr(y+i, x, f'{self.editing_field}', curses.color_pair(1))
                    else:
                        self.item = k
                        stdscr.addstr(y+i, x, f'{k}', curses.color_pair(1))
                else:
                    stdscr.addstr(y+i, x, f'{k}')
                i += 1
    
    def input(self, char):
        key = self.item[0] if type(self.object) is dict else self.index
        self.instance.refresh = True # Ugly hack
        if self.editing:
            if char == 10:
                self.editing = False
                self.object[key] = self.editing_field
                self.instance.settings.save()
            else:
                t = type(self.editing_field)
                if t is bool:
                    self.editing_field = not self.editing_field
                if t is int:
                    if char == 259:
                        self.editing_field += 1
                    elif char == 258:
                        self.editing_field -= 1
                if t is str:
                    if char == 263: # delete
                        self.editing_field = self.editing_field[:-1]
                    elif char == 8: # Ctrl+delete
                        self.editing_field = ""
                    else: # Normal key
                        self.editing_field += chr(char)
            return False, None
        if char == 259:
            if self.index > 0:
                self.index -= 1
        elif char == 258:
            if self.index < len(self.object) - 1:
                self.index += 1
        elif char == 10:
            item = self.item[1] if type(self.object) is dict else self.object[self.index]
            if type(item) is dict or type(item) is list:
                return False, EditorIntent(self.instance, item)                
            self.editing = True
            self.editing_field = item
        elif char == 27:
            self.instance.override_global_keys = False
            return True, None
        return False, None
