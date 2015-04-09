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
# $Id: colvals.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/colvals.py,v $

import re
import sets
import fnmatch
import cPickle, binascii
from libsoomexplorer.common import *

def make_re(pattern):
    if pattern.find('*') < 0:
        pattern = '*%s*' % pattern
    return re.compile(fnmatch.translate(pattern), re.IGNORECASE)

def shorten_trans(col, v, split_long=50):
    if v is None:
        v = 'None'
    v_trans = col.do_format(col.do_outtrans(v)).strip()
    if len(v_trans) > split_long:
        n = split_long / 2 - 2
        v_trans = '%s ... %s' % (v_trans[:n], v_trans[-n:])
    return v_trans

def to_datatype(col, v):
    try:
        return col.datatype.as_pytype(v)
    except (ValueError, TypeError):
        return v

def encode_val(v):
    return binascii.b2a_base64(cPickle.dumps(v, -1)).strip()

def decode_val(d):
    return cPickle.loads(binascii.a2b_base64(d))

class ColValSelect:
    too_many_results = 200

    def __init__(self, name, value, ignore_vals=None, multiple=True):
        self.name = name
        self.multiple = multiple
        if self.multiple:
            if value is None:
                value = []
            else:
                value = list(value)
        self.value = value
        self.search_pat = ''
        self.errorstr = ''
        if ignore_vals is None:
            ignore_vals = sets.ImmutableSet()
        self.ignore_vals = ignore_vals

    def cardinality_is_high(self, workspace):
        col = workspace.get_dataset()[self.name]
        return col.cardinality() > 100

    def select_values(self, workspace):
        col = workspace.get_dataset()[self.name]
        values = col.inverted.keys()
        if col.is_ordered():
            values.sort()
        values = [(shorten_trans(col, v), v) 
                  for v in values
                  if v not in self.ignore_vals]
        if not col.is_ordered():
            values.sort()
        return [(v, l) for l, v in values]

    def search(self, workspace):
        self.errorstr = ''
        pattern = self.search_pat
        if not pattern:
            return []
        col = workspace.get_dataset()[self.name]
        values = []
        ignore_vals = sets.Set(self.ignore_vals)
        if self.multiple:
            ignore_vals.union_update(self.value)
        else:
            ignore_vals.add(self.value)
        if pattern.find('*') < 0:
            pattern = '*%s*' % pattern
        pattern = make_re(pattern)
        ignored = False
        for v in col.inverted.keys():
            if v not in ignore_vals:
                v_trans = col.do_format((col.do_outtrans(v)))
                if pattern.match(v_trans):
                    values.append((v_trans, encode_val(v)))
            else:
                ignored = True
        if not values:
            if ignored:
                self.errorstr = 'No more matches'
            else:
                self.errorstr = 'No matches'
        elif len(values) > self.too_many_results:
            self.errorstr = 'Too many matches (%d)' % len(values)
            values = []
        values.sort()
        return [(v, l) for l, v in values]

    def trans_values(self, workspace):
        values = self.value
        if not self.multiple:
            values = [self.value]
        col = workspace.get_dataset()[self.name]
        values = [(col.do_outtrans(v), encode_val(v)) for v in values]
        values.sort()
        return [(v, l) for l, v in values]

    def __nonzero__(self):
        return len(self) > 0

    def __len__(self):
        if self.multiple:
            return len(self.value)
        elif self.value is None:
            return 0
        else:
            return 1

    def pretty_value(self, workspace):
        values = self.value
        if not self.multiple:
            values = [self.value]
        col = workspace.get_dataset()[self.name]
        return ', '.join([shorten_trans(col, v) for v in values])

    def op_add(self, workspace, value):
        v = decode_val(value)
        if self.multiple:
            if v not in self.value:
                self.value.append(v)
        else:
            self.value = v

    def op_del(self, workspace, value):
        assert self.multiple
        try:
            self.value.remove(decode_val(value))
        except ValueError:
            pass

    def op_all(self, workspace, value):
        assert self.multiple
        for v, l in self.search(workspace):
            self.value.append(decode_val(v))

    def op_none(self, workspace, value):
        assert self.multiple
        self.value = []

    def op_clr(self, workspace, value):
        self.search_pat = ''
        self.errorstr = ''

    def sop(self, workspace, op, field):
        meth = getattr(self, 'op_' + op)
        return meth(workspace, field)
        
    def as_pytypes(self, workspace):
        col = workspace.get_dataset()[self.name]
        if self.multiple:
            values = []
            for value in self.value:
                values.append(to_datatype(col, value))
            return tuple(values)
        else:
            assert type(self.value) not in (tuple, list)
            return to_datatype(col, self.value)
