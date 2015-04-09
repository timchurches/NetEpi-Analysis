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
# $Id: plot_demo.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/plot_demo.py,v $

# Standard python modules
import os, sys, time
import optparse

#
from SOOMv0 import *
from testrunner import Test, TestRunner

optp = optparse.OptionParser()
optp.add_option('--soompath', dest='soompath',
                help='SOOM dataset path')
options, args = optp.parse_args()
if not options.soompath:
    options.soompath = os.path.normpath(os.path.join(os.path.dirname(__file__), 
                                                     '..', 'SOOM_objects'))
soom.setpath(options.soompath)


# Load dataset
nhds = dsload("nhds")


tests = [

    Test('Simple bar chart, check that origin correctly defaults to zero.',
         plot.barchart, nhds, 'sex'),

    Test('Test of titles and footers.',
         plot.barchart, nhds, 'sex',title="A funny thing happened on the way to the forum",
         footer="E tu, Brute!"),

    Test('Test of titles and footers with line breaks and tabs.',
         plot.barchart, nhds, 'sex',title="A funny\nthing\nhappened\non the\nway to the\nforum",
         footer="E tu,\t\t\t\t\Brute!"),

    Test('Simple bar chart, using pre-summarised data, check that it is automatically recognised it as a summary dataset - currently this does not happen.',
         plot.barchart, nhds.summ("sex"), 'sex',),

    Test('Simple bar chart, using pre-summarised data, using manually specified weighting.',
         plot.barchart, nhds.summ("sex"), 'sex', measure=freq(), weightcol='_freq_'),

    Test('Stacked bar chart, conditioning column same as stackby column.',
         plot.barchart, nhds, 'sex', stackby='sex'),

    Test('Grouped bar chart, conditioning column same as groupby column.',
         plot.barchart, nhds, 'sex', groupby='sex'),

    Test('Stacked bar chart, conditioning column different to stackby column.',
         plot.barchart, nhds, 'geog_region', stackby='sex'),

    Test('Stacked bar chart, packed bars (pack=True), conditioning column different to stackby column.',
         plot.barchart, nhds, 'geog_region', stackby='sex',pack=True),

    Test('Grouped bar chart, conditioning column different to groupby column.',
         plot.barchart, nhds, 'geog_region', groupby='sex'),

    Test('Barchart with a non-zero origin.',
         plot.barchart, nhds,"sex",origin=100000),

    Test('Barchart with a non-zero origin and some values below the origin',
         plot.barchart, nhds,"sex",origin=1000000),
    
    Test('Barchart with explicit y scale 0 to 2,000,000',
         plot.barchart, nhds,"sex",ylim=(0,2000000)),

    Test('Barchart with explicit y scale 0 to 2,000,000 and increased number of tick marks',
         plot.barchart, nhds,"sex",ylim=(0,2000000),yticks=10),

    Test('Barchart with log scale',
         plot.barchart, nhds,"sex",logyscale=10),

    Test('Barchart with unusual bases for log scale',
         plot.barchart, nhds,"sex",logyscale=7),

    # Test('Charts can\'t use explicit scales and log scales together in current version.',
    #     plot.barchart, nhds,"sex",ylim=(0,2000000),logyscale=7),

    Test('Horizontal barchart',
         plot.barchart, nhds,"sex",horizontal=True),

    Test('Horizontal barchart with more categories',
         plot.barchart, nhds,"prin_src_payment2",horizontal=True),

    Test('Vertical barchart with more categories',
         plot.barchart, nhds,"prin_src_payment2",horizontal=False),

    Test('Vertical barchart with rotated labels',
         plot.barchart, nhds,"prin_src_payment2",xlabelrotate=45),

    Test('Barchart panel plot by specifying more than one conditioning column',
         plot.barchart, nhds,"prin_src_payment2","sex"),

    Test('Barchart panel plot by specifying more than one conditioning column - reversed order of conditioning columns',
         plot.barchart, nhds,"sex","prin_src_payment2"),

    Test('Panel plots - can specify layout of panels using a tuple (cols, rows, pages)',
         plot.barchart, nhds,"prin_src_payment2","sex",layout=(1,2,1)),

    # This aspect of layout not implemented yet.
    #Test('Panel plots - can specify layout of panels using a string "h" or "v" ("h" used here)',
    #     plot.barchart, nhds,"geog_region","sex",layout='h'),

    #Test('Panel plots - can specify layout of panels using a string "h" or "v" ("v" used here)',
    #     plot.barchart, nhds,"geog_region","sex",layout='v'),

    #Test('Panel plots - this should not break...',
    #     plot.barchart, nhds,"sex","geog_region",filterexpr="geog_region in (1,2)",layout='v'),

    Test('Panel plots - horizontal panel plots also OK',
         plot.barchart, nhds,"hosp_ownership","sex",horizontal=True),

    # Test('Panel plots - panelling by a scalar column (filtered for speed)',
    #      plot.barchart, nhds,"sex","age",filterexpr="diagnosis1 =: '410'"),

    # Test('Stacking by a scalar column...',
    #      plot.barchart, nhds,"sex",stackby="age",filterexpr="diagnosis1 =: '410'"),

    Test('Barcharts - dates on x-axis',
         plot.barchart, nhds,"randomdate",filterexpr="randomdate between (date(2002,1,1),date(2002,1,31))"),

    Test('Barcharts - dates on y-axis',
         plot.barchart, nhds,"randomdate",filterexpr="randomdate between (date(2002,1,1),date(2002,1,31))",horizontal=True),

    Test('Barcharts - horizontal layout with coloured bars due to pseudo-stacking',
          plot.barchart, nhds,"hosp_ownership","geog_region",stackby="hosp_ownership"),

    Test('Barcharts - measure column is mean(\'age\') rather than frequency',
         plot.barchart, nhds,"marital_status",measure=mean('age')),

    Test('Barcharts - measure column is mean(\'age\') weighted by \'analysis_wgt\', rather than frequency',
         plot.barchart, nhds,"marital_status",measure=mean('age',weightcol='analysis_wgt')),

    Test('Plotting proportions - measure=(\'marital_status\',)',
         plot.barchart, nhds,"marital_status",measure=('marital_status',)),

    Test('Plotting proportions - measure=(\'marital_status\',) weighted by \'analysis_wgt\'',
         plot.barchart, nhds,"marital_status",measure=('marital_status',),weightcol='analysis_wgt'),

    Test('Panelled proportions plot - measure=(\'marital_status\',\'sex\') weighted by \'analysis_wgt\'',
         plot.barchart, nhds,"marital_status","sex",measure=('marital_status','sex'),weightcol='analysis_wgt'),

    Test('Panelled proportions plot - measure=(\'sex\',) weighted by \'analysis_wgt\'',
         plot.barchart, nhds,"marital_status","sex",measure=('sex',),weightcol='analysis_wgt'),

    Test('Panelled proportions plot - measure=(\'marital_status\',) weighted by \'analysis_wgt\'',
         plot.barchart, nhds,"marital_status","sex",measure=('marital_status',),weightcol='analysis_wgt'),

    Test('Stacked proportions plot - measure=(\'marital_status\',\'sex\') weighted by \'analysis_wgt\'',
         plot.barchart, nhds,"marital_status",stackby="sex",measure=('marital_status','sex'),weightcol='analysis_wgt'),

    Test('Stacked proportions plot - measure=(\'marital_status\',) weighted by \'analysis_wgt\'',
         plot.barchart, nhds,"marital_status",stackby="sex",measure=('marital_status',),weightcol='analysis_wgt'),

    Test('Stacked proportions plot - measure=(\'sex\',) weighted by \'analysis_wgt\'',
         plot.barchart, nhds,"marital_status",stackby="sex",measure=('sex',),weightcol='analysis_wgt'),

    Test('Simple dotchart.',
         plot.dotchart, nhds,"sex"),

    Test('Panelled dotchart',
         plot.dotchart, nhds,"marital_status","sex"),

    Test('Horizontal panelled dotchart using median(\'days_of_care\') weighted by \'analysis_wgt\'',
         plot.dotchart, nhds,"marital_status","sex",measure=median('days_of_care'),weightcol='analysis_wgt',horizontal=True),

    Test('Grouped dotchart',
         plot.dotchart, nhds,"admission_type",groupby="hosp_ownership",measure=freq(),weightcol='analysis_wgt'),

    # Test('Stacked dotchart - seems to be idetical to grouped dotchart (or v-v) - no weighting',
    #      plot.dotchart, nhds,"admission_type",stackby="hosp_ownership",measure=freq()),

    # Test('Stacked dotchart - seems to be idetical to grouped dotchart (or v-v) - with weighting',
    #      plot.dotchart, nhds,"admission_type",stackby="hosp_ownership",measure=freq(),weightcol='analysis_wgt'),

    # Test('Stacked dotchart with bigger symbols...curent doesn\'t have any effect...',
    #      plot.dotchart, nhds,"admission_type",stackby="hosp_ownership",measure=freq(),dotsize=2),

    Test('Histogram - filtered to reduce data volume',
         plot.histogram, nhds,"age",filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Count histograms...',
         plot.histogram, nhds,"age",hist_type='count',filterexpr="diagnosis1 =: '410'",
         filterlabel="Admissions for acute myocardial infarction"),

    Test('Density histograms...',
         plot.histogram, nhds,"age",hist_type='density',filterexpr="diagnosis1 =: '410'",
         filterlabel="Admissions for acute myocardial infarction"),

    Test('Density plot...',
         plot.densityplot, nhds,"age",filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Percentage histograms with more bins...',
         plot.histogram, nhds,"age",bins=55,filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Percentage histograms with panelling...works OK',
         plot.histogram, nhds,"age","sex",filterexpr="diagnosis1 =: '410'",bins=55,
         filterlabel="Admissions for acute myocardial infarction"),

    Test('Vertically stacked histograms of age distribution using layout parameter',
         plot.histogram, nhds,"age","sex",bins=50,layout=(1,2,1),filterexpr="diagnosis1 =: '410'",
         filterlabel="Admissions for acute myocardial infarction"),

    Test('Panelled count histograms - is the y scale labelling correct?',
         plot.histogram, nhds,"age","sex",hist_type='count',filterexpr="diagnosis1 =: '410'",bins=55,
         filterlabel="Admissions for acute myocardial infarction"),

    Test('Panelled count histograms with 18 age bins...',
         plot.histogram, nhds,"age","sex",hist_type='count',filterexpr="diagnosis1 =: '410'",bins=18,
         filterlabel="Admissions for acute myocardial infarction"),

    Test('Panelled barchart - compare counts to those from panelled histogram by 5 yr age groups.',
         plot.barchart, nhds,"agegrp","sex",filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Panelled density plot',
         plot.densityplot, nhds,"age","sex",filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Box plot',
         plot.boxplot, nhds,"age","sex",filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Box plot with variable width disabled',
         plot.boxplot, nhds,"age","sex",variable_width=False,filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Box plot with outliers display disabled - Lattice bwplot doesn\'t seem to support this?',
         plot.boxplot, nhds,"age","sex",outliers=False,filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Box plot with notches display disabled - Lattice bwplot doesn\'t seem to support notches?',
         plot.boxplot, nhds,"age","sex",notches=False,filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Panelled box plot',
         plot.boxplot, nhds,"age","marital_status",
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Horizontal panelled box plot',
         plot.boxplot, nhds,"age","num_beds",horizontal=True,
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Box plot with vertical=True',
         plot.boxplot, nhds,"age","num_beds",vertical=True,
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Box plot with vertical=False',
         plot.boxplot, nhds,"age","num_beds",vertical=False,
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Panelled box plot',
         plot.boxplot, nhds,"age","num_beds","sex",
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Panelled horizontal box plot',
         plot.boxplot, nhds,"age","num_beds","sex",horizontal=True,
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Two-way panelled box plot',
         plot.boxplot, nhds,"age","num_beds","sex","geog_region",
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    # Test('Three-way panelled box plot',
    #      plot.boxplot, nhds,"age","num_beds","sex","geog_region","marital_status",
    #      filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Scatter plot',
         plot.scatterplot, nhds,"age","days_of_care",
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Scatter plot showing support for missing values',
         plot.scatterplot, nhds,"age","randomvalue",
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Scatter plot with log scales',
         plot.scatterplot, nhds,"age","randomvalue",logxscale=10,logyscale=2,
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Scatter plot with date/time values',
         plot.scatterplot, nhds,"age","randomdate",
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Panelled scatter plot',
         plot.scatterplot, nhds,"age","days_of_care","agegrp",
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Panelled scatter plot using continuous panelling column',
         plot.scatterplot, nhds,"age","days_of_care","randomvalue",
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Scatter plot matrix',
         plot.scattermatrix, nhds,"age","days_of_care","randomvalue",
         filterexpr="diagnosis1 =: '410'",filterlabel="Admissions for acute myocardial infarction"),

    Test('Simple time-series line plot',
         plot.lineplot, nhds, "randomdate",
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487'",filterlabel="Admissions for pneumonia and influenza"),

    Test('Simple time-series line plot using weighted frequencies',
         plot.lineplot, nhds, "randomdate",measure=freq(),weightcol="analysis_wgt",
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487' and randomdate >= date(2002,6,1)",
         filterlabel="Admissions for pneumonia and influenza, June-December 2002"),

    # Test('Simple time-series line plot using weighted frequencies and different date formating - not current supported',
    #      plot.lineplot, nhds, "randomdate",measure=freq(),weightcol="analysis_wgt",dateformat='%d-%B',
    #      filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487' and randomdate >= date(2002,6,1)",
    #      filterlabel="Admissions for pneumonia and influenza, June-December 2002"),

    # Test('Simple time-series line plot - note automatic date axis labelling',
    #      plot.lineplot, nhds, "randomdate",measure=freq(),weightcol="analysis_wgt",dateformat='%d-%B',
    #      filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487' and randomdate between (date(2002,6,1),date(2002,6,15))",
    #      filterlabel="Admissions for pneumonia and influenza, 1-15 June 2002"),

    Test('Simple time-series line plot - with a statistic as the measure',
         plot.lineplot, nhds, "randomdate",measure=mean('age'),weightcol="analysis_wgt",
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487' and randomdate between (date(2002,6,1),date(2002,6,15))",
         filterlabel="Admissions for pneumonia and influenza, 1-15 June 2002"),

    Test('Time-series line plot with groupby',
         plot.lineplot, nhds,"randomdate",groupby="sex",
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487'",filterlabel="Admissions for pneumonia and influenza"),

    Test('Time-series line plot with groupby and thicker lines',
         plot.lineplot, nhds,"randomdate",groupby="sex",line_width=6,
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487'",filterlabel="Admissions for pneumonia and influenza"),

    Test('Time-series line plot with groupby and different line style',
         plot.lineplot, nhds,"randomdate",groupby="geog_region",line_style=6,
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487'",filterlabel="Admissions for pneumonia and influenza"),

    Test('Panelled time-series line plot',
         plot.lineplot, nhds,"randomdate","geog_region",
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487'",filterlabel="Admissions for pneumonia and influenza"),

    Test('Panelled time-series line plot with groupby',
         plot.lineplot, nhds,"randomdate","geog_region",groupby='sex',
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487'",filterlabel="Admissions for pneumonia and influenza"),

    Test('Line plot of a categorical column',
         plot.lineplot, nhds,"marital_status",
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487'",filterlabel="Admissions for pneumonia and influenza"),

    Test('Line plot of an ordinal column',
         plot.lineplot, nhds,"agegrp",
         filterexpr="diagnosis1 >=: '480' and diagnosis1 <=: '487'",filterlabel="Admissions for pneumonia and influenza"),

]

runner = TestRunner()


# Run tests
try:
    runner.run(tests)
finally:
    runner.close()

