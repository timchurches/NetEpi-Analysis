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
# $Id: rplot.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Plot/rplot.py,v $

# Standard Python modules
import sys
import textwrap
import sets

# 3rd Party modules
import RandomArray
from rpy import *

# SOOM bits
from SOOMv0.SummaryStats import freq
from SOOMv0.Filter import sampled_ds
from SOOMv0.common import *

# SOOM.Plot bits
from SOOMv0.Plot import panelfn, rconv
import raxis
import _output

class RArgs(dict):
    """
    Container for arguments to be passed to the R plot function.
    """


class SummArgs:
    """
    Container for arguments to be passed to the SOOM summ() method.
    """
    def __init__(self, *args, **kwargs):
        self.condcols = []
        self.kwargs = dict(*args, **kwargs)

    def set_kw(self, name, value):
        self.kwargs[name] = value

    def add_condcol(self, condcol):
        if condcol and condcol != '_freq_':
            try:
                i = self.condcols.index(condcol)
            except ValueError:
                self.condcols.append(condcol)
            else:
                # condcol()'s override str specifications
                if not isinstance(condcol, basestring):
                    self.condcols[i] = condcol


class RPlotBase(object):
    dates_as_factor = False

    def __init__(self, ds, debug=False):
        if not hasattr(ds, 'name') or not hasattr(ds, 'get_column'):
            raise AttributeError('first argument must be a dataset')
        if not ds:
            raise PlotError('dataset is empty')
        self.debug = debug
        self.r_args = RArgs()
        self.filter_args = {}
        self.condcols = []
        self.title = None
        self.footer = None

    def add_percent(self, ds, **kwargs):
        self.condcols.append(raxis.RPercentAxisCol(ds, **kwargs))

    def add_density(self, ds, **kwargs):
        self.condcols.append(raxis.RDensityAxisCol(ds, **kwargs))

    def add_continuous(self, ds, colname, **kwargs):
        self.condcols.append(raxis.RContinuousCondCol(ds, colname, **kwargs))

    def add_discrete(self, ds, colname, **kwargs):
        self.condcols.append(raxis.RDiscreteCondCol(ds, colname, **kwargs))

    def add_any(self, ds, colname, **kwargs):
        if ds[colname].is_discrete():
            self.add_discrete(ds, colname, **kwargs)
        else:
            self.add_continuous(ds, colname, **kwargs)

    def add_filter(self, **kwargs):
        self.filter_args = kwargs

    def set_params(self, title=None, footer=None, debug=None):
        if title is not None:
            self.title = title.replace('\r', '')
        if footer is not None:
            self.footer = footer.replace('\r', '')
        if debug is not None:
            self.debug = debug

    def get_title(self, ds):
        if self.title is not None:
            return self.title
        labels = []
        cols = sets.Set()
        for condcol in self.condcols:
            if condcol.colname not in cols:
                label = condcol.title(ds)
                if label:
                    cols.add(condcol.colname)
                    labels.append(label)
        title = ' by '.join(labels)
        if self.label:
            title = '%s of %s' % (self.label, title)
        return title

    def get_footer(self, ds):
        if self.footer is not None:
            return self.footer
        return str(ds.describe(NO_DETAIL))

    def get_filtered_ds(self, ds):
        filtered_ds = ds.filter(kwargs=dict(self.filter_args))
        if not filtered_ds:
            raise PlotError('filter returns no records')
        return filtered_ds

    def to_r_args(self, ds):
        title = str(self.get_title(ds))
        if title:
            self.r_args['main'] = rconv.rwrap(title, 1.2)
        footer = self.get_footer(ds)
        if footer:
            self.r_args['sub'] = rconv.rwrap(footer)

    def get_rmethod(self):
        return getattr(r, self.rmethod)


