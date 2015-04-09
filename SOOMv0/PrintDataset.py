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
"""
Magic to take a dataset and pretty-print it in a form suitable for
a terminal device.
"""
# $Id: PrintDataset.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/PrintDataset.py,v $

import textwrap

from SOOMv0 import soom

__all__ = 'DSFormatter',

class ColFormatter:
    def __init__(self, col, low, high):
        col.load("data")
        # Format the column data as strings, determine if it should
        # be right or left justified, and the maximum column width
        self.right_just = col.is_numerictype()
        self.fmtrows = []
        for v in col[low:high]:
            v = col.do_outtrans(v)
            if self.right_just and type(v) in (str, unicode):
                self.right_just = False
            self.fmtrows.append(col.do_format(v))
        colwidth = 0
        if self.fmtrows:
            colwidth = max([len(v) for v in self.fmtrows])
        # Now format up the column label, attempting to minimise its
        # length, even if that means wrapping it over multiple rows
        labelwrap = textwrap.TextWrapper(width=max(colwidth, 16))
        self.labelrows = labelwrap.wrap(col.label or col.name)
        labelwidth = max([len(v) for v in self.labelrows])
        self.colwidth = max(colwidth, labelwidth)

    def insert_label_rows(self, label_row_count):
        # After we've collected all the columns, we work out how many
        # header rows will be required, then insert them before the data
        # rows.
        pad_needed = label_row_count - len(self.labelrows)
        rule = '-' * self.colwidth
        self.fmtrows[:0] = self.labelrows + [''] * pad_needed + [rule]

    def __getitem__(self, i):
        if self.right_just:
            return self.fmtrows[i].rjust(self.colwidth)
        else:
            return self.fmtrows[i].ljust(self.colwidth)

class DSFormatter:
    """
    Instances of this object are iterables that return pretty-printed
    dataset rows.
    """

    def __init__(self, ds, colnames=None, low=None, high=None): 
        if colnames is None:
            cols = ds.get_print_columns()
        else:
            cols = ds.get_columns(colnames)
        cols = [c for c in cols if c.name != 'row_ordinal']
        if soom.row_ordinals:
            cols.insert(0, ds.get_column('row_ordinal'))
        self.fmtcols = [ColFormatter(col, low, high) for col in cols]
        label_row_count = max([len(fmtcol.labelrows) 
                               for fmtcol in self.fmtcols])
        for fmtcol in self.fmtcols:
            fmtcol.insert_label_rows(label_row_count)

    def __iter__(self):
        rowcnt = min([len(colfmt.fmtrows) for colfmt in self.fmtcols])
        for rownum in xrange(rowcnt):
            row = [fmtcol[rownum] for fmtcol in self.fmtcols]
            yield '  '.join(row)
