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
"""
Start a virtual X server on the specified screen if not already
running.

$Id: xvfb_spawn.py 2626 2007-03-09 04:35:54Z andrewm $
$Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/xvfb_spawn.py,v $
"""

import sys
import os
import errno
import md5

xpath = '/usr/X11R6/bin/'
xvfb = xpath + 'Xvfb'
xauth = xpath + 'xauth'
default_xauth_file = '.xvfb-auth'

class VFBError(Exception): pass
class PipeIOError(Exception): pass

def is_running(display_num):
    """
    Check to see if an X server for the given screen is running on
    the local machine.
    """
    lock_filename = '/tmp/.X%d-lock' % display_num
    try:
        lock_file = open(lock_filename)
    except IOError, (eno, estr):
        if eno == errno.ENOENT:
            return False
        raise
    try:
        try:
            pid = int(lock_file.readline().strip())
        except (ValueError, EOFError, IOError):
            return True                 # Have to assume it is?!
        try:
            os.kill(pid, 0)
        except OSError, (eno, etsr):
            if eno == errno.ESRCH:
                return False
            elif eno == errno.EPERM:
                return True
            raise
        return True
    finally:
        lock_file.close()

def fork_vfb(display_num, xauth_file, nullerrors=False):
    """
    Start virtual X server in a backgrounded process that is
    disassociated from the controlling TTY (no HUP signals).
    Second fork is required to prevent subsequently opened TTY's
    becoming our controlling TTY [Stevens 93], and so init becomes
    the parent of Xvfb (and therefore avoiding zombies).
    """
    pid = os.fork()
    if not pid:
        os.close(0)
        os.open('/dev/null', os.O_RDONLY)
        os.close(1)
        os.open('/dev/null', os.O_WRONLY)
        if nullerrors:
            os.close(2)
            os.open('/dev/null', os.O_WRONLY)
        # Close any other fd's inherited from our parent (such as client
        # sockets). A max fd of 31 isn't correct, but is a trade-off that
        # resolves most problems without wasting too many cycles.
        for fd in range(3, 32):
            try:
                os.close(fd)
            except OSError:
                pass
        os.setsid()
        pid = os.fork()
        if pid:
            os._exit(1)
        try:
            os.execl(xvfb, os.path.basename(xvfb),
                    ':%d' % display_num, 
                    '-nolisten', 'tcp',
    #                '-terminate',
                    '-auth', xauth_file) 
        finally:
            os._exit(1)

class PipeIO:
    def __init__(self, mode, *args):
        read_fd, write_fd = os.pipe()
        self.pid = os.fork()
        self.cmd = args[0]
        if self.pid:
            # Parent
            if mode == 'w':
                os.close(read_fd)
                self.file = os.fdopen(write_fd, 'w')
            else:
                os.close(write_fd)
                self.file = os.fdopen(read_fd, 'r')
        else:
            # Child
            if mode == 'w':
                os.close(write_fd)
                os.dup2(read_fd, 0)
                os.close(read_fd)
            else:
                os.close(read_fd)
                os.dup2(write_fd, 1)
                os.close(write_fd)
            try:
                os.execl(self.cmd, os.path.basename(args[0]), *args[1:])
            except OSError, (eno, estr):
                print >> sys.stderr, 'exec %s: %s' % (self.cmd, estr)
                os._exit(1)

    def __getattr__(self, a):
        return getattr(self.file, a)

    def close(self):
        self.file.close()
        while 1:
            try:
                pid, status = os.waitpid(self.pid, 0)
            except OSError, (eno, estr):
                if errno == errno.ECHILD:
                    raise PipeIOError('Couldn\'t fork xauth')
                elif errno != errno.EINTR:
                    raise
            else:
                break
        if os.WIFEXITED(status) and os.WEXITSTATUS(status):
            raise PipeIOError('%s exited with status %d' %\
                              (self.cmd, os.WEXITSTATUS(status)))

def init_auth(display_num, xauth_file):
    f = open('/dev/urandom', 'rb')
    try:
        cookie = md5.new(f.read(40)).hexdigest()
    finally:
        f.close()
    f = PipeIO('w', xauth, '-q', '-f', xauth_file, '-')
    try:
        f.write('add :%d MIT-MAGIC-COOKIE-1 %s\n' % (display_num, cookie))
    finally:
        f.close()

def auth_display(xauth_file):
    f = PipeIO('r', xauth, '-f', xauth_file, 'list')
    try:
        for line in f:
            try:
                dpy, auth_type, auth_str = line.split(None, 2)
                display_host, display_num = dpy.split(':')
                display_num = int(display_num)
            except ValueError:
                continue
            if is_running(display_num):
                return display_num
    finally:
        f.close()

def spawn_xvfb(display_num, divorce=False):
    """
    Start a virtual X server on the specified screen if not already running
    """
    os.environ['DISPLAY'] = ':%d' % display_num
    os.environ['XAUTHORITY'] = auth_filename()
    if not is_running(display_num):
        init_auth(display_num)
        fork_vfb(display_num, divorce=divorce)

def spawn_if_necessary(xauth_file = default_xauth_file):
    if not os.environ.get('DISPLAY'):
        xauth_file = os.path.abspath(xauth_file)
        display_num = auth_display(xauth_file)
        if display_num is None:
            for display_num in xrange(10, 1000):
                if not is_running(display_num):
                    break
            else:
                raise VFBError('no free displays!')
            init_auth(display_num, xauth_file)
            fork_vfb(display_num, xauth_file)
        os.environ['DISPLAY'] = ':%d' % display_num
        os.environ['XAUTHORITY'] = xauth_file
