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
# $Id: SummaryStats.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/SummaryStats.py,v $

from MA import Numeric
from SOOMv0 import Stats
from SOOMv0 import common

def label_or_name(col):
    if col.label:
        return col.label
    return col.name

class _UseDefault: pass

class _SummaryStatBase:
    usage = '(col, <weightcol=...>)'
    short_label = None

    def __init__(self, srccolname, weightcol = _UseDefault, **kwargs):
        self.srccolname = srccolname
        self.wgtcolname = weightcol
        self.args = []
        self.kwargs = kwargs

    def select_weightcol(self, default_weightcol):
        if self.wgtcolname == _UseDefault:
            return default_weightcol
        else:
            return self.wgtcolname

    def get_statcolname(self, default_weightcol):
        wgtcolname = self.select_weightcol(default_weightcol)
        colname = self.name_fmt % self.srccolname
        if wgtcolname:
            colname = '%s_wgtd_by_%s' % (colname, wgtcolname)
        return colname

    def get_label(self, dataset, default_weightcol):
        col = dataset[self.srccolname]
        label = '%s of %s' % (self.short_label or self.__doc__, 
                              label_or_name(col))
        wgtcolname = self.select_weightcol(default_weightcol)
        if wgtcolname:
            wgtcol = dataset[wgtcolname]
            label = '%s weighted by %s' % (label, label_or_name(wgtcol))
        return label

    def args_okay(self, dataset, default_weightcol):
        col = dataset.get_column(self.srccolname)
        if not col.is_scalar():
            raise common.Error('%s of %s column must be scalar' % 
                               self.__doc__, label_or_name(col))
        wgtcolname = self.select_weightcol(default_weightcol)
        if wgtcolname:
            wgtcol = dataset.get_column(wgtcolname)
            if not wgtcol.is_scalar():
                raise common.Error('%s weighting column %r must be scalar' % 
                                   self.__doc__, label_or_name(wgtcol))
            if not self.statcol_fns[1]:
                raise common.Error('%s method does not support weighting' %
                                   self.__doc__)

    def add_statcol(self, dataset, statcolname, summaryset, default_weightcol):
        label = self.get_label(dataset, default_weightcol)
        summaryset.addcolumn(statcolname, label)

    def _calc(self, statcolname, summaryset, colvectors, default_weightcol):
        col = colvectors[self.srccolname]
        wgtcolname = self.select_weightcol(default_weightcol)
        if wgtcolname:
            wgtcol = colvectors[wgtcolname]
        if col.data:
            statcol_fn, wgtd_statcol_fn = self.statcol_fns
            try:
                if wgtcolname:
                    return wgtd_statcol_fn(col.data, wgtcol.data,
                                           *self.args, **self.kwargs)
                else:
                    return statcol_fn(col.data, *self.args, **self.kwargs)
            except:
                import sys
                exc_type, exc_value, exc_tb = sys.exc_info()
                try:
                    if wgtcolname:
                        exc_str = '%s: %s (%r,%r,%r,%r)' % (statcolname, 
                                                         exc_value, col.data, 
                                                         wgtcol.data,
                                                         self.args, self.kwargs)
                    else:
                        exc_str = '%s: %s (%r,%r,%r)' % (statcolname, 
                                                         exc_value, col.data, 
                                                         self.args, self.kwargs)
                    raise exc_type, exc_str, exc_tb
                finally:
                    del exc_type, exc_value, exc_tb
        return None

    def calc(self, statcolname, summaryset, colvectors, default_weightcol):
        statdata = self._calc(statcolname, summaryset, colvectors, 
                              default_weightcol)
        summaryset[statcolname].data.append(statdata)

    def __repr__(self):
        params = []
        if hasattr(self, 'srccolname'):
            params.append(repr(self.srccolname))
        if self.wgtcolname != _UseDefault:
            params.append('wgtcolname=%r' % self.wgtcolname)
        if hasattr(self, 'args'):
            for arg in self.args:
                params.append(repr(a))
        for k, v in self.kwargs.items():
            params.append('%s=%r' % (k, v))
        return '%s(%s)' % (self.__class__.__name__, ', '.join(params))


