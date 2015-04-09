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
# $Id: whotext.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/loaders/whotext.py,v $

# Python standard modules
import os
import csv
import sys

# 3rd Party Modules
# http://www.pfdubois.com/numpy/
import Numeric, MA
from mx.DateTime import DateTime

# SOOM modules
from SOOMv0 import *
from SOOMv0.Sources.CSV import *

def make_whotext(options):
    label="WHO outbreak reports 2003-2004"
    whotext = makedataset("who_text", label=label)

    whotext.addcolumn("title",label="Report Title",coltype="searchabletext",datatype=str)
    whotext.addcolumn("repdate",label="Report Date",coltype="date",datatype='recodedate')
    whotext.addcolumn("report",label="Report Text",coltype="searchabletext",datatype=str)
    if options.verbose:
        print whotext
    return whotext

def whotext_xform_pre(row_dict):
    months = {'January':1,
                    'February':2,
                    'March':3,
                    'April':4,
                    'May':5,
                    'June':6,
                    'July':7,
                    'August':8,
                    'September':9,
                    'October':10,
                    'November':11,
                    'December':12}
                    
    rawdate = row_dict['repdate']
    try:    
        day, wordmonth, year = rawdate.split()
    except:
        print rawdate
        sys.exit()
    month = months[wordmonth]
    newdate = DateTime(int(year), month, int(day))
    row_dict['repdate'] = str(newdate.day) + '/' + str(newdate.month) + '/' + str(newdate.year)
    row_dict['report'] = row_dict['report'].replace('<p>','\n')
    return row_dict

def whotext_source(filename):
    whotext_columns = [
            DataSourceColumn("title",label="Title",coltype="searchabletext",ordinalpos=0),
            DataSourceColumn("repdate",label="Report Date",coltype="date",ordinalpos=1),
            DataSourceColumn("report",label="Report Text",coltype="searchabletext",ordinalpos=2),
    ]

    return CSVDataSource("whotext_data", whotext_columns, filename=filename, header_rows=0,
                         label="WHO outbreak reports 2003-05",xformpre=whotext_xform_pre)


def load_whotext(whotext, filename, options):
    filename = os.path.join(options.datadir, filename)
    whotext_src = whotext_source(filename)
    if options.verbose:
        print whotext
    whotext.initialise()
    whotext.loaddata(whotext_src,
                      chunkrows=options.chunkrows,
                      rowlimit=options.rowlimit)
    whotext.finalise()

def load(options):
    ds = make_whotext(options)
    load_whotext(ds, 'whoreps.csv.gz', options)
    ds.save()
