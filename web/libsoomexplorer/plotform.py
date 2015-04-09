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
"""
Machinery for collecting plot and table arguments and producing an
output object from them.
"""
# $Id: plotform.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/plotform.py,v $

import sets
import re
import cgi
import SOOMv0, SOOMv0.SummaryStats
from SOOMv0.soomparse import soomparseScanner
import Numeric
# Application modules
from common import UIError, ConversionError
from libsoomexplorer.dsparams import DSParams
from libsoomexplorer.condcol import CondColParams, StratifyParams
from libsoomexplorer.twobytwoparams import TwoByTwoColParams
from libsoomexplorer.fields import set_target


class DupCol(Exception): pass

class ColList(list):
    def __init__(self, colparams=None, nodups=True):
        self.colparams = colparams
        self.nodups = nodups
        self.cols = sets.Set()

    def set(self, name, cols):
        if type(cols) not in (list, tuple):
            cols = [cols]
        for col in cols:
            if col in self.cols:
                if self.nodups:
                    raise DupCol(col)
            else:
                self.cols.add(col)
                if self.colparams is not None and col in self.colparams:
                    col = SOOMv0.condcol(col, *self.colparams[col])
                self.append(col)


class KWArgs(dict):
    def set(self, name, value):
        self[name] = value

class _FieldsMeta(type):
    def __init__(cls, name, bases, ns):
        targets_fields = {}
        if hasattr(cls, 'fields'):
            for field in cls.fields:
                if field.target:
                    for target in field.target:
                        targets_fields.setdefault(target, []).append(field)
            cls.targets_fields = targets_fields
        super(_FieldsMeta, cls).__init__(name, bases, ns)


class _SummaryBase(object):
    __metaclass__ = _FieldsMeta
    options = []

    def __init__(self, workspace):
        self.workspace = workspace
        self.hide_params = False

    def get_target(self, target, ns, param, no_verify=True):
        kwargs = {target: param}
        for field in self.targets_fields[target]:
            try:
                field.get_params(ns, kwargs)
            except UIError:
                if not no_verify:
                    raise
        return param

    def set_default(self):
        params = self.workspace.params
        params.set_default('condcolparams', {})
        params.set_default('sys_title', '')
        params.set_default('sys_subtitle', '')
        for field in self.fields:
            field.set_default(self.workspace, params)

    def condcol_params(self, condcol):
        params = self.workspace.params
        if condcol in params.condcolparams:
            return SOOMv0.condcol(condcol, *params.condcolparams[condcol])
        return condcol

    def new_args(self):
        params = self.workspace.params
        return {
            'stratacols': ColList(),
            'stndrdcols': ColList(params.condcolparams),
            'summcols': ColList(params.condcolparams),
            'plotcols': ColList(params.condcolparams),
            'measures': ColList(),
            'summkw': KWArgs(),
            'plotkw': KWArgs(),
            'outputkw': KWArgs(),
        }

    def get_params(self):
        kwargs = self.new_args()
        try:
            for field in self.fields:
                field.get_params(self.workspace.params, kwargs)
        except DupCol, colname:
            col = SOOMv0.dsload(self.workspace.dsname)[str(colname)]
            raise UIError('%r column used more than once' % 
                            (col.label or col.name))
        return kwargs

    def get_collist(self, target='stratacols', nodups=False):
        return self.get_target(target, self.workspace.params, 
                               ColList(nodups=nodups))

    def get_condcolparams(self, workspace):
        return CondColParams(workspace, workspace.params.condcolparams, 
                             self.get_collist())

    def refresh(self):
        pass

    def user_title(self):
        """
        If the user has set a title, return that, but if no title
        is set, or if the title matches the last system generated
        title, return None.
        """
        if not self.workspace.params.is_sys('title'):
            return self.workspace.params.title.replace('\r', '')
        return None

    def user_subtitle(self):
        if not self.workspace.params.is_sys('subtitle'):
            return self.workspace.params.subtitle.replace('\r', '')
        return None

    def generate_title(self, ds, condcols):
        """
        Generate a title and subtitle if the user has not supplied
        an explicit one.
        """
        def get_col_label(ds, colname):
            col = ds.get_column(colname)
            if col.label:
                return col.label
            else:
                return col.name
        params = self.workspace.params
        if params.is_sys('title'):
            labels = []
            for condcol in condcols:
                if SOOMv0.isstatmethod(condcol):
                    labels.append(condcol.get_label(ds, None))
                else:
                    try:
                        colname = condcol.get_colname()
                    except AttributeError:
                        colname = condcol
                    labels.append(get_col_label(ds, colname))
            title = ' by '.join(labels)
            params.set_sys('title', title)
        if params.is_sys('subtitle'):
            params.set_sys('subtitle', ds.short_description())
        self.workspace.output.title = params.title
        self.workspace.output.subtitle = params.subtitle


