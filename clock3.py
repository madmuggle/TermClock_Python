#! /usr/bin/env python3


import signal
import termios
import fcntl
import struct
import time
import os.path
import sys


def load_font(fontfile):
    """ Load font from disk file, and return it as a list of list of str """
    with open(adjust_filepath(fontfile)) as f:
        return [i.split("\n") for i in f.read().split("\n\n")]


def terminal_size():
    """ TIOCGWINSZ is 0x5413 on linux, but 0x40087468 on mac os x. """
    return struct.unpack("HH", fcntl.ioctl(0, termios.TIOCGWINSZ, b"    "))


def initialize_terminal():
    """ clear the screen and hide the cursor, ready for time display """
    print("\033[2J\033[0;0H\033[s\033[?25l")


def reset_cursor():
    """ restore the initial position of cursor, for next display """
    print("\033[u", end="")


def user_interrupt(num, frm):
    """ need to restore terminal setting before this program stop """
    print("\033[2J\033[0;0H\033[?25h", end="")
    exit()


def current_script_path():
    return (os.path.dirname(__file__) or ".") + "/"


def adjust_filepath(filepath):
    """ if the filepath is not a absolute path, then fill it to absolute """
    if not os.path.isabs(filepath):
        return current_script_path() + filepath
    else:
        return filepath


def printbuff_indent(buff, indent=0):
    """ for static display, with spaces ahead to make the display center """
    print("\n".join(
            " " * indent + "".join(buff[i]) for i in range(len(buff))))

def printbuff_normal(buff):
    print("\n".join("".join(buff[i]) for i in range(len(buff))))


def show_static_clock(env):
    """ to show static clock, just call printbuff_indent """
    printbuff_indent(env.c_buff, env.indent)

def show_sliding_clock(env):
    """ update window buffer first, then flush it """
    update_w_buff(env)
    printbuff_normal(env.w_buff)

def show_clock(env):
    """ Just a wrapper for "printbuff_normal" and "printbuff_indent" """
    if env.slide: show_sliding_clock(env)
    else: show_static_clock(env)



def fill_number(env, numidx, col):
    """ fill the c_buff with bitmap in font file """
    for c in range(env.f_width):
        for r in range(env.f_height):
            env.c_buff[r][c + col] = env.fontbits[numidx][r][c]


def toggle_speidx(env):
    """ env.sepidx can only be 11 or 10, toggle it when called """
    if env.sepidx == 11: env.sepidx = 10
    else: env.sepidx = 11

def reverse_separator(env):
    """ separators have two shapes, toggle it (fill to c_buff) when called """
    fill_number(env, env.sepidx, env.f_width * 2)
    fill_number(env, env.sepidx, env.f_width * 5)
    toggle_speidx(env)


def fill_fields(env, timelst):
    """ clock have 3 fields: hour, minute, second. fill them to c_buff """
    for i in range(3):
        fill_number(env, timelst[i * 2 + 1], env.f_width * (i * 3 + 1))
        fill_number(env, timelst[i * 2], env.f_width * i * 3)


def update_c_buff(env, h, m, s):
    timelst = h // 10, h % 10, m // 10, m % 10, s // 10, s % 10
    fill_fields(env, timelst)
    if s != env.prevtime:
        reverse_separator(env)
        env.prevtime = s


def shift_offset(env):
    """ the sliding effect of the clock depend on the changing of offset """
    env.offset -= 1
    if env.offset + env.c_width < 0:
        env.offset = env.w_width


def update_w_buff(env):
    """ copy c_buff to w_buff, and do the necessary shift """
    for c in range(env.w_width):
        for r in range(env.f_height):
            if (c - env.offset <= env.c_width - 1) and (c >= env.offset):
                env.w_buff[r][c] = env.c_buff[r][c - env.offset]
            else:
                env.w_buff[r][c] = " "
    shift_offset(env)



def main_job(env):
    """ update buffer using current time, reset cursor, and draw the clock """
    update_c_buff(env, *time.localtime()[3:6])
    reset_cursor()
    show_clock(env)


def start(env):
    """ initialize terminal, then go into the print <-> update loop """
    initialize_terminal();
    while True:
        main_job(env)
        time.sleep(0.05)



class ClockEnv:
    """ clock have many related values, store them in one object """
    def __init__(self, **kwargs):
        self.__dict__ = kwargs



if __name__ == "__main__":
    # set the system signal handler for interrupt signal
    signal.signal(signal.SIGINT, user_interrupt)

    # font is stored in list of list of string
    fontbits = load_font("font.txt")

    # font size will be frequently used
    f_height, f_width = len(fontbits[0]), len(fontbits[0][0])

    # there are 8 character to be shown (6 numbers and 2 separators)
    c_width = f_width * 8

    # window buffer size depend on the size of terminal
    w_width = terminal_size()[1]

    # content buffer
    c_buff = [[" "] * c_width for i in range(f_height)]

    # window buffer
    w_buff = [[" "] * w_width for i in range(f_height)]

    # the spaces that make the static display center
    indent = round((w_width - c_width) / 2)

    # slide is an optional function, specified by command line
    if "slide" in sys.argv: slide = True
    else: slide = False

    # create an object to store clock related values
    clock = ClockEnv(
        fontbits=fontbits, f_height=f_height, f_width=f_width,
        c_width=c_width, w_width=w_width,
        c_buff=c_buff, w_buff=w_buff,
        indent=indent, slide=slide,
        sepidx=10, prevtime=0, offset=0)

    # start the clock
    start(clock)