class SummPlotMixin(object):
    def __init__(self, ds):
        super(SummPlotMixin, self).__init__(ds)
        self.weightcol = None

    def set_params(self, weightcol=None, **kwargs):
        super(SummPlotMixin, self).set_params(**kwargs)
        if weightcol:
            self.weightcol = weightcol

    def get_weightcol(self, ds):
        if self.weightcol:
            return self.weightcol
        return ds.weightcol

    def get_filtered_ds(self, ds):
        if ds.is_summarised():
            summ_ds = ds
        else:
            summargs = SummArgs(self.filter_args,
                                weightcol=self.get_weightcol(ds),
                                nomt=True)
            for condcol in self.condcols:
                condcol.to_summ_args(summargs)
            if self.debug: print 'summ:', summargs
            summ_ds = ds.summ(*summargs.condcols, **summargs.kwargs)
        if not summ_ds:
            raise PlotError('summarisation yields an empty dataset')
        return summ_ds


class RPlot(RPlotBase):
    """
    Interface to traditional R plots (no panelling)
    """

    def plot(self, ds):
        _output.dev.new_page()

        rpy_mode = get_default_mode()
        try:
            # Don't convert R objects to Python objects by default
            set_default_mode(NO_CONVERSION)
            rmethod = self.get_rmethod()
            self.to_r_args(ds)
            data = self.condcols.to_r(ds)
            r.print_(rmethod(model, data=frame, **self.r_args))
        finally:
            set_default_mode(rpy_mode)


