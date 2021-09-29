import unicodedata
import curses
import glob
import time

def clear_line(stdscr, x, y, w, color_pair=0):
    stdscr.addstr(y, x, " "*(w), curses.color_pair(color_pair))

def str_len(str):  # I hate curses
    l = 0
    for c in str:
        l += 2 if unicodedata.east_asian_width(c) == "W" else 1
    return l

def cut_text(old_index, string, w):
    strlen = str_len(string)
    if strlen < w:
        return 0, string
    ob = strlen -w
    if old_index >= ob:
        return -old_index, string[abs(old_index):w-abs(old_index)]
    return old_index + 1, string[abs(old_index):w-abs(old_index+1)]

def trim(string, w):
    l = 0
    l2 = 0
    for c in string:
        l += 2 if unicodedata.east_asian_width(c) == "W" else 1
        l2 += 1
        if l > w:
            return string[:l2-1]
        elif l == w:
            return string[:l2]
    return string


class Intent:

    def __init__(self):
        pass

    def render(self, stdscr, x, y, w, h):
        pass

    def input(self, char): # {exit: bool, intent: intent}
        return False, None

class TitleBarIntent(Intent):

    def __init__(self, instance):
        super().__init__()
        self.instance = instance
        
    def render(self, stdscr, x, y, w, h):
        strlen = len(self.instance.settings.titlebar_title)
        padding = " " * int((w - strlen) / 2)
        stdscr.addstr(y, x, f"{padding}{self.instance.settings.titlebar_title}{padding}", curses.color_pair(1))

class PlayingStatusIntent(Intent):

    def __init__(self, instance):
        super().__init__()
        self.instance = instance
        self.time = time.time()
        self.override = False
        self.status_text = ''
        self.anim = 0
        try:
            self.status = self.instance.player.get_status()
        except:
            self.status = None

    def render(self, stdscr, x, y, w, h):

        try: # Workaround for python's curses bug, where you can't write to the last cell without raising an Exception 
            clear_line(stdscr, x, y, w, 1)
        except:
            pass
        if self.override: # Display status_text instead
            stdscr.addstr(y, x, self.status_text, curses.color_pair(1))
            if time.time() - self.time > 2:
                self.time = time.time()
                self.override = False
            return
        
        update = False

        if time.time() - self.time > 1:
            update = True
            self.time = time.time()
            try:
                self.status = self.instance.player.get_status()
            except:
                self.status = None

        if self.status is None:
            stdscr.addstr(y, x, "Can't connect to PlayerD", curses.color_pair(1))
        elif self.status['playing']:
            current = time.strftime('%M:%S', time.gmtime(int(self.status['position'])))
            duration = time.strftime('%M:%S', time.gmtime(int(self.status['duration'])))
            string = f"{current} / {duration} - {self.status['name']} {w}"
            string += f" {str_len(string)}"
            i, s = cut_text(self.anim, string, w)
            try:
                stdscr.addstr(y, 0, s, curses.color_pair(1))
            except:
                pass
            if update:
                self.anim = i
        else:
            stdscr.addstr(y, x, "Not playing", curses.color_pair(1))
    
    def input(self, char):
        if self.status is None:
            return
        if char == self.instance.settings.key_pause:
            if self.status is not None and self.status['playing']:
                if self.status['paused']:
                    self.instance.player.resume()
                else:
                    self.instance.player.pause()
        elif not self.status['playing']:
            return
        elif char == self.instance.settings.key_volume_up:
            self.instance.player.set_volume(self.status['volume'] + self.instance.settings.volume_steps)
            self.status['volume'] += self.instance.settings.volume_steps
        elif char == self.instance.settings.key_volume_down:
            self.instance.player.set_volume(self.status['volume'] - self.instance.settings.volume_steps)
            self.status['volume'] -= self.instance.settings.volume_steps
        elif char == self.instance.settings.key_close:
            self.instance.player.close()

class ConsoleIntent(Intent):

    def __init__(self, instance, engine):
        super().__init__()
        self.instance = instance
        self.engine = engine
        self.text = str()

    def render(self, stdscr, x, y, w, h):
        render_text = self.text
        if len(self.text) == 0:
            render_text = "..."
        stdscr.addstr(y, x, " " * (x+w - 1), curses.color_pair(1))
        stdscr.addstr(y, x, ">" + render_text, curses.color_pair(1))
    
    def input(self, char):
        if char == 263: # delete
            if len(self.text) == 0:
                return False, None
            self.text = self.text[:-1]
        elif char == 8: # Ctrl+delete
            self.text = ""
        elif char == self.instance.settings.key_ok:
            intent = self.engine.execute(self.text)
            self.text = ""
            return True, intent
        elif char == self.instance.settings.key_exit:
            self.text = ''
            return True, None
        else: # Normal key
            self.text += chr(char)
        return False, None

