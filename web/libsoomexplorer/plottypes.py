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
# $Id: plottypes.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/plottypes.py,v $

from libsoomexplorer.fields import *
from libsoomexplorer import plotform

common_first_fields = [
        ShowDatasetField(),
        AnalysisTypeField(),
        FilterField(),
]

crosstab_common_fields = [
        ChooseOneField('rounding', 'Rounding', target='outputkw',
            options = [
                (None, 'None'),
                (-5, '100k'),
                (-4, '10k'),
                (-3, '1000'),
                (-2, '100'),
                (-1, '10'),
                (0, '1'),
                (2, '2dp'),
                (4, '4dp'),
            ],
            pytype=int, default=False, horizontal=True),
        BoolField('simple_table', 'Alternate rendering', target='outputkw',
                  default=False),
    ]


class Scatter(plotform.PlotTypeBase):
    name = 'scatterplot'
    label = 'Scatter Plot'
    sample = True

    fields = common_first_fields + [
        ColField('xcolname', 'X Column', 
                 colfilter=ordinalcol, logscale_attr='logxscale'),
        ColField('ycolname', 'Y Column', 
                 colfilter=ordinalcol, logscale_attr='logyscale'),
        ColsField('condcols', 'Panel(s)'),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        OutputField(),
    ]

class ScatterMatrix(plotform.PlotTypeBase):
    name = 'scattermatrix'
    label = 'Scatter Matrix Plot'
    sample = True

    fields = common_first_fields + [
        ColsField('condcols', 'Measures', colfilter=scalarcol),
        GroupByColField(),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        OutputField(),
    ]

class Box(plotform.PlotTypeBase):
    name = 'boxplot'
    label = 'Box and Whisker Plot'
    sample = True

    fields = common_first_fields + [
        ColField('ycolname', 'Y Column', colfilter=scalarcol),
        ColField('xcolname', 'X Column', colfilter=discretecol),
        ColsField('condcols', 'Panel(s)'),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        BoolField('horizontal', 'Horizontal', target='plotkw', default=False),
        BoolField('notches', 'Notches', target='plotkw', default=True),
        BoolField('outliers', 'Outliers', target='plotkw', default=True),
        BoolField('variable_width', 'Variable Width', target='plotkw', 
                  default=True),
        BoolField('violins', 'Violins', target='plotkw', default=False),
        OutputField(),
    ]


class Histogram(plotform.PlotTypeBase):
    name = 'histogram'
    label = 'Histogram Plot'
    sample = True

    fields = common_first_fields + [
        ColField('xcolname', 'X Column', colfilter=scalarcol),
        ColsField('condcols', 'Panel(s)'),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        ChooseOneField('hist_type', 'Type', target='plotkw', 
            options = [
                ('percent', 'Percent'),
                ('count', 'Frequency'),
                ('density', 'Density'),
            ],
            default = 'percent'),
        IntField('bins', 'Bins', target='plotkw', default=''),
        OutputField(),
    ]

class Density(plotform.PlotTypeBase):
    name = 'densityplot'
    label = 'Density Plot'
    sample = True

    fields = common_first_fields + [
        ColField('xcolname', 'X Column', colfilter=scalarcol),
        ColsField('condcols', 'Panel(s)'),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        IntField('bins', 'Bins', target='plotkw', default=''),
        OutputField(),
    ]

class Line(plotform.PlotTypeBase):
    name = 'lineplot'
    label = 'Line Plot'

    fields = common_first_fields + [
#        DateTimeColField('xcolname', 'X Column'),
        ColField('xcolname', 'X Column', colfilter=discretecol),
        GroupByColField(),
        ColsField('condcols', 'Panel(s)', colfilter=discretecol),
        MeasureColField('measure'),
        CondColParamsField(),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        ConfLevField(note='(when applicable)'),
        OutputField(),
    ]


class CatChartBase(plotform.PlotTypeBase):
    stack = False

class Barchart(CatChartBase):
    name = 'barchart'
    label = 'Bar Chart'

    fields = common_first_fields + [
        ColField('xcolname', 'X Column', colfilter=discretecol),
        MeasureColField('measure'),
        GroupByColField(allow_stack=True),
        ColsField('condcols', 'Panel(s)', colfilter=discretecol),
        CondColParamsField(),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        ConfLevField(note='(when applicable)'),
        BoolField('horizontal', 'Horizontal', target='plotkw', default=False),
        FloatField('origin', 'Origin', target='plotkw', default=0),
        OutputField(),
    ]

class Dotchart(CatChartBase):
    name = 'dotchart'
    label = 'Dot Chart'

    fields = common_first_fields + [
        ColField('xcolname', 'X Column', colfilter=discretecol),
        MeasureColField('measure'),
        GroupByColField(),
        ColsField('condcols', 'Panel(s)', colfilter=discretecol),
        CondColParamsField(),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        ConfLevField(note='(when applicable)'),
        BoolField('horizontal', 'Horizontal', target='plotkw', default=False),
        OutputField(),
    ]

