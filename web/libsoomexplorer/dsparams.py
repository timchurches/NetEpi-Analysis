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
# $Id: dsparams.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/dsparams.py,v $

import copy
import SOOMv0
from libsoomexplorer.filterstore import filterstore

class DSParams:
    def __init__(self, dsname=None):
        self.dsname = dsname
        self.clear()

    def __getstate__(self):
        state = dict(self.__dict__)
        state['_DSParams__filtered_ds'] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def clear(self):
        self.filterexpr = None
        self.filterlabel = None
        self.filter = None
        self.filtername = None
        self.__filtered_ds = None

    def set_dsname(self, dsname):
        if dsname is not None and self.dsname != dsname:
            self.clear()
            self.dsname = dsname

    def _clean_filterexpr(self):
        return self.filterexpr.replace('\n', ' ').replace('\r', '')

    def filter_args(self, kw):
        if self.filterexpr:
            kw['filterexpr'] = self._clean_filterexpr()
            if self.filterlabel:
                kw['filterlabel'] = self.filterlabel

    def available_filters(self):
        if not self.dsname:
            return []
        filter_list = [(f.label, f.name) 
                       for f in filterstore.available_filters(self.dsname)]
        filter_list.sort()
        if self.filter is not None and self.filter.modified():
            filter_list.insert(0, ('<modified>', ''))
        return [(n, l) for l, n in filter_list]

    def use_filter(self, filter):
        self.filterexpr = filter.as_string()
        if filter.label:
            self.filterlabel = filter.label 
        else:
            label = self.filterexpr
            if len(label) > 60:
                label = label[:60] + ' ...'
            self.filterlabel = label 
        self.filter = filter
        if filter.modified():
            self.filtername = ''
        else:
            self.filtername = filter.name

    def save_filter(self, filter):
        filterstore.update_filter(filter)
        self.use_filter(filter)

    def delete_filter(self, filter):
        if filter.name:
            filterstore.delete_filter(filter)
        self.clear()

    def get_filtered_dataset(self):
        if self.__filtered_ds is None:
            kw = {}
            self.filter_args(kw)
            self.__filtered_ds = SOOMv0.dsload(self.dsname).filter(kwargs=kw)
        return self.__filtered_ds

    def do_clear(self, ctx):
        self.clear()

    def do_new(self, ctx):
        self.edit_filter = filterstore.new_filter(self.dsname)
        ctx.push_page('filter', self)

    def do_edit(self, ctx):
        filter = self.filter
        if not filter:
            filter = filterstore.new_filter(self.dsname)
        elif self.filtername:
            filter = filterstore.load_filter(self.dsname, self.filtername)
        self.edit_filter = copy.deepcopy(filter)
        ctx.push_page('filter', self)

    def do_load(self, ctx):
        if self.filtername:
            self.use_filter(filterstore.load_filter(self.dsname, self.filtername))
