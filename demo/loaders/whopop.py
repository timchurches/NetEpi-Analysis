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
#   Define and load new WHO World Standard Population data
#
# $Id: whopop.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/loaders/whopop.py,v $

# Python standard modules
import os
import csv

# 3rd Party Modules
# http://www.pfdubois.com/numpy/
import Numeric, MA

# SOOM modules
from SOOMv0 import *
from SOOMv0.Sources.CSV import *

def make_worldpop(options):
    world_agegrp = Numeric.array(range(1,19) + range(1,19))
    sex_outtrans = {1:'Male',2:'Female'}
    agegrp_outtrans = {
                            0:"All ages",
                            1:"0 - 4 yrs",
                            2:"5 - 9 yrs",
                        3:"10 - 14 yrs",
                        4:"15 - 19 yrs",
                        5:"20 - 24 yrs",
                        6:"25 - 29 yrs",
                        7:"30 - 34 yrs",
                        8:"35 - 39 yrs",
                        9:"40 - 44 yrs",
                    10:"45 - 49 yrs",
                    11:"50 - 54 yrs",
                    12:"55 - 59 yrs",
                    13:"60 - 64 yrs",
                    14:"65 - 69 yrs",
                    15:"70 - 74 yrs",
                    16:"75 - 79 yrs",
                    17:"80 - 84 yrs",
                    18:"85+ yrs"}

    world_pop = Numeric.array([ 0.0886,
                    0.0869,
                    0.0860,
                    0.0847,
                    0.0822,
                    0.0793,
                    0.0761,
                    0.0715,
                    0.0659,
                    0.0604,
                    0.0537,
                    0.0455,
                    0.0372,
                    0.0296,
                    0.0221,
                    0.0152,
                    0.0091,
                    0.0060]*2,typecode=Numeric.Float)
    world_pop = (world_pop * 1000000).astype(Numeric.Int32)
    world_sex = Numeric.array([1]*18 + [2]*18,typecode=Numeric.Int)
    # Dataset with both sexes
    worldpop_mf = makedataset("worldpop_mf",label="WHO World Standard (Theoretical) Population - male and female (identical propostions)")
    worldpop_mf.addcolumnfromseq(name="_stdpop_",data=world_pop,mask=None,label="Standard population",datatype=int,coltype="scalar")
    worldpop_mf.addcolumnfromseq(name="agegrp",data=world_agegrp,mask=None,label="Age group",coltype="ordinal",datatype=int,outtrans=agegrp_outtrans)
    worldpop_mf.addcolumnfromseq(name="sex",data=world_sex,mask=None,label="Sex",coltype="categorical",datatype=int,outtrans=sex_outtrans)
    # Dataset with just persons
    worldpop_p = makedataset("worldpop_p",label="WHO World Standard (Theoretical) Population - persons only")
    worldpop_p.addcolumnfromseq(name="_stdpop_",data=world_pop[0:18],mask=None,label="Standard population",datatype=int,coltype="scalar")
    worldpop_p.addcolumnfromseq(name="agegrp",data=world_agegrp[0:18],mask=None,label="Age group",coltype="ordinal",datatype=int,outtrans=agegrp_outtrans)
    if options.verbose:
        print worldpop_mf
        print worldpop_p
    return worldpop_mf, worldpop_p

years = [2000,2001,2002]

def merge_who_indicator_data(datadir, scratchdir):
    """
    load some data extracted from the WHO WHOSIS Web site - data
    files are in ./rawdata directory

    This transposes the data, converting rows into columns and v-v
    """
    data = {}
    for year in years:
        src_fn = os.path.join(datadir, 'who%s.csv' % year)
        csv_reader = csv.reader(open(src_fn, 'U'))
        colmap = {}
        for line_no, fields in enumerate(csv_reader):
            # print line_no, fields
            if line_no == 0:
                pass
            elif line_no == 1:
                for i, colname in enumerate(fields):
                    data[(colname,year)] = []
                    colmap[i] = (colname,year)
            else:
                for i, value in enumerate(fields):
                    value = value.strip()
                    data[colmap[i]].append(value)

    # Check if indicators the same in all years
    indicators = None
    for year in years:
        if indicators:
            if indicators != data[('Indicators', year)]:
                print "Indicators changed"
        else:
            indicators = data[('Indicators', year)]
    else:
        print "Indicators equal"

    # Write CSV file
    csv_fn = os.path.join(scratchdir, 'whodata.csv')
    fo = open(csv_fn, 'w')
    try:
        for country, year in data.keys():
            if country != "Indicators":
                dataseq = [country, str(year)] + data[(country,year)]
                line = ','.join(dataseq)
                print >> fo, line
    finally:
        fo.close()

    return csv_fn, indicators, 


def make_whoindic(options):
    label="WHO indicators %d-%d" % (years[0], years[-1])
    whoindic = makedataset("who_indicators", label=label)

    whoindic.addcolumn("country",label="Country",coltype="categorical",datatype=str)
    whoindic.addcolumn("year",label="Year",coltype="ordinal",datatype=int)
    if options.verbose:
        print whoindic
    return whoindic


def whoindic_source(whoindic, filename, indicators):
    whodata_columns = [
            DataSourceColumn("country",label="Country",coltype="categorical",ordinalpos=0,posbase=0),
            DataSourceColumn("year",label="Year",coltype="ordinal",ordinalpos=1,posbase=0),
    ]

    i = 2
    for indic in indicators:
        varname = '_'.join(indic.lower().split())
        varname = varname.replace('(', '').replace(')', '').replace(';', '')
        varname = varname.replace('%', 'percent')
        varname = varname.replace('+', '_plus')
        varname = varname.replace('-', '_')
        varname = varname.replace('$', '_dollars')
        coldef = DataSourceColumn(varname,label=indic,coltype="scalar",ordinalpos=i,posbase=0)
        whodata_columns.append(coldef)
        i += 1         
        whoindic.addcolumn(varname,label=indic,datatype=float,coltype="scalar")

    return CSVDataSource("who_indicators_data", whodata_columns, filename=filename, header_rows=0, label="WHO indicators 2000-2002")


def load_whoindic(whoindic, options):
    filename, indicators = merge_who_indicator_data(options.datadir, 
                                                    options.scratchdir)
    whodata = whoindic_source(whoindic, filename, indicators)
    if options.verbose:
        print whodata
    whoindic.initialise()
    whoindic.loaddata(whodata,
                      chunkrows=options.chunkrows,
                      rowlimit=options.rowlimit)
    whoindic.finalise()

def load(options):
    mf_ds, p_ds = make_worldpop(options)
    mf_ds.save()
    p_ds.save()
    ind_ds = make_whoindic(options)
    load_whoindic(ind_ds, options)
    ind_ds.save()
