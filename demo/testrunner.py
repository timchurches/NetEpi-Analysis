#
#   The contents of this file are subject to the HACOS License Version 1.2
#   (the "License"); you may not use this file except in compliance with
#   the License.  Software distributed under the License is distributed
#   on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
#   implied. See the LICENSE file for the specific language governing
#   rights and limitations under the License.  The Original Software
#   is "NetEpi Analysis". The Initial Developer of the Original
#   Software is the Health Administration Corporation, incorporated in
#   the State of New South Wales, Australia.
#
#   Copyright (C) 2004,2005 Health Administration Corporation. 
#   All Rights Reserved.
#
# $Id: testrunner.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/testrunner.py,v $

import sys, time
from SOOMv0 import *

import curses
import textwrap
import traceback
import logging

class CursesLoggingHandler(logging.Handler):
    def __init__(self, w):
        logging.Handler.__init__(self)
        self.w = w
        self.setFormatter(logging.Formatter('%(levelname)s %(message)s'))

    def emit(self, record):
        self.w.addstr('%s\n' % self.format(record))
        self.w.refresh()

class TestRunner:
    enter_keys = 13, 10, curses.KEY_ENTER
    dn_keys = (ord(' '), curses.KEY_DOWN, curses.KEY_RIGHT) + enter_keys
    up_keys = curses.KEY_UP, curses.KEY_LEFT
    quit_keys = ord('q'), ord('Q'), 4
    bs_keys = 8, curses.KEY_BACKSPACE

    def __init__(self):
        self.w = curses.initscr()
        self.real_stdout, sys.stdout = sys.stdout, self
        curses.noecho()
        curses.cbreak()
        self.w.keypad(1)
        self.w.scrollok(1)
        self.w.idlok(1)
        soom.add_logging_handler(CursesLoggingHandler(self.w))

    def write(self, buf):
#        y, x = self.w.getyx()
        self.w.addstr(buf)
        self.w.refresh()

    def close(self):
        self.w.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        sys.stdout = self.real_stdout

    def run(self, tests):
        i = 0
        while 1:
            test = tests[i]
            print '\n## Starting test %d of %d' % (i + 1, len(tests))
            test.run(self.w)
            self.w.addstr('Finished test %d of %d> ' % (i + 1, len(tests)))
            seek = ''
            while 1:
                curses.flushinp()
                c = self.w.getch()
                if c in self.enter_keys and seek:
                    try:
                        i = int(seek) - 1
                        if i < 0 or i >= len(tests):
                            raise ValueError
                        break
                    except ValueError:
                        curses.beep()
                        continue
                if c in self.dn_keys:
                    if i < len(tests) - 1:
                        i += 1
                        break
                    else:
                        curses.beep()
                elif c in self.up_keys:
                    if i > 0:
                        i -= 1
                        break
                    else:
                        curses.beep()
                elif c in self.quit_keys:
                    return
                elif ord('0') <= c <= ord('9'):
                    seek = seek + chr(c)
                    self.w.echochar(c)
                elif c in self.bs_keys:
                    if seek:
                        seek = seek[:-1]
                        self.w.echochar(8)
                        self.w.clrtoeol()
#                else:
#                    self.w.addstr('%s\n' % c)

class Test:
    def __init__(self, commentary, fn, *args, **kwargs):
        self.commentary = commentary
        self.fn = fn
        self.args = args
        self.disabled = kwargs.pop('disabled', False)
        self.kwargs = kwargs

    def run(self, w):
        lines = [l.strip() for l in self.commentary.split('\n')]
        lines = textwrap.wrap(' '.join(lines), 75)
        args = []
        if hasattr(self.args[0], 'name'):
            args.append(self.args[0].name)
        else:
            args.append(repr(self.args[0]))
        for a in self.args[1:]:
            args.append(repr(a))
        for k, v in self.kwargs.items():
            args.append('%s=%r' % (k, v))
        print '## %s(%s)' % (self.fn.__name__, ', '.join(args))
        if self.disabled:
            print '## DISABLED ##'
        else:
            start = time.time()
            try:
                self.fn(*self.args, **self.kwargs)
            except:
                for line in traceback.format_exception(*sys.exc_info()):
                    w.addstr(line, curses.A_BOLD)
            elapsed = time.time() - start
        for line in lines:
            print '## ' + line
        if not self.disabled:
            print '## %.3f seconds' % elapsed
