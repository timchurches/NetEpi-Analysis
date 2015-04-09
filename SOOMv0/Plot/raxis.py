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
# $Id: raxis.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Plot/raxis.py,v $

# Standard Python modules
import sys
import types
import textwrap

# 3rd Party modules
from rpy import *
import MA, Numeric
from mx import DateTime

# SOOM bits
from soomfunc import union
from SOOMv0.common import *
from SOOMv0.SummaryProp import proportion_label

# SOOM.Plot bits
from SOOMv0.Plot import rconv
from SOOMv0.Plot import panelfn

class RCondCol(object):
    def __init__(self, ds, colname, axislabel=None, 
                 ticks=None, labelrotate=None):
        self.summ_arg = colname
        try:
            self.colname = colname.get_colname()
        except AttributeError:
            self.colname = colname
        self.axislabel = axislabel
        self.axisscale = {}
        if ticks is not None:
            self.setscale('tick.number', ticks)
        self.labelrotate = labelrotate
        self.long_labels = False

    def __repr__(self):
        cls = self.__class__
        return '<%s.%s for %r>' % (cls.__module__, cls.__name__, self.colname)

    def rname(self):
        """
        Return the SOOM column name in a form acceptable to R

        If None or a null string is returned, the column will not
        be included in the resulting R data frame.

        If None is returned, the column will not be included
        in the resulting R formula. A null string will result
        in a null formula field.
        """
        if self.colname is not None:
            return rconv.rname(self.colname)

    def title(self, ds):
        if self.axislabel:
            return self.axislabel
        else:
            return ds.get_column(self.colname).label

    def setscale(self, attr, value):
        self.axisscale[attr] = value

    def setscaledefault(self, attr, value):
        self.axisscale.setdefault(attr, value)

    def date_ticks(self, ds, npanels):
        """
        Generate tickmarks for date/time axis

        Attempts to be intelligent about the number and alignment
        of the tickmarks, reducing the tickmarks when more panels
        are in use, and align the tickmarks with natural boundaries
        (years, months, weeks, days, etc).
        """
        col = ds[self.colname]
        if not col.is_datetimetype():
            return
        def reldate(**kwargs):
            if not kwargs.has_key('hours'):
                kwargs['hour'] = 0
            if not kwargs.has_key('minutes'):
                kwargs['minute'] = 0
            kwargs['second'] = 0
            return DateTime.RelativeDateTime(**kwargs)

        # need to account for possible None values, hence can't use 
        # min() & max()
        mindatetime = None
        maxdatetime = None
        for datetime in col:
            if datetime:
                if maxdatetime is None or datetime > maxdatetime:
                    maxdatetime = datetime
                if mindatetime is None or datetime < mindatetime:
                    mindatetime = datetime
        if mindatetime is None or maxdatetime is None:
            raise PlotError('No date/time data to plot')
        range = maxdatetime - mindatetime
        step = range / (20 / math.sqrt(npanels))
        pad = step / 3

        dateformat = '%d-%b-%y'
        if step.days > 300:
            # Years
            step = reldate(years=round(step.days / 365.25), month=1, day=1)
        elif step.days >= 28:
            # Months
            step = reldate(months=round(step.days / 30.4375), day=1)
        elif step.days > 5:
            # Weeks
            step = reldate(days=7*round(step.days / 7), weekday=(0,0))
        elif step.days >= 1:
            # Days
            step = reldate(days=1)
        elif step.hours >= 1:
            # Hours
            step = reldate(hours=round(step.hours))
            dateformat = '%d-%b-%y %H:%M'
        else:
            dateformat = '%d-%b-%y %H:%M'
        dates = []
        dates.append(mindatetime)
        date = mindatetime + pad + step
        while date < maxdatetime - pad:
            dates.append(date)
            date += step
        dates.append(maxdatetime)
        self.long_labels = True
        self.setscale('at', [rconv.Date_to_R(dates)] * npanels)
        self.setscale('relation', 'free')
        self.setscale('format', dateformat)

    def to_r_args(self, ds, plot, r_args, axisname, npanels):
        """
        Collect R plot method kwargs
        """
        if axisname:
            if self.colname and plot.rmethod not in ('barchart', 'dotplot'):
                self.date_ticks(ds, npanels)
            if self.labelrotate is not None:
                self.setscale('rot', self.labelrotate)
            elif self.long_labels:
                if axisname == 'x':
                    self.setscale('rot', 90)
                else:
                    self.setscale('rot', 0)
            if self.axisscale:
                scales = r_args.setdefault('scales', {})
                scales[axisname] = self.axisscale
            label = self.title(ds)
            if label:
                r_args[axisname + 'lab'] = label

    def to_summ_args(self, summargs):
        """
        Collect SOOM summ() args and kwargs (for methods using summ)
        """
        summargs.add_condcol(self.summ_arg)

    def to_frame(self, frame, ds, **kwargs):
        rname = self.rname()
        if rname:
            frame[self.rname()] = self.to_R(ds, **kwargs)


    def __repr__(self):
        return '%s(%r, axislabel=%r)' % (self.__class__.__name__,
                                         self.colname, self.axislabel)

