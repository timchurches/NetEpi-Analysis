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
# $Id: Discrete.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/ColTypes/Discrete.py,v $

import time
import sets
import operator

import Numeric, MA
import soomfunc
from soomarray import ArrayDict
from SOOMv0.common import *
from SOOMv0.Soom import soom
from SOOMv0.ColTypes.base import DatasetColumnBase

class _DiscreteDatasetColumn(DatasetColumnBase):
    loadables = ['data', 'inverted']

    def __init__(self, parent_dataset, name, 
                 all_value=None, all_label=None, 
                 **kwargs):
        DatasetColumnBase.__init__(self, parent_dataset, name, **kwargs)
        self._inverted = {}
        if all_label is None:
            all_label = '<All>'
        self.all_label = all_label
        # the datatype of the value used to represent "all" must be
        # consistent with the datatype of the column...
        if all_value is None:
            self.all_value = self.datatype.default_all_value
        else:
            try:
                self.all_value = self.datatype.as_pytype(all_value)
            except (ValueError, TypeError):
                raise Error('The all_value given, %r, for column %s does not match datatype %s' % (all_value, self.name, self.datatype.name))

    def do_outtrans(self, v):
        try:
            if not isinstance(v, MA.MaskedScalar) and v == self.all_value:
                return self.all_label
        except:
            # mx.DateTime can raise mx.DateTime.Error here, sigh.
            pass
        return DatasetColumnBase.do_outtrans(self, v)

    def is_discrete(self):
        return True

    def cardinality(self):
        """Method to report the cardinality of a categorical column"""
        return len(self.inverted)

    def load_inverted(self):
        if self.parent_dataset.backed:
            if self._inverted is None:
                starttime = time.time()
                filename = self.object_path('SOOMblobstore', 'inverted')
                self._inverted = ArrayDict(filename, 'r')
                elapsed = time.time() - starttime
                soom.info('load of %r index took %.3f seconds.' %\
                            (self.name, elapsed))
        else:
            # we need to build the inverted index!
            self._build_inverted()

    def unload_inverted(self):
        self._inverted = None

    def get_inverted(self):
        if self._inverted is None:
            self.load_inverted()
        return self._inverted
    inverted = property(get_inverted)

    def _build_inverted(self):
        """
        Build an inverted index

        NOTE - This is now only used where there is no on-disk
        inverted index, but the column is discrete. For persistent
        discrete columns, the inverted index is built as the data
        is filtered, and the inverted index is saved along with
        the data.
        """
        starttime = time.time() # keep track of time
        inverted_dict = {}
        # Use fast NumPy methods if the column type is numeric
        if self.is_numerictype():
            # first get all the unique values
            uniquevalues = soomfunc.unique(Numeric.sort(self._data.compressed()))
            ordinals = Numeric.array(range(len(self._data)),
                                        typecode=Numeric.Int)
            for value in uniquevalues:
                inverted = Numeric.compress(Numeric.where(Numeric.equal(self._data,value),1,0),ordinals)
                inverted_dict[value] = inverted
        else:
            # loop over each element
            for rownum, value in enumerate(self._data):
                if type(value) is tuple:
                    for v in value:
                        row_nums = inverted_dict.setdefault(v, [])
                        row_nums.append(rownum)
                else:
                    row_nums = inverted_dict.setdefault(value, [])
                    row_nums.append(rownum)
            for value, row_nums in inverted_dict.iteritems():
                row_array = Numeric.array(row_nums, typecode=Numeric.Int)
                if self.datatype.name == 'tuple':
                    row_array = soomfunc.unique(Numeric.sort(row_array))
                inverted_dict[value] = row_array
        self._inverted = inverted_dict
        soom.info('Building inverted index for column %s in dataset %s took %.3f seconds' % (self.name, self.parent_dataset.name, time.time() - starttime))

    def _store_inverted(self, inverted=None):
        """
        Stores the passed inverted index as a memory-mapped dict
        of NumPy ID vectors
        """
        indexfilename = None
        inverted_blob = {}
        if self.parent_dataset.backed:
            indexfilename = self.object_path('SOOMblobstore', 'inverted',
                                             mkdirs=True)
            inverted_blob = ArrayDict(indexfilename, 'w+')
        # now write out the Numpy array for each value in the column to a file
        for value, rownums in inverted.iteritems():
            # TO DO: need to determine the smallest Numpy integer type required
            # to hold all the row ids
            row_array = Numeric.array(rownums, Numeric.Int)
            if self.datatype.name == 'tuple':
                row_array = soomfunc.unique(Numeric.sort(row_array))
            inverted_blob[value] = row_array
        if self.heterosourcecols is not None:
            # we need to assemble an output translation dict
            self.outtrans = {}
            for keytuple in inverted.keys():
                for cname in self.parent_dataset.get_columns():
                    pcol = getattr(self.parent_dataset,cname)
                    if pcol.columnid == keytuple[0]:
                        clabel = pcol.label
                        if callable(pcol.outtrans):
                            cdesc = pcol.outtrans(keytuple[1])
                        else:
                            cdesc = pcol.outtrans[keytuple[1]]
                        newdesc = clabel + ":" + cdesc
                        getattr(self.parent_dataset,colname).outtrans[keytuple] = newdesc
        del inverted                # Not needed anymore
        if indexfilename:
            inverted_blob = None           # Closes and flushes to disk
        self._inverted = inverted_blob

    def _inverted_gen(self, src):
        inverted = {}
        for rownum, value in enumerate(src):
            if type(value) is tuple:
                for v in value:
                    if v is not None or not self.ignorenone:
                        row_nums = inverted.setdefault(v, [])
                        row_nums.append(rownum)
            else:
                try:
                    row_nums = inverted.setdefault(value, [])
                except TypeError, e:
                    raise Error('column %r: Bad value: %r %s: %s' % 
                                (self.name, value, type(value), e))
                row_nums.append(rownum)
            yield value
        self._store_inverted(inverted)

    def get_store_chain(self, data, mask=None):
        src = DatasetColumnBase.get_store_chain(self, data, mask)
        src = self._inverted_gen(src)
        return src

    def _op_general(self, op, value, filter_keys=[], prefix = False):
        # handle the general case for an operator combining vectors of results
        # for each operator.
        #
        # We use sets.Set() in here because numpy intersect doesn't handle
        # anything but numeric types, and we may be comparing strings, etc.
        if not callable(op):
            op = getattr(operator, op)
        possible_keys = sets.Set(self.inverted.keys())
        if filter_keys:
            possible_keys = possible_keys.intersection(sets.Set(filter_keys))
        if prefix:
            value = self.do_format(value)
            rows = [self.inverted[v] 
                    for v in possible_keys 
                    if op(self.do_format(v)[:len(value)], value)]
        else:
            rows = [self.inverted[v] 
                    for v in possible_keys 
                    if op(v, value)]
        if len(rows) == 1:
            vectors = rows[0]
        elif len(rows) > 1:
            vectors = soomfunc.union(*rows)
        else:
            vectors = []
        return vectors

    def describe(self, detail=ALL_DETAIL):
        d = DatasetColumnBase.describe(self, detail)
        if detail >= SOME_DETAIL:       # Don't load .inverted otherwise
            d.add('data', SOME_DETAIL, 'Cardinality', self.cardinality())
        d.add('data', SOME_DETAIL, 'Label for <All>', self.all_label)
        d.add('data', SOME_DETAIL, 'Value for <All>', str(self.all_value))
        return d

    # special case for operator equal as we don't have to step through whole
    # list if we have a match
    def op_equal(self, value, filter_keys):
        return self.inverted.get(value, [])

    def op_between(self, value, filter_keys):
        try:
            start, end = value
        except (ValueError, TypeError):
            raise ExpressionError('between(start, end)')
        possible_keys = sets.Set(self.inverted.keys())
        if filter_keys:
            possible_keys = possible_keys.intersection(sets.Set(filter_keys))
        rows = [self.inverted[v] 
                for v in possible_keys 
                if start <= v < end]
        if len(rows) == 0:
            vectors = []
        elif len(rows) == 1:
            vectors = rows[0]
        else:
            vectors = soomfunc.union(*rows)
        return vectors

    def op_less_than(self, value, filter_keys):
        return self._op_general('lt', value, filter_keys)

    def op_less_equal(self, value, filter_keys):
        return self._op_general('le', value, filter_keys)

    def op_greater_than(self, value, filter_keys):
        return self._op_general('gt', value, filter_keys)

    def op_greater_equal(self, value, filter_keys):
        return self._op_general('ge', value, filter_keys)

    def op_not_equal(self, value, filter_keys):
        return self._op_general('ne', value, filter_keys)

    def op_equal_col(self, value, filter_keys):
        return self._op_general('eq', value, filter_keys, prefix=True)

    def op_not_equal_col(self, value, filter_keys):
        return self._op_general('ne', value, filter_keys, prefix=True)

    def op_less_than_col(self, value, filter_keys):
        return self._op_general('lt', value, filter_keys, prefix=True)

    def op_less_equal_col(self, value, filter_keys):
        return self._op_general('le', value, filter_keys, prefix=True)

    def op_greater_than_col(self, value, filter_keys):
        return self._op_general('gt', value, filter_keys, prefix=True)

    def op_greater_equal_col(self, value, filter_keys):
        return self._op_general('ge', value, filter_keys, prefix=True)

    def _assert_value_is_list(self, value):
        if type(value) not in (list, tuple):
            raise ExpressionError('"in" operator must be followed by a list')

    def op_in(self, value, filter_keys):
        self._assert_value_is_list(value)
        return self._op_general(lambda v, value: v in value, 
                                 value, filter_keys)

    def op_not_in(self, value, filter_keys):
        self._assert_value_is_list(value)
        return self._op_general(lambda v, value: v not in value, 
                                 value, filter_keys)

    def op_in_col(self, value, filter_keys):
        self._assert_value_is_list(value)
        return self._op_general(has_in_col_value_list, value, filter_keys)

    def op_not_in_col(self, value, filter_keys):
        self._assert_value_is_list(value)
        return self._op_general(lambda v, value: not has_in_col_value_list(v, value), value, filter_keys)

# test whether v is in value_list for "in:" operator.  Tests whether v is the
# leading string in any value in value_list.  Values can end in "*" which is
# ignored.
def has_in_col_value_list(v, value_list):
    for value in value_list:
        value = str(value)
        if value.endswith('*'):
            value = value[:-1]
        if v.startswith(str(value)):
            return True
    return False


class CategoricalDatasetColumn(_DiscreteDatasetColumn):
    coltype = 'categorical'


class OrdinalDatasetColumn(_DiscreteDatasetColumn):
    coltype = 'ordinal'

    def is_ordered(self):
        return True