class RLatticePlotBase(RPlotBase):
    """
    Interface to R lattice (panelling) plots
    """
    def __init__(self, ds):
        super(RLatticePlotBase, self).__init__(ds)
        self.line_width = 2
        self.line_style = 1
        self.point_style = 19
        self.horizontal = False
        self.layout = None
        self.xlim = self.ylim = None
        self.grouping = False
        self.conflev = None

    def get_title(self, ds):
        title = super(RLatticePlotBase, self).get_title(ds)
        if self.conflev is not None:
            title += ' (%g%% conf. limits)' % (self.conflev * 100)
        return title

    def _get_model(self):
        mod_str = []
        for condcol in self.condcols:
            rname = condcol.rname()
            if rname is None:
                continue
            if len(mod_str) == 1:
                mod_str.append('~')
            elif len(mod_str) == 3:
                mod_str.append('|')
            elif len(mod_str) > 3:
                mod_str.append('*')
            mod_str.append(rname)
        if self.horizontal:
            mod_str[0], mod_str[2] = mod_str[2], mod_str[0]
        mod_str = ' '.join(mod_str)
        if self.debug: print >> sys.stderr, 'model: %r' % mod_str
        try:
            return r(mod_str)
        except:
            exc_type, exc_val, exc_tb = sys.exc_info()
            try:
                raise exc_type, '%s (mod_str: %s)' % (exc_val, mod_str), exc_tb
            finally:
                del exc_type, exc_val, exc_tb

    def _get_frame(self, ds):
        frame = {}
        for i, condcol in enumerate(self.condcols):
            dates_as_factor = i > 1 or self.dates_as_factor
            condcol.to_frame(frame, ds, dates_as_factor=dates_as_factor)
        if self.debug: 
            for key, value in frame.items():
                if isinstance(value, type(r.eval)):
                    print >> sys.stderr, 'frame: %r: ' % key
                    r.print_(value)
                else:
                    print >> sys.stderr, 'frame: %r: %r' % (key, value)
        try:
            return r.data_frame(**frame)
        except Exception, e:
            if 1:
                print >> sys.stderr, 'Frame:'
                cols = frame.keys()
                cols.sort()
                for col in cols:
                    print '--- %r ---' % col
                    r.print_(frame[col])
            raise

    def _set_trellis_params(self, value, attr, *params):
        trellis_params = with_mode(BASIC_CONVERSION, r.trellis_par_get)()
        for param_name in params:
            param = trellis_params[param_name]
            if isinstance(param[attr], list):
                param[attr] = [value] * len(param[attr])
            else:
                param[attr] = value
            with_mode(BASIC_CONVERSION, r.trellis_par_set)(param_name, param)

    def _set_line_width(self, line_width=2):
        self._set_trellis_params(float(line_width), 'lwd',
                                 'plot.line', 'superpose.line', 'add.line',
                                 'box.rectangle', 'box.umbrella')

    def _set_line_style(self, line_style=1):
        self._set_trellis_params(line_style, 'lty',
                                 'plot.line', 'superpose.line', 'add.line',
                                 'box.rectangle', 'box.umbrella')

    def _set_point_style(self, point_style=19):
        self._set_trellis_params(point_style, 'pch', 
                                 'dot.symbol', 'plot.symbol', 
                                 'superpose.symbol')

    def set_params(self, line_width=None, line_style=None, point_style=None, 
                   horizontal=None, vertical=None, layout=None, 
                   xlim=None, ylim=None, conflev=None, **kwargs):
        super(RLatticePlotBase, self).set_params(**kwargs)
        if line_width is not None:
            self.line_width = line_width
        if line_style is not None:
            self.line_style = line_style
        if point_style is not None:
            self.point_style = point_style
        if horizontal is not None:
            self.horizontal = horizontal
        if vertical is not None:
            self.horizontal = not vertical
        if layout is not None:
            self.layout = layout
        if xlim is not None:
            self.xlim = xlim
        if ylim is not None:
            self.ylim = ylim
        if conflev is not None:
            if conflev <= 0 or conflev > 1:
                raise PlotError('conflev argument must be between 0 and 1')
            self.conflev = conflev

    def to_r_args(self, ds):
        super(RLatticePlotBase, self).to_r_args(ds)
        npanels = 1
        for condcol in self.condcols[2:]:
            if condcol.colname and ds[condcol.colname].is_discrete():
                npanels *= ds[condcol.colname].cardinality()
        if self.layout is not None:
            self.r_args['layout'] = self.layout
        if self.xlim is not None:
            self.r_args['xlim'] = self.xlim
        if self.ylim is not None:
            self.r_args['ylim'] = self.ylim
        self.r_args['par_strip_text'] = r.list(lines=2,cex=.8)
        for i, condcol in enumerate(self.condcols):
            axis = None
            if self.horizontal:
                if i == 0: axis = 'x'
                elif i == 1: axis = 'y'
            else:
                if i == 0: axis = 'y'
                elif i == 1: axis = 'x'
            condcol.to_r_args(ds, self, self.r_args, axis, npanels)

    def _lattice_init(self):
        r.library('lattice')
        _output.dev.new_page(r.trellis_device)
        # the set the background to white, not the default grey...
        r('trellis.par.set(theme=list(background = list(col = "white")))')

        self._set_line_width(self.line_width)
        self._set_line_style(self.line_style)
        self._set_point_style(self.point_style)


    def _rplot(self, model, *args, **kwargs):
        rmethod = self.get_rmethod()
        try:
            r.print_(rmethod(model, *args, **kwargs), newpage=False)
        except RException, e:
            if self.debug:
                print 'Method:', self.rmethod
                print 'KWargs:', kwargs
                print 'Model:'
                r.print_(model)
                #print 'Data:'
                #r.print_(bcd)
            raise PlotError('R: %s' % e)


    def plot(self, ds):
        if not self.condcols:
            raise PlotError('No columns to plot?')
        self._lattice_init()
        filtered_ds = self.get_filtered_ds(ds)

        rpy_mode = get_default_mode()
        try:
            set_default_mode(NO_CONVERSION)
            model = self._get_model()
            frame = self._get_frame(filtered_ds)
            self.to_r_args(filtered_ds)
            if self.debug: print 'r_args:', self.r_args
            # Most plot types are satisfied with the frame being passed via the
            # "data" argument, but matrix scatter plots and CI bars need to
            # access it directly, so we put it into the R environment.
            r.assign('plotframe', frame)
            try:
                self._rplot(model, data=frame, **self.r_args)
            finally:
                r.remove('plotframe')
            _output.dev.done()
        finally:
            set_default_mode(rpy_mode)


class RLatticePlot(RLatticePlotBase):
    autosample = False                  # Sample if len(ds) > sample_target
    sample_target = 100000              # Biggest vector R will handle quickly

    def __init__(self, ds):
        super(RLatticePlot, self).__init__(ds)
        self.sample = None

    def set_params(self, sample=None, conflev=None, **kwargs):
        super(RLatticePlot, self).set_params(**kwargs)
        if sample is not None:
            if sample <= 0 or sample > 1:
                raise PlotError('sample argument must be between 0 and 1')
            self.sample = sample

    def get_filtered_ds(self, ds):
        ds = super(RLatticePlot, self).get_filtered_ds(ds)
        if self.sample is not None:
            if self.sample < 1:
                ds = sampled_ds(ds, self.sample)
        elif self.autosample:
            if len(ds) > self.sample_target:
                ds = sampled_ds(ds, float(self.sample_target) / len(ds))
        return ds


