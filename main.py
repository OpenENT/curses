from ui import PlayingStatusIntent, TitleBarIntent, ConsoleIntent, MainIntent
from clients import PlayerD, Backend
from console import Console
from curses import wrapper

import settings
import curses
import time

class Player:
    
    def __init__(self):
        self.settings = settings.Settings('settings.json')
        self.player = PlayerD(self.settings.playerd)
        self.set_backend(Backend(self.settings.backend))

        self.playingstatus = PlayingStatusIntent(self)
        self.titlebar = TitleBarIntent()
        self.console = ConsoleIntent(Console(self))
        self.console_override = False
        self.intents = [MainIntent()] # Questionable, rly needed?

        self.old_w = 0
        self.old_h = 0
        self.refresh = False

    def set_backend(self, backend):
        self.backend = backend
        try:
            backend.connect()
        except Exception:
            return False
        for provider in self.backend.providers:
            if provider not in self.settings.providers:
                self.settings.providers[provider] = settings.ProviderSettings(provider)
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
        else:
            self.playingstatus.input(char)
            ret, intent = self.intents[-1].input(char)
            # ???

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
        if self.console_override:
            self.console.render(stdscr, 0, h-1, w, 1)
        self.intents[-1].render(stdscr, 0, offset_y, w, h-2)
        self.handle_input(stdscr)
        stdscr.refresh()

        return True

    def loop(self, stdscr):
        stdscr.clear()
        stdscr.nodelay(1)
        curses.curs_set(0)
        curses.init_pair(1, self.settings.foreground, self.settings.background)
        while self.render(stdscr):
            time.sleep(1000 / self.settings.refresh_rate / 1000)

wrapper(Player().loop)