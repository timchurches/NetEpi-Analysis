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
# $Id: DatasetSummary.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/DatasetSummary.py,v $

import time
import sets
from SOOMv0 import Utils
from SOOMv0 import SummaryStats
from SOOMv0.common import *
from SOOMv0.Soom import soom
from SOOMv0.SummaryProp import calc_props
import MA, Numeric
import soomfunc

class DatasetTakeCol:
    """
    Column object returned by DatasetTake
    """
    def __init__(self, col, cellrows):
        if len(col.data) > 0 and len(cellrows) > 0:
            self.data = col.take(cellrows)
        else:
            self.data = []
        self.name = col.name
        self.label = col.label

class DatasetTake:
    """
    Caching lazy "take" of a dataset
    """
    def __init__(self, dataset, cellrows):
        self.dataset = dataset
        self.cellrows = cellrows
        self.colvectors = {}

    def __getitem__(self, colname):
        try:
            return self.colvectors[colname]
        except KeyError:
            col = self.dataset.get_column(colname)
            coltake = DatasetTakeCol(col, self.cellrows)
            self.colvectors[colname] = coltake
            return coltake

    def __len__(self):
        return len(self.cellrows)

class CondColArg:
    def __init__(self, *values):
        self.callable = None
        if values:
            if callable(values[0]):
                if len(values) > 1:
                    self.usage('only one callable argument')
                self.callable = values[0]
                values = ()
            elif type(values[0]) in (list, tuple):
                if len(values) > 1:
                    self.usage('only one list argument')
                values = values[0]
        self.values = values

    def calc_values(self, available):
        if self.callable:
            return [v for v in available if self.callable(v)]
        return self.values

    def usage(self, msg):
        raise Error('%s: %s' % (self.__class__.__name__, msg))

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join([repr(v) for v in self.values]))

def numcmp(a, b):
    import math
    try:
        a = float(a)
        b = float(b)
    except ValueError:
        return 0
    else:
        return int(math.ceil(a - b))

class suppress(CondColArg):
    pass

class retain(CondColArg):
    pass

class order(CondColArg):
    pass

class reversed(CondColArg):
    pass

class coalesce(CondColArg):
    def __init__(self, *values, **kwargs):
        CondColArg.__init__(self, *values)
        self.label = kwargs.pop('label', None)
        self.value = kwargs.pop('value', None)
        if kwargs:
            raise TypeError('coalesce: unknown keywords arg(s): %s' % 
                            ', '.join(kwargs.keys()))

    def __repr__(self):
        repr = CondColArg.__repr__(self)
        if self.label:
            repr = '%s, value=%r, label=%r)' % (repr[:-1], self.value, 
                                                self.label)
        return repr

class condcol:
    def __init__(self, colname, *args):
        self.colname = colname
        self.coalesce = []
        self.suppress = []
        self.order = None
        for arg in args:
            if isinstance(arg, (suppress, retain)):
                self.suppress.append(arg)
            elif isinstance(arg, (order, reversed)):
                if self.order:
                    raise Error('only one "order" per condcol allowed')
                self.order = arg
            elif isinstance(arg, coalesce):
                self.coalesce.append(arg)
            else:
                raise Error('Unknown condcol() argument: %r' % arg)

    def __cmp__(self, other):
        if isinstance(other, self.__class__):
            return cmp(self.colname, other.colname)
        # This allows others to compare new-style condcol() args with old-style
        # string column name args (we convert all to condcol internally).
        return cmp(self.colname, other)

    def get_colname(self):
        return self.colname

    def __repr__(self):
        res = []
        res.append(repr(self.colname))
        for coalesce in self.coalesce:
            res.append(repr(coalesce))
        for suppress in self.suppress:
            res.append(repr(suppress))
        return 'condcol(%s)' % (', '.join(res))

