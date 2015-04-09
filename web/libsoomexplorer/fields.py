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
Abstractions used to describe the markup elements that make up a
plot/table configuration page.

Plot type descriptions subclass PlotTypeBase. Class attributes on the
concrete subclass describe aspects of the resulting form. Attributes include:

    name        internal name of plot type
    label       user visible name of plot type
    fields      a list of _FieldBase subclasses describing markup elements
                within the form.
    options     used by the OptionsField, describes markup elements within
                the options field.


Fields include:

    _FieldBase                  abstract base
    ColField                    select a column
    MeasureColField             select a measure column
    ColsField                   select zero or more columns
    GroupByColField             select a discrete group-by column
    StatColsField               select zero or more stat methods and cols
    CondColParamsField          buttons to push to suppress/coalesce pages
    OutputField                 select plot output options
    OptionsField                select options (described by options attr)

    _SimpleFieldBase            abstract base, args: param, label, default
    BoolField                   checkbox
    ChooseOneField              radio, args: + list of 2-tuple name/labels,
                                pytype.
    ChooseManyField             checkbox, args: + list of 2-tuple name/labels,
                                pytype.
    DropField                   option list, args: + list of 2-tuple name/label,
                                pytype.
    TextField
    TextAreaField
    FloatField
    IntField

"""
# $Id: fields.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/fields.py,v $

import SOOMv0
# Application modules
from common import UIError, ConversionError

def _propn_optionexpr(ds, cols):
    return SOOMv0.propn_names_and_labels(ds, filter(None, cols))

def _get_measure(methname, colname, weightcol, conflev=None):
    kwargs = {}
    method = getattr(SOOMv0, methname)
    if weightcol == '_none_':
        kwargs['weightcol'] = None
    elif weightcol != '_default_':
        kwargs['weightcol'] = weightcol
    if methname.endswith('cl') and conflev:
        kwargs['conflev'] = conflev
    if methname in ('freq', 'freqcl'):
        return method(**kwargs)
    else:
        if not colname:
            raise UIError('%r statistical method requires that a scalar '
                            'column be specified' % method.__doc__)
        return method(colname, **kwargs)

def _get_param(ns, param, pytype=None):
    value = getattr(ns, param, None)
    if str(value).lower() == 'other':
        value = getattr(ns, 'other_' + param)
    if value == 'None':
        value = None
    if pytype and value is not None:
        value = pytype(value)
    return value

def set_target(kwargs, targets, name, value):
    if targets:
        assert isinstance(targets, list)
        for target in targets:
            try:
                param = kwargs[target]
            except KeyError:
                pass
            else:
                param.set(name, value)
    else:
        kwargs[name] = value

def _get_conflev(ns):
    try:
        return _get_param(ns, 'conflev', float) / 100
    except (AttributeError, ValueError):
        return None


# Column filters, used by _ColFieldBase and derived classes
def anycol(col, workspace):
    return True
anyds = anycol

def discretecol(col, workspace):
    return col.is_discrete()

def scalarcol(col, workspace):
    return col.is_scalar()

def ordinalcol(col, workspace):
    return col.is_scalar() or col.is_ordered()

def weightingcol(col, workspace):
    return col.is_weighting()

def datetimecol(col, workspace):
    return col.is_datetimetype()

def notstandardisecol(col, workspace):
    return col.name != workspace.params.standardiseby

def notcol(param):
    "exclude a column that appears in another parameter"
    def _notcol(col, workspace):
        return col.name != getattr(workspace.params, param)
    return _notcol

def filterlist(filters):
    def _filterlist(o, workspace):
        for filter in filters:
            if not filter(o, workspace):
                return False
        return True
    return _filterlist


class _FieldBase:
    """
    Abstract base class for plot parameter fields
    """
    default = None
    note = None
    target = None

    def __init__(self, param=None, label=None, target=None, 
                 note=None, default=None):
        if param is not None:
            self.param = param
        if label is not None:
            self.label = label
        if target is not None:
            self.target = target.split('|')
        if note is not None:
            self.note = note
        if default is not None:
            self.default = default
#       AM - debug aid - find targetless fields
#        elif getattr(self, 'param', None):
#            print self.param

    def get_params(self, ns, kwargs):
        pass

    def set_default(self, workspace, ns):
        pass

    def enabled(self, workspace):
        return True


class ShowDatasetField(_FieldBase):
    markup = 'showdataset'
    label = 'Dataset'

    def __init__(self, label=None, target=None, note=None):
        _FieldBase.__init__(self, label=label, target=target, note=note)


class AnalysisTypeField(_FieldBase):
    label = 'Analysis type'
    markup = 'analysis'


class FilterField(_FieldBase):
    label = 'Filter'
    markup = 'filter'
    param = 'dsparams'


class _SimpleFieldBase(_FieldBase):
    def _find_leaf(self, ns):
        path = self.param.split('.')
        ns = reduce(getattr, path[:-1], ns)
        attr = path[-1]
        return ns, attr, getattr(ns, attr, None)

    def set_default(self, workspace, ns):
        ns, attr, value = self._find_leaf(ns)
        ns.set_default(attr, self.default)

    def get_params(self, ns, kwargs):
        value = getattr(ns, self.param, None)
        set_target(kwargs, self.target, self.param, value)


class BoolField(_SimpleFieldBase):
    markup = 'bool'

    def get_params(self, ns, kwargs):
        value = getattr(ns, self.param, None) == 'True'
        set_target(kwargs, self.target, self.param, value)


class DropField(_SimpleFieldBase):
    markup = 'drop'

    def __init__(self, param, label, options, target=None, 
                 note=None, default=None):
        _SimpleFieldBase.__init__(self, param, label, target=target, 
                                  note=note, default=default)
        self.options = options

    def set_default(self, workspace, ns):
        ns, attr, value = self._find_leaf(ns)
        default = self.default
        if default is None:
            default = self.options[0][0]
        ns.set_default(attr, default)


class ChooseOneField(_SimpleFieldBase):
    markup = 'chooseone'

    def __init__(self, param, label, options, target=None, note=None, 
                 default=None, horizontal=False,
                 pytype=None):
        _SimpleFieldBase.__init__(self, param, label, target=target, 
                                  note=note, default=default)
        self.options = options
        self.horizontal = horizontal
        self.pytype = pytype

    def set_default(self, workspace, ns):
        value = getattr(ns, self.param, None)
        optval = [o[0] for o in self.options]
        default = self.default
        if default is None:
            default = optval[0]
        if value not in optval:
            setattr(ns, self.param, default)

    def get_params(self, ns, kwargs):
        try:
            value = _get_param(ns, self.param, self.pytype)
        except (TypeError, ValueError), e:
            raise UIError('Bad value for %s field' % self.label)
        set_target(kwargs, self.target, self.param, value)

    def onchangejs(self):
        return r"document.nea.elements['workspace.params.%s'][%d].checked = 1;" % (self.param, len(self.options)-1)


class ChooseManyField(_SimpleFieldBase):
    markup = 'choosemany'

    def __init__(self, param, label, options, target=None, note=None, 
                 default=None, horizontal=False, pytype=None):
        _SimpleFieldBase.__init__(self, param, label, target=target, 
                                  note=note, default=default)
        self.options = options
        self.horizontal = horizontal
        self.pytype = pytype

    def set_default(self, workspace, ns):
        ns, attr, values = self._find_leaf(ns)
        if values is not None:
            # Remove any illegal values
            okay = [option[0] for option in self.options]
            values = [value for value in values if value in okay]
            if not values:
                # Removed all values, so set default
                values = None
        if values is None:
            if self.default is None:
                values = []
            else:
                values = self.default
        if not isinstance(values, list):
            values = [values]
        setattr(ns, attr, values)

    def get_params(self, ns, kwargs):
        ns, attr, value = self._find_leaf(ns)
        if self.pytype:
            try:
                value = [self.pytype(v) for v in value]
            except (TypeError, ValueError), e:
                raise UIError('Bad value for %s field' % self.label)
        set_target(kwargs, self.target, self.param, value)


class TextField(_SimpleFieldBase):
    markup = 'text'


class TextAreaField(_SimpleFieldBase):
    markup = 'textarea'


class FloatField(_SimpleFieldBase):
    markup = 'float'

    def get_params(self, ns, kwargs):
        ns, attr, value = self._find_leaf(ns)
        try:
            value = float(value)
        except ConversionError:
            value = None
        set_target(kwargs, self.target, self.param, value)


class IntField(_SimpleFieldBase):
    markup = 'int'

    def get_params(self, ns, kwargs):
        ns, attr, value = self._find_leaf(ns)
        try:
            value = int(value)
        except ConversionError:
            value = None
        set_target(kwargs, self.target, self.param, value)


class DatasetField(_FieldBase):
    label = 'Dataset'
    markup = 'dataset'

    def __init__(self, param=None, label=None, target=None, 
                 note=None, dsfilter=None):
        _FieldBase.__init__(self, param, label, target=target, note=note)
        if dsfilter is not None:
            self.dsfilter = dsfilter

    def set_default(self, workspace, ns):
        avail = [n for n, l in self.availablesets(workspace)]
        if avail and getattr(ns, self.param, None) not in avail:
            setattr(ns, self.param, avail[0][0])

    def availablesets(self, workspace):
        filter = self.dsfilter
        if filter is None:
            filter = anyds
        elif type(filter) in (tuple, list):
            filter = filterlist(filter)
        return workspace.available_datasets(filter)


class ProportionColsField(_FieldBase):
    label = 'Proportions'
    markup = 'propcols'

    def propcols(self, workspace):
        ds = SOOMv0.dsload(workspace.dsname)
        return _propn_optionexpr(ds, workspace.plottype.get_collist())


class OutputField(_FieldBase):
    label = 'Output'
    markup = 'output'


class _ColFieldBase(_FieldBase):
    """
    Abstract base class for fields that manipulate column names.
    """
    colfilter = None

    def __init__(self, param=None, label=None, target=None, 
                 note=None, colfilter=None):
        _FieldBase.__init__(self, param, label, target=target, note=note)
        if colfilter is not None:
            self.colfilter = colfilter

    def _getds(self, workspace):
        return SOOMv0.dsload(workspace.dsname)

    def availablecols(self, workspace, filter=None): 
        if filter is None:
            filter = self.colfilter
        if filter is None:
            filter = anycol
        elif type(filter) in (tuple, list):
            filter = filterlist(filter)
        ds = self._getds(workspace)
        if ds is None:
            return []
        cols = [(col.label, col.name) 
                for col in ds.get_columns() 
                if filter(col, workspace)]
        cols.sort()
        return [(name, label) for label, name in cols]


class ColsField(_ColFieldBase):
    """
    Abstract base class for fields that manipulate lists of column names.
    """
    markup = 'condcols'
    target = ['stratacols', 'summcols', 'plotcols']
    min = 0

    def __init__(self, param=None, label=None, target=None, note=None, 
                 colfilter=None, min=None):
        _ColFieldBase.__init__(self, param, label, target=target, 
                               note=note, colfilter=colfilter)
        if min is not None:
            self.min = min

    def set_default(self, workspace, ns):
        # We remove any values not permitted by this plottype
        values = getattr(ns, self.param, [])
        okay = [v[0] for v in self.availablecols(workspace)]
        values = [v for v in values if v in okay]
        while len(values) < self.min:
            try:
                v = okay.pop(0)
            except IndexError:
                break
            if v not in values:
                values.append(v)
        setattr(ns, self.param, values)

    def get_params(self, ns, kwargs):
        cols = filter(None, getattr(ns, self.param, []))
        if len(cols) < self.min:
            raise UIError('Must specify at least %d %s' % 
                          (self.min,self.label.lower()))
        if self.target:
            set_target(kwargs, self.target, self.param, cols)


class StratifyColField(_ColFieldBase):
    markup = 'groupbycol'
    label = 'Stratify by'
    target = ['stratacols', 'summcols', 'plotcols']
    allow_stack=False

    def __init__(self, param=None, label=None, target=None, note=None, 
                 colfilter=discretecol):
        _ColFieldBase.__init__(self, param, label, target=target, note=note, 
                               colfilter=colfilter)

    def groupbycols(self, workspace):
        return [('', 'None')] + self.availablecols(workspace) 

    def set_default(self, workspace, ns):
        ns.set_default(self.param, [])

    def get_params(self, ns, kwargs):
        value = getattr(ns, self.param, None)
        if value and self.target:
            set_target(kwargs, self.target, self.param, value)


class GroupByColField(StratifyColField):
    label = 'Group-by Column'
    target = ['stratacols', 'summcols', 'plotkw']

    def __init__(self, param='groupby', label=None, target=None, note=None,
                 colfilter=discretecol, allow_stack=False):
        StratifyColField.__init__(self, param, label, target=target, note=note, 
                                  colfilter=colfilter)
        self.allow_stack = allow_stack

    def set_default(self, workspace, ns):
        StratifyColField.set_default(self, workspace, ns)
        ns.set_default('stack', False)

    def get_params(self, ns, kwargs):
        value = getattr(ns, self.param, None)
        if value:
            if self.allow_stack and ns.stack == 'True':
                param = 'stackby'
            else:
                param = 'groupby'
            set_target(kwargs, self.target, param, value)


class WeightColField(_ColFieldBase):
    label = 'Weight by column'
    markup = 'weightcol'

    def weightcols(self, workspace):
        collist = self.availablecols(workspace, weightingcol)
        collist.insert(0, ('', 'No weighting'))
        return collist


class _StatColFieldBase(_ColFieldBase):
    param = 'statcols'
    target = ['summcols', 'measures']

    def statcols(self, workspace):
        collist = self.availablecols(workspace, scalarcol)
        collist.insert(0, '')
        return collist

    def statmethods(self, workspace):
        stat_methods = [(m.__doc__, m.__name__) 
                        for m in SOOMv0.stat_methods()
                        if m.__name__ not in ('applyto', 'quantile')]
        stat_methods.sort()
        return [(n, l) for l, n in stat_methods]

    def weightcols(self, workspace):
        collist = self.availablecols(workspace, weightingcol)
        collist.insert(0, ('_none_', 'No weighting'))
        return collist


class MeasureColField(_StatColFieldBase):
    label = 'Measure Column'
    markup = 'measurecol'
    target = ['summcols', 'measures', 'plotkw']

    def statmethods(self, workspace):
        ds = SOOMv0.dsload(workspace.dsname)
        stat_methods = []
        condcols = workspace.plottype.get_collist()
        stat_methods.extend(_propn_optionexpr(ds, condcols))
        stat_methods.extend(_StatColFieldBase.statmethods(self, workspace))
        return stat_methods

    def get_params(self, ns, kwargs):
        if getattr(ns, 'measure_stat', None):
            propn_cols = SOOMv0.extract_propn_cols(ns.measure_stat)
            if propn_cols:
                value = propn_cols
                if ns.measure_weight != '_none_':
                    set_target(kwargs, self.target, 'weightcol', ns.measure_weight)
            else:
                value = _get_measure(ns.measure_stat, ns.measure_col,
                                     ns.measure_weight, _get_conflev(ns))
            set_target(kwargs, self.target, self.param, value)

    def set_default(self, workspace, ns):
        if not hasattr(ns, 'measure_stat'):
            ns.measure_stat = 'freq'
            ns.measure_col = ''
            ds = SOOMv0.dsload(workspace.dsname)
            ns.measure_weight = ds.weightcol


class StatColsField(_StatColFieldBase):
    label = 'Statistic(s)'
    markup = 'statcols'

    def weightcols(self, workspace):
        collist = _StatColFieldBase.weightcols(self, workspace)
        collist.insert(0, ('_default_', 'Default weighting'))
        return collist

    def get_params(self, ns, kwargs):
        for meth_args in ns.statcols:
            if meth_args[0]:
                value = _get_measure(*meth_args + [_get_conflev(ns)])
                if self.target:
                    set_target(kwargs, self.target, self.param, value)


class CondColParamsField(_FieldBase):
    label = 'Column Parameters'
    markup = 'condcolparams'


class ColField(_ColFieldBase):
    markup = 'colname'
    target = ['stratacols', 'summcols', 'plotcols']

    def __init__(self, param, label, target=None, note=None, colfilter=None, 
                 logscale_attr=None):
        _ColFieldBase.__init__(self, param, label, target=target, note=note, 
                               colfilter=colfilter)
        self.logscale_attr = logscale_attr

    def get_params(self, ns, kwargs):
        value = getattr(ns, self.param, None)
        if value and self.target:
            set_target(kwargs, self.target, self.param, value)
        if self.logscale_attr:
            logscale = getattr(ns, self.logscale_attr, None)
            if logscale and logscale != 'No':
                try:
                    value = float(logscale)
                except (ValueError, TypeError):
                    pass
                else:
                    set_target(kwargs, self.target, self.logscale_attr, value)

    def set_default(self, workspace, ns):
        value = getattr(ns, self.param, None)
        cols = self.availablecols(workspace)
        if not cols:
            raise UIError('Dataset does not support this analysis type')
        # is the current value one of the available cols? Fix, if not.
        for name, label in cols:
            if value == name:
                break
        else:
            setattr(ns, self.param, cols[0][0])
        if self.logscale_attr and not hasattr(ns, self.logscale_attr):
            setattr(ns, self.logscale_attr, 'No')


class TwoByTwoColField(ColField):
    markup = 'twobytwocolname'

    def get_condcolparams(self, workspace):
        return getattr(workspace.params, self.param+'_params')


def dssummarised(ds, workspace):
    return ds.is_summarised()

def dshascols(target):
    def _dshascols(ds, workspace):
        for colname in workspace.plottype.get_collist(target):
            if not ds.has_column(colname):
                return False
        return True
    return _dshascols


class PopulationDSField(_ColFieldBase, DatasetField):
    markup = 'popdataset'
    dsfilter = [dssummarised]

    def __init__(self, param=None, label=None, target=None, 
                 note=None, colfilter=scalarcol, dsfilter=None):
        _ColFieldBase.__init__(self, param, label, target=target, note=note,
                               colfilter=colfilter)
        if dsfilter is not None:
            self.dsfilter = dsfilter

    def _getds(self, workspace):
        dsname = getattr(workspace.params, self.param, None)
        if dsname:
            return SOOMv0.dsload(dsname)
        return None

    def set_default(self, workspace, ns):
        if not hasattr(ns, self.param):
            cols = self.availablecols(workspace)
            if cols:
                setattr(ns, self.param + '_popcol', cols[0][0])


class ConfLevField(ChooseOneField):
    options = [
        (None, 'None'),
        ('90', '90%'),
        ('95', '95%'),
        ('99', '99%'),
        ('other', 'Other'),
    ]
    def __init__(self, param='conflev', label='Confidence limits', 
                 target=None, note=None, default='95', optional=False): 
        options = self.options
        if not optional:
            options = self.options[1:]
        ChooseOneField.__init__(self, param=param, label=label, 
                                options=options, target=target, note=note, 
                                horizontal=True, default=default, pytype=float)

    def get_params(self, ns, kwargs):
        try:
            value = _get_param(ns, self.param, self.pytype)
        except (TypeError, ValueError), e:
            raise UIError('Bad value for %s field - %s' % (self.label, e))
        if value is not None:
            value /= 100
        set_target(kwargs, self.target, self.param, value)
