
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
# $Id: base.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/ColTypes/base.py,v $

import sys
import os
import time
import itertools

import MA, Numeric

from SOOMv0.common import *
from SOOMv0.Soom import soom
from SOOMv0.Describe import Describe
from SOOMv0.DataTypes import get_datatype_by_name

"""
Base classes for dataset columns

Arguments are:
    desc            longer description of the column
    label           label for the column when printing output
    coltype
    datatype
    all_label       label for summaries of this column
    all_value       value used to represent summaries of this 
                    column
    maxoutlen       maximum length of column value strings for 
                    printing - not currently used
    use_outtrans    whether to use the out translation
    outtrans        output translation of coded values for 
                    presentation (either a dict or a callable).
    ignorenone      flag for multivalues (tuples) to ignore the None value
    calculatedby    If not None then this is a calculated column
    calculatedargs  Sequence or dictionary of arguments to be 
                    passed to the calculatedby function
    missingvalues   a dictionary of values which represent 
                    missing data
    multisourcecols contains a homogenous sequence of other
                    categorical or ordinal columns (of same type
                    of data) if a multicolumn - multicolumns
                    are multi-valued attributes (tricky!)
    heterosourcecols contains a heterogenous sequence of other 
                    categorical or ordinal columns

Attributes are:
    data            data values in row order - referred to as 
                    the data fork
    mask            mask of missing (0) and non-missing (1) 
                    values for the data fork
    inverted        mapped to lists of record IDs - referred 
                    to as the inverted fork

Column types are:
    categorical     discrete values, inverted index provided
    ordinal         discrete *ordered* values, inverted index provided
    scalar          continuous values, no inverted index
    identity        discrete values, no inverted index (also called
                    "noncategorical")
    weighting       continuous weighting to be applied to other columns
    searchabletext  text strings which may be broken into words and indexed
                    for text searches

"""

class AbstractDatasetColumnBase(object):
    __slots__ = ()

class SimpleDatasetColumnBase(AbstractDatasetColumnBase):
    coltype = None

    def __init__(self, parent_dataset, name, label=None, desc=None, 
                 datatype=None, format_str=None):
        soom.check_name_ok(name, 'DatasetColumn')
        self.parent_dataset = parent_dataset
        self.name = name
        self.label = label or name
        self.desc = desc
        self.datatype = get_datatype_by_name(datatype)
        self.format_str = format_str
        if self.format_str is None:
            self.format_str = self.datatype.default_format_str

    def get_metadata(self):
        """
        Returns the column "metadata" - basically the column
        attributes, minus data or indicies. The result is a
        dictionary suitable for use as kwargs in creating a new
        shallow copy of the column.
        """
        m = dict(vars(self))
        del m['parent_dataset']
        m['coltype'] = self.coltype     # Class attribute
        m['datatype'] = self.datatype.name
        return m

    def rename_column(self, newname):
        soom.check_name_ok(newname, 'DatasetColumn')
        self.name = newname

    def delete_column(self):
        pass

    def is_discrete(self):
        """
        Coltype: Is the column indexable?
        """
        return False

    def is_scalar(self):
        """
        Coltype: Does the column contain continuous values (typically floats)
        """
        return False

    def is_ordered(self):
        """
        Coltype: Is there a natural ordering for the column?
        """
        return False

    def is_weighting(self):
        """
        Coltype: Can the column be used for weighting frequency counts?
        """
        return False

    def is_searchabletext(self):
        """
        Coltype: Does the column support free text searches?
        """
        return False

    def is_multivalue(self):
        """
        Datatype: Is the column made up of multiple values per row?
        """
        return self.datatype.is_multivalue

    def is_datetimetype(self):
        """
        Datatype: Is the column data dates or times?

        Date and time columns are handled differently when being
        plotted, and require alternate import schemes in web
        interfaces.
        """
        return self.datatype.is_datetime

    def is_numerictype(self):
        """
        Datatype: Is the column data numeric?
        
        Typically this is right justified on output, whereas other
        data types are left justified
        """
        return self.datatype.is_numeric

    def will_outtrans(self):
        """
        Is output translation enabled?
        """
        return False

    def do_outtrans(self, v):
        """
        Translate the given value (if needed)
        """
        return v

    def do_format(self, v):
        """
        Convert the value into a string, applying column-specific
        (or datatype specific) formatting conventions.
        """
        if self.format_str is None:
            self.format_str = self.datatype.default_format_str
        return self.datatype.do_format(v, self.format_str)


    def load(self, *args):
        """
        Load column data
        """
        pass

    def unload(self, *args):
        """
        Unload column data
        """
        pass

    def describe(self, detail=ALL_DETAIL):
        """
        Return a "Describe" object, which contains a string
        description of the object metadata.
        """
        d = Describe(detail, 'col', 'data', 'out', 'misc')
        d.add('col', NO_DETAIL, 'Name', self.name)
        d.add('col', NO_DETAIL, 'Label', self.label)
        d.add('col', SOME_DETAIL, 'Description', self.desc)
        d.add('col', NO_DETAIL, 'Column Type', self.coltype)
        d.add('col', NO_DETAIL, 'Data Type', self.datatype.name)
        d.add('out', SOME_DETAIL, 'Format String', self.format_str)
        return d

    def filter_op(self, op, value, filter_keys):
        """
        Execute comparisons from expression parser for DatasetFilter.

        Each returns a list of rows indexes that match the condition.

        "filter_keys" is a list of keys that are known to be in
        the result set, if possible we exclude keys that aren't
        part of that set.
        """

        try:
            opmeth = getattr(self, op)
        except AttributeError:
            op_name = op.replace('_', ' ')
            if op_name.startswith('op '):
                op_name = op_name[3:]
            if op_name.endswith(' col'):
                op_name = op_name[:-3] + 'starting'
            raise ExpressionError('%r operator not supported on %s column %r' %
                                  (op_name, self.coltype, self.name))
        else:
            return opmeth(value, filter_keys)


