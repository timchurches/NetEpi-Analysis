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
# $Id: base.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/output/base.py,v $

import os
import tempfile

import config

class OutputError(Exception):
    pass


class _OutputFile(object):
    def __init__(self, fn, label):
        self.fn = fn
        self.label = label

    def delete(self):
        try:
            os.unlink(self.fn)
        except OSError:
            pass

    def url(self):
        # XXX hard coded path
        return '/nea/dynamic/' + os.path.basename(self.fn)

    def exists(self):
        return os.path.exists(self.fn)


class OutputBase(object):
    def __init__(self):
        self._reset()

    def _reset(self):
        self._files = []

    def clear(self):
        for of in self._files:
            of.delete()
        self._reset()

    def files(self):
        return [of for of in self._files if of.exists()]

    def have_files(self):
        return len(self.files()) > 0

    def tempfile(self, ext, label=None):
        f, path = tempfile.mkstemp('.' + ext.lower(), 'soom', 
                                   config.dynamic_target)
        os.close(f)
        of = _OutputFile(path, label)
        self._files.append(of)
        return of

    def output_names(self):
        return [of.url() for of in self._files]


class NullOut(OutputBase):
    pass
