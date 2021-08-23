from clients import PlayerD, Backend
from curses import wrapper
from ui import MainIntent

import curses
import time


c = PlayerD("http://127.0.0.1:5000")
b = Backend("http://127.0.0.1:5001")

console_override = False
intents = [MainIntent()]
index = 0
text = ""


def draw_titlebar(stdscr):
    # Shitfest alert
    h, w = stdscr.getmaxyx()
    str = "OpenPlayer"
    strlen = len(str)
    padding = " " * int((w - strlen) / 2)
    str = padding + str + padding
    #stdscr.addstr(0, 0, " " * (w - 1)) # Clear line
    stdscr.addstr(0, 0, str, curses.color_pair(1))

def draw_playingbar(stdscr):
    s = c.get_status()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h-1, 0, " "*(w-1), curses.color_pair(1))
    if s['playing']:
        current = int(s['position'])
        duration = s['duration']
        stdscr.addstr(h-1, 0, f"{current} / {duration} - {s['name']}", curses.color_pair(1))
    else:
        stdscr.addstr(h-1, 0, "Not playing", curses.color_pair(1))

def draw_console(stdscr):
    if not console_override:
        return
    h, w = stdscr.getmaxyx()
    if len(text) == 0:
        render_text = "..."
    else:
        render_text = text
    stdscr.addstr(h-1, 0, " " * (w - 1), curses.color_pair(1)) # Clear line
    stdscr.addstr(h-1, 0, ">" + render_text, curses.color_pair(1))

def execute():
    pass

def handle_input(stdscr):

    global console_override
    global text
    
    x = stdscr.getch()

    if x == -1:
        return
    elif x == 62:
        console_override = not console_override
    elif console_override:
        if x == 127:
            if len(text) == 0:
                return
            text = text[:-1]
        elif x == 263:
            text = ""
        elif x == 10:
            execute()
            console_override = False
        else:
            text += chr(x)
    else:
        intents[-1].input(x)  # TODO: handle intent change


def render(stdscr):
    draw_titlebar(stdscr)
    draw_playingbar(stdscr)
    draw_console(stdscr)
    h, w = stdscr.getmaxyx()
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