class DatasetColumnBase(SimpleDatasetColumnBase):
    # The primary difference between this class and its parent is that this
    # class has additional loadable components (data, index, etc), as well as
    # supporting data loading and output translation.
    coltype = '[unknown]'
    loadables = ('data',)

    def __init__(self, parent_dataset, name, label=None, desc=None,
                 datatype=None, format_str=None,
                 calculatedby=None, calculatedargs=(),
                 ignorenone=True,
                 missingvalues=None, 
                 use_outtrans=True, outtrans=None,
                 multisourcecols=None, heterosourcecols=None,
                 trace_load=False): 
        SimpleDatasetColumnBase.__init__(self, parent_dataset, 
                                         name, label, desc, datatype,
                                         format_str)
        self.calculatedby = calculatedby
        self.calculatedargs = calculatedargs
        self.ignorenone = ignorenone
        self.missingvalues = missingvalues
        self.outtrans = outtrans
        self.use_outtrans = use_outtrans
        if self.outtrans is None:
            self.use_outtrans = False
            self.outtrans = {}
        self.multisourcecols = multisourcecols
        self.heterosourcecols = heterosourcecols
        self.trace_load = trace_load
        self._data = []

    def get_metadata(self):
        m = SimpleDatasetColumnBase.get_metadata(self)
        for attr in self.loadables:
            del m['_' + attr]
        return m

    def __getstate__(self):
        """
        Returns a copy of the DatasetColumn's state but with the
        loadable elements "unloaded".
        """
        if self.parent_dataset.backed:
            # copy the dict since we will be changing it
            odict = self.__dict__.copy()
            for attr in self.loadables:
                odict['_' + attr] = None
            return odict
        else:
            return self.__dict__

    def __setstate__(self, odict):
        self.__dict__.update(odict)

    def rename_column(self, newname):
        raise NotImplementedError               # XXX future work
        SimpleDatasetColumnBase.rename_column(self, newname)

    def delete_column(self):
        # XXX this is wrong in the context of versioned datasets
        soom.warning('deleting column %r (hope there are no concurrent users!' %
                     self.name)
        SimpleDatasetColumnBase.delete_column(self)

    def do_outtrans(self, v):
        if self.use_outtrans and self.outtrans:
            if callable(self.outtrans):
                return self.outtrans(v)
            else:
                return self.outtrans.get(v, v)
        else:
            return v

    def will_outtrans(self):
        """
        Is an outtrans active?
        """
        if not self.use_outtrans or not self.outtrans:
            return False
        return True

    def get_inverted(self):
        # This is not strictly necessary, but helps to give a more useful
        # diagnostic to the end user.
        raise Error('%r is a %s, not a discrete column (no index)' % 
                    (self.name, self.coltype))
    inverted = property(get_inverted)

    def _loadables(self, op, want):
        if self.parent_dataset.backed:
            if not want:
                want = self.loadables
            for loadable in want:
                try:
                    meth = getattr(self, '%s_%s' % (op, loadable))
                except AttributeError:
                    pass
                else:
                    meth()

    def load(self, *want):
        self._loadables('load', want)

    def unload(self, *want):
        self._loadables('unload', want)

    def load_data(self):
        if self.parent_dataset.backed:
            if self._data is None:
                starttime = time.time()
                filename = self.object_path(self.datatype.file_extension)
                self._data = self.datatype.load_data(filename)
                elapsed = time.time() - starttime
                soom.info('load of %r data vector took %.3f seconds.' %\
                            (self.name, elapsed))

    def unload_data(self):
        self._data = None

    def get_data(self):
        if self._data is None:
            self.load_data()
        return self._data
    data = property(get_data)

    def __getitem__(self, index):
        return self.data[index]

    def take(self, rows):
        return self.datatype.take(self.data, rows)

    def __len__(self):
        return len(self.data)

    def describe(self, detail=ALL_DETAIL):
        d = SimpleDatasetColumnBase.describe(self, detail)
        if detail >= SOME_DETAIL:       # otherwise would load .data
            d.add('data', SOME_DETAIL, 'Data Vector Length', len(self.data))
        d.add('data', SOME_DETAIL, 'Values calculated by', self.calculatedby)
        d.add('data', SOME_DETAIL, 'Calculated-by arguments', self.calculatedby)
        d.add('data', SOME_DETAIL, 'Missing Values', self.missingvalues)
        if self.is_multivalue():
            d.add('data', SOME_DETAIL, 'Ignore None values', self.ignorenone)

            d.add('data', SOME_DETAIL, 'Multi-source cols', self.multisourcecols)
            d.add('data', SOME_DETAIL, 'Hetero-source cols', self.heterosourcecols)
        d.add('out', SOME_DETAIL, 'Use Output Translation', yesno(self.use_outtrans))
        d.add('out', SOME_DETAIL, 'Output Translation', self.outtrans)
        return d

    def __str__(self):
        return self.parent_dataset.print_cols(self.name)

    def object_path(self, datatype, objtype='data', mkdirs=False):
        object_name = os.path.join(self.name, '%s.%s' % (objtype, datatype))
        return self.parent_dataset.object_path(object_name,
                                               gen=True, mkdirs=mkdirs)

    def _display_hook(self):
        print str(self.describe())

    # Generator functions for processing newly loaded columns
    def _mask_gen(self, src, mask):
        for value, mask in itertools.izip(src, mask):
            if mask:
                value = None
            yield value

    def _calcby_gen(self, src, calcfn, calcargs):
        if type(calcargs) is dict:
            for value in src:
                if value is None:
                    value = calcfn(**calcargs)
                yield value
        else:
            for value in src:
                if value is None:
                    value = calcfn(*calcargs)
                yield value

    def _missing_gen(self, src, missingvalues):
        for value in src:
            if value in missingvalues:
                value = None
            yield value

    def _multisrc_gen(self, multisourcecols):
        srcs = []
        for colname in multisourcecols:
            srcs.append(self.parent_dataset[colname].data)
        return itertools.izip(*srcs)

    def _tuple_gen(self, src, ignorenone):
        for value in src:
            if value is None:
                value = ()
            elif ignorenone:
                value = tuple([v for v in value if v is not None])
            yield value

    def _tuplemissing_gen(self, src, missingvalues):
        for value in src:
            yield tuple([v for v in value if v not in missingvalues])

    def _storedata_gen(self, src):
        # If persisent, set data file name
        datafilename = None
        if self.parent_dataset.backed:
            datafilename = self.object_path(self.datatype.file_extension,
                                            mkdirs=True)
        ds_len = len(self.parent_dataset)
        store_data = self.datatype.get_array(datafilename, ds_len)
        maskval = self.datatype.masked_value
        store_mask = self.datatype.get_mask(ds_len)
        for rownum, value in enumerate(src):
            if value is None:
                store_value = maskval
                if store_mask is not None:
                    store_mask[rownum] = 1
            else:
                store_value = value
            try:
                store_data[rownum] = store_value
            except TypeError:
                raise Error('bad data type, column %r at index %d, '
                            'value %r, should be datatype %r' %\
                            (self.name, rownum, value, 
                            self.datatype.name))
            yield value
        # If have a mask, but no values masked, use Numeric rather than MA
        if store_mask is not None and not Numeric.sometrue(store_mask):
            store_mask = None
        self._data = self.datatype.store_data(store_data, store_mask,
                                              datafilename)
        # Give the datatype a chance to set the format string if none
        # specified
        if self.format_str is self.datatype.default_format_str:
            format_str = self.datatype.derive_format_str(store_data)
            if format_str:
                self.format_str = format_str

    def get_store_chain(self, data, mask=None):
        """
        Return a chain of generators for processing the src data,
        which can either be a list or an iterable.
        """
        multisourcecols = self.multisourcecols or self.heterosourcecols
        if multisourcecols:
            src = self._multisrc_gen(multisourcecols)
        else:
            src = iter(data)
        if MA.isMaskedArray(data) and mask is None:
            mask = data.mask()
        if mask is not None:
            src = self._mask_gen(src, mask)
        if self.is_multivalue():
            src = self._tuple_gen(src, self.ignorenone)
            if self.missingvalues:
                src = self._tuplemissing_gen(src, self.missingvalues)
        else:
            if self.calculatedby:
                src = self._calcby_gen(src, self.calculatedby, 
                                            self.calculatedargs)
            if self.missingvalues:
                src = self._missing_gen(src, self.missingvalues)
        src = self._storedata_gen(src)
        return src

    def store_column(self, data, mask=None): 
        st = time.time()
        # The chain of generators returned by get_store_chain does the actual
        # processing.
        if not getattr(self, 'trace_load', False):
            for value in self.get_store_chain(data, mask):
                pass
        else:
            tracer = store_trace()
            for value in self.get_store_chain(data, mask):
                tracer.flush()
            tracer.done()
        soom.info('Stored data for column %s in dataset %s (%.3fs)' %
                  (self.name, self.parent_dataset.name, time.time() - st))
        if self.multisourcecols:
            # We unload source cols to contain mapped memory use on 32 bit plats
            for colname in self.multisourcecols:
                self.parent_dataset[colname].unload()
        soom.mem_report()


class store_trace:
    """
    A debug aide for the store generator chain that enables tracing
    and reports (any) generator return values.
    """
    def __init__(self):
        sys.settrace(self.trace)
        self.frames = []
        
    def trace(self, frame, event, arg):
        def line_trace(frame, event, arg):
            if event == 'return':
                self.frames.append((frame, arg))
            return line_trace
        if frame.f_code.co_flags & 0x20:    # Generator
            return line_trace
    
    def flush(self):
        res = []
        for frame, arg in self.frames:
            res.append(frame.f_code.co_name)
            res.append(repr(arg))
        print '->'.join(res)
        self.frames = []

    def done(self):
        sys.settrace(None)
        self.frames = []


def is_dataset_col(obj):
    return isinstance(obj, AbstractDatasetColumnBase)

