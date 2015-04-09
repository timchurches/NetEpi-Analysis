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
# $Id: Filter.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Filter.py,v $

import os
import new
import time
import errno
import cPickle

import Numeric, RandomArray
# implements memory-mapped Numpy arrays stored in BLOBs
from soomarray import ArrayDict, MmapArray
import soomfunc

from SOOMv0 import soomparse, Utils
from SOOMv0.Soom import soom
from SOOMv0.common import *
from SOOMv0.PrintDataset import DSFormatter
from SOOMv0.BaseDataset import BaseDataset
from SOOMv0.ColTypes.RowOrdinal import FilteredRowOrdinalColumn

from SOOMv0.DatasetColumn import column_types

class FilteredColumnMixin(object):
    """
    A column proxy that presents a filtered view of the target
    column. The class is not a true DatasetColumn object in its own
    right, rather it is intended to be a lightweight layer on top of
    a column object (either a real column, or another filter proxy).
    """
    __slots__ = ('_src_col','_all_record_ids')

    def __init__(self, src_col, record_ids):
        self._src_col = src_col
        self._all_record_ids = record_ids

    def get_data(self):
        return self._src_col.take(self._all_record_ids)
    data = property(get_data)

    def get_inverted(self):
        inverted = {}
        for value in self._src_col.inverted.keys():
            inverted[value] = soomfunc.intersect(self._src_col.inverted[value], 
                                                 self._all_record_ids)
        return inverted
    inverted = property(get_inverted)

    def describe(self, detail=ALL_DETAIL):
        return self._src_col.describe(detail)

    def take(self, rows):
        return self._src_col.take(Numeric.take(self._record_ids, rows))
    
    def __len__(self):
        return len(self._all_record_ids)

    def __getitem__(self, i):
        if type(i) is slice:
            return self._src_col.take(self._all_record_ids[i])
        else:
            return self._src_col.data[self._all_record_ids[i]]

# Magic Be Here - dynamically create versions of coltypes with a
# FilteredColumnMixin layered on top. The FilteredColumnMixin proxies
# access to .data and .inverted attributes so as to provide a filtered
# view of them.
namespace = globals()
filter_coltypes_map = {}
for coltype in column_types:
    name = 'Filtered' + coltype.__name__
    cls = new.classobj(name, (FilteredColumnMixin, coltype), {})
    namespace[name] = filter_coltypes_map[coltype] = cls

def get_filtered_col(col, record_ids):
    cls = filter_coltypes_map[col.__class__]
    inst = cls(col, record_ids)
    inst.__dict__.update(col.__dict__)
    return inst

class FilteredDataset(BaseDataset):
    def __init__(self, parent_dataset, record_ids, filter_label=None, **kwargs):
        m = parent_dataset.get_metadata()
        m.update(kwargs)
        BaseDataset.__init__(self, **m)
        if isinstance(parent_dataset, FilteredDataset):
            record_ids = Numeric.take(parent_dataset.record_ids, record_ids)
            filter_label = '%s, %s' % (filter_label,parent_dataset.filter_label)
            parent_dataset = parent_dataset.parent_dataset
        self.parent_dataset = parent_dataset
        self.record_ids = record_ids
        self.filter_label = filter_label
        self.addcolumn(FilteredRowOrdinalColumn(self, record_ids))
        for col in parent_dataset.get_columns():
            if col.name == 'row_ordinal':
                continue
            self.addcolumn(get_filtered_col(col, self.record_ids))

#    def __getattr__(self, name):
#        if name[0] == '_':
#            raise AttributeError(name)
#        value = getattr(self.parent_dataset, name)
#        if hasattr(value, 'im_func'):
#            # Rebind bound methods
#            value = new.instancemethod(value.im_func, self, self.__class__)
#        return value
#
    def __len__(self):
        return len(self.record_ids)


    def describe(self, detail=ALL_DETAIL, date_fmt=None):
        d = BaseDataset.describe(self, detail, date_fmt)
        d.add('prov', SUB_DETAIL, 'Filter', self.filter_label)
        return d

def filtered_ds(parent_dataset, record_ids, name=None, **kwargs):
    if name is None:
        name = '%s_filtered' % parent_dataset.name
    return FilteredDataset(parent_dataset, record_ids, name=name, **kwargs)