class SummCondCol:
    """
    Summary helper class to manage the values assocated with a
    discrete conditioning column.
    """
    def __init__(self, dataset, index, condcol):
        self.name = condcol.colname
        self.index = index
        self.col = dataset.get_column(self.name)
        if not self.col.is_discrete():
            raise Error('%r is not a discrete column' % self.name)
        self.vector = self.col.inverted
        # Coalesce
        if condcol.coalesce:
            self.use_outtrans = True
            self.vector = dict(self.vector)
            self.outtrans = {}
            for coalesce in condcol.coalesce:
                if coalesce.callable:
                    for v in self.vector.keys():
                        agv = coalesce.callable(v)
                        if agv != v:
                            v_rows = self.vector.pop(v)
                            agv_rows = self.vector.get(agv)
                            if agv_rows is not None:
                                v_rows = soomfunc.union(agv_rows, v_rows)
                            self.vector[agv] = v_rows
                elif coalesce.values:
                    if coalesce.value is None:
                        newvalue = coalesce.values[0]
                    else:
                        newvalue = coalesce.value
                    if (newvalue not in coalesce.values 
                            and newvalue in self.vector):
                        raise Error('coalesce target value %d conflicts' %\
                                    newvalue)
                    valrows = []
                    vals = []
                    for v in coalesce.values:
                        rows = self.vector.pop(v, None)
                        if rows:
                            valrows.append(rows)
                            vals.append(v)
                    if len(valrows) == 0:
                        self.vector[newvalue] = []
                    elif len(valrows) == 1:
                        self.vector[newvalue] = valrows[0]
                    else:
                        self.vector[newvalue] = soomfunc.union(*valrows)
                    if coalesce.label:
                        self.outtrans[newvalue] = coalesce.label
                    else:
                        vals = [self.col.do_outtrans(v) for v in vals]
                        self.outtrans[newvalue] = ', '.join(vals)
            for v in self.vector.keys():
                if v not in self.outtrans:
                    trans = self.col.do_outtrans(v)
                    if trans != v:
                        self.outtrans[v] = trans
            self.use_outtrans = bool(self.outtrans)
        self.keys = self.vector.keys()
        # Value suppression
        if condcol.suppress:
            suppress_set = None
            for op in condcol.suppress:
                if isinstance(op, retain):
                    if suppress_set is None:
                        suppress_set = sets.Set(self.keys)
                    suppress_set.difference_update(op.calc_values(self.keys))
                elif isinstance(op, suppress):
                    if suppress_set is None:
                        suppress_set = sets.Set()
                    suppress_set.union_update(op.calc_values(self.keys))
            self.suppress_set = suppress_set
        else:
            self.suppress_set = {}
        # Ordering
        if condcol.order and condcol.order.callable:
            self.keys.sort(condcol.order.callable)
        else:
            # Unconditionally sort keys so results are consistent, even if
            # order is arbitrary (ignoring col.is_ordered()).
            self.keys.sort()
            if condcol.order and condcol.order.values:
                prepend = []
                for v in condcol.order.values:
                    try:
                        self.keys.remove(v)
                    except ValueError:
                        pass
                    else:
                        prepend.append(v)
                self.keys = prepend + self.keys
        if condcol.order and isinstance(condcol.order, reversed):
            self.keys.reverse()

    def get_metadata(self):
        meta = {}
        for attr, srccol_value in self.col.get_metadata().items():
            if attr in ('multisourcecols', 'heterosourcecols'):
                continue
            condcol_value = getattr(self, attr, None)
            if attr == 'datatype':
                if self.col.is_multivalue():
                    condcol_value = 'recode'
            meta[attr] = condcol_value or srccol_value
        return meta

    def veckey_pairs(self, zeros):
        """ Returns a list of (value, row ids, suppress, condcol) tuples """
        return [(key, self.vector[key], key in self.suppress_set, self) 
                for key in self.keys 
                if zeros or len(self.vector[key]) > 0]

class SummCondCols(list):
    """
    A list representing the summary "conditioning columns" 
    """
    def extract_args(self, dataset, args):
        args_remain = []
        cols_seen = {}
        for arg in args:
            if type(arg) in (unicode, str):
                arg = condcol(arg)
            if isinstance(arg, condcol):
                if cols_seen.has_key(arg.colname):
                    raise Error('Column %r appears more than once' % 
                                arg.colname)
                cols_seen[arg.colname] = True
                self.append(SummCondCol(dataset, len(self), arg))
            elif isinstance(arg, CondColArg):
                raise Error("Use condcol('colname', %s(...)) instead!" %
                             arg.__class__.__name__)
            else:
                args_remain.append(arg)
        return self, args_remain

    def cols(self):
        return [condcol.col for condcol in self]

    def names(self):
        return [condcol.name for condcol in self]

    def veckey_pairs(self, zeros):
        return [condcol.veckey_pairs(zeros) for condcol in self]

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, 
                           ', '.join([c.name for c in self]))

class TempSummaryColumn:
    """
    Temporary column object for results of summarisation
    """
    def __init__(self, metadata):
        self.__dict__.update(metadata)
        self.data = []
    
    def fromargs(cls, name, label, datatype='float', coltype='scalar',**kwargs):
        return cls(dict(name=name, label=label, datatype=datatype, 
                        coltype=coltype, **kwargs))
    fromargs = classmethod(fromargs)

    def fromcondcol(cls, condcol):
        return cls(condcol.get_metadata())
    fromcondcol = classmethod(fromcondcol)

    def filter_rows(self, vector):
        self.data = [self.data[i] for i in vector]

    def todict(self):
        metadata = self.__dict__.copy()
        if not metadata['label']:
            metadata['label'] = metadata['name']
        metadata['mask'] = [v is None for v in self.data]
        return metadata

