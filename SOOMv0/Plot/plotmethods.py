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
# $Id: plotmethods.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Plot/plotmethods.py,v $

# Standard Python modules
import sys

# 3rd Party modules
from rpy import *

# SOOM bits
from SOOMv0.common import *

# SOOM.Plot bits
import rplot

class KWArgMap:
    def __init__(self, *args, **mapped):
        self.args = args
        self.mapped = mapped

    def apply(self, dest, source, unused):
        def _set(d, s):
            try:
                dest[d] = source[s]
            except KeyError:
                pass
            else:
                try:
                    del unused[s]
                except KeyError:
                    pass
        for v in self.args:
            if isinstance(v, KWArgMap):
                v.apply(dest, source, unused)
            else:
                _set(v, v)
        for k, v in self.mapped.items():
            _set(k, v)
        return dest


class KWArgs:
    """
    Magic repository of keyword args

    When instances are called, they yield up (potentially remapped)
    keyword args. When all arg processing is complete, assert_all_used
    can be called to check that there are no unused arguments.
    """

    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.unused = dict(kwargs)        # Copy

    def __call__(self, *args, **mapped):
        return KWArgMap(*args, **mapped).apply({}, self.kwargs, self.unused)

    def assert_all_used(self):
        if self.unused:
            params = self.unused.keys()
            params.sort()
            raise TypeError('Unknown parameter(s): %s' % ', '.join(params))

# "Canned" argument sets
filter_args = KWArgMap('nofilter', 'filtername', 'filterexpr', 'filterlabel')
common_args = KWArgMap('title', 'footer', 'debug')
compan_args = KWArgMap('layout', 'xlim', 'ylim')
yaxis_args = KWArgMap(ticks='yticks', 
                      labelrotate='ylabelrotate')
xaxis_args = KWArgMap(ticks='xticks', 
                      labelrotate='xlabelrotate')


class histogram(rplot.RLatticeBinPlot):
    label = 'Distribution'
    rmethod = 'histogram'
    autosample = True
    # Complete

    def __init__(self, ds, *args, **kwargs):
        super(histogram, self).__init__(ds)
        if args:
            self.procargs(ds, *args, **kwargs)
            self.plot(ds)

    def procargs(self, ds, measurecol, *condcols, **kwargs):
        kwargs = KWArgs(kwargs)
        self.add_filter(**kwargs(filter_args))
        self.set_params(**kwargs(common_args, compan_args, 'bins', 'sample'))
        self.add_percent(ds, **kwargs('hist_type', yaxis_args))
        self.add_continuous(ds, measurecol, **kwargs(xaxis_args))
        for colname in condcols:
            self.add_discrete(ds, colname)
        kwargs.assert_all_used()


class densityplot(rplot.RLatticeBinPlot):
    label = 'Density'
    rmethod = 'densityplot'
    autosample = True
    # Complete?

    def __init__(self, ds, *args, **kwargs):
        super(densityplot, self).__init__(ds)
        if args:
            self.procargs(ds, *args, **kwargs)
            self.plot(ds)

    def procargs(self, ds, measurecol, *condcols, **kwargs):
        kwargs = KWArgs(kwargs)
        self.add_filter(**kwargs(filter_args))
        self.set_params(**kwargs(common_args, compan_args,
                                 'bins', 'line_width', 'line_style', 'sample'))
        self.add_density(ds, **kwargs('plot_points', 'ref', yaxis_args))
        self.add_continuous(ds, measurecol, **kwargs(xaxis_args))
        for colname in condcols:
            self.add_discrete(ds, colname)
        kwargs.assert_all_used()


class scatterplot(rplot.RLatticePlot):
    label = 'Scatter plot'
    rmethod = 'xyplot'
    autosample = True

    def __init__(self, ds, *args, **kwargs):
        super(scatterplot, self).__init__(ds)
        if args:
            self.procargs(ds, *args, **kwargs)
            self.plot(ds)

    def procargs(self, ds, xcolname, ycolname, *condcols, **kwargs):
        kwargs = KWArgs(kwargs)
        self.add_filter(**kwargs(filter_args))
        self.set_params(**kwargs(common_args, compan_args,
                                 'horizontal', 'vertical', 
                                 'point_style', 'sample'))
        self.add_continuous(ds, ycolname, **kwargs(yaxis_args, 
                                logscale='logyscale')) 
        self.add_continuous(ds, xcolname, **kwargs(xaxis_args,
                                logscale='logxscale')) 
        for colname in condcols:
            self.add_discrete(ds, colname)
        kwargs.assert_all_used()


class scattermatrix(rplot.RLatticeMatrixPlot):
    label = 'Scatter plot matrices'
    rmethod = 'splom'
    autosample = True

    def __init__(self, ds, *args, **kwargs):
        super(scattermatrix, self).__init__(ds)
        if args:
            self.procargs(ds, *args, **kwargs)
            self.plot(ds)

    def procargs(self, ds, *cols, **kwargs):
        kwargs = KWArgs(kwargs)
        self.add_filter(**kwargs(filter_args))
        self.set_params(**kwargs(common_args, compan_args,
                                 'horizontal', 'vertical', 
                                 'point_style', 'sample'))
        if len(cols) < 2:
            raise PlotError('must specify at least 2 continuous columns')
        for colname in cols:
            self.add_any(ds, colname)
        self.add_groupby(ds, **kwargs('groupby'))
        kwargs.assert_all_used()


