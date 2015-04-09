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
# $Id: filterstore.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/filterstore.py,v $

# Standard libraries
import os
import cPickle
import fcntl
import time
import errno
import re
import tempfile

from libsoomexplorer.filter import Filter, FilterError

import config

__all__ = ('filterstore',)

safe_dsname_re = re.compile(r'^[a-z0-9_-]{1,16}$', re.IGNORECASE)

def dsfilters_filename(dsname):
    if not safe_dsname_re.match(dsname):
        # Shouldn't happen, but, because we use this as a filename,
        # we need to be paranoid.
        raise FilterError('Bad dataset name: %r' % dsname)
    return os.path.join(config.data_dir, '%s_filters.pkl' % dsname)


class DSFilterStore:
    def __init__(self, dsname):
        self.dsname = dsname
        self.mtime = None
        self.filters = {}

    def refresh(self):
        filename = dsfilters_filename(self.dsname)
        try:
            mtime = os.path.getmtime(filename)
        except OSError, (eno, estr):
            if eno == errno.ENOENT:
                self.filters = {}
                return
            raise
        if self.mtime is None or self.mtime < mtime:
            try:
                f = open(filename, 'rb')
            except IOError, (eno, estr):
                if eno != errno.ENOENT:
                    raise
                self.filters = {}
            else:
                try:
                    self.filters = cPickle.load(f)
                finally:
                    f.close()

    def _update(self, filter, delete=False):
        """
        Merge the given filter into the saved filters for this dataset

        We first obtain an exclusive lock on the current file,
        read it, and check to make sure someone else hasn't already
        updated the filter in question. If this condition is met,
        a new temporary filters pickle is writen, then renamed into
        place (an atomic operation).
        """
        if not filter.name:
            raise FilterError('A filter name must be specified!')
#        if not self.name_re.match(filter.name):
#            raise FilterError('Invalid filter name %r' % filter.name)
        if not delete and not filter.modified():
            raise FilterError('Filter is not modified!')
        filename = dsfilters_filename(self.dsname)
        readit = True
        try:
            f = open(filename, 'r+b')
        except IOError, (eno, estr):
            if eno != errno.ENOENT:
                raise
            f = open(filename, 'wb')
            readit = False
        try:
            fcntl.lockf(f, fcntl.LOCK_EX)
            if readit:
                self.filters = cPickle.load(f)
                f.seek(0)
            else:
                self.filters = {}
            old_filter = self.filters.get(filter.name.lower())
            if old_filter and old_filter.updatetime != filter.updatetime:
                raise FilterError('filter %r updated by another user!' % 
                                  filter.name)
            if delete:
                try:
                    del self.filters[filter.name.lower()]
                except KeyError:
                    pass
            else:
                filter.clear_undo()
                filter.updatetime = time.time()
                self.filters[filter.name.lower()] = filter
            dir, fn = os.path.split(filename)
            tf, tempname = tempfile.mkstemp(prefix='.filter.', dir=dir)
            tf = os.fdopen(tf, 'wb')
            try:
                cPickle.dump(self.filters, tf, -1)
            except:
                tf.close()
                os.unlink(tempname)
                raise
            else:
                tf.close()
                os.rename(tempname, filename)
                self.mtime = os.path.getmtime(filename)
        finally:
            f.close()

    def update(self, filter):
        self._update(filter)

    def delete(self, filter):
        self._update(filter, delete=True)

    def __getitem__(self, name):
        return self.filters[name.lower()]

    def values(self):
        return self.filters.values()


class FilterStore:
    """
    This represents "saved" filters, and provides
    concurrent-access-safe methods for loading, saving and deleting
    filters.
    """

    def __init__(self):
        self._dsfilters = {}

    def __getstate__(self):
        raise NotImplementedError

    def _get_dsfilters(self, dsname):
        try:
            dsfilters = self._dsfilters[dsname]
        except KeyError:
            dsfilters = self._dsfilters[dsname] = DSFilterStore(dsname)
        dsfilters.refresh()
        return dsfilters

    def available_filters(self, dsname):
        return self._get_dsfilters(dsname).values()

    def load_filter(self, dsname, filtername):
        return self._get_dsfilters(dsname)[filtername]

    def update_filter(self, filter):
        self._get_dsfilters(filter.dsname).update(filter)

    def delete_filter(self, filter):
        self._get_dsfilters(filter.dsname).delete(filter)

    def new_filter(self, dsname):
        return Filter(dsname)

filterstore = FilterStore()