class TempSummarySet(dict):
    """
    Temporary dataset for results of summarisation prior to the
    result being turned into a real dataset object.
    """
    __slots__ = ('marginal_total_idx', 'marginal_total_rows', 
                 'suppressed_rows', 'colorder')
    def __init__(self):
        self.marginal_total_idx = {}
        self.marginal_total_rows = []
        self.suppressed_rows = []
        self.colorder = []

    def _addcol(self, col):
        self[col.name] = col
        self.colorder.append(col.name)
        return col

    def addcolumn(self, name, *args, **kwargs):
        return self._addcol(TempSummaryColumn.fromargs(name, *args, **kwargs))

    def addcolumnfromcondcol(self, condcol):
        return self._addcol(TempSummaryColumn.fromcondcol(condcol))

    def suppress_rows(self, suppress_marginal_totals=False):
        """ Remove marginal totals and suppressed rows from vectors """
        if (not (suppress_marginal_totals and self.marginal_total_rows)
            and not self.suppressed_rows):
            return
        all_rows = Numeric.arrayrange(len(self.values()[0].data))
        suppressed_rows = self.suppressed_rows
        if suppress_marginal_totals:
            suppressed_rows = soomfunc.union(suppressed_rows,
                                             self.marginal_total_rows) 
        non_mt_rows = soomfunc.outersect(all_rows, suppressed_rows)
        for col in self.values():
            col.filter_rows(non_mt_rows)

    def columntodataset(self, dataset):
        for colname in self.colorder:
            dataset.addcolumnfromseq(**self[colname].todict())

class SummaryRow(object):
    """
    A temporary object yielded by the Summarise.yield_rows() method
    """
    __slots__ = (
        'colnames', 'colvalues', 'count', 'extract', 'level',
        'suppress', 'type_string',
    )

    def __str__(self):
        colvals = ['%s=%s' % (c, v)
                   for c, v in zip(self.colnames,self.colvalues)]
        return 'lvl %d %s (%d rows)' % (self.level, ', '.join(colvals), 
                                         self.count)

