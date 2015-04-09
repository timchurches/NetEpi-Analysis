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
# $Id: table.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/output/table.py,v $

import MA

from libsoomexplorer.output.base import OutputBase

class AxisBase(object):
    __slots__ = 'label', 'span', 'total'

    def __init__(self, label, span, total = False):
        self.label, self.span, self.total = label, span, total

    def __repr__(self):
        return '<label %r, span %s>' % (self.label, self.span)
    
class AxisHeader(AxisBase):
    __slots__ = ()
    markup = 'label'

class AxisLabel(AxisBase):
    __slots__ = ()
    markup = 'value'

class HeaderLevelBase:
    def __init__(self, col, prev, mt_lead = False):
        self.next = None
        if prev:
            prev.next = self
        self.col = col
        self.values = col.inverted.keys()
        if col.is_ordered():
            self.values.sort()
        if col.all_value is not None:
            # Move all_value to end of list
            try:
                self.values.remove(col.all_value)
                if mt_lead:
                    self.values.insert(0, col.all_value)
                else:
                    self.values.append(col.all_value)
            except ValueError:
                pass

    def get_values(self):
        """ enumerate all values below this node """
        if self.next:
            sub_values = self.next.get_values()
            return [(v,) + sv for v in self.values for sv in sub_values]
        else:
            return [(v,) for v in self.values]

    def span(self):
        span = len(self.values)
        if self.next:
            span *= self.next.span()
        return span

class BannerLevel(HeaderLevelBase):
    """
    This represents one level in the hierarchial column banner -
    a linked list of these objects is used to represent the whole
    banner (strictly, it's a tree, but sub-nodes are simply repeated
    """
    def get_col_headers(self):
        headings = []
        sub_span = 1
        if self.next:
            sub_span = self.next.span()
        headings.append((AxisHeader(self.col.label, sub_span * len(self.values)),))
        labels = []
        for v in self.values:
            strvalue = self.col.do_format(self.col.do_outtrans(v))
            labels.append(AxisLabel(strvalue, sub_span))
        headings.append(labels)
        if self.next:
            for sh in self.next.get_col_headers():
                headings.append(sh * len(self.values))
        return headings

    def get_tot_flags(self):
        if self.next:
            return self.next.get_tot_flags() * len(self.values)
        return [v == self.col.all_value for v in self.values]

class StubLevel(HeaderLevelBase):
    """
    Thios represents on level in the hierarchial row banner -
    a linked list of these objects is used to represent the whole
    banner (strictly, it's a tree, but sub-nodes are simply repeated
    """
    def get_row_headers(self):
        label = AxisHeader(self.col.label, 1)
        if self.next:
            return (label,) + self.next.get_row_headers()
        else:
            return (label,)

    def get_row_labels(self):
        """
        Returns a list of tuples of AxisLabel instances, each
        tuple representing a row in the output table. The AxisLabel
        instances know the appropriate rowspan (and None is used
        where no table element should be generated.
        """
        headings = []
        sub_headings = [()]
        sub_span = 1
        if self.next:
            sub_headings = self.next.get_row_labels()
            sub_span = self.next.span()
        for v in self.values:
            for sh in sub_headings:
                axisvalue = None
                if sh is sub_headings[0]:
                    strvalue = self.col.do_format(self.col.do_outtrans(v))
                    axisvalue = AxisLabel(strvalue, sub_span,
                                          self.col.all_value == v)
                headings.append((axisvalue,) + sh)
        return headings

    def get_lv_headings(self):
        """
        Similar to get_row_labels, but includes row headers elements
        inline - not currently used.
        """
        headings = []
        sub_headings = [()]
        sub_span = 1
        if self.next:
            sub_headings = self.next.get_lv_headings()
            sub_span = self.next.span()
        span = sub_span * len(self.values)
        for v in self.values:
            for sh in sub_headings:
                a = b = None
                if sh is sub_headings[0]:
                    strvalue = self.col.do_format(self.col.do_outtrans(v))
                    b = AxisLabel(strvalue, sub_span)
                    if v is self.values[0]:
                        a = AxisHeader(self.col.label, span)
                headings.append((a, b) + sh)
        return headings

class HeaderBase:
    def __init__(self, summset, colnames, mt_lead = False):
        self.axislabels = None
        self.len = len(colnames)
        axislabel = None
        for col in summset.get_columns(colnames):
            axislabel = self.axis_level_class(col, axislabel, mt_lead)
            if not self.axislabels:
                self.axislabels = axislabel
        self.values = self.axislabels.get_values()

    def __len__(self):
        return self.len

