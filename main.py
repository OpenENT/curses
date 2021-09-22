from ui import PlayingStatusIntent, PlaylistSubmenu, TitleBarIntent, ConsoleIntent, DocsIntent, MainIntent
from playlist import PlaylistManager
from clients import PlayerD, Backend
from console import Console
from curses import wrapper
from cache import Cache
import settings
import curses
import time
import os

class Player:
    
    def __init__(self):
        self.settings = settings.Settings('settings.json')
        self.playlist = PlaylistManager('playlists')
        self.player = PlayerD(self, self.settings.playerd)
        self.cache = Cache('cache.json', self.settings)
        self.set_backend(Backend(self.settings.backend))
        self.init_gui()

    def init_gui(self):
        self.playingstatus = PlayingStatusIntent(self)
        self.titlebar = TitleBarIntent(self)
        self.console = ConsoleIntent(Console(self))
        self.console_override = False
        self.menu = None
        self.menu_override = False
        self.override_global_keys = False
        self.intents = [MainIntent(self)]
        self.old_w = 0
        self.old_h = 0
        self.refresh = False
        self.reload = False

    def set_backend(self, backend):
        self.backend = backend
        try:
            backend.connect()
        except Exception:
            return False
        for provider in self.backend.providers:
            if provider not in self.settings.providers:
                self.settings.providers[provider] = settings.ProviderSettings(provider)
        if len(self.settings.global_search) == 0:
            self.settings.global_search = self.backend.providers.copy()
        self.settings.save()
        return True

    def handle_input(self, stdscr):

        char = stdscr.getch()

        if char == -1:
            return
        elif char == 62:
            self.console_override = not self.console_override
        elif self.console_override:
            ret, intent = self.console.input(char)
            if ret:
                self.console_override = False
            if intent is not None:
                self.refresh = True
                if type(intent) is str:
                    self.playingstatus.status_text = intent
                    self.playingstatus.override = True
                else:
                    self.intents.append(intent)
        elif self.menu_override:
            ret, intent = self.menu.input(char)
            if ret:
                self.menu_override = False
                self.refresh = True
            if intent is not None:
                self.refresh = True
                if type(intent) is str:
                    self.playingstatus.status_text = intent
                    self.playingstatus.override = True
                else:
                    self.intents.append(intent)
        else:
            ret, intent = self.intents[-1].input(char)
            if ret:
                self.refresh = True
                self.intents.pop(-1)
            if intent is not None:
                self.refresh = True
                if type(intent) is str:
                    self.playingstatus.status_text = intent
                    self.playingstatus.override = True
                else:
                    self.intents.append(intent)
            elif not ret and not self.override_global_keys:
                self.playingstatus.input(char)
                if char == 112:
                    self.menu_override = True
                    self.menu = PlaylistSubmenu(self, True)
                elif char == 104:
                    self.intents.append(DocsIntent('docs'))
                    self.refresh = True

    def render(self, stdscr):

        h, w = stdscr.getmaxyx()

        if self.old_h != h or self.old_w != w or self.refresh:
            stdscr.clear()
            self.old_h = h
            self.old_w = w
            self.refresh = False
        offset_y = 0
        if self.settings.titlebar:
            self.titlebar.render(stdscr, 0, 0, w, 1)
            offset_y += 1
        self.playingstatus.render(stdscr, 0, h-1, w, 1)
        self.intents[-1].render(stdscr, 0, offset_y, w, h-2)
        if self.console_override:
            self.console.render(stdscr, 0, h-1, w, 1)
        if self.menu_override:
            self.menu.render(stdscr, int(w/3), int(h/2), int(w/3), 1)
        self.handle_input(stdscr)
        stdscr.refresh()

        return not self.reload

    def loop(self, stdscr):
        stdscr.clear()
        stdscr.nodelay(1)
        curses.curs_set(0)
        curses.init_pair(1, self.settings.foreground, self.settings.background)
        curses.init_pair(2, self.settings.foreground_alt, self.settings.background_alt)
        while self.render(stdscr):
            time.sleep(1000 / self.settings.refresh_rate / 1000)
        self.init_gui()
        self.loop(stdscr)

os.environ.setdefault('ESCDELAY', '0') # Fixes terrible ESC delay in menus
wrapper(Player().loop)