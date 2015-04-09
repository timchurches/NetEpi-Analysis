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
import time
import sets
import itertools
import Numeric, MA
from SOOMv0.common import *
from SOOMv0.Soom import soom
from SOOMv0.BaseDataset import BaseDataset

def fully_masked(shape, typecode='i'):
    return MA.array(Numeric.empty(shape, typecode=typecode),
                    mask=Numeric.ones(shape, typecode='b', savespace=1))

def sum_axis(data, axis):
    # We cast to float to avoid integer overflow
    data = data.astype(Numeric.Float64)
    return MA.add.reduce(data, axis)

def replicate_axis(data, axis, size):
    """
    Returns a new array with an additional axis of the specified size.

    The new axis is formed by replicating along the other axes.
    """
    assert axis > 0
    repeat_map = size * Numeric.ones(data.shape[axis-1])
    shape = list(data.shape)
    data = MA.repeat(data, repeat_map, axis=axis-1)
    shape.insert(axis, size)
    data.shape = tuple(shape)
    return data

class CrossTabAxis:
    def __init__(self, name, label, values=None, col=None):
        self.name = name
        self.label = label
        if values is not None:
            self.values = values
        self.col = col

    def from_col(cls, col, values=None):
        self = cls(col.name, col.label, col=col)
        if values is not None:
#            this_values = sets.Set(col.inverted.keys())
#            wanted_values = sets.Set(values)
#            if not wanted_values.issubset(this_values):
#                missing_vals = [repr(v) for v in (wanted_values - this_values)]
#                raise Error('column %r values mismatch - %r' %
#                            (self.name, ', '.join(missing_vals)))
            self.values = values
        else:
            self.values = col.inverted.keys()
            self.values.sort()
        self.indices = fully_masked(len(col))
        if 0:
            # AM - the .inverted attribute of filtered datasets is returning
            # invalid row indices, and the summ code relies on these indices,
            # so the following code cannot be used until they are fixed.
            self.axis_map = {}
            for i, v in enumerate(self.values):
                self.axis_map[v] = i
                vec = col.inverted.get(v)
                if vec is not None:
                    for idx in vec:
                        try:
                            self.indices[idx] = i
                        except IndexError:
                            print col.name, idx
                            raise
                    MA.put(self.indices, vec, i)
        else:
            axis_map = dict([(v, i) for i, v in enumerate(self.values)])
            for i, v in enumerate(col.data):
                try:
                    self.indices[i] = axis_map[v]
                except KeyError:
                    pass
            self.axis_map = axis_map
        return self
    from_col = classmethod(from_col)

    def copy(self):
        return self.__class__(self.name, self.label, self.values, self.col)

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def __repr__(self):
        lines = []
        lines.append('Axis name: %r, label: %r' % (self.name, self.label))
        if hasattr(self, 'axis_map'):
            for value in self.values:
                lines.append('    %5r: %5r: %s' % (self.axis_map[value], value, 
                                                self.col.do_outtrans(value)))
        else:
            lines.append(repr(self.values))
        lines.append('')
        return '\n'.join(lines)

class CrossTabData:
    def __init__(self, name, data=None, label=None):
        self.name = name
        self.data = data
        self.label = label

def xtab_axes(xtab_or_axes):
    if isinstance(xtab_or_axes, CrossTab):
        return xtab_or_axes.axes
    elif hasattr(xtab_or_axes, 'get_columns'):
        return [CrossTabAxis.from_col(col)
                for col in xtab_or_axes.get_columns()
                if not col.name.startswith('_') and col.is_discrete()]
    else:
        return xtab_or_axes

def dims(xtab_or_axes):
    return tuple([len(s) for s in xtab_axes(xtab_or_axes)])

def shape_union(a, b):
    a = xtab_axes(a)
    b = xtab_axes(b)
    b_remainder = list(b)
    a_remainder = []
    common = []
    for a_axis in a:
        for b_axis in b:
            if a_axis.name == b_axis.name:
                if a_axis.values != b_axis.values:
                    raise Error('%s column values not compatible: %r vs %r' %
                                (a_axis.name, a_axis.values, b_axis.values))
                b_remainder.remove(b_axis)
                common.append(a_axis.copy())
                break
        else:
            a_remainder.append(a_axis.copy())
    b_remainder = [b_axis.copy() for b_axis in b_remainder]
    return a_remainder + common + b_remainder