class RLatticeMatrixPlot(RLatticePlot):

    def add_groupby(self, ds, groupby=None, stackby=None, **kwargs):
        if groupby or stackby:
            self.condcols.append(raxis.RGroupByCol(ds, groupby=groupby,
                                                   stackby=stackby, **kwargs))

    def to_r_args(self, ds):
        super(RLatticeMatrixPlot, self).to_r_args(ds)
        # xlab and ylab don't make sense for this plot type
        del self.r_args['xlab'], self.r_args['ylab']
        self.r_args['varnames'] = [condcol.title(ds) 
                                   for condcol in self.condcols
                                   if condcol.rname()]

    def _get_model(self):
        return r('~plotframe')


class RLatticeBinPlot(RLatticePlot):

    def __init__(self, ds):
        super(RLatticeBinPlot, self).__init__(ds)
        self.bins = None

    def set_params(self, bins=None, **kwargs):
        super(RLatticeBinPlot, self).set_params(**kwargs)
        if bins is not None:
            self.bins = bins
        if kwargs.has_key('horizontal'):
            raise AttributeError('"horizontal" not supported')

    def to_r_args(self, ds):
        super(RLatticeBinPlot, self).to_r_args(ds)
        if self.bins is not None:
            self.r_args['n'] = int(self.bins)


class RLatticeBoxPlot(RLatticePlot):

    def __init__(self, ds):
        super(RLatticeBoxPlot, self).__init__(ds)
        self.notches = True
        self.outliers = True
        self.variable_width = True
        self.violins = False

    def set_params(self, notches=None, outliers=None, 
                   variable_width=None, violins=None, **kwargs):
        super(RLatticeBoxPlot, self).set_params(**kwargs)
        if notches is not None:
            self.notches = notches
        if outliers is not None:
            self.outliers = outliers
        if variable_width is not None:
            self.variable_width = variable_width
        if violins is not None:
            self.violins = violins

    def to_r_args(self, ds):
        super(RLatticeBoxPlot, self).to_r_args(ds)
        self.r_args['varwidth'] = bool(self.variable_width)
        self.r_args['horizontal'] = bool(self.horizontal)
        # Following two don't work - speculate bwplot doesn't support these
        # but the core boxplot does? 
        self.r_args['do_conf'] = bool(self.notches)
        self.r_args['do_out'] = bool(self.outliers)
        if self.violins:
            self.r_args['panel'] = panelfn.violin_panel()


class RLatticeSummPlot(SummPlotMixin,RLatticePlotBase):

    def __init__(self, ds):
        super(RLatticeSummPlot, self).__init__(ds)
        self.pack = False

    def set_params(self, pack=None, **kwargs):
        super(RLatticeSummPlot, self).set_params(**kwargs)
        if pack is not None:
            self.pack = pack

#    def get_footer(self, ds):
#        # We need to find a way to get the source dataset description, 
#        # but include the filter description (i.e., the description of
#        # the filtered_ds internal to the summ method).
#        return ds.short_description()

    def add_measure(self, ds, measure=None, axislabel=None, **kwargs):
        if measure is None:
            measure = '_freq_'
        # AM - This was a mistake:
        # if type(measure) in (str, unicode) and measure != '_freq_':
        #    measure = [measure]         # implicit proportion
        weightcol=self.get_weightcol(ds)
        if type(measure) in (list, tuple):
            measurecol = raxis.RPropnMeasureCol(ds, measure, 
                                                axislabel=axislabel,
                                                **kwargs)
        else:
            if isinstance(measure, basestring):
                colname = measure
            else:
                # should be a stat method
                try:
                    get_statcolname = measure.get_statcolname
                except AttributeError:
                    raise AttributeError('measure column should be a stat '
                                         'method, string column name, or '
                                         'proportion list')
                else:
                    colname = get_statcolname(weightcol)
                if not axislabel:
                    axislabel = measure.get_label(ds, weightcol)
                try:
                    self.conflev = measure.conflev
                except AttributeError:
                    pass

            measurecol = raxis.RMeasureCondCol(ds, colname, measure, 
                                               axislabel=axislabel, **kwargs)
        self.condcols.append(measurecol)

    def add_groupby(self, ds, groupby=None, stackby=None, **kwargs):
        if groupby or stackby:
            self.condcols.append(raxis.RGroupByCol(ds, groupby=groupby,
                                                   stackby=stackby, **kwargs))
            self.grouping = True

    def to_r_args(self, ds):
        super(RLatticeSummPlot, self).to_r_args(ds)
        self.r_args['horizontal'] = bool(self.horizontal)
        if self.pack:
            self.r_args['box_ratio'] = sys.maxint