class _CISummaryStatBase(_SummaryStatBase):
    def __init__(self, srccolname, weightcol=_UseDefault, 
                 conflev=0.95, **kwargs):
        _SummaryStatBase.__init__(self, srccolname, weightcol=weightcol, **kwargs)
        self.kwargs['conflev'] = self.conflev = conflev
    
    def add_statcol(self, dataset, statcolname, summaryset, default_weightcol):
        label = self.get_label(dataset, default_weightcol)
        conflev_label = ' (%g%% conf. limit)' % (self.conflev * 100)
        summaryset.addcolumn(statcolname + '_ll', 
                             'Lower limit of ' + label + conflev_label)
        summaryset.addcolumn(statcolname, label)
        summaryset.addcolumn(statcolname + '_ul', 
                             'Upper limit of ' + label + conflev_label)

    def calc(self, statcolname, summaryset, colvectors, default_weightcol):
        statdata = self._calc(statcolname, summaryset, 
                              colvectors, default_weightcol)
        if statdata:
            statdata, lower, upper = statdata
        else:
            statdata = lower = upper = None
        summaryset[statcolname].data.append(statdata)
        summaryset[statcolname+'_ll'].data.append(lower)
        summaryset[statcolname+'_ul'].data.append(upper)


class freq(_SummaryStatBase):
    'Frequency'
    usage = '(<weightcol=...>)'

    def __init__(self, weightcol = _UseDefault, **kwargs):
        self.wgtcolname = weightcol
        self.kwargs = kwargs

    def args_okay(self, dataset, default_weightcol):
        wgtcolname = self.select_weightcol(default_weightcol)
        if wgtcolname:
            wgtcol = dataset.get_column(wgtcolname)
            if not wgtcol.is_scalar():
                raise common.Error('%s weighting column %r must be scalar' % 
                                   self.__doc__, label_or_name(wgtcol))
    
    def get_statcolname(self, default_weightcol):
        wgtcolname = self.select_weightcol(default_weightcol)
        if wgtcolname:
            return 'freq_wgtd_by_%s' % wgtcolname
        return '_freq_'

    def get_label(self, dataset, default_weightcol):
        wgtcolname = self.select_weightcol(default_weightcol)
        label = 'Frequency'
        if wgtcolname:
            wgtcol = dataset[wgtcolname]
            label += ' weighted by %s' % label_or_name(wgtcol)
        return label

    def add_statcol(self, dataset, statcolname, summaryset, default_weightcol):
        wgtcolname = self.select_weightcol(default_weightcol)
        if wgtcolname:
            label = self.get_label(dataset, default_weightcol)
            summaryset.addcolumn(statcolname, label)

    def calc(self, statcolname, summaryset, colvectors, default_weightcol):
        # Odd one out - if not weighted, just reuse core _freq_ column.
        wgtcolname = self.select_weightcol(default_weightcol)
        if wgtcolname:
            wgtcol = colvectors[wgtcolname]
            summaryset[statcolname].data.append(Stats.wn(wgtcol.data, 
                                                         **self.kwargs))

class freqcl(freq):
    'Frequency (with confidence limits)'
    short_label = 'Frequency'

    def __init__(self, weightcol=_UseDefault, conflev=0.95, **kwargs):
        freq.__init__(self, weightcol=weightcol, **kwargs)
        self.kwargs['conflev'] = self.conflev = conflev

    def add_statcol(self, dataset, statcolname, summaryset, default_weightcol):
        label = self.get_label(dataset, default_weightcol)
        wgtcolname = self.select_weightcol(default_weightcol)
        if wgtcolname:
            summaryset.addcolumn(statcolname, label)
        conflev_label = ' (%g%% conf. limit)' % (self.conflev * 100)
        summaryset.addcolumn(statcolname + '_ll', 
                             'Lower limit of ' + label + conflev_label)
        summaryset.addcolumn(statcolname + '_ul', 
                             'Upper limit of ' + label + conflev_label)

    def calc(self, statcolname, summaryset, colvectors, default_weightcol):
        wgtcolname = self.select_weightcol(default_weightcol)
        if wgtcolname:
            wgtcol = colvectors[wgtcolname]
            statdata = Stats.wfreqcl(wgtcol.data, **self.kwargs)
        else:
            statdata = Stats.freqcl(len(colvectors), **self.kwargs)
        if statdata:
            statdata, lower, upper = statdata
        else:
            statdata = lower = upper = None
        if wgtcolname:
            summaryset[statcolname].data.append(statdata)
        summaryset[statcolname+'_ll'].data.append(lower)
        summaryset[statcolname+'_ul'].data.append(upper)
    
