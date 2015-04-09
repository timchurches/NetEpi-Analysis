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
# $Id: twobytwoparams.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/twobytwoparams.py,v $

import copy
import sets
import fnmatch
import SOOMv0
from libsoomexplorer.common import *
from libsoomexplorer import colvals


def short_desc(col, values):
    limit = 200
    desc = []
    length = 0
    for value in values:
        value = colvals.shorten_trans(col, value)
        length += len(value)
        desc.append(value)
        if length > limit:
            break
    remaining = len(values) - len(desc)
    if remaining:
        desc.append('and %d more ...' % remaining)
    return ', '.join(desc)


class TwoByTwoColParams:
    too_many_results = 200

    def __init__(self, label):
        self.label = label
        self.colname = None
        self.saved = None
        self.clear()

    def clear(self, colname=None):
        self.colname = colname
        self.positive_label = self.label.capitalize()
        self.negative_label = 'Not ' + self.label
        self.inc = []
        self.low_cardinality = False
        self.high_cardinality = False
        self.cardinality = 0
        self.clear_search()

    def _get_values(self, col):
        return [value
                for value, rows in col.inverted.items()
                if value is not None and len(rows) > 0]

    def _get_positive(self, col):
        inc = sets.Set(self.inc)
        return [v for v in self._get_values(col) if str(v) in inc]

    def _get_negative(self, col):
        inc = sets.Set(self.inc)
        return [v for v in self._get_values(col) if str(v) not in inc]

    def get_col(self, workspace):
        return workspace.get_filtered_dataset()[self.colname]

    def set_colname(self, workspace, colname):
        if colname != self.colname:
            self.clear(colname)
            col = self.get_col(workspace)
            values = self._get_values(col)
            values.sort()
            self.cardinality = len(values)
            if self.cardinality < 2:
                self.low_cardinality = True
            elif self.cardinality == 2:
                if col.do_format(col.do_outtrans(values[0])).lower() in ('yes', 'positive'):
                    i = 0
                else:
                    i = 1
                self.inc = [str(values[i])]
                self.positive_label = col.do_outtrans(values[i])
                self.negative_label = col.do_outtrans(values[not i])
            elif self.cardinality > 30:
                self.high_cardinality = True

    def is_okay(self):
        return len(self.inc) > 0 and len(self.inc) < self.cardinality

    def desc_positive(self, workspace):
        col = self.get_col(workspace)
        return short_desc(col, self._get_positive(col))

    def desc_negative(self, workspace):
        col = self.get_col(workspace)
        return short_desc(col, self._get_negative(col))

    def options(self, workspace):
        col = self.get_col(workspace)
        return [(v, col.do_outtrans(v)) for v in self._get_values(col)]

    def inc_options(self, workspace):
        col = self.get_col(workspace)
        return [(v, col.do_outtrans(v)) for v in self._get_positive(col)]

    def result_options(self, workspace):
        col = self.get_col(workspace)
        return [(v, col.do_outtrans(v)) for v in self.result]

    def do_res(self, ctx, op, collection):
        col = self.get_col(ctx.locals.workspace)
        inc = sets.Set(self.inc)
        if collection == 'checked':
            collection = sets.Set(self.result_inc)
        else:
            collection = sets.Set([str(v) for v in self.result])
        if op == 'add':
            inc |= collection
        else:
            inc -= collection
        self.inc = list(inc)

    def do_swap(self, ctx):
        col = self.get_col(ctx.locals.workspace)
        self.inc = self._get_negative(col)
        self.negative_label, self.positive_label = \
            self.positive_label, self.negative_label

    def do_clear(self, ctx):
        colname = self.colname
        self.clear()
        self.set_colname(ctx.locals.workspace, colname)

    def get_map(self, workspace):
        if self.colname is None:
            return {}
        col = self.get_col(workspace)
        positive = []
        negative = []
        ignore = []
        for value, rows in col.inverted.items():
            if value is None or len(rows) == 0:
                ignore.append(value)
            elif str(value) in self.inc:
                positive.append(value)
            else:
                negative.append(value)
        if not positive:
            raise UIError('%s: at least one value must be selected' %
                          self.positive_label)
        if not negative:
            raise UIError('%s: at least one value must be selected' %
                          self.negative_label)
        param_map = {
            self.colname: (
                SOOMv0.coalesce(positive, value=-2, label=self.positive_label),
                SOOMv0.coalesce(negative, value=-1, label=self.negative_label),
                SOOMv0.suppress(ignore),
                SOOMv0.order(-2),
            )
        }
        return param_map

    def clear_search(self):
        self.pattern = None
        self.result_inc = []
        self.result = []
        self.search_error = ''

    def do_search_clear(self, ctx):
        self.clear_search()

    def search(self, workspace):
        col = self.get_col(workspace)
        self.result = []
        self.search_error = ''
        if self.pattern:
            pattern = colvals.make_re(self.pattern)
            for v in self._get_values(col):
                if self.pattern == str(v):
                    self.result.append(v)
                if pattern.match(str(col.do_outtrans(v))):
                    self.result.append(v)
            if not self.result:
                self.search_error = 'No matches'
            elif len(self.result) > self.too_many_results:
                self.search_error = 'Too many matches (%d)' % len(self.result)
                self.result = []
            self.result.sort()


    def save_undo(self):
        self.saved = self.inc, self.positive_label, self.negative_label
        self.inc = self.inc[:]

    def clear_undo(self):
        self.saved = None

    def undo(self):
        if self.saved is not None:
            self.inc, self.positive_label, self.negative_label = self.saved
            self.saved = None

