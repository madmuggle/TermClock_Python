#! /usr/bin/env python3


import signal
import termios
import fcntl
import struct
import time
import os.path


def signal_handle(num, frm):
    """ enable Ctrl-c (the SIGINT signal) to exit the clock program """
    print("\033[2J\033[0;0H\033[?25h", end="")
    exit()

signal.signal(signal.SIGINT, signal_handle)


script_path = (os.path.dirname(__file__) or ".") + "/"

with open(script_path + "font.txt") as f:
    fontbits = [i.split("\n") for i in f.read().split("\n\n")]


font_width = len(fontbits[0][0])
font_height = len(fontbits[0])

#print("font_width:{} font_height:{}".format(font_width, font_height))
#exit()

## there are 8 character to be shown (6 numbers and 2 separators)
## c_buff -> content buffer
c_buff_width = font_height * 8
c_buff = [[" "] * c_buff_width for i in range(font_height)]


## TIOCGWINSZ is 0x5413 on linux, but 0x40087468 on mac os x.
w_buff_height, w_buff_width = \
    struct.unpack("HH", fcntl.ioctl(0, termios.TIOCGWINSZ, b"    "))


## the spaces that make the static display center
indent = round((w_buff_width - c_buff_width) / 2)


## w_buff -> window buffer
w_buff = [[" "] * w_buff_width for i in range(font_height)]


def fill_number(number, col):
    """ fill the c_buff with bitmap in font file """
    for c in range(font_width):
        for r in range(font_height):
            c_buff[r][c + col] = fontbits[number][r][c]


## this global variable is needed by function:reverse_separator
separator_idx = 10

def reverse_separator():
    """ reverse the separator when called """
    global separator_idx
    fill_number(separator_idx, font_width * 2)
    fill_number(separator_idx, font_width * 5)

    if separator_idx == 11:
        separator_idx = 10
    else:
        separator_idx = 11



## this global variable is needed by function:update_c_buff
prev_second = 0

def update_c_buff(h, m, s):
    """ timelst is a list of time. e.g. 10:50:23 -> [10, 50, 23] """
    global prev_second
    t = h // 10, h % 10, m // 10, m % 10, s // 10, s % 10
    for i in range(3):
        fill_number(t[i * 2], font_width * i * 3)
        fill_number(t[i * 2 + 1], font_width * (i * 3 + 1))
    if s != prev_second:
        reverse_separator()
        prev_second = s



offset = 0

def update_w_buff():
    """ copy c_buff to w_buff, and do the necessary shift, this function will
    NOT print anything to the terminal """
    global offset
    for col in range(w_buff_width):
        for row in range(font_height):
            if col - offset <= c_buff_width - 1 and col >= offset:
                w_buff[row][col] = c_buff[row][col - offset]
            else:
                w_buff[row][col] = " "
    offset -= 1
    if offset + c_buff_width < 0:
        offset = w_buff_width



def print_static():
    """ for static display, with spaces ahead to make the display center """
    print("\n".join(
            " " * indent + "".join(c_buff[i]) for i in range(len(c_buff))))


def print_dynamic():
    """ for dynamic display (shift). will always update w_buff first """
    update_w_buff()
    print("\n".join("".join(w_buff[i]) for i in range(len(w_buff))))



def initialize_terminal():
    """ clear the screen and hide the cursor, ready for time display """
    print("\033[2J\033[0;0H\033[s\033[?25l")

def reset_cursor():
    """ restore the initial position for the display """
    print("\033[u", end="")


def run_clock(print_function=print_static):
    initialize_terminal();
    while True:
        update_c_buff(*time.localtime()[3:6])
        reset_cursor()
        print_function()
        time.sleep(0.05)


if __name__ == "__main__":
    import sys
    if "slide" in sys.argv:
        run_clock(print_function=print_dynamic)
    else:
        run_clock(print_function=print_static)