class boxplot(rplot.RLatticeBoxPlot):
    label = 'Box and whisker plot'
    rmethod = 'bwplot'
    autosample = True

    def __init__(self, ds, *args, **kwargs):
        super(boxplot, self).__init__(ds)
        if args:
            self.procargs(ds, *args, **kwargs)
            self.plot(ds)

    def procargs(self, ds, measurecol, xcolname, *condcols, **kwargs):
        kwargs = KWArgs(kwargs)
        self.set_params(**kwargs(common_args, compan_args,
                                 'horizontal', 'vertical',
                                 'line_width', 'line_style', 'sample',
                                 'notches', 'outliers', 'variable_width',
                                 'violins'))
        self.add_filter(**kwargs(filter_args))
        self.add_continuous(ds, measurecol, **kwargs(yaxis_args, 
                                logscale='logyscale'))
        self.add_discrete(ds, xcolname, **kwargs(labelrotate='xlabelrotate'))
        for colname in condcols:
            self.add_discrete(ds, colname)
        kwargs.assert_all_used()


class lineplot(rplot.RLatticeSummPlot):
    label = 'Line plot'
    rmethod = 'xyplot'

    def __init__(self, ds, *args, **kwargs):
        super(lineplot, self).__init__(ds)
        self.horizontal = True
        self.r_args['type'] = 'l'
        if args:
            self.procargs(ds, *args, **kwargs)
            self.plot(ds)

    def procargs(self, ds, xcolname, *condcols, **kwargs):
        kwargs = KWArgs(kwargs)
        self.set_params(**kwargs(common_args, compan_args,
                                 'weightcol', 'horizontal', 'vertical', 
                                 'line_width', 'line_style', 'conflev'))
        self.add_filter(**kwargs(filter_args))
        self.add_discrete(ds, xcolname, 
                            **kwargs(labelrotate='xlabelrotate'))
        self.add_measure(ds, **kwargs('measure', yaxis_args,
                                logscale='logyscale'))
        self.add_groupby(ds, **kwargs('groupby'))
        for colname in condcols:
            self.add_discrete(ds, colname)
        kwargs.assert_all_used()


class barchart(rplot.RLatticeCatPlot):
    label = 'Barchart'
    rmethod = 'barchart'

    def __init__(self, ds, *args, **kwargs):
        super(barchart, self).__init__(ds)
        if args:
            self.procargs(ds, *args, **kwargs)
            self.plot(ds)

    def procargs(self, ds, xcolname, *condcols, **kwargs):
        kwargs = KWArgs(kwargs)
        self.set_params(**kwargs(common_args, compan_args,
                                 'weightcol', 'horizontal', 'vertical', 
                                 'origin', 'reference', 'pack', 'conflev'))
        self.add_filter(**kwargs(filter_args))
        self.add_measure(ds, **kwargs('measure', yaxis_args,
                                logscale='logyscale'))
        self.add_discrete(ds, xcolname, 
                            **kwargs(labelrotate='xlabelrotate'))
        self.add_groupby(ds, **kwargs('groupby', 'stackby'))
        for colname in condcols:
            self.add_discrete(ds, colname)
        kwargs.assert_all_used()
    

class dotchart(rplot.RLatticeCatPlot):
    label = 'Dotplot'
    rmethod = 'dotplot'

    def __init__(self, ds, *args, **kwargs):
        super(dotchart, self).__init__(ds)
        if args:
            self.procargs(ds, *args, **kwargs)
            self.plot(ds)

    def procargs(self, ds, xcolname, *condcols, **kwargs):
        kwargs = KWArgs(kwargs)
        self.set_params(**kwargs(common_args, compan_args,
                                 'weightcol', 'horizontal', 'vertical',
                                 'point_size', 'point_style',
                                 'origin', 'reference', 'conflev'))
        self.add_filter(**kwargs(filter_args))
        self.add_measure(ds, **kwargs('measure', yaxis_args,
                                logscale='logyscale'))
        self.add_discrete(ds, xcolname, 
                                **kwargs(labelrotate='xlabelrotate'))
        self.add_groupby(ds, **kwargs('groupby'))
        for colname in condcols:
            self.add_discrete(ds, colname)
        kwargs.assert_all_used()
    

class piechart(rplot.RPlot):
    label = 'Pie Chart'
    rmethod = 'pie'

    def __init__(self, ds, *args, **kwargs):
        raise NotImplemented
        super(densityplot, self).__init__(ds)
        if args:
            plotargs = _plotutils.PlotArgs(ds, *condcols, 
                                        **dict(kwargs, measure=measurecol))
            ds = plotargs.summarised_dataset
            kwargs = KWArgs(kwargs)
            self.add_discrete(ds, measurecol)
            kwargs.assert_all_used()
            self.plot(ds)

class fourfold(rplot.TwoByTwoPlot):
    label = 'Fourfold 2 x 2 x k'
    rmethod = 'fourfold'

    def __init__(self, ds, *args, **kwargs):
        super(fourfold, self).__init__(ds)
        if args:
            self.procargs(ds, *args, **kwargs)
            self.plot(ds)

    def procargs(self, ds, sidecol, topcol, stratacol=None, **kwargs):
        kwargs = KWArgs(kwargs)
        self.set_params(**kwargs(common_args, 'weightcol', 'margin', 'conflev',
                                 'extended', 'std'))
        self.add_filter(**kwargs(filter_args))
        self.add_discrete(ds, topcol, 
                                **kwargs(labelrotate='xlabelrotate'))
        self.add_discrete(ds, sidecol, 
                                **kwargs(labelrotate='ylabelrotate'))
        if stratacol is not None:
            self.add_discrete(ds, stratacol)
        kwargs.assert_all_used()