def sampled_ds(parent_dataset, sample, name=None, filter_label=None, **kwargs):
    parent_len = len(parent_dataset)
    samp_len = int(parent_len * sample)
    record_ids = Numeric.sort(RandomArray.randint(0, parent_len, samp_len))
    if name is None:
        name = 'samp%02d_%s' % (sample * 100, parent_dataset.name)
    if filter_label is None:
        filter_label = '%.3g%% sample' % (sample * 100)
    return FilteredDataset(parent_dataset, record_ids, name=name, 
                           filter_label=filter_label, **kwargs)

def sliced_ds(parent_dataset, idx, name=None, filter_label=None, **kwargs):
    assert isinstance(idx, slice)
    indicies = idx.indices(len(parent_dataset))
    record_ids = Numeric.arrayrange(*indicies)
    if name is None:
        name = 'slice_%d_%d_%d_%s' % (indicies + (parent_dataset.name,))
    if filter_label is None:
        filter_label = '[%d:%d:%d] slice' % indicies
    return FilteredDataset(parent_dataset, record_ids, name=name, 
                           filter_label=filter_label, **kwargs)

class DatasetFilters:
    '''
    Dataset filter registry
    '''
    def __init__(self, dataset):
        self.dataset = dataset
        self.filters = {}

    def load_metadata(self):
        # Parent dataset has just been loaded, scan for applicable filters
        paths = soom.find_metadata(os.path.join(self.dataset.name, 'filters'))
        for path in paths:
            filter = load_filter(self.dataset, path)
            self.filters[filter.name] = filter

    def _display_hook(self):
        filters = self.filters.items()
        filters.sort()
        print 'Filters:'
        if filters:
            for name, filter in filters:
                desc = filter.desc
                if not desc:
                    desc = '(no description)'
                print '    %-12s %s, %d elements\n%16s expr: %s' % \
                    (filter.name, desc, len(filter), 
                     '', filter.expr)
        else:
            print '    (no filters defined)'

    def delete(self, name):
        filter = self.filters.pop(name, None)
        if filter:
            filter.delete()
            soom.info('deleted filter %r' % name)

    def add(self, name, filter):
        assert name not in self.filters
        self.filters[name] = filter

    def __getitem__(self, name):
        filter = self.filters[name]
        filter.load()
        return filter

    def filter(self, **kwargs):
        return filter_dataset(self.dataset, filters=self, **kwargs)


def filter_dataset(dataset, expr=None, name=None, label=None, 
                   kwargs=None, filters=None):
    '''
    Parse filter method arguments and return record_ids if
    filter active:

    - If "nofilter" - returns raw dataset
    - If "filtername", use pre-defined named filter, 
        return dataset extract
    - If "filterexpr", creates an anonymous filter, 
        return dataset extract
    - Else return raw dataset
    '''
    if kwargs:
        nofilter = kwargs.pop('nofilter', False)
        if nofilter:
            return dataset
        name = kwargs.pop('filtername', None)
        expr = kwargs.pop('filterexpr', None)
        label = kwargs.pop('filterlabel', None)
    if expr or name:
        if expr:
            if name and filters:
                filters.delete(name)
            filter = DatasetFilter(dataset, name,
                                   expr, backed=bool(name), 
                                   label=label) 
            if name and filters:
                filters.add(name, filter)
        else:
            try:
                if filters:
                    filter = filters[name]
                else:
                    raise KeyError
            except KeyError:
                raise Error('Unknown filter %s' % repr(name))
        return filter.get_filtered_ds()
    return dataset