class SummTable(plotform.TableTypeBase):
    name = 'summtable'
    label = 'Summary Table'

    fields = common_first_fields + [
        ColsField('condcols', 'Columns(s)', colfilter=discretecol, min=1),
        StatColsField(),
        CondColParamsField(),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        ConfLevField(note='(when applicable)'),
    ]

crosstabcols = [
        ColsField('colcols', 'Column(s)', target='stratacols|summcols|colcols',
                  colfilter=discretecol, min=1),
        ColsField('rowcols', 'Row(s)', target='stratacols|summcols|rowcols',
                  colfilter=discretecol, min=1),
]

class CrossTab(plotform.CrosstabBase):
    name = 'crosstab'
    label = 'Crosstab'

    fields = common_first_fields + crosstabcols + [
        WeightColField(),
        StatColsField(),
        ProportionColsField(),
        CondColParamsField(),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        ConfLevField(note='(when applicable)'),
        ChooseOneField('marginal_totals', 'Marginal Totals', target='outputkw',
            options = [
                ('none', 'None'),
                ('before', 'Top/Left'),
                ('after', 'Bottom/Right'),
            ],
            default='none'),
    ] + crosstab_common_fields

class DatasetRows(plotform.DatasetRowsBase):
    name = 'dsrows'
    label = 'Dataset Rows'

    fields = common_first_fields + [
        ColsField('condcols', 'Columns(s)'),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        ChooseOneField('pagesize', 'Rows per page', 
            options = [
                ('5', '5'),
                ('10', '10'),
                ('25', '25'),
                ('50', '50'),
                ('100', '100'),
                ('0', 'All'),
            ],
            default='10', horizontal=True),
    ]

rate_common_fields = [
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        ConfLevField(optional=True),
    ]

rateplot_common_fields = rate_common_fields + [
        DropField('output_type', 'Output type', 
            options = [
                ('barchart', 'Bar Chart (vertical)'),
                ('barchart_horizontal', 'Bar Chart (horizontal)'),
                ('lineplot', 'Line Plot'),
            ]),
        OutputField(),
    ]

ratetab_common_fields = rate_common_fields + crosstab_common_fields
 
class DSRPlot(plotform.DSRMixin, plotform.RatePlotBase):
    name = 'dsrplot'
    label = 'Directly Standardised Event Rates Plot'

    fields = [
        ShowDatasetField('Numerator Dataset'),
        AnalysisTypeField(),
        FilterField(label='Numerator Filter'),
        ColField('standardiseby', 'Standardise by', 
                 target='stndrdcols', colfilter=discretecol),
        ColField('xcolname', 'X Column',
                 colfilter=(discretecol, notstandardisecol)),
        GroupByColField(colfilter=(discretecol, notstandardisecol)),
        ColsField('condcols', 'Panel(s)',
                  colfilter=(discretecol, notstandardisecol)),
        PopulationDSField('popset', 'Denominator Population',
                          dsfilter=dssummarised),
        FilterField('popsetparams', label='Denom. Popn. filter'),
        PopulationDSField('stdpopset', 'Standard Population',
                          dsfilter=[dssummarised, dshascols('stndrdcols')]),
        FilterField('stdpopsetparams', label='Std. Pop. filter'),
    ] + rateplot_common_fields


class DSRCrosstab(plotform.DSRMixin, plotform.RateTabBase):
    name = 'dsrcrosstab'
    label = 'Directly Standardised Event Rates Crosstab'

    fields = [
        ShowDatasetField('Numerator Dataset'),
        AnalysisTypeField(),
        FilterField(label='Numerator Filter'),
        ColField('standardiseby', 'Standardise by', 
                 target='stndrdcols', colfilter=discretecol),
    ] + crosstabcols + [
        PopulationDSField('popset', 'Denominator Population',
                          dsfilter=dssummarised),
        FilterField('popsetparams', label='Denom. Popn. filter'),
        PopulationDSField('stdpopset', 'Standard Population',
                          dsfilter=[dssummarised, dshascols('stndrdcols')]),
        FilterField('stdpopsetparams', label='Std. Pop. filter'),
        ChooseManyField('statcols', 'Measures', target='outputkw',
            options = [
                ('summfreq', 'Events'),
                ('popfreq', 'Population at risk'),
                ('std_strata_summfreq', 'Std Events'),
                ('cr', 'CR'),
                ('dsr', 'DSR'),
            ],
            horizontal=True, default='dsr'),
    ] + ratetab_common_fields


class SRPlot(plotform.SRMixin, plotform.RatePlotBase):
    name = 'srplot'
    label = 'Stratified Population Rates Plot'

    fields = [
        ShowDatasetField('Numerator Dataset'),
        AnalysisTypeField(),
        FilterField(label='Numerator Filter'),
        ColField('xcolname', 'Stratify by', colfilter=discretecol),
        GroupByColField(),
        ColsField('condcols', 'Panel(s)', colfilter=discretecol),
        PopulationDSField('popset', 'Denominator Population',
                          dsfilter=dssummarised),
        FilterField('popsetparams', label='Denom. Popn. filter'),
    ] + rateplot_common_fields