class RPercentAxisCol(RCondCol):
    axislabel_map = {
        'percent': 'Per cent',
        'count': 'Frequency',
        'density': 'Probability density',
    }

    def __init__(self, ds, hist_type = None, **kwargs):
        super(RPercentAxisCol, self).__init__(ds, None, **kwargs)
        if hist_type is None:
            hist_type = 'percent'
        try:
            self.axislabel = self.axislabel_map[hist_type]
        except KeyError:
            raise KeyError('Unsupported histogram type: %r' % hist_type)
        self.hist_type = hist_type

    def rname(self):
        return ''

    def title(self, ds):
        return None

    def to_r_args(self, ds, plot, r_args, axisname, npanels):
        super(RPercentAxisCol, self).to_r_args(ds, plot, r_args, axisname, npanels)
        r_args['type'] = self.hist_type


class RDensityAxisCol(RCondCol):
    # Closely related to RPercentAxisCol

    def __init__(self, ds, plot_points = False, ref = True, **kwargs):
        super(RDensityAxisCol, self).__init__(ds, None, **kwargs)
        self.plot_points = plot_points
        self.ref = ref
        self.axislabel = 'Probability density'

    def rname(self):
        return ''

    def title(self, ds):
        return None

    def to_r_args(self, ds, plot, r_args, axisname, npanels):
        super(RDensityAxisCol, self).to_r_args(ds, plot, r_args, axisname, npanels)
        r_args['plot_points'] = self.plot_points
        r_args['ref'] = self.ref


class RContinuousCondCol(RCondCol):
    def __init__(self, ds, colname, logscale=None, **kwargs):
        super(RContinuousCondCol, self).__init__(ds, colname, **kwargs)
        if logscale:
            self.setscale('log', logscale)

    def to_R(self, ds, dates_as_factor, **kwargs):
        col = ds[self.colname]
        if MA.isMaskedArray(col.data):
            if Numeric.alltrue(col.data.mask()):
                raise PlotError('%r: all data-points masked' % col.name)
            return rconv.MA_to_R(col.data)
        elif col.is_datetimetype():
            return rconv.Missing_Date_to_R(col.data)
        else:
            return col.data


class RMeasureCondCol(RContinuousCondCol):
    """
    Simple scalar measure with optional associated confidence
    interval columns.
    """

    def __init__(self, ds, colname, measure, **kwargs):
        super(RMeasureCondCol, self).__init__(ds, colname, **kwargs)
        self.summ_arg = measure
        self.max = None
        self.min = None

    def limit_cols(self, ds):
        colname_ul = self.colname + '_ul'
        colname_ll = self.colname + '_ll'
        if (ds.has_column(colname_ul) and ds.has_column(colname_ll)):
            return colname_ul, colname_ll
        else:
            return None

    def to_frame(self, frame, ds, **kwargs):
        limit_cols = self.limit_cols(ds)
        if limit_cols:
            self.max = 0
            self.min = 0
            for colname in (self.colname,) + limit_cols:
                col = ds[colname]
                if MA.isMaskedArray(col.data):
                    if Numeric.alltrue(col.data.mask()):
                        raise PlotError('%r: all data-points masked' % col.name)
                    data = rconv.MA_to_R(col.data)
                    self.max = max(MA.maximum(col.data), self.max)
                    self.min = min(MA.minimum(col.data), self.min)
                else:
                    data = col.data
                    self.max = max(max(col.data), self.max)
                    self.min = min(min(col.data), self.min)
                frame[rconv.rname(colname)] = data
        else:
            super(RMeasureCondCol, self).to_frame(frame, ds, **kwargs)

    def to_r_args(self, ds, plot, r_args, axisname, npanels):
        super(RMeasureCondCol, self).to_r_args(ds, plot, r_args, axisname, 
                                                 npanels)
        if self.limit_cols(ds):
            r_args['panel'] = panelfn.ci_panel(self.rname(), plot.rmethod, 
                                               axisname, plot.grouping)
        if self.max is not None and self.min is not None:
            range = self.max - self.min
            r_args[axisname + 'lim'] = (self.min - range * 0.1, 
                                        self.max + range * 0.1)