class PlotTypeBase(_SummaryBase):
    def __init__(self, workspace):
        _SummaryBase.__init__(self, workspace)
        self.workspace.set_outtype('image')

    def get_params(self):
        kwargs = _SummaryBase.get_params(self)
        plotkw = kwargs['plotkw']
        for kw in ('groupby', 'stackby'):
            if kw in plotkw:
                plotkw.set(kw, self.condcol_params(plotkw[kw]))
        kwargs.pop('title', None)
        kwargs.pop('subtitle', None)
        return kwargs

    def _getplot(self, ds):
        params = self.workspace.params
        kwargs = self.get_params()
        params.dsparams.filter_args(kwargs['plotkw'])
        kwargs['title'] = self.user_title()
        kwargs['footer'] = self.user_subtitle()
        plot_method = getattr(SOOMv0.plot, self.name)(ds)
        plot_method.procargs(ds, *kwargs['plotcols'], **kwargs['plotkw'])
        filtered_ds = plot_method.get_filtered_ds(ds)
        if params.is_sys('title'):
            params.set_sys('title', plot_method.get_title(filtered_ds))
        if not self.user_subtitle():
            params.set_sys('subtitle', plot_method.get_footer(filtered_ds))
        return plot_method

    def refresh(self):
        super(PlotTypeBase, self).refresh()
        ds = self.workspace.get_dataset()
        try:
            plot_method = self._getplot(ds)
        except TypeError:
            # Most likely due to missing args at this stage - ignore
            pass

    def go(self):
        self.workspace.output.start(self.name)
        ds = self.workspace.get_dataset()
        plot_method = self._getplot(ds)
        plot_method.plot(ds)
        self.hide_params = self.workspace.output.inline


class TableTypeBase(_SummaryBase):
    def __init__(self, workspace):
        _SummaryBase.__init__(self, workspace)
        self.workspace.set_outtype('table')

    def set_default(self):
        super(TableTypeBase, self).set_default()
        self.workspace.params.set_default('statcols', [])

    def go(self):
        kwargs = self.get_params()
        self.workspace.params.dsparams.filter_args(kwargs['summkw'])
        ds = self.workspace.get_dataset()
        self.generate_title(ds, kwargs['stratacols'])
        self.workspace.output.summaryset = ds.summ(*kwargs['summcols'], 
                                                   **kwargs['summkw'])
        self.hide_params = True


