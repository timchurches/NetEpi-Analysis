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
#   Define and load example data from the EpiTools web site
#   http: //www.medepi.net/epitools/examples.html
#
# Python standard modules
import os

# 3rd Party Modules
# http: //www.egenix.com/files/python/eGenix-mx-Extensions.html
from mx.DateTime import DateTime
# http: //www.pfdubois.com/numpy/
import Numeric, MA

# SOOM modules
from SOOMv0.Sources.CSV import *
from SOOMv0 import *

# Project modules
import urlfetch

# http: //www.medepi.net/epitools/examples.html
oswego_url = 'http://www.medepi.net/data/oswego/oswego.txt'
wnv_url = 'http://www.medepi.net/data/wnv/wnv2004-12-14.txt'


def fetch(scratchdir, dataset, url):
    """
    Caching URL fetcher, returns filename of cached file.
    """
    filename = os.path.join(scratchdir, os.path.basename(url))
    print 'Fetching dataset %r from %s' % (dataset, url)
    urlfetch.fetch(url, filename)
    return filename

# Add 5 year age groups
def agegrp(age):
    agrp = MA.choose(MA.greater_equal(age, 85), (age, -18.0))
    agrp = MA.choose(MA.greater_equal(agrp, 80), (agrp, -17.0))
    agrp = MA.choose(MA.greater_equal(agrp, 75), (agrp, -16.0))
    agrp = MA.choose(MA.greater_equal(agrp, 70), (agrp, -15.0))
    agrp = MA.choose(MA.greater_equal(agrp, 65), (agrp, -14.0))
    agrp = MA.choose(MA.greater_equal(agrp, 60), (agrp, -13.0))
    agrp = MA.choose(MA.greater_equal(agrp, 55), (agrp, -12.0))
    agrp = MA.choose(MA.greater_equal(agrp, 50), (agrp, -11.0))
    agrp = MA.choose(MA.greater_equal(agrp, 45), (agrp, -10.0))
    agrp = MA.choose(MA.greater_equal(agrp, 40), (agrp, -9.0))
    agrp = MA.choose(MA.greater_equal(agrp, 35), (agrp, -8.0))
    agrp = MA.choose(MA.greater_equal(agrp, 30), (agrp, -7.0))
    agrp = MA.choose(MA.greater_equal(agrp, 25), (agrp, -6.0))
    agrp = MA.choose(MA.greater_equal(agrp, 20), (agrp, -5.0))
    agrp = MA.choose(MA.greater_equal(agrp, 15), (agrp, -4.0))
    agrp = MA.choose(MA.greater_equal(agrp, 10), (agrp, -3.0))
    agrp = MA.choose(MA.greater_equal(agrp, 5), (agrp, -2.0))
    agrp = MA.choose(MA.greater_equal(agrp, 0), (agrp, -1.0))
    returnarray = -agrp.astype(MA.Int)
    return returnarray

agegrp_outtrans = {
    None: 'Unknown',
    0: 'All ages',
    1: '0 - 4 yrs',
    2: '5 - 9 yrs',
    3: '10 - 14 yrs',
    4: '15 - 19 yrs',
    5: '20 - 24 yrs',
    6: '25 - 29 yrs',
    7: '30 - 34 yrs',
    8: '35 - 39 yrs',
    9: '40 - 44 yrs',
    10: '45 - 49 yrs',
    11: '50 - 54 yrs',
    12: '55 - 59 yrs',
    13: '60 - 64 yrs',
    14: '65 - 69 yrs',
    15: '70 - 74 yrs',
    16: '75 - 79 yrs',
    17: '80 - 84 yrs',
    18: '85+ yrs',
}

yn_outtrans = {
    None: 'Unknown',
    'Y': 'Yes', 
    'N': 'No'
} 

def oswego_xform_post(row_dict):
    # create synthetic meal date/time
    meal_time = row_dict['meal_time']
    if meal_time != None:
        mt_hrmin, mt_ampm = meal_time.split()
        mt_hr, mt_min = map(int, mt_hrmin.split(':'))
        if mt_ampm == 'PM':
            mt_hr += 12
        row_dict['meal_datetime'] = DateTime(1980, 4, 18, mt_hr, mt_min)
    else:
        row_dict['meal_datetime'] = None
    # create synthetic onset date/time
    onset_time = row_dict['onset_time']
    onset_date = row_dict['onset_date']
    if onset_time != None and onset_date != None:
        on_hrmin, on_ampm = onset_time.split()
        on_hr, on_min = map(int, on_hrmin.split(':'))
        if on_ampm == 'PM':
            on_hr += 12
        on_mth, on_day = map(int, onset_date.split('/'))
        row_dict['onset_datetime'] = DateTime(1980, on_mth, on_day, on_hr, on_min)
    else:
        row_dict['onset_datetime'] = None
    return row_dict