class RLatticeCatPlot(RLatticeSummPlot):
    dates_as_factor = True

    def __init__(self, ds):
        super(RLatticeCatPlot, self).__init__(ds)
        self.origin = 0
        self.reference = True
        self.point_size = 2

    def set_params(self, origin=None, reference=None, 
                   point_size=None, **kwargs):
        super(RLatticeCatPlot, self).set_params(**kwargs)
        if origin is not None:
            self.origin = origin
        if reference is not None:
            self.reference = reference
        if point_size is not None:
            self.point_size = point_size

    def to_r_args(self, ds):
        super(RLatticeCatPlot, self).to_r_args(ds)
        # Only work for barchart
        self.r_args['origin'] = float(self.origin)
        self.r_args['reference'] = bool(self.reference)
        if 'stack' in self.r_args and 'panel' in self.r_args:
            raise PlotError('%s plot does not allow stacking and confidence '
                            'limits simultaneously' % self.label)

        # Doesn't work
        self._set_trellis_params(self.point_size, 'cex', 'dot.symbol')


class TwoByTwoPlot(SummPlotMixin,RPlotBase):
    def __init__(self, ds):
        super(TwoByTwoPlot, self).__init__(ds)
        self.margin = None
        self.conflev = None
        self.extended = None
        self.std = None

    def set_params(self, margin=None, conflev=None, extended=None, 
                   std=None, **kwargs):
        super(TwoByTwoPlot, self).set_params(**kwargs)
        if margin is not None:
            self.margin = margin
        if conflev is not None:
            self.conflev = conflev
        if extended is not None:
            self.extended = extended
        if std is not None:
            self.std = std

    def to_r_args(self, ds):
        super(TwoByTwoPlot, self).to_r_args(ds)
        if self.margin is not None:
            self.r_args['margin'] = self.margin
        if self.conflev is not None:
            self.r_args['conf_level'] = self.conflev
        if self.extended is not None:
            self.r_args['extended'] = bool(self.extended)
        if self.std is not None:
            self.r_args['std'] = self.std
        self.r_args['newpage'] = False
        if 'sub' in self.r_args:
            # VCD plots currently don't support subtitles - hopefully will be
            # fixed soon.
            del self.r_args['sub']

    def _vcd_init(self):
        if 'vcd' not in r._packages(all=True):
            raise PlotError('The required R "vcd" package is not installed')
        try:
            # The vcd import produces a lot of noise on startup - deadly to CGI
            r.sink("/dev/null")
            try:
                r.library('vcd')
            finally:
                r.sink()
        except RException, e:
            raise PlotError('R: %s' % e)

    def get_rmethod(self):
        # Necessary because we can't otherwise specify arguments with
        # underscores in their name.
        return r('function(x, conf.level=0.95, ...) { %s(x, conf_level=conf.level, ...)}' % self.rmethod)

    def plot(self, ds):
        self._vcd_init()
        _output.dev.new_page()
        filtered_ds = self.get_filtered_ds(ds)

        rpy_mode = get_default_mode()
        try:
            set_default_mode(NO_CONVERSION)
            rmethod = self.get_rmethod()
            self.to_r_args(filtered_ds)
            data = rconv.summ_to_array(filtered_ds, '_freq_')
            try:
                r.print_(rmethod(data, **self.r_args))
            except RException, e:
                raise PlotError('R: %s' % e)
        finally:
            set_default_mode(rpy_mode)
        _output.dev.done()


