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
# $Id: plot.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/output/plot.py,v $

import os

import SOOMv0

import config

from libsoomexplorer.output.base import OutputBase, OutputError

class ImageOut(OutputBase):
    horizontal = True
    format = 'PNG'
    formats = ['PNG', 'PDF', 'SVG']
    size = '750x550'
    want_inline = False
    markup = 'imageout'

    def __init__(self):
        super(ImageOut, self).__init__()
        self.inline = False

    def start(self, methodname):
        self.clear()
        of = self.tempfile(self.format)
        kwargs = {}
        kwargs['file'] = of.fn
        if self.format == 'PNG':
            w, h = [int(r) for r in self.size.split('x')]
            if w > 10000 or h > 10000:
                raise WorkspaceError('bad output resolution')
            kwargs['height'] = h
            kwargs['width'] = w
            self.inline = True
        elif self.format == 'PDF':
            kwargs['horizontal'] = (self.horizontal == 'True')
            self.inline = False
        elif self.format == 'SVG':
            self.inline = (self.want_inline == 'True')
        else:
            raise WorkspaceError('bad output format')
        SOOMv0.plot.output(self.format, **kwargs)
        return getattr(SOOMv0.plot, methodname)