class CrosstabBase(TableTypeBase):
    def __init__(self, workspace):
        TableTypeBase.__init__(self, workspace)
        self.workspace.set_outtype('crosstab')

    def new_args(self):
        kwargs = super(CrosstabBase, self).new_args()
        kwargs['rowcols'] = ColList()
        kwargs['colcols'] = ColList()
        return kwargs

    def set_default(self):
        super(CrosstabBase, self).set_default()
        ds = self.workspace.get_dataset()
        self.workspace.params.set_default('propcols', [])
        self.workspace.params.set_default('proptype', 'density')
        self.workspace.params.set_default('heatmap', False)
        self.workspace.params.set_default('weightcol', ds.weightcol)

    def go(self):
        ds = self.workspace.get_dataset()
        params = self.workspace.params
        if not params.statcols and not params.propcols:
            params.statcols = [['freq', None, '_default_']]
        # Generate the summary!
        kwargs = self.get_params()
        params.dsparams.filter_args(kwargs['summkw'])
        if kwargs['outputkw']['marginal_totals'] in ('before', 'after'):
            kwargs['summkw'].set('allcalc', True)
        if params.propcols:
            available = [n for n, l in SOOMv0.propn_names_and_labels(ds, kwargs['stratacols'])]
            for propcol in params.propcols:
                if propcol not in available:
                    raise UIError('Conditioning columns have changed, reselect proportions')
            kwargs['summkw'].set('proportions', True)
        self.workspace.output.proptype = params.proptype
        self.workspace.output.heatmap = str(params.heatmap) == 'True'
        for condcol in kwargs['summcols']:
            if hasattr(condcol, 'conflev'):
                kwargs['outputkw'].set('show_limits', True)
                break
        summaryset = ds.summ(*kwargs['summcols'], **kwargs['summkw'])
        # XXX
        statcolnames = [summaryset.get_method_statcolname(col)
                        for col in kwargs['measures']]
        self.workspace.output.go(summaryset, 
                                 kwargs['rowcols'], kwargs['colcols'], 
                                 statcolnames, params.propcols, 
                                 **kwargs['outputkw'])
        self.generate_title(ds, kwargs['rowcols'] + kwargs['colcols'])
        self.hide_params = True


class DatasetRowsBase(TableTypeBase):
    def __init__(self, workspace):
        TableTypeBase.__init__(self, workspace)
        self.workspace.set_outtype('dsrows')

    def generate_title(self, ds, filterexpr):
        params = self.workspace.params
        if params.is_sys('title'):
            params.set_sys('title', filterexpr)
        if params.is_sys('subtitle'):
            params.set_sys('subtitle', ds.short_description())
        self.workspace.output.title = params.title
        self.workspace.output.subtitle = params.subtitle

    # we know our filter expression is well-formed so we can write clean REs
    SEARCH_EXPR_RE = re.compile(r'(\w+)\s+contains\s+\[\[(.*?)\]\]', re.I | re.S)
    NEARNESS_RE = re.compile(r'\[\s*\d+\s*\]', re.S)
    WORD_RE = dict(soomparseScanner.patterns)['WORD']

    def get_highlight_fns(self, filterexpr):
        # Find all words used to search specific columns and generate a specific
        # regular expression based outtrans function for that column
        outtrans_fns = {}
        if filterexpr:
            for mexpr in self.SEARCH_EXPR_RE.finditer(filterexpr):
                column, sexpr = mexpr.group(1), mexpr.group(2)
                # remove [n] nearness specifiers
                sexpr = self.NEARNESS_RE.sub('', sexpr)
                terms = sets.Set()
                for mword in self.WORD_RE.finditer(sexpr):
                    word = "'?".join(list(mword.group().replace("'", "")))
                    term_re = word.replace('*', r'\S*?')
                    terms.add(term_re)
                trans_re = re.compile(r"\b(%s)\b" % "|".join(terms), re.I)
                outtrans_fns[column] = Highlighter(trans_re)
        return outtrans_fns

    def go(self):
        kwargs = self.get_params()
        ds = self.workspace.get_dataset()
        filterexpr = self.workspace.params.dsparams.filterexpr
        if filterexpr:
            try:
                dsrows = ds.filter(filterexpr).record_ids
            except Exception, e:
                raise UIError('Could not make filter: %s' % e)
        else:
            dsrows = Numeric.arrayrange(len(ds))
        # set any output translations
        self.generate_title(ds, filterexpr)
        self.workspace.output.dsrows = dsrows
        self.workspace.output.highlight_fns = self.get_highlight_fns(filterexpr)
        self.workspace.output.colnames = kwargs['stratacols']
        try:
            self.workspace.output.pagesize = int(self.workspace.params.pagesize)
        except ValueError:
            self.workspace.output.pagesize = 0
        self.hide_params = True