class RPropnMeasureCol(RContinuousCondCol):
    def __init__(self, ds, propncols, axislabel=None, **kwargs):
        colname, label = proportion_label(ds, propncols)
        if axislabel is None:
            axislabel = label
        super(RPropnMeasureCol, self).__init__(ds, colname, 
                                              axislabel=axislabel, **kwargs)
        self.propncols = propncols

    def to_summ_args(self, summargs):
        for propncol in self.propncols:
            summargs.add_condcol(propncol)
        summargs.set_kw('proportions', True)


class RDiscreteCondCol(RCondCol):
    def __init__(self, ds, colname, 
                 missing_as_none=False,
                 **kwargs):
        # Logscale?
        super(RDiscreteCondCol, self).__init__(ds, colname, **kwargs)
        self.missing_as_none = missing_as_none

    def discrete_col_to_R(self, col, rdata, suppress_all_value=False):
        if col.will_outtrans() or col.is_datetimetype():
            levels = []
            labels = []
            col_levels = col.inverted.keys()
            if suppress_all_value:
                col_levels = [l for l in col_levels if l != col.all_value]
            if col.is_ordered():
                col_levels.sort()
            if self.missing_as_none:
                for l in col_levels:
                    if l is None:
                        levels.append(sys.maxint)
                    else:
                        levels.append(l)
                    labels.append(col.do_outtrans(l))
            else:
                for l in col_levels:
                    if l is not None:
                        levels.append(l)
                        labels.append(col.do_outtrans(l))
            if col.is_datetimetype():
                rdata = r.as_POSIXct(rdata)
                levels = r.as_POSIXct(rconv.Date_to_R(levels))
                labels = [col.do_format(l) for l in labels]
            if labels:
                wrapper = textwrap.TextWrapper(width=20)
                labels = [wrapper.wrap(str(label))[:2]
                        for label in labels]
                maxlen = max([len(line)
                            for label in labels 
                            for line in label])
                labels = ['\n'.join(label) for label in labels]
                if maxlen > 5:
                    self.long_labels = True
            return r.factor(rdata, levels=levels, labels=labels, 
                            ordered=col.is_ordered())
        else:
            # No outtrans - R will work it out
            return r.factor(rdata, ordered=col.is_ordered())

    def continuous_col_to_R(self, col, rdata):
        # equal.count returns an R shingle
        return r.equal_count(rdata)

    def to_R(self, ds, dates_as_factor, suppress_all_value=True, **kwargs):
        if not self.colname:
            return
        col = ds[self.colname]
        if col.is_datetimetype():
            rdata = rconv.Missing_Date_to_R(col)
            if not dates_as_factor:
                return rdata
        elif MA.isMaskedArray(col.data):
            if self.missing_as_none:
                rdata = MA.filled(col.data,sys.maxint)
            else:
                if Numeric.alltrue(col.data.mask()):
                    raise PlotError('%r: all data-points masked' % col.name)
                rdata = rconv.MA_to_R(col.data)
        else:
            rdata = col.data
        if col.is_discrete():
            if 0 and suppress_all_value:
                row_vecs = [vec for value, vec in col.inverted.items()
                            if value != col.all_value]
                row_vec = union(*row_vecs)
                rdata = MA.take(rdata, row_vec)
            return self.discrete_col_to_R(col, rdata, suppress_all_value)
        else:
            return self.continuous_col_to_R(col, rdata)


class RGroupByCol(RDiscreteCondCol):
    keyarg_map = {
        'xyplot':   {'rectangles': False, 'lines': True, 'points': False},
        'barchart': {'rectangles': True, 'lines': False, 'points': False},
        'dotplot':  {'rectangles': False, 'lines': False, 'points': True},
        'splom':    {'rectangles': False, 'lines': False, 'points': True},
    }

    def __init__(self, ds, groupby=None, stackby=None, **kwargs):
        assert groupby or stackby
        super(RGroupByCol, self).__init__(ds, stackby or groupby, **kwargs)
        self.stack = bool(stackby)

    def to_r_args(self, ds, plot, r_args, axisname, npanels):
        super(RGroupByCol, self).to_r_args(ds, plot, r_args, axisname, npanels)
        rdata = super(RGroupByCol, self).to_R(ds, dates_as_factor=True)
        key_args = dict(self.keyarg_map[plot.rmethod])
        levels = r.levels(rdata)
        if len(levels) >= 15:
            key_args['columns'] = 3
        elif len(levels) >= 10:
            key_args['columns'] = 2
        r_args['groups'] = rdata
        r_args['key'] = r.simpleKey(levels, **key_args)
        if self.stack:
            r_args['stack'] = True

    def rname(self):
        return None