class CrossTab:
    """
    The CrossTab class provides an alternate N-dimensional array
    representation of summary datasets.
    """
    def __init__(self, name=None):
        self.name = name
        self.table_dict = {}
        self.table_order = []
        self.axes = []

    def from_summset(cls, ds, shaped_like=None):
        self = cls(ds.name)
        st = time.time()
        cols = ds.get_columns()
        if shaped_like is not None:
            for axis in xtab_axes(shaped_like):
                try:
                    col = ds[axis.name]
                except KeyError:
                    pass
                else:
                    self.axes.append(CrossTabAxis.from_col(col, axis.values))
                    cols.remove(col)
        for col in cols:
            if col.is_discrete() and not col.name.startswith('_'):
                self.axes.append(CrossTabAxis.from_col(col))
        if not self.axes:
            raise Error('dataset %r must have at least one discrete column' % 
                        (ds.name,))
        indices = [axis.indices.filled() for axis in self.axes]
        masks = [axis.indices.mask() for axis in self.axes]
        map = MA.transpose(MA.array(indices, mask=masks))
        shape = self.get_shape()
        for col in ds.get_columns():
            if col.is_scalar():
                self.add_table(col.name, 
                               data=self.from_vector(map, col.data, shape),
                               label=col.label)
        elapsed = time.time() - st
        soom.info('%r crosstab generation took %.3f, %.1f rows/s' % 
                    (self.name, elapsed, len(map) / elapsed))
        return self
    from_summset = classmethod(from_summset)

    def to_summset(self, name, **kwargs):
        ds = BaseDataset(name, summary=True, **kwargs)
        axes = self.axes[:]
        axes.reverse()
        colsdata = []
        colsindex = []
        colslen = 1
        for axis in axes:
            data = []
            index = []
            datalen = len(axis.values)
            for i, value in enumerate(axis.values):
                data.extend([value] * colslen)
                index.extend([i] * colslen)
            colsdata = [coldata * datalen for coldata in colsdata]
            colsindex = [colindex * datalen for colindex in colsindex]
            colsdata.append(data)
            colsindex.append(index)
            colslen *= datalen
        colsdata.reverse()
        colsindex.reverse()
        map = zip(*colsindex)
        for data, axis in zip(colsdata, self.axes):
            col = axis.col
            # This nonsense needs to be replaced with a common way of
            # extracting column metadata.
            ds.addcolumnfromseq(axis.name, data=data, label=axis.label, 
                                coltype=col.coltype, datatype=col.datatype.name,
                                outtrans=col.outtrans, 
                                use_outtrans=col.use_outtrans,
                                format_str=col.format_str, 
                                all_value=col.all_value)
        for table in self.tables():
            ds.addcolumnfromseq(table.name, 
                                data=self.to_vector(map, table.data),
                                label=table.label, 
                                coltype='scalar', datatype='float')
        return ds

    def empty_copy(self):
        """Returns an empty crosstab with the same shape"""
        crosstab = self.__class__()
        crosstab.axes = list(self.axes)
        return crosstab

    def get_shape(self):
        return dims(self)

    def from_vector(self, map, data, shape):
        table = fully_masked(shape, typecode=data.typecode())
        for idx, v in itertools.izip(map, data):
            if not Numeric.sometrue(idx.mask()):
                table[idx] = v
        return table

    def to_vector(self, map, table):
        size = Numeric.multiply.reduce(self.get_shape())
        if size != len(map):
            raise AssertionError('size/shape %r/%d != map len %d' % 
                                 (self.get_shape(), size, len(map)))
        v = fully_masked(size, typecode=table.typecode())
        for i, idx in enumerate(map):
            v[i] = table[idx]
        return v

    def collapse_axes_not_in(self, shaped_like):
        """
        This method summs frequency columns along any axes not
        appearing in the target dataset.
        """
        foreign_axes = xtab_axes(shaped_like)
        i = 0
        while i < len(self.axes):
            if (i < len(foreign_axes) 
                and self.axes[i].name == foreign_axes[i].name):
                i += 1
            else:
                if len(self.axes) == 1:
                    raise Error('crosstab %r: cannot collapse last axis: %r' %
                                (self.name, self.axes[i].name))
                del self.axes[i]
                for table in self.tables():
                    table.data = sum_axis(table.data, i)

    def replicate_axes(self, shaped_like):
        for i, foreign_axis in enumerate(xtab_axes(shaped_like)):
            if i == len(self.axes) or self.axes[i].name != foreign_axis.name:
                self.axes.insert(i, foreign_axis.copy())
                for table in self.tables():
                    table.data = replicate_axis(table.data,i,len(foreign_axis))
        assert dims(self) == dims(shaped_like)

    def __getitem__(self, key):
        return self.table_dict[key]

    def add_table(self, name, data, label=None):
        shape = self.get_shape()
        assert shape == data.shape, 'data shape %r != crosstab shape %r' %\
                                    (data.shape, shape)
        table = CrossTabData(name, data, label)
        self.table_dict[name] = table
        self.table_order.append(table)

    def tables(self):
        return self.table_order

    def _display_hook(self):
        res = []
        res.append('Axes')
        for i, axis in enumerate(self.axes):
            res.append('%3d:%s' % (i, axis.label))
        for table in self.tables():
            res.append(table.label or 'None')
            lines = str(table.data).split('\n')
            for line in lines:
                res.append('  ' + line)
        print '\n'.join(res)

if __name__ == '__main__':
    from SOOMv0 import datasets

    ds = datasets.dsload('nhds', path='/usr/src/oc/health/SOOM_objects_real')
    s = ds.summ('agegrp', 'sex')
    t = CrossTab(s)
