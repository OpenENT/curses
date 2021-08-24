from ui import PlayingStatusIntent, TitleBarIntent, ConsoleIntent, MainIntent
from clients import PlayerD, Backend
from console import Console
from curses import wrapper

import curses
import time


c = PlayerD("http://127.0.0.1:5000")
b = Backend("http://127.0.0.1:5001")

playingstatus = PlayingStatusIntent(c)
titlebar = TitleBarIntent()
console = ConsoleIntent(Console(c, b))

console_override = False
intents = [MainIntent()]
index = 0

old_w = 0
old_h = 0

def execute():
    pass

def handle_input(stdscr):

    global console_override    
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
            intents.append(intent)
    else:
        ret, intent = intents[-1].input(char)

def render(stdscr):

    global old_h, old_w
    h, w = stdscr.getmaxyx()

    if old_h != h or old_w != w:
        stdscr.clear()
        old_h = h
        old_w = w
    
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
        time.sleep(1000 / 120 / 1000)

wrapper(main)