def oswego_load(options):
    oswego_columns = (
        DataSourceColumn('id', ordinalpos=0),
        DataSourceColumn('age', ordinalpos=1),
        DataSourceColumn('sex', ordinalpos=2),
        DataSourceColumn('meal_time', ordinalpos=3),
        DataSourceColumn('ill', ordinalpos=4),
        DataSourceColumn('onset_date', ordinalpos=5),
        DataSourceColumn('onset_time', ordinalpos=6),
        DataSourceColumn('baked_ham', ordinalpos=7),
        DataSourceColumn('spinach', ordinalpos=8),
        DataSourceColumn('mashed_potato', ordinalpos=9),
        DataSourceColumn('cabbage_salad', ordinalpos=10),
        DataSourceColumn('jello', ordinalpos=11),
        DataSourceColumn('rolls', ordinalpos=12),
        DataSourceColumn('brown_bread', ordinalpos=13),
        DataSourceColumn('milk', ordinalpos=14),
        DataSourceColumn('coffee', ordinalpos=15),
        DataSourceColumn('water', ordinalpos=16),
        DataSourceColumn('cakes', ordinalpos=17),
        DataSourceColumn('vanilla_ice_cream', ordinalpos=18),
        DataSourceColumn('chocolate_ice_cream', ordinalpos=19),
        DataSourceColumn('fruit_salad', ordinalpos=20),
    )

    filename = fetch(options.scratchdir, 'oswego', oswego_url)
    oswego_source = CSVDataSource('oswego', oswego_columns, delimiter=' ',
                                  filename=filename, header_rows=1,
                                  missing='NA',
                                  xformpost=oswego_xform_post)

    oswego = makedataset('oswego', 
        label='Oswego County gastrointestinal illness investigation data', 
        desc='Dataset derived from: ' + oswego_url)

    oswego.addcolumn('id', label='ID Number', datatype=int, coltype='identity')
    oswego.addcolumn('age', label='Age (years)', datatype=int, coltype='scalar')
    oswego.addcolumn('sex', label='Sex', 
                     datatype='recode', coltype='categorical', 
                     outtrans={'M': 'Male', 'F': 'Female'})
    oswego.addcolumn('meal_time', label='Meal time', datatype=str)
    oswego.addcolumn('meal_datetime', label='Meal date/time', 
                     datatype='datetime', coltype='ordinal')
    oswego.addcolumn('ill', label='Became ill?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('onset_date', label='Onset date', datatype=str)
    oswego.addcolumn('onset_time', label='Onset time', datatype=str)
    oswego.addcolumn('onset_datetime', label='Illness onset date/time', 
                     datatype='datetime', coltype='ordinal')
    oswego.addcolumn('baked_ham', label='Ate baked ham?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('spinach', label='Ate spinach?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('mashed_potato', label='Ate mashed potato?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('cabbage_salad', label='Ate cabbage salad?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('jello', label='Ate jello?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('rolls', label='Ate bread rolls?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('brown_bread', label='Ate brown bread?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('milk', label='Drank milk?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('coffee', label='Drank coffee?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('water', label='Drank water?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('cakes', label='Ate cakes?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('vanilla_ice_cream', label='Ate vanilla ice cream?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('chocolate_ice_cream', label='Ate chocolate ice cream?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)
    oswego.addcolumn('fruit_salad', label='Ate fruit salad?', 
                     datatype='recode', coltype='categorical', 
                     outtrans=yn_outtrans)

    oswego.initialise()
    oswego.loaddata(oswego_source)
    oswego.finalise()

    oswego.derivedcolumn(dername='agegrp', dercols=('age', ), derfunc=agegrp, 
                         coltype='ordinal', datatype=int, 
                         outtrans=agegrp_outtrans, label='Age Group', 
                         all_value=0, all_label='All ages')
    oswego.save()


def wnv_load(options):
    wnv_columns = (
        DataSourceColumn('id', ordinalpos=0),
        DataSourceColumn('county', ordinalpos=1),
        DataSourceColumn('age', ordinalpos=2),
        DataSourceColumn('sex', ordinalpos=3),
        DataSourceColumn('syndrome', ordinalpos=4),
        DataSourceColumn('onset_date', format='iso-date', ordinalpos=5),
        DataSourceColumn('test_date', format='iso-date', ordinalpos=6),
        DataSourceColumn('death', ordinalpos=7),
    )

    filename = fetch(options.scratchdir, 'wnv', wnv_url)
    wnv_source = CSVDataSource('wnv', wnv_columns,
                               filename=filename, header_rows=1,
                               missing='NA')

    wnv = makedataset('wnv', 
        label='Human cases of West Nile virus, California 2004', 
        desc='Dataset derived from: ' + wnv_url)

    wnv.addcolumn('id', label='ID Number', datatype=int, coltype='identity')
    wnv.addcolumn('county', label='County', datatype='recode', 
                  coltype='categorical', missingvalues={None: 'Unknown'})
    wnv.addcolumn('age', label='Age (years)', datatype=int, coltype='scalar')
    wnv.addcolumn('sex', label='Sex', datatype='recode', coltype='categorical', 
                  outtrans={'M': 'Male', 'F': 'Female'}, 
                  missingvalues={None: 'Unknown'}, 
                  all_value='P', all_label='Persons')
    wnv.addcolumn('syndrome', label='Syndrome', datatype='recode', 
                  coltype='categorical', 
                  missingvalues={None: 'Unknown'}, 
                  outtrans={'WNF': 'West Nile fever', 'WNND': 'West Nile neuroinvasive disease'})
    wnv.addcolumn('onset_date', label='Onset date', datatype='date', 
                  coltype='date')
    wnv.addcolumn('test_date', label='Test date', datatype='date', 
                  coltype='date')
    wnv.addcolumn('death', label='Died?', 
                  datatype='recode', coltype='categorical', 
                  outtrans=yn_outtrans)

    wnv.initialise()
    wnv.loaddata(wnv_source)
    wnv.finalise()

    wnv.derivedcolumn(dername='agegrp', dercols=('age', ), derfunc=agegrp, 
                      coltype='ordinal', datatype=int, 
                      outtrans=agegrp_outtrans, label='Age Group', 
                      all_value=0, all_label='All ages')
    wnv.save()

def load(options):
    oswego_load(options)
    wnv_load(options)
