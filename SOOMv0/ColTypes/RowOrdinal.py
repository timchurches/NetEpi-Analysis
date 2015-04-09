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
# $Id: RowOrdinal.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/ColTypes/RowOrdinal.py,v $

import itertools

import Numeric

from SOOMv0.ColTypes.base import SimpleDatasetColumnBase

class _RowOrdinalColumn(SimpleDatasetColumnBase):
    coltype = 'ordinal'

    def __init__(self, parent_dataset):
        SimpleDatasetColumnBase.__init__(self, parent_dataset, 'row_ordinal', 
                                         label='Ordinal', datatype='int')

    def is_numerictype(self):
        return True

    def is_ordered(self):
        return True

    def op_less_than(self, value, filter_keys):
        return Numeric.arrayrange(value)

    def op_less_equal(self, value, filter_keys):
        return Numeric.arrayrange(value+1)

    def op_greater_than(self, value, filter_keys):
        return Numeric.arrayrange(value+1, len(self))

    def op_greater_equal(self, value, filter_keys):
        return Numeric.arrayrange(value, len(self))

    def op_equal(self, value, filter_keys):
        return [value]

    def op_between(self, value, filter_keys):
        return Numeric.arrayrange(*value)

    def op_in(self, value):
        return value


class RowOrdinalColumn(_RowOrdinalColumn):
    """
    The row_ordinal column contains the record number of the row by
    convention. For continuous datasets (an example of non-continuous
    datasets are the results of a filter), the data is synthersized
    on demand.
    """
    def __len__(self):
        return len(self.parent_dataset)

    def get_data(self):
        return self
    data = property(get_data)

    def __iter__(self):
        return iter(xrange(len(self.parent_dataset)))

    def __getitem__(self, i):
        if type(i) is slice:
            start, stop, stride = i.indices(len(self.parent_dataset))
            if stride > 1:
                return Numeric.arrayrange(start, stop, stride)
            else:
                return Numeric.arrayrange(start, stop)
        else:
            if i < len(self.parent_dataset):
                return i
            raise IndexError

    def take(self, rows):
        return rows

class FilteredRowOrdinalColumn(_RowOrdinalColumn):
    coltype = 'ordinal'

    def __init__(self, parent_dataset, record_ids):
        _RowOrdinalColumn.__init__(self, parent_dataset)
        self.data = record_ids

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, i):
        return self.data[i]
        
    def take(self, rows):
        return Numeric.take(self.data, rows)