class Banner(HeaderBase):
    axis_level_class = BannerLevel
    
    def __init__(self, summset, colnames, mt_lead):
        HeaderBase.__init__(self, summset, colnames, mt_lead)
        self.header_and_values = zip(self.axislabels.get_tot_flags(), 
                                     self.values)

    def get_col_headers(self):
        return self.axislabels.get_col_headers()

    def col_group_count(self):
        axislabel = self.axislabels
        count = 1
        while axislabel:
            if axislabel.next:
                count *= len(axislabel.values)
            else:
                return [len(axislabel.values)] * count
            axislabel = axislabel.next

class Stub(HeaderBase):
    axis_level_class = StubLevel

    def grouped_rows(self):
        if self.len == 1:
            return [zip(self.get_row_labels(), self.values)]
        last = None
        groups = []
        group = []
        for labels, row_values in zip(self.get_row_labels(), self.values):
            if row_values[:-1] != last:
                last = row_values[:-1]
                if group:
                    groups.append(group)
                group = []
            group.append((labels, row_values))
        if group:
            groups.append(group)
        return groups
                
    def get_lv_headings(self):
        return self.axislabels.get_lv_headings()

    def get_row_headers(self):
        return self.axislabels.get_row_headers()

    def get_row_labels(self):
        return self.axislabels.get_row_labels()

class TableOutBase(OutputBase):
    def __init__(self):
        super(TableOutBase, self).__init__()
        self.summaryset = None
        self.inline = True
        self.title = ''
        self.subtitle = ''

    def clear(self):
        self.summaryset = None


class CrosstabOut(TableOutBase):
    markup = 'crosstab'

    def __init__(self):
        super(CrosstabOut, self).__init__()
        self.proptype = 'density'

    def go(self, summaryset, rowcols, colcols, statcols, propcols, 
           marginal_totals='none', show_limits=False, rounding=None,
           simple_table=False):
        self.summaryset = summaryset
        self.rowcols = rowcols
        self.colcols = colcols
        self.statcols = statcols
        self.propcols = propcols
        self.marginal_totals = marginal_totals
        self.show_limits = show_limits
        self.rounding = rounding
        self.simple_table = simple_table
        mt_lead = (marginal_totals == 'before')
        assert rowcols
        assert colcols
        self.row_axis = Stub(self.summaryset, rowcols, mt_lead)
        self.col_axis = Banner(self.summaryset, colcols, mt_lead)
        self.value_to_rownum_map = self.make_condcol_index(summaryset,
                                                           rowcols + colcols)

    def get_rownum(self, row_values, col_values):
        return self.value_to_rownum_map[tuple(row_values + col_values)]

    def make_condcol_index(self, summset, colnames):
        valuemap = [[] for i in xrange(len(summset))]
        for col in summset.get_columns(colnames):
            for value, rows in col.inverted.iteritems():
                for row in rows:
                    valuemap[row].append(value)
        return dict([(tuple(v), i) for i, v in enumerate(valuemap)])

    def colours(self, v):
        colmap = ['#ffc6c6', '#ffd2c6', '#ffddc6', '#ffe8c6', '#fff3c6', 
                  '#ffffc6', '#f3ffc6', '#e8ffc6', '#ddffc6', '#d2ffc6', 
                  '#c6ffc6', '#c6ffd2', '#c6ffdd', '#c6ffe8', '#c6fff3', 
                  '#c6ffff', '#c6f3ff', '#c6e8ff', '#c6ddff', '#c6d2ff']
        if type(v) is MA.MaskedScalar:
            return '#ffffff'
        return colmap[int(round((1-v) * (len(colmap) - 1)))]

    def format_cell(self, colname, index):
        col = self.summaryset[colname]
        data = col.data[index]
        if type(data) is MA.MaskedScalar:
            return '--'
        if self.rounding is None:
            fmt = col.do_format
        else:
            def fmt(v):
                if type(v) is MA.MaskedScalar:
                    return '--'
                if self.rounding < 1:
                    try:
                        return '%d' % round(v, self.rounding)
                    except:
                        print repr(v), type(v)
                        raise
                else:
                    return '%.*f' % (self.rounding, v)
        if self.show_limits:
            try:
                ul = self.summaryset[colname + '_ul'].data[index]
                ll = self.summaryset[colname + '_ll'].data[index]
            except KeyError:
                pass
            else:
                return '%s (%s..%s)' % (fmt(data).strip(), 
                                        fmt(ll).strip(), fmt(ul).strip())
        return fmt(data)

    def propn2perc(self, v):
        if type(v) is MA.MaskedScalar:
            return '--'
        return '%.1f%%' % (v * 100)


class TableOut(TableOutBase):
    markup = 'tableout'

class DatasetRowsOut(TableOutBase):
    markup = 'dsrows'

    def clear(self):
        self.dsrows = None