class asum(_SummaryStatBase):
    'Sum'

    name_fmt = 'sum_of_%s'
    statcol_fns = Stats.asum, Stats.wsum

class mean(_SummaryStatBase):
    'Mean'

    name_fmt = 'mean_of_%s'
    statcol_fns = Stats.amean, Stats.wamean

class meancl(_CISummaryStatBase):
    'Mean (with confidence limits)'
    short_label = 'Mean'

    name_fmt = 'mean_of_%s'
    statcol_fns = Stats.ameancl, Stats.wameancl

class geomean(_SummaryStatBase):
    'Geometric Mean'

    name_fmt = 'geomean_of_%s'
    statcol_fns = Stats.geomean, Stats.wgeomean

class minimum(_SummaryStatBase):
    'Minimum'

    name_fmt = 'minimum_of_%s'
    statcol_fns = Stats.aminimum, Stats.wminimum

class maximum(_SummaryStatBase):
    'Maximum'

    name_fmt = 'maximum_of_%s'
    statcol_fns = Stats.amaximum, Stats.wmaximum

class arange(_SummaryStatBase):
    'Range'

    name_fmt = 'range_of_%s'
    statcol_fns = Stats.arange, Stats.wrange

class median(_SummaryStatBase):
    'Median'

    name_fmt = 'median_of_%s'
    statcol_fns = Stats.median, Stats.wmedian

class p10(_SummaryStatBase):
    '10th Percentile'

    name_fmt = 'p10_of_%s'
    statcol_fns = Stats.quantile, Stats.wquantile

    def __init__(self, srccolname, **kwargs):
        _SummaryStatBase.__init__(self, srccolname, **kwargs)
        self.args.append(0.10)


class p25(_SummaryStatBase):
    '25th Percentile'

    name_fmt = 'p25_of_%s'
    statcol_fns = Stats.quantile, Stats.wquantile

    def __init__(self, srccolname, **kwargs):
        _SummaryStatBase.__init__(self, srccolname, **kwargs)
        self.args.append(0.25)


class p75(_SummaryStatBase):
    '75th Percentile'

    name_fmt = 'p75_of_%s'
    statcol_fns = Stats.quantile, Stats.wquantile

    def __init__(self, srccolname, **kwargs):
        _SummaryStatBase.__init__(self, srccolname, **kwargs)
        self.args.append(0.75)


class p90(_SummaryStatBase):
    '90th Percentile'

    name_fmt = 'p90_of_%s'
    statcol_fns = Stats.quantile, Stats.wquantile

    def __init__(self, srccolname, **kwargs):
        _SummaryStatBase.__init__(self, srccolname, **kwargs)
        self.args.append(0.90)


class quantile(_SummaryStatBase):
    'Percentile'

    statcol_fns = Stats.quantile, Stats.wquantile

    def __init__(self, srccolname, p, **kwargs):
        _SummaryStatBase.__init__(self, srccolname, **kwargs)
        percent = int(round(p * 100))
        sufidx = percent % 10
        suffix = 'th'
        if sufidx <= 3:
            suffix = ['th', 'st', 'nd', 'rd'][sufidx]
        self.name_fmt = 'p%02d_of_%%s' % percent
        self.__doc__ = '%d%s %s' % (percent, suffix, self.__doc__)
        self.args.append(p)

class samplevar(_SummaryStatBase):
    'Sample Variance'

    name_fmt = 'samplevar_of_%s'
    statcol_fns = Stats.samplevar, Stats.wsamplevar

class popvar(_SummaryStatBase):
    'Population Variance'

    name_fmt = 'popvar_of_%s'
    statcol_fns = Stats.populationvar, Stats.wpopulationvar

