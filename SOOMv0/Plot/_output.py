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
# $Id: _output.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Plot/_output.py,v $

import os
from SOOMv0.common import *
from SOOMv0 import soom
import atexit
from rpy import *

# R creates litter in /tmp and rpy doesn't call their cleanup function because
# it kills the interpreter (preventing random python object cleanup occuring).
# So we attempt a minimal workaround here (will not remove directories with
# contents, will not be called if interpreter dies):
def rmdirignore(dir):
    try:
        os.rmdir(dir)
    except OSError:
        pass
rtmp = r.tempdir()
if rtmp.startswith('/tmp/Rtmp'):         # Safety
    atexit.register(rmdirignore, rtmp)

def default_init(device, **kwargs):
    """Make standard dev init functions look like r.trellis_device, etc"""
    try:
        init_fn = getattr(r, device)
    except AttributeError:
        raise Error('Unknown device')
    return init_fn(**kwargs)

class _OutputBase(object):
    def __init__(self, **kwargs):
        self.init_args = kwargs

    def done(self):
        while r.dev_list():
            r.dev_off()

    def new_page(self, init_fn = default_init):
        r.plot_new()

class _OutputNull(_OutputBase):
    def done(self):
        pass

class _OutputScreenBase(_OutputBase):
    def __init__(self, **kwargs):
        super(_OutputScreenBase, self).__init__(**kwargs)
        self.initialised = False
        self.done()

    def new_page(self, init_fn = default_init):
        if not self.initialised:
            init_fn(self.devname, **self.init_args)
            self.initialised = True
        super(_OutputScreenBase, self).new_page()

    def done(self):
        pass

class _OutputFileBase(_OutputBase):
    def new_page(self, init_fn = default_init):
        self.done()
        init_fn(self.devname, **self.init_args)
        super(_OutputFileBase, self).new_page()

class _OutputX11(_OutputScreenBase):
    devname = 'X11'

    def __init__(self, **kwargs):
        kwargs.setdefault('width', 10)
        kwargs.setdefault('height', 7.333)
        super(_OutputX11, self).__init__(**kwargs)

if 'GDD' in r._packages(all=True):
    # The optional GDD package produces superior PNG and JPEG output, and does
    # not require a connection to an X11 server, as the built-in PNG and JPEG
    # renders do, so we use this if it is available. GDD is available from:
    #
    #       http://www.rosuda.org/R/GDD/

    class _OutputGDDBase(_OutputFileBase):
        def __init__(self, **kwargs):
            kwargs.setdefault('file', self.default_file)
            kwargs.setdefault('height', 550)
            kwargs.setdefault('width', 750)
            super(_OutputGDDBase, self).__init__(**kwargs)

        def new_page(self, init_fn_ignored = None):
            self.done()
            r.library('GDD')
            args = dict(self.init_args)
            args['h'] = args.pop('height')
            args['w'] = args.pop('width')
            r.GDD(type=self.devname, **args)
            r.plot_new()

    class _OutputPNG(_OutputGDDBase):
        devname = 'png'
        default_file = '/tmp/soom.png'

    class _OutputJPEG(_OutputGDDBase):
        devname = 'jpeg'
        default_file = '/tmp/soom.jpeg'
else:
    class _OutputPNG(_OutputFileBase):
        devname = 'png'

        def __init__(self, **kwargs):
            from SOOMv0 import xvfb_spawn
            xauth_file = None
            if soom.writepath:
                xauth_file = os.path.join(soom.writepath, '.xvfb-auth')
            xvfb_spawn.spawn_if_necessary(xauth_file)
            kwargs.setdefault('file', '/tmp/soom.png')
            kwargs.setdefault('height', 550)
            kwargs.setdefault('width', 750)
            super(_OutputPNG, self).__init__(**kwargs)

    class _OutputJPEG(_OutputFileBase):
        devname = 'jpeg'

        def __init__(self, **kwargs):
            from SOOMv0 import xvfb_spawn
            xauth_file = None
            if soom.writepath:
                xauth_file = os.path.join(soom.writepath, '.xvfb-auth')
            xvfb_spawn.spawn_if_necessary(xauth_file)
            kwargs.setdefault('file', '/tmp/soom.jpeg')
            kwargs.setdefault('height', 550)
            kwargs.setdefault('width', 750)
            super(_OutputJPEG, self).__init__(**kwargs)

class _OutputPS(_OutputFileBase):
    devname = 'postscript'

    def __init__(self, **kwargs):
        kwargs.setdefault('file', '/tmp/soom.ps')
        kwargs.setdefault('horizontal', True)
        kwargs.setdefault('paper', 'a4')
        super(_OutputPS, self).__init__(**kwargs)

class _OutputPDF(_OutputFileBase):
    devname = 'pdf'

    def __init__(self, **kwargs):
        kwargs.setdefault('file', '/tmp/soom.pdf')
        kwargs.setdefault('horizontal', True)
        kwargs.setdefault('paper', 'a4')
        if kwargs['horizontal']: 
            kwargs['height'] = kwargs.get('height', 20.9) / 2.54
            kwargs['width'] = kwargs.get('width', 29.6) / 2.54
        else:
            kwargs['width'] = kwargs.get('width', 20.9) / 2.54
            kwargs['height'] = kwargs.get('height', 29.6) / 2.54
        super(_OutputPDF, self).__init__(**kwargs)

class _OutputSVG(_OutputFileBase):
    devname = 'devSVG'

    def __init__(self, **kwargs):
        r.library('RSvgDevice')
        super(_OutputSVG, self).__init__(**kwargs)


_devices = {
    'x11': _OutputX11,
    'png': _OutputPNG,
    'jpeg': _OutputJPEG,
    'postscript': _OutputPS,
    'pdf': _OutputPDF,
    'svg': _OutputSVG,
}

dev = _OutputNull()

class Output:
    """Set Plot output device 

    First argument is one of 'X11, 'PNG', 'JPEG', 'Postscript',
    or 'PDF'. Other kwargs are passed to the R output device,
    and typically include 'file', 'height', 'width', 'paper',
    'horizontal'
    """
    def __call__(self, device, **kwargs):
        global dev
        try:
            dev_cls = _devices[device.lower()]
        except KeyError:
            raise Error('Unknown output device %r' % device)
        dev = dev_cls(**kwargs)

    def _display_hook(self):
        lines = [self.__doc__]
        devices = _devices.keys()
        devices.sort()
        lines.append('Available devices: %s' % ', '.join(devices))
        for name, cls in _devices.items():
            if isinstance(dev, cls):
                lines.append('Currently selected: %s' % name)
                break
        print '\n'.join(lines)

output = Output()