class DatasetFilter(object):
    """
    Base class for data set filters (resolved record IDs and definition)
    """
    def __init__(self, parent_dataset, name, expr,
                 desc=None, label=None, backed=True):
        """
        Method to define and evaluate a dataset filter i.e. a
        where clause.

        Arguments:
            parent_dataset      
            name                short name for filter
            expr                filter expression
            desc                longer description of the filter
            label               label for the filter when printing
                                output
        """

        self.parent_dataset = parent_dataset
        self.name = name
        self.desc = desc
        self.label = label
        self.record_ids = None          # "list" of matching row/record ID's
        self.generation = None
        self.length = 0
        self.expr = expr
        self.path = None
        self.backed = bool(backed and name)
        self.path = None
        self.filter()

    def __getstate__(self):
        """
        Returns a copy of the DatasetFilter's state but with the
        .record_ids attributes set to None, instead of BLOBstore
        object instances, and parent_dataset set to None (so we don't
        save that as well).
        """
        odict = self.__dict__.copy()
        odict['filter_blob'] = None
        odict['record_ids'] = None
        odict['parent_dataset'] = None
        return odict

    def __setstate__(self, state):
        self.__dict__.update(state)

    def _fixpath(self):
        self.path = os.path.join(soom.writepath, 
                                 self.parent_dataset.name,
                                 'filters',
                                 self.name)
        Utils.helpful_mkdir(self.path)

    def save_metadata(self):
        if self.backed and soom.writepath:
            self._fixpath()
            filename = os.path.join(self.path, soom.metadata_filename)
            f = open(filename, 'wb')
            try:
                cPickle.dump(self, f, -1)
            finally:
                f.close()

    def _blobstore_filename(self, mkdirs=False):
        if self.backed and soom.writepath:
            self._fixpath()
        if self.path:
            return os.path.join(self.path, 'record_ids.SOOMblobstore')

    def filter(self):
        starttime = time.time()
        parser = soomparse.SoomFilterParse(self.parent_dataset, self.expr)
        record_ids = parser.filter()
        # Empty filter?
        if record_ids is None or len(record_ids) == 0:
            record_ids = []
        self.record_ids = Numeric.array(record_ids, typecode=Numeric.Int)
        del record_ids
        self.generation = self.parent_dataset.generation
        self.length = len(self.record_ids)

        filename = self._blobstore_filename(mkdirs=True)
        if self.backed and filename:
            # initialise a BLOB dict to hold filter record ID vector
            self.filter_blob = ArrayDict(filename, 'w+')
            self.filter_blob['vector'] = self.record_ids
            # this syncs the data to disc - EVIL - relying on cyclic GC to
            # reap immediately.
            del self.filter_blob
            # re-instate the reference to the BLOBstore
            self.filter_blob = ArrayDict(filename, 'r')
            self.record_ids = self.filter_blob['vector']
        else:
            self.filter_blob = None
        self.save_metadata()

        soom.info('Assembling filter %s containing %d elements took %.3fs' %\
                  (self.name, len(self.record_ids), time.time() - starttime))

    def get_filtered_ds(self):
        return filtered_ds(self.parent_dataset, self.record_ids,
                           name=self.name, 
                           filter_label=self.label or self.expr, 
                           desc=self.desc)

    def __len__(self):
        if self.generation != self.parent_dataset.generation:
            self.filter()
        return self.length

    def describe(self):
        """Method to print metadata about a data set filter instance"""
        m = ["","-"*20]
        m.append("Metadata for dataset filter: %s" % self.name)
        if self.label:
            m.append("Label: %s" % self.label)
        if self.desc:
            m.append("Description: %s" % self.desc)
        m.append("Parent dataset: %s" % self.parent_dataset.name)
        m.append("Number of records returned by filter: %i" % self.length)
        m.append("Definition: %s" % self.expr)
        m.append("-"* 20)
        m.append("")
        return os.linesep.join(m)

    def _display_hook(self):
        """
        Prints a DatasetFilter's metadata 
        """
        print self.describe()

    def load(self, verbose=1):
        """
        Function to load a filter vector for a data set, regenerating
        it if the parent dataset has changed.

        It checks to see if the filter has already been loaded,
        and does nothing if it has.
        """
        if self.generation != self.parent_dataset.generation:
            self.filter()
        elif self.record_ids is None and self.backed:
            filename = self._blobstore_filename()
            starttime = time.time()
            try:
                self.filter_blob = ArrayDict(filename, 'r+')
            except IOError, e:
                raise IOError, "couldn't open filter \"%s\" blobstore: %s" %\
                    (self.name, e)
            self.record_ids = self.filter_blob["vector"]
            elapsed = time.time() - starttime
            if verbose: 
                print "load_filter(): memory mapping of \"%s\" containing %d elements took %.3f seconds." % (self.name, len(self.record_ids), elapsed)

    def unload(self):
        self.filter_blob = None
        self.record_ids = None

    def delete(self):
        self.unload()
        if self.backed and self.path:
            try:
                os.unlink(os.path.join(self.path, soom.metadata_filename))
                os.unlink(self._blobstore_filename())
                os.rmdir(self.path)
            except OSError, (eno, estr):
                if eno != errno.ENOENT:
                    raise

def load_filter(dataset, path):
    f = open(os.path.join(path, soom.metadata_filename), 'rb')
    try:
        filter = cPickle.load(f)
        filter.path = path
        filter.parent_dataset = dataset
    finally:
        f.close()
    return filter