class Highlighter:
    def __init__(self, trans_re):
        self.trans_re = trans_re

    def __call__(self, v):
        return self.trans_re.sub(r'<b style="color:black;background-color:#fdd">\1</b>', cgi.escape(v))

    def __repr__(self):
        return "<Highlighter: %s>" % self.trans_re.pattern


class PopRateBase(_SummaryBase):

    def set_default(self):
        super(PopRateBase, self).set_default()
        params = self.workspace.params
        params.set_default('popsetparams', DSParams())
        params.set_default('stdpopsetparams', DSParams())
        params.set_default('stdsetparams', DSParams())

    def refresh(self):
        super(PopRateBase, self).refresh()
        params = self.workspace.params
        params.popsetparams.set_dsname(getattr(params, 'popset', None))
        params.stdpopsetparams.set_dsname(getattr(params, 'stdpopset', None))
        params.stdsetparams.set_dsname(getattr(params, 'stdset', None))


class DSRMixin(PopRateBase):
    measure = 'dsr'

    def calc_rates(self, kwargs):
        from SOOMv0 import Analysis
        params = self.workspace.params
        ds = self.workspace.get_dataset()
        popset = params.popsetparams.get_filtered_dataset()
        stdpopset = SOOMv0.dsload(params.stdpopset)
        summcols = kwargs['stndrdcols'] + kwargs['summcols']
        summset = ds.summ(*summcols, **kwargs['summkw'])
        return Analysis.calc_directly_std_rates(summset, popset, stdpopset,
                                popset_popcol=params.popset_popcol,
                                stdpopset_popcol=params.stdpopset_popcol,
                                conflev=kwargs['conflev'])


class SRMixin(PopRateBase):
    measure = 'sr'

    def calc_rates(self, kwargs):
        from SOOMv0 import Analysis
        params = self.workspace.params
        ds = self.workspace.get_dataset()
        popset = params.popsetparams.get_filtered_dataset()
        summset = ds.summ(*kwargs['summcols'], **kwargs['summkw'])
        return Analysis.calc_stratified_rates(summset, popset, 
                                popset_popcol=params.popset_popcol,
                                conflev=kwargs['conflev'])


class ISRMixin(PopRateBase):
    measure = 'isr'

    def calc_rates(self, kwargs):
        from SOOMv0 import Analysis
        params = self.workspace.params
        params.dsparams.filter_args(kwargs['summkw'])
        kwargs['summkw'].set('zeros', True)
        ds = self.workspace.get_dataset()
        popset = params.popsetparams.get_filtered_dataset()
        stdpopset = params.stdpopsetparams.get_filtered_dataset()
        summset = ds.summ(*kwargs['summcols'], **kwargs['summkw'])
        stdset = SOOMv0.dsload(params.stdset)
        stdsetkw = {'zeros': True}
        params.stdsetparams.filter_args(stdsetkw)
        stdsummset = stdset.summ(*kwargs['stndrdcols'], **stdsetkw)
        return Analysis.calc_indirectly_std_ratios(summset, popset, 
                                stdsummset, stdpopset,
                                popset_popcol=params.popset_popcol,
                                stdpopset_popcol=params.stdpopset_popcol,
                                conflev=kwargs['conflev'])


class RatePlotBase(PlotTypeBase):

    def _getplot(self, ds):
        params = self.workspace.params
        kwargs = self.get_params()
        if params.is_sys('title'):
            self.generate_title(ds, kwargs['stratacols'])
            params.set_sys('title', self.label + ' of ' + params.title)
        kwargs['title'] = self.user_title()
        kwargs['footer'] = self.user_subtitle()

    def go(self):
        params = self.workspace.params
        kwargs = self.get_params()
        params.dsparams.filter_args(kwargs['summkw'])
        output_type = kwargs.pop('output_type')
        if output_type == 'barchart_horizontal':
            kwargs['plotkw'].set('horizontal', True)
            output_type = 'barchart'
        elif output_type not in ('barchart', 'lineplot'):
            raise UIError('Unsupported plot type')
        plotmethod = self.workspace.output.start(output_type)
        rateset = self.calc_rates(kwargs)
        plot = plotmethod(rateset)
        kwargs['plotkw'].set('measure', self.measure)
        plot.procargs(rateset, *kwargs['plotcols'], **kwargs['plotkw'])
        plot.plot(rateset)