class Summarise:
    def __init__(self, dataset, *args, **kwargs):
        self.dataset = dataset
        # process keyword args
        self.levels = kwargs.pop('levels', None)
        self.allcalc = kwargs.pop('allcalc', False)
        self.nomt = kwargs.pop('nomt', False)   # Suppress marginal totals
        self.proportions = kwargs.pop('proportions', False)
        self.default_weightcol = kwargs.pop('weightcol', self.dataset.weightcol)
        self.suppress_by_col = None
        self.zeros = kwargs.pop('zeros', False)
        suppress = kwargs.pop('suppress', None)
        if suppress:
            self.suppress_by_col = {}
            for colname, col_values in suppress.items():
                value_map = dict([(v, None) for v in col_values])
                self.suppress_by_col[colname] = value_map
        self.filtered_ds = self.dataset.filter(kwargs=kwargs)

        # process positional args, separating conditioning columns from
        # statistical methods.
        self.stat_methods, args = SummaryStats.extract(args, 
                                                       self.default_weightcol)
        self.stat_methods.check_args(dataset)
        self.condcols, args = SummCondCols().extract_args(self.filtered_ds, 
                                                          args)
        Utils.assert_args_exhausted(args)

        if self.proportions:
            self.allcalc = True
        if self.allcalc:
            self.levels = range(len(self.condcols)+1)
        elif self.levels is None:
            self.levels = [len(self.condcols)]

    def yield_rows(self):
        row = SummaryRow()
        isect_time = 0.0
        for item in Utils.combinations(*self.condcols.veckey_pairs(self.zeros)):
            row.level = len(item)
            row.suppress = False
            if row.level in self.levels:
                row.type_string = ['0'] * len(self.condcols)
                colnames = []
                colvalues = []
                intersect_rows = []
                for var_val, var_rows, suppress, condcol in item:
                    row.type_string[condcol.index] = '1'
                    intersect_rows.append(var_rows)
                    colnames.append(condcol.name)
                    colvalues.append(var_val)
                    if suppress:
                        row.suppress = True
                isect_start = time.time()
                if len(intersect_rows) == 0:
                    row.count = len(self.filtered_ds)
                    row.extract = self.filtered_ds
                else:
                    if len(intersect_rows) == 1:
                        cellrows = intersect_rows[0]
                    else:
                        cellrows = soomfunc.intersect(*intersect_rows)
                    row.count = len(cellrows)
                    row.extract = DatasetTake(self.dataset, cellrows)
                isect_time += time.time() - isect_start
                row.colnames = tuple(colnames)
                row.colvalues = tuple(colvalues)
                yield row
        soom.info('Summarise intersect() time: %.3f' % isect_time)

    def as_dict(self):
        start_time = time.time()

        freqcol = '_freq_'
        if self.proportions and self.default_weightcol:
            # proportions code needs to know weighted frequency
            wgtfreq_method = SummaryStats.freq()
            self.stat_methods.append(wgtfreq_method)
            freqcol = self.stat_methods.get_method_statcolname(wgtfreq_method)

        summaryset = TempSummarySet()
        summaryset.addcolumn('_freq_', 'Frequency', 'int', 'weighting')
        summaryset.addcolumn('_level_', 'Level', 'int', 'scalar')
        summaryset.addcolumn('_type_', 'Summary type', 'str', 'categorical')
        summaryset.addcolumn('_condcols_', 'Conditioning Columns', 
                                            'tuple', 'categorical')
        for condcol in self.condcols:
            summaryset.addcolumnfromcondcol(condcol)
        _freq = summaryset['_freq_'].data
        _level = summaryset['_level_'].data
        _type = summaryset['_type_'].data
        _condcols = summaryset['_condcols_'].data
        self.stat_methods.add_statcols(self.dataset, summaryset)
        row_ordinal = -1
        for row in self.yield_rows():
            row_ordinal += 1
            _freq.append(row.count)
            _level.append(row.level)
            _type.append(''.join(row.type_string))
            _condcols.append(row.colnames)
            for colname, colvalue in zip(row.colnames, row.colvalues):
                summaryset[colname].data.append(colvalue)
            if row.suppress:
                summaryset.suppressed_rows.append(row_ordinal)
            if row.level != len(self.condcols):
                mtvals = []
                for condcol in self.condcols:
                    if condcol.name not in row.colnames:
                        colvalue = condcol.col.all_value
                        summaryset[condcol.name].data.append(colvalue)
                    mtvals.append(summaryset[condcol.name].data[-1])
                summaryset.marginal_total_idx[tuple(mtvals)] = row_ordinal
                summaryset.marginal_total_rows.append(row_ordinal)
            self.stat_methods.calc(summaryset, row.extract)

        if self.proportions:
            allvals = [col.all_value for col in self.condcols.cols()]
            calc_props(summaryset, self.condcols.names(), allvals, freqcol)
        summaryset.suppress_rows(suppress_marginal_totals=self.nomt)
        soom.info('Summarise as_dict() time: %.3f' % (time.time() - start_time))
        return summaryset


def summ(self, *args, **kwargs):
    '''Summarise a Dataset

    summ(conditioning_columns..., stat_methods..., options...)

For example:

    summary_set = dataset.summ('sex', 'agegrp', 
                                mean('age'), median('age'), 
                                allcalc = True)

Options include:

    name                    name of summary set
    label                   summary set label
    allcalc                 calculate all combinations
    datasetpath             for persistent summary sets,
                            the dataset path.
    filtername              apply the named filter
    levels                  calculate combinations at the
                            specified levels, eg: 2 & 3 is '23'
    permanent               resulting summary dataset should
                            be written to disk.
    proportions

'''
    from SOOMv0.Dataset import SummarisedDataset

    starttime = time.time()
    # Method argument parsing
    label = kwargs.pop('label', None)
#    datasetpath = kwargs.pop('datasetpath', soom.default_object_path)
    name = kwargs.pop('name', None)
#    permanent = kwargs.pop('permanent', False)

    summarise = Summarise(self, *args, **kwargs)
    summaryset = summarise.as_dict()

    # print "summaryset:", # debug
    # print summaryset # debug

    soom.info('Summarise took %.3fs' % (time.time() - starttime))

    if not name:
        by = ['_by_%s' % condcol.name for condcol in summarise.condcols]
        name = 'sumof_%s%s' % (self.name, ''.join(by))
    if not label:
        label = self.label

    by = [' by %s' % condcol.col.label 
            for condcol in summarise.condcols]
    summ_label = ''.join(by)

    starttime = time.time()
    sumset = SummarisedDataset(name, label=label,
                            summ_label=summ_label,
                            filter_label=summarise.filtered_ds.filter_label,
#                            path=datasetpath, backed=permanent,
                            weightcol="_freq_",
                            date_created=summarise.filtered_ds.date_created,
                            date_updated=summarise.filtered_ds.date_updated)
    summaryset.columntodataset(sumset)
    sumset.stat_methods = summarise.stat_methods
    sumset.nonprintcols = ('_level_', '_type_', '_condcols_')
    soom.info('summary dict into dataset took %.3f' % (time.time() - starttime))
    return sumset