class SRCrosstab(plotform.SRMixin, plotform.RateTabBase):
    name = 'srcrosstab'
    label = 'Stratified Population Rates Crosstab'

    fields = [
        ShowDatasetField('Numerator Dataset'),
        AnalysisTypeField(),
        FilterField(label='Numerator Filter'),
    ] + crosstabcols + [
        PopulationDSField('popset', 'Denominator Population',
                          dsfilter=dssummarised),
        FilterField('popsetparams', label='Denom. Pop. filter'),
        ChooseManyField('statcols', 'Measures', target='outputkw',
            options = [
                ('summfreq', 'Events'),
                ('popfreq', 'Population at risk'),
                ('sr', 'SR'),
            ],
            horizontal=True, default='sr'),
    ] + ratetab_common_fields


class ISRPlot(plotform.ISRMixin, plotform.RatePlotBase):
    name = 'iserp'
    label = 'Indirectly Standardised Event Ratio Plot'

    fields = [
        ShowDatasetField('Events dataset'),
        AnalysisTypeField(),
        FilterField(label='Events filter'),
        ColsField('stdcols', 'Standardisation', min=1,
                  target='stndrdcols', colfilter=discretecol),
        ColField('xcolname', 'X Column',
                 colfilter=(discretecol,)),
        GroupByColField(colfilter=(discretecol, )),
        ColsField('condcols', 'Panel(s)',
                colfilter=(discretecol, )),
        PopulationDSField('popset', 'Population for events',
                dsfilter=[dssummarised, 
                          dshascols('stratacols'),
                          dshascols('stndrdcols')]),
        FilterField('popsetparams', label='Event Pop. filter'),
        DatasetField('stdset', 'Standard events dataset',
                dsfilter=dshascols('stndrdcols')),
        FilterField('stdsetparams', label='Std. events filter'),
        PopulationDSField('stdpopset', 'Std. events population',
                dsfilter=[dssummarised, dshascols('stndrdcols')]),
        FilterField('stdpopsetparams', label='Std. Pop. filter'),
    ] + rateplot_common_fields


class ISRCrosstab(plotform.ISRMixin, plotform.RateTabBase):
    name = 'isercrosstab'
    label = 'Indirectly Standardised Event Ratio Crosstab'

    fields = [
        ShowDatasetField('Events Dataset'),
        AnalysisTypeField(),
        FilterField(label='Events filter'),
        ColsField('stdcols', 'Standardisation', target='stndrdcols', 
                colfilter=discretecol),
    ] + crosstabcols + [
        PopulationDSField('popset', 'Population for events',
                dsfilter=[dssummarised, 
                          dshascols('stratacols'),
                          dshascols('stndrdcols')]),
        FilterField('popsetparams', label='Event Pop. filter'),
        DatasetField('stdset', 'Standard events dataset',
                dsfilter=dshascols('stndrdcols')),
        FilterField('stdsetparams', label='Std. events filter'),
        PopulationDSField('stdpopset', 'Std. events population',
                dsfilter=[dssummarised, dshascols('stndrdcols')]),
        FilterField('stdpopsetparams', label='Std. Pop. filter'),
        ChooseManyField('statcols', 'Measures', target='outputkw',
            options = [
                ('isr', 'ISR'),
                ('observed', 'Observed'),
                ('expected', 'Expected'),
                ('popfreq', 'Population at risk'),
            ],
            horizontal=True, default='isr'),
    ] + ratetab_common_fields


class TwoByTwo(plotform.TwoByTwoBase):
    name = 'twobytwo'
    label = '2 x 2 x k Analysis'

    fields = common_first_fields + [
        TwoByTwoColField('exposure', 'Exposure Column', 
                    colfilter=discretecol),
        TwoByTwoColField('outcome', 'Outcome Column', 
                    colfilter=(discretecol,notcol('exposure'))),
        StratifyColField('stratacolname'),
        CondColParamsField(label='Stratify Parameters'),
        TextAreaField('title', 'Title'),
        TextAreaField('subtitle', 'Footer'),
        ChooseOneField('std', 'Fourfold standardise', 
            options = [
                ('None', 'No Fourfold plot'),
                ('margins_1', 'Standardise row'),
                ('margins_2', 'Standardise column'),
                ('margins_12', 'Standardise rows and columns'),
                ('ind.max', 'Individually standardised'),
                ('all.max', 'Simultaneously standardised'),
            ],
            default='ind.max'),
        ConfLevField(),
    ]


plottypes = (
    Line, Barchart, Dotchart,
    Scatter, ScatterMatrix, Histogram, Density, Box, 
    SummTable, CrossTab, DatasetRows, 
    TwoByTwo,
    DSRPlot, DSRCrosstab,
    SRPlot, SRCrosstab,
    ISRPlot, ISRCrosstab,
)

