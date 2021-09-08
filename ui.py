import curses
import glob
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
        elif not self.status['playing']:
            return
        elif char == 337: # shift + up
            self.instance.player.set_volume(self.status['volume'] + self.instance.settings.volume_steps)
            self.status['volume'] += self.instance.settings.volume_steps
        elif char == 336: # shift + down
            self.instance.player.set_volume(self.status['volume'] - self.instance.settings.volume_steps)
            self.status['volume'] -= self.instance.settings.volume_steps
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

class ListItem:

    def __init__(self, object, text='Item', description='No description'):
        self.object = object
        self.text = text
        self.description = description

class ListIntent(Intent):

    def __init__(self, items):
        super().__init__()
        self.items = items
        self.index = 0

    def render(self, stdscr, x, y, w, h):
        i = 0
        offset = max(0, self.index - h + 2)
        for k in range(offset, len(self.items)):
            item = self.items[k]
            stdscr.addstr(y+i, x, " "*(w))
            stdscr.addstr(y+i, x, item.text[:w], curses.color_pair(1 if i + offset == self.index else 0))
            i += 1
            if i == y+h-1:
                break
        stdscr.addstr(y+h-1, x, " "*(w))
        stdscr.addstr(y+h-1, x, self.items[self.index].description[:w])

    def input(self, char):
        if char == 259:
            if self.index > 0:
                self.index -= 1
        elif char == 258:
            if self.index < len(self.items) - 1:
                self.index += 1
        elif char == 10:
            return self.items[self.index]
        elif char == 27:
            return 'exit'
        return None

class SearchIntent(ListIntent):

    def __init__(self, instance, results):
        self.instance = instance
        self.results = results
        self.on_submenu = False
        self.submenu = None
        self.items = list()
        self.index = 0
        for res in self.results:
            if res['type'] == "song":
                self.items.append(ListItem(res, res['title'], f'Provider: {res["provider"]}'))

    def render(self, stdscr, x, y, w, h):
        super().render(stdscr, x, y, w, h)
        if self.on_submenu:
            self.submenu.render(stdscr, int(x+w/2-8), int(y+h/2-2), 16, 4)

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
                elif ret == 'debug':
                    return False, EditorIntent(self.instance, self.items[self.index].object)
                elif type(ret) is dict:
                    ret['songs'].append(self.items[self.index].object)
                    self.instance.playlist.save()
                self.submenu = None
                self.on_submenu = False 
                self.instance.refresh = True
            return False, None
        ret = super().input(char)
        if char == 10:
            self.instance.player.play(url=self.instance.player.check_download(self.items[self.index].object))
        elif char == 109:
            self.submenu = Submenu({'playlist': 'Add to playlist', 'queue': 'Add to queue'})
            if self.instance.settings.debug_mode:
                self.submenu.choices['debug'] = 'Edit JSON'
            self.on_submenu = True
        elif char == 27:
            return True, None
        
        return False, None

class PlaylistIntent(ListIntent):

    def __init__(self, instance, playlist):
        self.instance = instance
        self.playlist = playlist
        self.on_submenu = False
        self.submenu = None
        self.index = 0
        self.items = list()
        for song in playlist['songs']:
            self.items.append(ListItem(song, song['title'], f'Provider: {song["provider"]}'))

    def render(self, stdscr, x, y, w, h):
        super().render(stdscr, x, y, w, h)
        if self.on_submenu:
            self.submenu.render(stdscr, int(x+w/2-8), int(y+h/2-1), 16, 4)

    def input(self, char):
        if self.on_submenu:
            ret = self.submenu.input(char)
            if ret is not None:
                if ret == 'debug':
                    return False, EditorIntent(self.instance, self.playlist['songs'][self.index])
                if ret == 'delete':
                    self.playlist['songs'].remove(self.items[self.index].object)
                    self.items.pop(self.index)
                    self.index -= 1
                    self.instance.playlist.save()
                self.submenu = None
                self.on_submenu = False 
                self.instance.refresh = True
            return False, None
        ret = super().input(char)
        if ret is not None:
            if ret == 'exit':
                return True, None
            playlist = self.playlist['songs'][ret]
            return True, None
        elif char == 109:
            self.submenu = Submenu({'delete': 'Delete'})
            if self.instance.settings.debug_mode:
                self.submenu.choices['debug'] = 'Edit JSON'
            self.on_submenu = True
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
        self.instance.override_global_keys = True
        i = 0
        if type(self.object) is dict:
            for k, v in self.object.items():
                if self.index == i:
                    if self.editing:
                        stdscr.addstr(y+i, x, f'{k}: {self.editing_field}'[:w], curses.color_pair(1))
                    else:
                        self.item = (k, v)
                        stdscr.addstr(y+i, x, f'{k}: {v}'[:w], curses.color_pair(1))
                else:
                    stdscr.addstr(y+i, x, f'{k}: {v}'[:w])
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

class DocsIntent(Intent):
    
    def __init__(self, path: str):
        super().__init__()
        self.pages = list()
        for file in glob.glob(f"{path}/*.txt"):
            with open(file) as f:
                self.pages.append(f.read())
        self.index = 0
    
    def render(self, stdscr, x, y, w, h):
        stdscr.addstr(y, x, self.pages[self.index])

    def input(self, char):
        if char == 259:
            if self.index > 0:
                self.index -= 1
        elif char == 258:
            if self.index < len(self.pages) - 1:
                self.index += 1
        elif char == 27:
            return True, None
        return False, None