class MainIntent(Intent):

    def __init__(self, instance):
        super().__init__()
        self.instance = instance
        self.index = [0, 0, 0, 0] # [Playlist index, Song history index, Search history index, Current index]

    def render(self, stdscr, x, y, w, h):
        offset_x = 0
        offset_y = 1
        stdscr.addstr(y, x, "Playlists")
        i = 0
        
        for playlist in self.instance.playlist.playlists:
            if offset_x + len(playlist['name']) > w:
                offset_x = 0
                offset_y += 1
            stdscr.addstr(y+offset_y, x+offset_x, playlist['name'], curses.color_pair(1 if self.index[3] == 0 else 2) if self.index[0] == i else curses.color_pair(0))
            offset_x += len(playlist['name']) + 1
            i += 1

        if i == 0:
            stdscr.addstr(y+offset_y, x+offset_x, "Nothing here", curses.color_pair(1 if self.index[3] == 0 else 2) if self.index[0] == i else curses.color_pair(0))
        
        offset_y += 1
        stdscr.addstr(y+offset_y, x, "Last played")
        offset_y += 1
        offset_x = 0
        i = 0
        
        for i in range(0, min(25, len(self.instance.settings.song_history['songs']))):
            song = self.instance.settings.song_history['songs'][i]
            if offset_x + len(song['title']) > w:
                offset_x = 0
                offset_y += 1
            stdscr.addstr(y+offset_y, x+offset_x, song['title'], curses.color_pair(1 if self.index[3] == 1 else 2) if self.index[1] == i else curses.color_pair(0))
            offset_x += len(song['title']) + 1
        
        if offset_x == 0:
            stdscr.addstr(y+offset_y, x+offset_x, "Nothing here", curses.color_pair(1 if self.index[3] == 1 else 2) if self.index[1] == i else curses.color_pair(0))
        offset_y += 1

        stdscr.addstr(y+offset_y, x, "Search history")
        offset_y += 1
        offset_x = 0
        i = 0
        
        for i in range(0, min(25, len(self.instance.settings.history))):
            query = self.instance.settings.history[i]
            if offset_x + len(query) > w:
                offset_x = 0
                offset_y += 1
            stdscr.addstr(y+offset_y, x+offset_x, query, curses.color_pair(1 if self.index[3] == 2 else 2) if self.index[2] == i else curses.color_pair(0))
            offset_x += len(query) + 1
            offset_y += 0
        
        if offset_x == 0:
            stdscr.addstr(y+offset_y, x+offset_x, "Nothing here", curses.color_pair(1 if self.index[3] == 2 else 2) if self.index[2] == i else curses.color_pair(0))
            offset_y += 1

        keybinds = {'>': 'Console', 'P': 'Playlists', 'V': 'View playlist', 'H': 'Help', 'Ret': 'Return'}
        offset_x = 0
        for keybind, description in keybinds.items():
            stdscr.addstr(y+h-2, x+offset_x, keybind, curses.color_pair(1))
            stdscr.addstr(y+h-2, x+offset_x+len(keybind) + 1, description)
            offset_x += len(keybind) + len(description) + 2
            
    def input(self, char):
        if char == self.instance.settings.key_up:
            self.index[3] -= 1
            if self.index[3] < 0:
                self.index[3] = 0
        elif char == self.instance.settings.key_down:
            self.index[3] += 1
            if self.index[3] > 1:
                self.index[3] = 2
        elif char == self.instance.settings.key_right:
            if self.index[3] == 0:
                self.index[0] += 1
                if self.index[0] >= len(self.instance.playlist.playlists):
                    self.index[0] = max(0, len(self.instance.playlist.playlists) - 1)
            elif self.index[3] == 1:
                self.index[1] += 1
                if self.index[1] >= len(self.instance.settings.song_history['songs']):
                    self.index[1] = max(0, len(self.instance.settings.song_history['songs']) - 1)
            elif self.index[3] == 2:
                self.index[2] += 1
                if self.index[2] >= len(self.instance.settings.history):
                    self.index[2] = max(0, len(self.instance.settings.history) - 1)

        elif char == self.instance.settings.key_left:
            self.index[self.index[3]] -= 1
            if self.index[self.index[3]] < 0:
                self.index[self.index[3]] = 0
        elif char == 118 and self.index[3] == 0:
            if len(self.instance.playlist.playlists) == 0:
                return False, None
            return False, PlaylistIntent(self.instance, self.instance.playlist.playlists[self.index[0]])
        elif char == self.instance.settings.key_ok:
            if self.index[3] == 0:
                if len(self.instance.playlist.playlists) == 0:
                    return False, None
                self.instance.player.play_playlist(self.instance.playlist.playlists[self.index[0]])
            elif self.index[3] == 1:
                if len(self.instance.settings.song_history['songs']) == 0:
                    return False, None
                self.instance.player.play(self.instance.player.check_download(self.instance.settings.song_history['songs'][self.index[1]]))
            elif self.index[3] == 2:
                if len(self.instance.settings.history) == 0:
                    return False, None
                text = self.instance.settings.history[self.index[2]]
                if self.instance.cache.get_cache('search', text) is not None:
                    res = self.instance.cache.get_cache('search', text)['res']
                else:
                    res = self.instance.backend.search_all(query=text, providers=self.instance.settings.global_search)
                    if self.instance.settings.collect_cache:
                        self.instance.cache.put_cache('search', text, {'res': res})
                return False, SearchIntent(self.instance, res)
            return False, None
        elif char == self.instance.settings.key_exit:
            return False, None
        return False, None


