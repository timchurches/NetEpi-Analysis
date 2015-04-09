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
# $Id: workspace.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/workspace.py,v $

from time import time
import SOOMv0
from libsoomexplorer import plottypes
from libsoomexplorer.dsparams import DSParams
from libsoomexplorer.output.base import NullOut, OutputError
from libsoomexplorer.output.plot import ImageOut
from libsoomexplorer.output.table import TableOut, CrosstabOut, DatasetRowsOut
from libsoomexplorer.output.twobytwo import TwoByTwoOut

# AM - debugging aid: reraise exceptions that would otherwise be "pretty
# printed" so tracebacks can be seen.
reraise = False


class Parameters:
    """
    A container for plot parameters
    """
    def set_default(self, attr, value):
        """Set an attribute if it doesn't already exist"""
        if not hasattr(self, attr):
            setattr(self, attr, value)

    def do_condcoladd(self, ctx, field):
        getattr(self, field).append(None)
        
    def do_condcoldel(self, ctx, field, index):
        del getattr(self, field)[int(index)]

    def do_statcoladd(self, ctx, field):
        getattr(self, field).append([None, None, None])

    def do_statcoldel(self, ctx, field, index):
        del getattr(self, field)[int(index)]

    def do_filter(self, ctx, op, field, *args):
        getattr(getattr(self, field), 'do_' + op)(ctx, *args)

    def is_sys(self, field):
        """
        "sys" fields know whether they've been set by the user or
        set to a default by the system.
        """
        value = getattr(self, field, None)
        if not value: 
            return True
        return value.replace('\r', '') == getattr(self, '_sys_' + field, None)

    def set_sys(self, field, value):
        setattr(self, field, value)
        setattr(self, '_sys_' + field, value)


class Timer:
    def __init__(self):
        self.last_t = None
        self.times = []
        self.last_name = None

    def _flush(self, now):
        if self.last_name:
            self.times.append((self.last_name, now - self.last_t))
            self.last_name = None

    def __len__(self):
        self._flush(time())
        return len(self.times)

    def start(self, name):
        now = time()
        self._flush(now)
        self.last_name = name
        self.last_t = now

    def end(self):
        self._flush(time())
        return self.times


class Workspace:
    def __init__(self):
        self.dsname = None
        self.last_dsname = None
        self.plottype = None
        self.plottype_name = None
        self.last_plottype_name = None
        self.errorstr = ''
        self.outputs = {
            'image': ImageOut(),
            'table': TableOut(),
            'crosstab': CrosstabOut(),
            'dsrows': DatasetRowsOut(),
            'twobytwo': TwoByTwoOut(),
        }
        self.output = NullOut()
        self.clear_params()

    def clear_params(self):
        self.params = Parameters()
        if self.plottype:
            self.plottype.set_default()
        self.params.dsparams = DSParams(self.dsname)

    def available_datasets(self, filter=None):
        datasets = [SOOMv0.dsload(dsname) 
                    for dsname in SOOMv0.soom.available_datasets()]
        labels = [(ds.label, ds.name) 
                  for ds in datasets
                  if filter is None or filter(ds, self)]
        labels.sort()
        return [(n, l) for l, n in labels]

    def get_dataset(self):
        return SOOMv0.dsload(self.dsname)

    def get_filtered_dataset(self):
        return self.params.dsparams.get_filtered_dataset()

    def get_dataset_cols(self):
        ds = self.get_dataset()
        cols = ds.get_columns()
        cols = [(col.label, i, col) for i, col in enumerate(cols)]
        cols.sort()
        return [col[2] for col in cols]

    def get_dataset_meta(self):
        return self.get_dataset().describe(SOOMv0.SOME_DETAIL).describe_tuples()

    def get_column_meta(self, colname):
        return self.get_dataset().get_column(colname).describe(SOOMv0.SOME_DETAIL).describe_tuples()


    def available_plottypes(self):
        return [(p.name, p.label) for p in plottypes.plottypes]

    def set_dsname(self):
        if self.dsname != self.last_dsname:
            self.last_dsname = self.dsname
            self.errorstr = ''
            ds = self.get_dataset()
            self.dslabel = ds.label
            self.params.dsparams.set_dsname(self.dsname)
            if self.plottype is not None:
                self.plottype.set_default()
            return True
        return False

    def set_plottype(self):
        if self.last_plottype_name != self.plottype_name:
            for plottype in plottypes.plottypes:
                if self.plottype_name == plottype.name:
                    break
            else:
                raise ValueError('bad plottype_name')
            self.output.clear()
            self.plottype = plottype(self)
            self.last_plottype_name = self.plottype_name
            self.plottype.set_default()
            return True
        return False

    def get_condcolparams(self):
        return self.plottype.get_condcolparams(self)

    def set_outtype(self, outtype):
        self.output = self.outputs[outtype]

    def refresh(self):
        try:
            self.timer = Timer()
            self.plottype.refresh()
        except SOOMv0.ExpressionError, e:
            self.errorstr = 'Filter: %s' % e
            if reraise:
                raise
        except (OutputError, SOOMv0.Error), e:
            self.errorstr = str(e)
            if reraise:
                raise

    def go(self):
        try:
            start = time()
            self.output.clear()
            self.timer = Timer()
            self.plottype.go()
            self.output.elapsed = time() - start
            return True
        except SOOMv0.ExpressionError, e:
            self.errorstr = 'Filter: %s' % e
            if reraise:
                raise
#        except (OutputError, SOOMv0.Error), e:
#            self.errorstr = str(e)
        return False
