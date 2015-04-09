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
# $Id: condcol.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/condcol.py,v $

import sets
import copy
import fnmatch
from libsoomexplorer.common import *
from libsoomexplorer import colvals

class _ValSelectBase(colvals.ColValSelect):
    param_ctor = None

    def to_param(self, workspace, params):
        values = self.as_pytypes(workspace)
        if values:
            params.insert(0, self.param_ctor(values))


class _SuppressVals(_ValSelectBase):
    op = 'suppress'
    param_ctor = SOOMv0.suppress

class _RetainVals(_ValSelectBase):
    op = 'retain'
    param_ctor = SOOMv0.retain

class _CoalesceVals(_ValSelectBase):
    op = 'coalesce'
    param_ctor = SOOMv0.coalesce

    def __init__(self, name, values, label, ignore_vals, idx=None):
        self.label = label
        self.idx = idx
        _ValSelectBase.__init__(self, name, values, ignore_vals)

    def to_param(self, workspace, params):
        values = self.as_pytypes(workspace)
        param = self.param_ctor(values, label=self.label)
        if self.idx is None:
            if values:
                params.append(param)
        else:
            if values:
                params[self.idx] = param
            else:
                del params[self.idx]


class _ColParams:
    _ops = _SuppressVals, _RetainVals, _CoalesceVals
    op_map = dict([(m.op, m) for m in _ops])

    def __init__(self, name, label, params):
        self.name = name
        self.label = label
        self.edit = None
        self.params = params

    def __cmp__(self, other):
        return cmp(self.label, other.label)

    def __repr__(self):
        return 'colparams(%r, edit=%s, %r)' %\
            (self.name, bool(self.edit), self.params)

    def describe(self, workspace):
        col = workspace.get_dataset()[self.name]
        res = []
        for param in self.params:
            s = ', '.join([colvals.shorten_trans(col, v) for v in param.values])
            label = getattr(param, 'label', None)
            if label:
                s = '%r: %s' % (label, s)
            res.append((param.__class__.__name__, s))
        return res

    def do_clear(self, workspace):
        self.params = []

    def _single(self, workspace, cls):
        values = []
        params = []
        for param in self.params:
            if not isinstance(param, (SOOMv0.suppress, SOOMv0.retain)):
                params.append(param)
            if isinstance(param, cls.param_ctor):
                values.extend(param.values)
        self.params = params
        self.edit = cls(self.name, values)

    def do_suppress(self, workspace):
        self._single(workspace, _SuppressVals)

    def do_retain(self, workspace):
        self._single(workspace, _RetainVals)

    def do_coalesce(self, workspace, idx=None):
        ignore_vals = sets.Set()
        for param in self.params:
            if isinstance(param, SOOMv0.coalesce):
                ignore_vals.union_update(param.values)
        if not idx:
            self.edit = _CoalesceVals(self.name, [], '', ignore_vals)
        else:
            idx = int(idx)
            param = self.params[idx]
            ignore_vals.difference_update(param.values)
            self.edit = _CoalesceVals(self.name, param.values, param.label, 
                                      ignore_vals, idx)

    def do_del(self, workspace, idx):
        idx = int(idx)
        del self.params[idx]

    def maybe_search(self, workspace):
        if self.edit is not None:
            return self.edit.search(workspace)
        return []

    def done_edit(self, workspace):
        if self.edit is not None:
            self.edit.to_param(workspace, self.params)
            self.edit = None


class CondColParams:
    inhibit_suppress = False

    def __init__(self, workspace, param_map, condcols):
        self.edit_col = None
        ds = workspace.get_dataset()
        self.init_cols(ds, condcols, param_map)

    def init_cols(self, ds, colnames, param_map):
        self.cols = []
        for colname in colnames:
            col = ds[colname]
            if col.is_discrete():
                self.cols.append(self.new_colparam(col, param_map))
        self.cols.sort()

    def new_colparam(self, col, param_map):
        return _ColParams(col.name, col.label, param_map.get(col.name, []))

    def __getitem__(self, i):
        return self.cols[i]

    def __len__(self):
        return len(self.cols)

    def clear(self, workspace):
        self.done_edit(workspace)
        for col in self.cols:
            col.do_clear(workspace)

    def do_col(self, workspace, op, colname, *args):
        self.done_edit(workspace)
        for col in self.cols:
            if col.name == colname:
                break
        else:
            return
        col_op = getattr(col, 'do_' + op)
        col_op(workspace, *args)
        self.edit_col = col

    def done_edit(self, workspace):
        if self.edit_col is not None:
            self.edit_col.done_edit(workspace)
            self.edit_col = None

    def maybe_search(self, workspace):
        if self.edit_col is not None:
            return self.edit_col.maybe_search(workspace)
        return []

    def get_map(self, workspace):
        self.done_edit(workspace)
        param_map = {}
        for col in self.cols:
            params = [p for p in col.params if p.values]
            if params:
                param_map[col.name] = params
        return param_map


class StratifyParams(CondColParams):
    inhibit_suppress = True

    def __init__(self, workspace, param_map, condcols):
        self.edit_col = None
        ds = workspace.get_dataset()
        self.init_cols(ds, condcols[2:], param_map)