class Submenu(Intent):

    def __init__(self, instance, choices):
        super().__init__()
        self.instance = instance
        self.choices = choices
        self.index = 0
    
    def render(self, stdscr, x, y, w, h):
        i = 0
        for k, v in self.choices.items():
            padding = " " * int((w - str_len(v)) / 2)
            formatted = f'{padding}{v}{padding}'
            if str_len(formatted) >= w:
                formatted = formatted[:w-1]
            stdscr.addstr(y+i, x, trim(formatted, w), curses.color_pair(2 if i == self.index else 1))
            i += 1

    def input(self, char):
        if char == self.instance.settings.key_up:
            if self.index > 0:
                self.index -= 1
        elif char == self.instance.settings.key_down:
            if self.index < len(self.choices) - 1:
                self.index += 1
        elif char == self.instance.settings.key_ok:
            return [*self.choices][self.index]
        elif char == self.instance.settings.key_exit:
            return 'exit'
        return None

class PlaylistSubmenu(Submenu):

    def __init__(self, instance, global_mode=False):
        self.global_mode = global_mode
        self.instance = instance
        self.choices = dict()
        self.index = 0
        index = 0
        if global_mode:
            self.choices[index] = 'History'
            index += 1
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
                    if self.index == 0:
                        self.instance.player.play_playlist(self.instance.settings.song_history)
                    else:
                        self.instance.player.play_playlist(self.instance.playlist.playlists[ret-1])
                    return True, None
                else:
                    return self.instance.playlist.playlists[ret]
        elif self.global_mode:
            if char == 118 and self.index < len(self.choices) - 1:
                if self.index == 0:
                    return True, PlaylistIntent(self.instance, self.instance.settings.song_history)
                else:
                    return True, PlaylistIntent(self.instance, self.instance.playlist.playlists[[*self.choices][self.index-1]])
            return False, None
        return ret

class QueueSubmenu(Submenu):

    def __init__(self, instance):
        self.instance = instance
        self.choices = dict()
        self.index = 0
        index = 0
        for song in self.instance.player.current_playlist['songs']:
            self.choices[index] = song['title']
            index += 1
        #self.choices['new'] = 'New playlist'

    def input(self, char):
        ret = super().input(char)
        if ret is not None:
            if ret == 'exit':
                return True, None
            if ret == 'new':
                return True, None
            else:
                self.instance.player.playlist_go(index=ret)
                return True, None
        return False, None

class ListItem:

    def __init__(self, object, text='Item', description='No description'):
        self.object = object
        self.text = text
        self.description = description