class RateTabBase(CrosstabBase):
    def go(self):
        params = self.workspace.params
        kwargs = self.get_params()
        params.dsparams.filter_args(kwargs['summkw'])
        rateset = self.calc_rates(kwargs)
        self.workspace.output.go(rateset, kwargs['rowcols'], kwargs['colcols'], 
                                 propcols=[], 
                                 show_limits=True, **kwargs['outputkw'])
        self.generate_title(rateset, kwargs['rowcols'] + kwargs['colcols'])
        self.hide_params = True


class TwoByTwoBase(_SummaryBase):
    def __init__(self, workspace):
        _SummaryBase.__init__(self, workspace)
        self.workspace.set_outtype('twobytwo')

    def set_default(self):
        super(TwoByTwoBase, self).set_default()
        params = self.workspace.params
        if not hasattr(params, 'exposure_params'):
            params.exposure_params = TwoByTwoColParams('exposed')
        params.exposure_params.set_colname(self.workspace, params.exposure)
        if not hasattr(params, 'outcome_params'):
            params.outcome_params = TwoByTwoColParams('outcome')
        params.outcome_params.set_colname(self.workspace, params.outcome)

    def get_params(self): 
        params = self.workspace.params
        condcolparams = params.condcolparams
        condcolparams.update(params.exposure_params.get_map(self.workspace))
        condcolparams.update(params.outcome_params.get_map(self.workspace))
        return super(TwoByTwoBase, self).get_params()

    def get_condcolparams(self, workspace):
        return StratifyParams(workspace, workspace.params.condcolparams, 
                              self.get_collist())

    def refresh(self):
        super(TwoByTwoBase, self).refresh()
        params = self.workspace.params
        if params.exposure:
            params.exposure_params.set_colname(self.workspace, params.exposure)
        if params.outcome:
            params.outcome_params.set_colname(self.workspace, params.outcome)

    def do_fourfold(self, ds, summaryset, summcols, kwargs, conflev, std):
        if not hasattr(SOOMv0.plot, 'fourfold') or std is None:
            return
        margin = None
        std_labels = {
            'margins_1': 'standardised by row',
            'margins_2': 'standardised by column',
            'margins_12': 'standardised by rows and columns',
            'ind.max': 'individually standardised',
            'all.max': 'simultaneously standardised',
        }
        std_label = std_labels[std]
        if std.startswith('margins_'):
            std, margin = std.split('_')
            margin = {'1': 1, '2': 2, '12': (1,2)}[margin]
        plotargs = dict(title='', footer='', conflev=conflev, 
                        std=std, margin=margin)
        if len(summcols) > 2:
            s_label = 'Stratified'
        else:
            s_label = 'Unstratified'
        p_label = ' (%g%% conf. limits, %s)' % (conflev * 100, std_label)
        of = self.workspace.output.tempfile('png', label=s_label + p_label)
        SOOMv0.plot.output('PNG', file=of.fn, width=800)
        SOOMv0.plot.fourfold(summaryset, *summcols, **plotargs)
        if len(summcols) > 2:
            unstratified_summcols = summcols[:2]
            of = self.workspace.output.tempfile('png', 
                                                label='Unstratified' + p_label)
            SOOMv0.plot.output('PNG', file=of.fn, width=800)
            SOOMv0.plot.fourfold(ds, *unstratified_summcols, 
                                    **plotargs)

    def go(self):
        params = self.workspace.params
        kwargs = self.get_params()
        std = kwargs.pop('std')
        ds = self.workspace.get_dataset()
        params.dsparams.filter_args(kwargs['summkw'])
        summcols = kwargs['summcols']
        summaryset = ds.summ(*summcols, **kwargs['summkw'])
        self.generate_title(summaryset, summcols)
        conflev = kwargs['conflev']
        self.do_fourfold(ds, summaryset, summcols, kwargs, conflev, std)
        self.workspace.output.go(summaryset, conflev=conflev)
