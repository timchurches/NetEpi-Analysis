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
# $Id: Soom.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Soom.py,v $

import sys
import os
import errno
import re
import logging
from SOOMv0 import common, Utils

class Soom(object):
    """
    Top-level SOOM configuration object

    Attributes include:

        messages                If True, information messages are sent to
                                sys.stdout.
        row_ordinals            If True, row ordinal column is printed
        lazy_column_loading     If True, column data is loaded on demand,
                                otherwise loaded with dataset.
    """

    version_info = common.version_info
    version = common.version

    # AM - I'm not happy allowing '$' through, but it's used by the
    # summ() method when generating a summary Dataset.
    valid_identifier_re = re.compile('^[a-z_-][a-z0-9_$-]*$', re.IGNORECASE)

    metadata_filename = 'Metadata.pickle'

    # default path for persistent storage of SOOM objects
    default_object_path = 'SOOM_objects'

    def __init__(self):
        self.init_logger()
        self.messages = False
        self.row_ordinals = True
        self.lazy_column_loading = True
        self.searchpath = [self.default_object_path]
        self.writepath = None
        self.nproc = 1
        if os.access(self.searchpath[0], os.W_OK | os.X_OK):
            self.writepath = self.searchpath[0]

    def check_name_ok(self, name, msg):
        if not name or not name.strip():
            raise common.Error, '%s has no name' % msg
        if not self.valid_identifier_re.match(name):
            raise common.Error, \
                '%s name "%s" contains illegal characters' % (msg, name)

    def setpath(self, path, writepath = None):
        if path is not None:
            self.searchpath = [os.path.normpath(os.path.expanduser(p))
                               for p in path.split(':')]
        if writepath:
            self.writepath = writepath

    def object_path(self, name, path = None):
        if path is not None:
            self.setpath(path)
        for pathdir in self.searchpath:
            if os.path.exists(os.path.join(pathdir, name)):
                return pathdir

    def find_metadata(self, prefix):
        paths = []
        for pathdir in self.searchpath:
            pathdir = os.path.join(pathdir, prefix)
            try:
                dirlist = os.listdir(pathdir)
            except OSError:
                continue
            for filename in dirlist:
                pd = os.path.join(pathdir, filename)
                if os.path.exists(os.path.join(pd, soom.metadata_filename)):
                    paths.append(pd)
        return paths

    def available_datasets(self):
        datasets = []
        for pathdir in self.searchpath:
            try:
                files = os.listdir(pathdir)
            except OSError, (eno, estr):
                if eno == errno.ENOENT:
                    self.warning('soompath: %r: %s - skipped' % (pathdir, estr))
                    continue
                raise
            for dsname in files:
                metadatapath = os.path.join(pathdir, dsname, 
                                            soom.metadata_filename)
                if os.access(metadatapath, os.R_OK):
                    datasets.append(dsname)
        datasets.sort()
        return datasets

    def _display_hook(self):
        print 'SOOM version (soom.version): %s' % self.version
        print 'Informational messages (soom.messages): %s' % bool(self.messages)
        print 'Print row ordinals (soom.row_ordinals): %s' % bool(self.row_ordinals)
        print 'Lazy column loading (soom.lazy_column_loading): %s' % bool(self.lazy_column_loading)

    def init_logger(self):
        self.logger = logging.getLogger('SOOM')
        self.default_handler = logging.StreamHandler()
        if not hasattr(sys, 'ps1'):
            # Not interactive, add timestamp
            fmt_str = '%(asctime)s %(name)s %(levelname)s %(message)s'
        else:
            fmt_str = '%(name)s %(levelname)s %(message)s'
        formatter = logging.Formatter(fmt_str)
        self.default_handler.setFormatter(formatter)
        self.logger.addHandler(self.default_handler)

    def _set_messages(self, v):
        if v:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)

    def _get_messages(self):
        return self.logger.getEffectiveLevel() < logging.WARNING

    messages = property(_get_messages, _set_messages)

    def add_logging_handler(self, handler):
        self.logger.removeHandler(self.default_handler)
        self.logger.addHandler(handler)

    def critical(self, *args):
        self.logger.critical(*args)

    def exception(self, *args):
        self.logger.exception(*args)

    def error(self, *args):
        self.logger.error(*args)

    def warning(self, *args):
        self.logger.warning(*args)

    def info(self, *args):
        self.logger.info(*args)

    def debug(self, *args):
        self.logger.debug(*args)

    if sys.platform == 'linux2':
        _pagesize = os.sysconf('SC_PAGESIZE')
        _lastsz = 0
        def mem_report(self):
            if self.messages:
                f = open('/proc/%d/statm' % os.getpid())
                try:
                    statm = [int(n) * self._pagesize for n in f.read().split()]
                finally:
                    f.close()
                delta = statm[0] - self._lastsz
                self._lastsz = statm[0]
                self.info('mem delta: %dk, total: %dk' % (delta / 1024, self._lastsz / 1024))
    else:
        def mem_report(self):
            pass
    if 0:
        def mem_report(self):
            if self.messages:
                labels = 'sz', 'res', 'share', 'txt', 'data', 'lib', 'dirty'
                f = open('/proc/%d/statm' % os.getpid())
                try:
                    statm = [int(n) * self._pagesize for n in f.read().split()]
                finally:
                    f.close()
                fields = ['%s %6.2fk' % (f, n / 1024) 
                          for f, n in zip(labels, statm)]
                self.info('Mem: %s' % ', '.join(fields))
        

soom = Soom()