class ListIntent(Intent):

    def __init__(self, instance, items):
        super().__init__()
        self.instance = instance
        self.items = items
        self.index = 0

    def render(self, stdscr, x, y, w, h):
        i = 0
        offset = max(0, self.index - h + 2)
        if len(self.items) == 0:
            stdscr.addstr(y+i, x, 'Nothing here.', curses.color_pair(1 if i + offset == self.index else 0))
            return
        for k in range(offset, len(self.items)):
            item = self.items[k]
            clear_line(stdscr, x, y+i, w)
            stdscr.addstr(y+i, x, item.text[:w], curses.color_pair(1 if i + offset == self.index else 0))
            i += 1
            if i == y+h-1:
                break
        clear_line(stdscr, x, y+h-1, w)
        stdscr.addstr(y+h-1, x, self.items[self.index].description[:w-6])

    def input(self, char):
        if char == self.instance.settings.key_up:
            if self.index > 0:
                self.index -= 1
        elif char == self.instance.settings.key_down:
            if self.index < len(self.items) - 1:
                self.index += 1
        elif char == self.instance.settings.key_ok:
            if len(self.items) == 0:
                return None
            return self.items[self.index]
        elif char == self.instance.settings.key_exit:
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
                self.items.append(ListItem(res, res['title'], f'Provider: {res["provider"]} Artist: {res["album"]["artist"]["name"] if "album" in res else "Unknown"}'))

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
        if char == self.instance.settings.key_exit:
            return True, None
        elif len(self.items) == 0:
            return False, None
        elif char == self.instance.settings.key_ok:
            self.instance.player.play_song(self.items[self.index].object)
        elif char == 109:
            self.submenu = Submenu(self.instance, choices={'playlist': 'Add to playlist', 'queue': 'Add to queue'})
            if self.instance.settings.debug_mode:
                self.submenu.choices['debug'] = 'Edit JSON'
            self.on_submenu = True
        
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
            self.items.append(ListItem(song, song['title'], f'Provider: {song["provider"]}  Artist: {song["album"]["artist"]["name"] if "album" in song else "Unknown"}'))

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
            self.instance.player.play_song(self.items[self.index].object)
            return False, None
        elif char == 109:
            self.submenu = Submenu(self.instance, {'delete': 'Delete'})
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
            if char == self.instance.settings.key_ok:
                self.editing = False
                self.object[key] = self.editing_field
                self.instance.settings.save()
            else:
                t = type(self.editing_field)
                if t is bool:
                    self.editing_field = not self.editing_field
                if t is int:
                    if char == self.instance.settings.key_up:
                        self.editing_field += 1
                    elif char == self.instance.settings.key_down:
                        self.editing_field -= 1
                if t is str:
                    if char == 263: # delete
                        self.editing_field = self.editing_field[:-1]
                    elif char == 8: # Ctrl+delete
                        self.editing_field = ""
                    else: # Normal key
                        self.editing_field += chr(char)
            return False, None
        if char == self.instance.settings.key_up:
            if self.index > 0:
                self.index -= 1
        elif char == self.instance.settings.key_down:
            if self.index < len(self.object) - 1:
                self.index += 1
        elif char == self.instance.settings.key_ok:
            item = self.item[1] if type(self.object) is dict else self.object[self.index]
            if type(item) is dict or type(item) is list:
                return False, EditorIntent(self.instance, item)                
            self.editing = True
            self.editing_field = item
        elif char == self.instance.settings.key_exit:
            self.instance.override_global_keys = False
            return True, None
        return False, None

class DocsIntent(Intent):
    
    def __init__(self, instance, path: str):
        super().__init__()
        self.instance = instance
        self.pages = list()
        for file in glob.glob(f"{path}/*.txt"):
            with open(file) as f:
                self.pages.append(f.read())
        self.index = 0
    
    def render(self, stdscr, x, y, w, h):
        stdscr.addstr(y, x, self.pages[self.index])

    def input(self, char):
        if char == self.instance.settings.key_up:
            if self.index > 0:
                self.index -= 1
        elif char == self.instance.settings.key_down:
            if self.index < len(self.pages) - 1:
                self.index += 1
        elif char == self.instance.settings.key_exit:
            return True, None
        return False, None

class ExceptionIntent(Intent):
    
    def __init__(self, instance, exception, traceback='No traceback'):
        super().__init__()
        self.instance = instance
        self.exception = exception
        self.traceback = traceback
    
    def render(self, stdscr, x, y, w, h):
        stdscr.addstr(y, x, 'An error occurred. Press Enter to raise Exception for debugging.')
        stdscr.addstr(y+1, x, repr(self.exception))
        stdscr.addstr(y+2, x, repr(self.traceback))

    def input(self, char):
        if char == self.instance.settings.key_ok:
            raise self.exception
        elif char == self.instance.settings.key_exit:
            return True, None
        return False, None
