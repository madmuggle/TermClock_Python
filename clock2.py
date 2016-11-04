#! /usr/bin/env python3


import signal
import termios
import fcntl
import struct
import time
import os.path


def load_font(fontfile):
    """ Load font from the font file, and return it as a list of list """
    with open(adjust_filepath(fontfile)) as f:
        return [i.split("\n") for i in f.read().split("\n\n")]


def current_script_path():
    return (os.path.dirname(__file__) or ".") + "/"


def adjust_filepath(filepath):
    """ if the filepath is not a absolute path, then fill it to absolute """
    if not os.path.isabs(filepath):
        return current_script_path() + filepath
    else:
        return filepath


def terminal_size():
    """ TIOCGWINSZ is 0x5413 on linux, but 0x40087468 on mac os x. """
    return struct.unpack("HH", fcntl.ioctl(0, termios.TIOCGWINSZ, b"    "))


def initialize_terminal():
    """ clear the screen and hide the cursor, ready for time display """
    print("\033[2J\033[0;0H\033[s\033[?25l")


def reset_cursor():
    """ restore the initial position for the display """
    print("\033[u", end="")


def printbuff_indent(buff, indent=0):
    """ for static display, with spaces ahead to make the display center """
    print("\n".join(
            " " * indent + "".join(buff[i]) for i in range(len(buff))))


def printbuff_normal(buff):
    print("\n".join("".join(buff[i]) for i in range(len(buff))))




class Clock:
    def __init__(self, slide=False, fontfile="font.txt"):
        # set the system signal handler for interrupt signal
        signal.signal(signal.SIGINT, lambda num, frm: self.interrupt())

        self.slide = slide

        self.fontbits = load_font(fontfile)

        self.font_height, self.font_width = \
            len(self.fontbits[0]), len(self.fontbits[0][0])

        # there are 8 character to be shown (6 numbers and 2 separators)
        self.c_buff_width = self.font_width * 8
        # content buffer
        self.c_buff = [[" "] * self.c_buff_width
                        for i in range(self.font_height)]

        self.w_buff_height, self.w_buff_width = terminal_size()
        # window buffer
        self.w_buff = [[" "] * self.w_buff_width
                        for i in range(self.font_height)]

        ## the spaces that make the static display center
        self.indent = round((self.w_buff_width - self.c_buff_width) / 2)

        self.separator_idx = 10
        self.prev_second = 0
        self.offset = 0

    def interrupt(self):
        """ the function to be called when ^c is pressed """
        print("\033[2J\033[0;0H\033[?25h", end="")
        exit()

    def fill_number(self, number, col):
        """ fill the c_buff with bitmap in font file """
        for c in range(self.font_width):
            for r in range(self.font_height):
                self.c_buff[r][c + col] = self.fontbits[number][r][c]

    def reverse_separator(self):
        """ reverse the separator when called """
        self.fill_number(self.separator_idx, self.font_width * 2)
        self.fill_number(self.separator_idx, self.font_width * 5)

        if self.separator_idx == 11:
            self.separator_idx = 10
        else:
            self.separator_idx = 11

    def update_c_buff(self, h, m, s):
        """ timelst is a list of time. e.g. 10:50:23 -> [10, 50, 23] """
        t = h // 10, h % 10, m // 10, m % 10, s // 10, s % 10
        for i in range(3):
            self.fill_number(t[i * 2 + 1], self.font_width * (i * 3 + 1))
            self.fill_number(t[i * 2], self.font_width * i * 3)
        if s != self.prev_second:
            self.reverse_separator()
            self.prev_second = s

    def nonempty_column(self, c):
        return c - self.offset <= self.c_buff_width - 1 and c >= self.offset

    def update_w_buff(self):
        """ copy c_buff to w_buff, and do the necessary shift """
        for c in range(self.w_buff_width):
            for r in range(self.font_height):
                if self.nonempty_column(c):
                    self.w_buff[r][c] = self.c_buff[r][c - self.offset]
                else:
                    self.w_buff[r][c] = " "
        self.offset -= 1
        if self.offset + self.c_buff_width < 0:
            self.offset = self.w_buff_width

    def start(self):
        initialize_terminal();
        while True:
            self.update_c_buff(*time.localtime()[3:6])
            reset_cursor()
            if not self.slide:
                printbuff_indent(self.c_buff, self.indent)
            else:
                self.update_w_buff()
                printbuff_normal(self.w_buff)
            time.sleep(0.05)



if __name__ == "__main__":
    import sys
    if "slide" in sys.argv:
        Clock(slide=True).start()
    else:
        Clock().start()