class stddev(_SummaryStatBase):
    'Sample Standard Deviation'

    name_fmt = 'samplestddev_of_%s'
    statcol_fns = Stats.sample_stddev, Stats.wsample_stddev

class popstddev(_SummaryStatBase):
    'Population Standard Deviation'

    name_fmt = 'popstddev_of_%s'
    statcol_fns = Stats.population_stddev, Stats.wpopulation_stddev

class samplecv(_SummaryStatBase):
    'Sample Co-efficient of Variation'

    name_fmt = 'samplecv_of_%s'
    statcol_fns = Stats.sample_cv, Stats.wsample_cv

class popcv(_SummaryStatBase):
    'Population Co-efficient of Variation'

    name_fmt = 'popcv_of_%s'
    statcol_fns = Stats.population_cv, Stats.wpopulation_cv

class stderr(_SummaryStatBase):
    'Standard Error'

    name_fmt = 'stderr_of_%s'
    statcol_fns = Stats.stderr, Stats.wstderr

class nonmissing(_SummaryStatBase):
    'Count of non-missing values'

    name_fmt = 'nonmissing_of_%s'
    statcol_fns = Stats.nonmissing, Stats.wnonmissing

class missing(_SummaryStatBase):
    'Count of missing values'

    name_fmt = 'missing_of_%s'
    statcol_fns = Stats.missing, Stats.wmissing

class studentt(_SummaryStatBase):
    'Student\'s T'

    name_fmt = 't_of_%s'
    statcol_fns = Stats.t, None

class applyto(_SummaryStatBase):
    'Apply method(s) to column(s)'
    usage = '(cols..., methods..., options...)'

    def __init__(self, *args, **kwargs):
        stat_classes = []
        cols = []
        for arg in args:
            if type(arg) in (unicode, str):
                cols.append(arg)
            else:
                stat_classes.append(arg)
        self.stat_methods = [cls(col, **kwargs) 
                             for cls in stat_classes
                             for col in cols]

def isstatmethod(arg):
    return isinstance(arg, _SummaryStatBase)

class StatMethods:
    """
    A collection of statistical methods (and associated parameters)
    """
    def __init__(self, default_weightcol):
        self.by_statcolname = {}
        self.in_order = []
        self.default_weightcol = default_weightcol

    def append(self, method):
        statcolname = method.get_statcolname(self.default_weightcol)
        if not self.by_statcolname.has_key(statcolname):
            self.by_statcolname[statcolname] = method
            self.in_order.append((statcolname, method))

    def __getitem__(self, statcolname):
        return self.by_statcolname[statcolname]

    def __iter__(self):
        return iter(self.in_order)

    def get_method_statcolname(self, method):
        return method.get_statcolname(self.default_weightcol)

    def check_args(self, dataset):
        for statcolname, stat_method in self:
            stat_method.args_okay(dataset, self.default_weightcol)

    def add_statcols(self, dataset, summaryset):
        for statcolname, stat_method in self:
            stat_method.add_statcol(dataset, statcolname, summaryset, 
                                    self.default_weightcol)

    def calc(self, summaryset, colvectors):
        for statcolname, stat_method in self:
            stat_method.calc(statcolname, summaryset, colvectors, 
                             self.default_weightcol)

def extract(args, default_weightcol = None):
    args_remain = []
    stat_methods = StatMethods(default_weightcol)
    for arg in args:
        if isinstance(arg, applyto):
            for stat_method in arg.stat_methods:
                stat_methods.append(stat_method)
        elif isstatmethod(arg):
            stat_methods.append(arg)
        else:
            args_remain.append(arg)
    return stat_methods, args_remain

def stat_methods():
    items = globals().items()
    items.sort()
    methods = []
    for name, obj in items:
        try:
            if not name.startswith('_') and issubclass(obj, _SummaryStatBase):
                methods.append(obj)
        except TypeError:
            pass
    return methods

def stat_method_help():
    help = ['Stat methods are optional. They include:']
    for obj in stat_methods():
        usage = obj.__name__ + obj.usage
        help.append('    %-40s %s' % (usage, obj.__doc__))
    return '\n'.join(help)

#del Stats, Numeric              # Keep namespace clean
