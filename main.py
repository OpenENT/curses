from ui import PlayingStatusIntent, TitleBarIntent, ConsoleIntent, MainIntent
from clients import PlayerD, Backend
from console import Console
from curses import wrapper

import settings
import curses
import time

class Instance:
    
    def __init__(self, backend, player, settings):
        self.player = player
        self.settings = settings
        self.set_backend(backend)

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

instance = Instance(Backend("http://127.0.0.1:5001"), PlayerD("http://127.0.0.1:5000"), settings.Settings('settings.json'))

playingstatus = PlayingStatusIntent(instance)
titlebar = TitleBarIntent()
console = ConsoleIntent(Console(instance))

console_override = False
intents = [MainIntent()]

old_w = 0
old_h = 0
refresh = False



def handle_input(stdscr):

    global console_override, refresh
    char = stdscr.getch()

    if char == -1:
        return
    elif char == 62:
        console_override = not console_override
    elif console_override:
        ret, intent = console.input(char)
        if ret:
            console_override = False
        if intent is not None:
            refresh = True
            intents.append(intent)
    else:
        playingstatus.input(char)
        ret, intent = intents[-1].input(char)

def render(stdscr):

    global old_h, old_w, refresh
    h, w = stdscr.getmaxyx()

    if old_h != h or old_w != w or refresh:
        stdscr.clear()
        old_h = h
        old_w = w
        refresh = False
    
    titlebar.render(stdscr, 0, 0, w, 1)
    playingstatus.render(stdscr, 0, h-1, w, 1)
    if console_override:
        console.render(stdscr, 0, h-1, w, 1)
    intents[-1].render(stdscr, 0, 1, w, h-2)
    handle_input(stdscr)
    stdscr.refresh()

    return True

def main(stdscr):
    stdscr.clear()
    stdscr.nodelay(1)
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    while render(stdscr):
        time.sleep(1000 / 60 / 1000)

wrapper(main)