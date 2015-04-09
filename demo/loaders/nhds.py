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
#   Define and load NHDS sample data
#
# $Id: nhds.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/loaders/nhds.py,v $

# Python standard modules
import os
import sys
import random
import cPickle

# 3rd Party Modules
# http://www.egenix.com/files/python/eGenix-mx-Extensions.html
from mx.DateTime import DateTime
# http://www.pfdubois.com/numpy/
import Numeric, MA


# SOOM modules
from SOOMv0.Sources.Columns import *
from SOOMv0 import *


# Project modules
import urlfetch

icd9cm_fmt_file = 'icd9cm_fmt.pkl'

# http://www.cdc.gov/nchs/about/major/hdasd/nhds.htm
nhds_data = {
    'nhds96': 'ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHDS/nhds96/nhds96.zip',
    'nhds97': 'ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHDS/nhds97/nhds97.zip',
    'nhds98': 'ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHDS/nhds98/nhds98.zip',
    'nhds99': 'ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHDS/nhds99/nhds99.zip',
    'nhds00': 'ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHDS/nhds00/nhds00.zip',
    'nhds01': 'ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHDS/nhds01/nhds01.zip',
    'nhds02': 'ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHDS/nhds02/NHDS02PU.zip',
}


def fetch(scratchdir, dataset):
    """
    Caching URL fetcher, returns filename of cached file.
    """
    url = nhds_data[dataset]
    filename = os.path.join(scratchdir, os.path.basename(url))
    print "Fetching dataset %r from %s" % (dataset, url)
    urlfetch.fetch(url, filename)
    return filename

diag_cols = 'diagnosis1', 'diagnosis2', 'diagnosis3', 'diagnosis4', \
            'diagnosis5', 'diagnosis6', 'diagnosis7'
proc_cols = 'procedure1', 'procedure2', 'procedure3', 'procedure4'

day_cnt = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def reformat_icd9cm_diag_codes(data):
    if data and len(data) == 5:
        if data[3] == "-":
            return data[0:3]
        elif data[4] == "-":
            if data[0] == "E":
                return data[0:4]
            else:
                return ".".join((data[0:3],data[3]))
        else:
            if data[0] == "E":
                return ".".join((data[0:4],data[4]))        
            else:           
                # return data[0:3] + "." + data[3:5]      
                return ".".join((data[0:3],data[3]))      
    else:
        return data

def reformat_icd9cm_proc_codes(data):
    if data and len(data) == 4:
        if data[2] == "-":
            return data[0:2]
        elif data[3] == "-":
            return ".".join((data[0:2],data[2]))
        else:
            return ".".join((data[0:2],data[2:4]))      
    else:
        return data

def nhds_xform_pre(row_dict):
    diags = []
    for col in diag_cols:
        diag = reformat_icd9cm_diag_codes(row_dict[col])
        row_dict[col] = diag
        if diag:
            diags.append(diag)
    row_dict['diagnosis_all'] = tuple(diags)
    procs = []
    for col in proc_cols:
        proc = reformat_icd9cm_proc_codes(row_dict[col])
        row_dict[col] = proc
        if proc:
            procs.append(proc)
    row_dict['procedure_all'] = tuple(procs)
    return row_dict

def nhds_xform_post(row_dict):
    yr = int(row_dict['year'])
    if yr < 10:
        yr += 2000
    else:
        yr += 1900
    row_dict['year'] = yr
    month = random.randint(1,12)
    if month != 4:
        day = random.randint(1, day_cnt[month])
        row_dict['randomdate'] = DateTime(yr, month, day)
    return row_dict


def random_missing():
    n = random.random()
    if n >= 0.7 and n < 0.8:
        return 999.0
    else:
        return n


def nhds96_source(options):
    nhds96_columns = (
        DataSourceColumn("year",label="Survey Year",startpos=1,length=2,posbase=1),
        DataSourceColumn("newborn_status",label="Newborn status",startpos=3,length=1,posbase=1),
        DataSourceColumn("age_units",label="Age Units",startpos=4,length=1,posbase=1),
        DataSourceColumn("raw_age",label="Raw age",startpos=5,length=2,posbase=1),
        DataSourceColumn("sex",label="Sex",startpos=7,length=1,posbase=1),
        DataSourceColumn("race1",label="Race",startpos=8,length=1,posbase=1),
        DataSourceColumn("marital_status",label="Marital Status",startpos=9,length=1,posbase=1),
        DataSourceColumn("month_of_admission",label="Month of Admission",startpos=10,length=2,posbase=1),
        DataSourceColumn("discharge_status",label="Discharge Status",startpos=12,length=1,posbase=1),
        DataSourceColumn("days_of_care",label="Days of Care",startpos=13,length=4,posbase=1),
        DataSourceColumn("los_flag",label="Length of Stay Flag",startpos=17,length=1,posbase=1),
        DataSourceColumn("geog_region",label="Geographic Region",startpos=18,length=1,posbase=1),
        DataSourceColumn("num_beds",label="Number of Beds",startpos=19,length=1,posbase=1),
        DataSourceColumn("hosp_ownership",label="Hospital Ownership",startpos=20,length=1,posbase=1),
        DataSourceColumn("analysis_wgt",label="Analysis Weight",startpos=21,length=5,posbase=1),
        DataSourceColumn("prin_src_payment1",label="Principal Expected Source of Payment",startpos=26,length=1,posbase=1),
        DataSourceColumn("sec_src_payment1",label="Secondary Expected Source of Payment",startpos=27,length=1,posbase=1),
        DataSourceColumn("diagnosis1",label="Diagnosis Code 1",startpos=28,length=5,posbase=1),
        DataSourceColumn("diagnosis2",label="Diagnosis Code 2",startpos=33,length=5,posbase=1),
        DataSourceColumn("diagnosis3",label="Diagnosis Code 3",startpos=38,length=5,posbase=1),
        DataSourceColumn("diagnosis4",label="Diagnosis Code 4",startpos=43,length=5,posbase=1),
        DataSourceColumn("diagnosis5",label="Diagnosis Code 5",startpos=48,length=5,posbase=1),
        DataSourceColumn("diagnosis6",label="Diagnosis Code 6",startpos=53,length=5,posbase=1),
        DataSourceColumn("diagnosis7",label="Diagnosis Code 7",startpos=58,length=5,posbase=1),
        DataSourceColumn("procedure1",label="Procedure Code 1",startpos=63,length=4,posbase=1),
        DataSourceColumn("procedure2",label="Procedure Code 2",startpos=67,length=4,posbase=1),
        DataSourceColumn("procedure3",label="Procedure Code 3",startpos=71,length=4,posbase=1),
        DataSourceColumn("procedure4",label="Procedure Code 4",startpos=75,length=4,posbase=1),
        DataSourceColumn("drg",label="DRG V13.0",startpos=79,length=3,posbase=1)
    )
    return ColumnDataSource("nhds96", nhds96_columns, filename=fetch(options.scratchdir, "nhds96"), header_rows=0, label="National Hospital Discharge Survey 1996", xformpre=nhds_xform_pre, xformpost=nhds_xform_post)


def nhds97_source(options):
    nhds97_columns = (
        DataSourceColumn("year",label="Survey Year",startpos=1,length=2,posbase=1),
        DataSourceColumn("newborn_status",label="Newborn status",startpos=3,length=1,posbase=1),
        DataSourceColumn("age_units",label="Age Units",startpos=4,length=1,posbase=1),
        DataSourceColumn("raw_age",label="Raw age",startpos=5,length=2,posbase=1),
        DataSourceColumn("sex",label="Sex",startpos=7,length=1,posbase=1),
        DataSourceColumn("race1",label="Race",startpos=8,length=1,posbase=1),
        DataSourceColumn("marital_status",label="Marital Status",startpos=9,length=1,posbase=1),
        DataSourceColumn("month_of_admission",label="Month of Admission",startpos=10,length=2,posbase=1),
        DataSourceColumn("discharge_status",label="Discharge Status",startpos=12,length=1,posbase=1),
        DataSourceColumn("days_of_care",label="Days of Care",startpos=13,length=4,posbase=1),
        DataSourceColumn("los_flag",label="Length of Stay Flag",startpos=17,length=1,posbase=1),
        DataSourceColumn("geog_region",label="Geographic Region",startpos=18,length=1,posbase=1),
        DataSourceColumn("num_beds",label="Number of Beds",startpos=19,length=1,posbase=1),
        DataSourceColumn("hosp_ownership",label="Hospital Ownership",startpos=20,length=1,posbase=1),
        DataSourceColumn("analysis_wgt",label="Analysis Weight",startpos=21,length=5,posbase=1),
        DataSourceColumn("prin_src_payment1",label="Principal Expected Source of Payment",startpos=26,length=1,posbase=1),
        DataSourceColumn("sec_src_payment1",label="Secondary Expected Source of Payment",startpos=27,length=1,posbase=1),
        DataSourceColumn("diagnosis1",label="Diagnosis Code 1",startpos=28,length=5,posbase=1),
        DataSourceColumn("diagnosis2",label="Diagnosis Code 2",startpos=33,length=5,posbase=1),
        DataSourceColumn("diagnosis3",label="Diagnosis Code 3",startpos=38,length=5,posbase=1),
        DataSourceColumn("diagnosis4",label="Diagnosis Code 4",startpos=43,length=5,posbase=1),
        DataSourceColumn("diagnosis5",label="Diagnosis Code 5",startpos=48,length=5,posbase=1),
        DataSourceColumn("diagnosis6",label="Diagnosis Code 6",startpos=53,length=5,posbase=1),
        DataSourceColumn("diagnosis7",label="Diagnosis Code 7",startpos=58,length=5,posbase=1),
        DataSourceColumn("procedure1",label="Procedure Code 1",startpos=63,length=4,posbase=1),
        DataSourceColumn("procedure2",label="Procedure Code 2",startpos=67,length=4,posbase=1),
        DataSourceColumn("procedure3",label="Procedure Code 3",startpos=71,length=4,posbase=1),
        DataSourceColumn("procedure4",label="Procedure Code 4",startpos=75,length=4,posbase=1),
        DataSourceColumn("drg",label="DRG V14.0",startpos=79,length=3,posbase=1)
    )
    return ColumnDataSource("nhds97", nhds97_columns, filename=fetch(options.scratchdir, "nhds97"), header_rows=0,label="National Hospital Discharge Survey 1997", xformpre=nhds_xform_pre, xformpost=nhds_xform_post)


def nhds98_source(options):
    nhds98_columns = (
        DataSourceColumn("year",label="Survey Year",startpos=1,length=2,posbase=1),
        DataSourceColumn("newborn_status",label="Newborn status",startpos=3,length=1,posbase=1),
        DataSourceColumn("age_units",label="Age Units",startpos=4,length=1,posbase=1),
        DataSourceColumn("raw_age",label="Raw age",startpos=5,length=2,posbase=1),
        DataSourceColumn("sex",label="Sex",startpos=7,length=1,posbase=1),
        DataSourceColumn("race1",label="Race",startpos=8,length=1,posbase=1),
        DataSourceColumn("marital_status",label="Marital Status",startpos=9,length=1,posbase=1),
        DataSourceColumn("month_of_admission",label="Month of Admission",startpos=10,length=2,posbase=1),
        DataSourceColumn("discharge_status",label="Discharge Status",startpos=12,length=1,posbase=1),
        DataSourceColumn("days_of_care",label="Days of Care",startpos=13,length=4,posbase=1),
        DataSourceColumn("los_flag",label="Length of Stay Flag",startpos=17,length=1,posbase=1),
        DataSourceColumn("geog_region",label="Geographic Region",startpos=18,length=1,posbase=1),
        DataSourceColumn("num_beds",label="Number of Beds",startpos=19,length=1,posbase=1),
        DataSourceColumn("hosp_ownership",label="Hospital Ownership",startpos=20,length=1,posbase=1),
        DataSourceColumn("analysis_wgt",label="Analysis Weight",startpos=21,length=5,posbase=1),
        DataSourceColumn("diagnosis1",label="Diagnosis Code 1",startpos=28,length=5,posbase=1),
        DataSourceColumn("diagnosis2",label="Diagnosis Code 2",startpos=33,length=5,posbase=1),
        DataSourceColumn("diagnosis3",label="Diagnosis Code 3",startpos=38,length=5,posbase=1),
        DataSourceColumn("diagnosis4",label="Diagnosis Code 4",startpos=43,length=5,posbase=1),
        DataSourceColumn("diagnosis5",label="Diagnosis Code 5",startpos=48,length=5,posbase=1),
        DataSourceColumn("diagnosis6",label="Diagnosis Code 6",startpos=53,length=5,posbase=1),
        DataSourceColumn("diagnosis7",label="Diagnosis Code 7",startpos=58,length=5,posbase=1),
        DataSourceColumn("procedure1",label="Procedure Code 1",startpos=63,length=4,posbase=1),
        DataSourceColumn("procedure2",label="Procedure Code 2",startpos=67,length=4,posbase=1),
        DataSourceColumn("procedure3",label="Procedure Code 3",startpos=71,length=4,posbase=1),
        DataSourceColumn("procedure4",label="Procedure Code 4",startpos=75,length=4,posbase=1),
        DataSourceColumn("prin_src_payment2",label="Principal Expected Source of Payment",startpos=79,length=2,posbase=1),
        DataSourceColumn("sec_src_payment2",label="Secondary Expected Source of Payment",startpos=81,length=2,posbase=1),
        DataSourceColumn("drg",label="DRG V15.0",startpos=83,length=3,posbase=1)
    )
    return ColumnDataSource("nhds98", nhds98_columns, filename=fetch(options.scratchdir, "nhds98"), header_rows=0,label="National Hospital Discharge Survey 1998", xformpre=nhds_xform_pre, xformpost=nhds_xform_post)


def nhds99_source(options):
    nhds99_columns = (
        DataSourceColumn("year",label="Survey Year",startpos=1,length=2,posbase=1),
        DataSourceColumn("newborn_status",label="Newborn status",startpos=3,length=1,posbase=1),
        DataSourceColumn("age_units",label="Age Units",startpos=4,length=1,posbase=1),
        DataSourceColumn("raw_age",label="Raw age",startpos=5,length=2,posbase=1),
        DataSourceColumn("sex",label="Sex",startpos=7,length=1,posbase=1),
        DataSourceColumn("race1",label="Race",startpos=8,length=1,posbase=1),
        DataSourceColumn("marital_status",label="Marital Status",startpos=9,length=1,posbase=1),
        DataSourceColumn("month_of_admission",label="Month of Admission",startpos=10,length=2,posbase=1),
        DataSourceColumn("discharge_status",label="Discharge Status",startpos=12,length=1,posbase=1),
        DataSourceColumn("days_of_care",label="Days of Care",startpos=13,length=4,posbase=1),
        DataSourceColumn("los_flag",label="Length of Stay Flag",startpos=17,length=1,posbase=1),
        DataSourceColumn("geog_region",label="Geographic Region",startpos=18,length=1,posbase=1),
        DataSourceColumn("num_beds",label="Number of Beds",startpos=19,length=1,posbase=1),
        DataSourceColumn("hosp_ownership",label="Hospital Ownership",startpos=20,length=1,posbase=1),
        DataSourceColumn("analysis_wgt",label="Analysis Weight",startpos=21,length=5,posbase=1),
        DataSourceColumn("diagnosis1",label="Diagnosis Code 1",startpos=28,length=5,posbase=1),
        DataSourceColumn("diagnosis2",label="Diagnosis Code 2",startpos=33,length=5,posbase=1),
        DataSourceColumn("diagnosis3",label="Diagnosis Code 3",startpos=38,length=5,posbase=1),
        DataSourceColumn("diagnosis4",label="Diagnosis Code 4",startpos=43,length=5,posbase=1),
        DataSourceColumn("diagnosis5",label="Diagnosis Code 5",startpos=48,length=5,posbase=1),
        DataSourceColumn("diagnosis6",label="Diagnosis Code 6",startpos=53,length=5,posbase=1),
        DataSourceColumn("diagnosis7",label="Diagnosis Code 7",startpos=58,length=5,posbase=1),
        DataSourceColumn("procedure1",label="Procedure Code 1",startpos=63,length=4,posbase=1),
        DataSourceColumn("procedure2",label="Procedure Code 2",startpos=67,length=4,posbase=1),
        DataSourceColumn("procedure3",label="Procedure Code 3",startpos=71,length=4,posbase=1),
        DataSourceColumn("procedure4",label="Procedure Code 4",startpos=75,length=4,posbase=1),
        DataSourceColumn("prin_src_payment2",label="Principal Expected Source of Payment",startpos=79,length=2,posbase=1),
        DataSourceColumn("sec_src_payment2",label="Secondary Expected Source of Payment",startpos=81,length=2,posbase=1),
        DataSourceColumn("drg",label="DRG V16.0",startpos=83,length=3,posbase=1)
    )
    return ColumnDataSource("nhds99", nhds99_columns, filename=fetch(options.scratchdir, "nhds99"), header_rows=0,label="National Hospital Discharge Survey 1999", xformpre=nhds_xform_pre, xformpost=nhds_xform_post)


def nhds00_source(options):
    nhds00_columns = (
        DataSourceColumn("year",label="Survey Year",startpos=1,length=2,posbase=1),
        DataSourceColumn("newborn_status",label="Newborn status",startpos=3,length=1,posbase=1),
        DataSourceColumn("age_units",label="Age Units",startpos=4,length=1,posbase=1),
        DataSourceColumn("raw_age",label="Raw age",startpos=5,length=2,posbase=1),
        DataSourceColumn("sex",label="Sex",startpos=7,length=1,posbase=1),
        DataSourceColumn("race2",label="Race",startpos=8,length=1,posbase=1),
        DataSourceColumn("marital_status",label="Marital Status",startpos=9,length=1,posbase=1),
        DataSourceColumn("month_of_admission",label="Month of Admission",startpos=10,length=2,posbase=1),
        DataSourceColumn("discharge_status",label="Discharge Status",startpos=12,length=1,posbase=1),
        DataSourceColumn("days_of_care",label="Days of Care",startpos=13,length=4,posbase=1),
        DataSourceColumn("los_flag",label="Length of Stay Flag",startpos=17,length=1,posbase=1),
        DataSourceColumn("geog_region",label="Geographic Region",startpos=18,length=1,posbase=1),
        DataSourceColumn("num_beds",label="Number of Beds",startpos=19,length=1,posbase=1),
        DataSourceColumn("hosp_ownership",label="Hospital Ownership",startpos=20,length=1,posbase=1),
        DataSourceColumn("analysis_wgt",label="Analysis Weight",startpos=21,length=5,posbase=1),
        DataSourceColumn("diagnosis1",label="Diagnosis Code 1",startpos=28,length=5,posbase=1),
        DataSourceColumn("diagnosis2",label="Diagnosis Code 2",startpos=33,length=5,posbase=1),
        DataSourceColumn("diagnosis3",label="Diagnosis Code 3",startpos=38,length=5,posbase=1),
        DataSourceColumn("diagnosis4",label="Diagnosis Code 4",startpos=43,length=5,posbase=1),
        DataSourceColumn("diagnosis5",label="Diagnosis Code 5",startpos=48,length=5,posbase=1),
        DataSourceColumn("diagnosis6",label="Diagnosis Code 6",startpos=53,length=5,posbase=1),
        DataSourceColumn("diagnosis7",label="Diagnosis Code 7",startpos=58,length=5,posbase=1),
        DataSourceColumn("procedure1",label="Procedure Code 1",startpos=63,length=4,posbase=1),
        DataSourceColumn("procedure2",label="Procedure Code 2",startpos=67,length=4,posbase=1),
        DataSourceColumn("procedure3",label="Procedure Code 3",startpos=71,length=4,posbase=1),
        DataSourceColumn("procedure4",label="Procedure Code 4",startpos=75,length=4,posbase=1),
        DataSourceColumn("prin_src_payment2",label="Principal Expected Source of Payment",startpos=79,length=2,posbase=1),
        DataSourceColumn("sec_src_payment2",label="Secondary Expected Source of Payment",startpos=81,length=2,posbase=1),
        DataSourceColumn("drg",label="DRG V16.0",startpos=83,length=3,posbase=1)
    )
    return ColumnDataSource("nhds00", nhds00_columns, filename=fetch(options.scratchdir, "nhds00"), header_rows=0,label="National Hospital Discharge Survey 2000", xformpre=nhds_xform_pre, xformpost=nhds_xform_post)


def nhds01_source(options):
    nhds01_columns = (
        DataSourceColumn("year",label="Survey Year",startpos=1,length=2,posbase=1),
        DataSourceColumn("newborn_status",label="Newborn status",startpos=3,length=1,posbase=1),
        DataSourceColumn("age_units",label="Age Units",startpos=4,length=1,posbase=1),
        DataSourceColumn("raw_age",label="Raw age",startpos=5,length=2,posbase=1),
        DataSourceColumn("sex",label="Sex",startpos=7,length=1,posbase=1),
        DataSourceColumn("race2",label="Race",startpos=8,length=1,posbase=1),
        DataSourceColumn("marital_status",label="Marital Status",startpos=9,length=1,posbase=1),
        DataSourceColumn("month_of_admission",label="Month of Admission",startpos=10,length=2,posbase=1),
        DataSourceColumn("discharge_status",label="Discharge Status",startpos=12,length=1,posbase=1),
        DataSourceColumn("days_of_care",label="Days of Care",startpos=13,length=4,posbase=1),
        DataSourceColumn("los_flag",label="Length of Stay Flag",startpos=17,length=1,posbase=1),
        DataSourceColumn("geog_region",label="Geographic Region",startpos=18,length=1,posbase=1),
        DataSourceColumn("num_beds",label="Number of Beds",startpos=19,length=1,posbase=1),
        DataSourceColumn("hosp_ownership",label="Hospital Ownership",startpos=20,length=1,posbase=1),
        DataSourceColumn("analysis_wgt",label="Analysis Weight",startpos=21,length=5,posbase=1),
        DataSourceColumn("diagnosis1",label="Diagnosis Code 1",startpos=28,length=5,posbase=1),
        DataSourceColumn("diagnosis2",label="Diagnosis Code 2",startpos=33,length=5,posbase=1),
        DataSourceColumn("diagnosis3",label="Diagnosis Code 3",startpos=38,length=5,posbase=1),
        DataSourceColumn("diagnosis4",label="Diagnosis Code 4",startpos=43,length=5,posbase=1),
        DataSourceColumn("diagnosis5",label="Diagnosis Code 5",startpos=48,length=5,posbase=1),
        DataSourceColumn("diagnosis6",label="Diagnosis Code 6",startpos=53,length=5,posbase=1),
        DataSourceColumn("diagnosis7",label="Diagnosis Code 7",startpos=58,length=5,posbase=1),
        DataSourceColumn("procedure1",label="Procedure Code 1",startpos=63,length=4,posbase=1),
        DataSourceColumn("procedure2",label="Procedure Code 2",startpos=67,length=4,posbase=1),
        DataSourceColumn("procedure3",label="Procedure Code 3",startpos=71,length=4,posbase=1),
        DataSourceColumn("procedure4",label="Procedure Code 4",startpos=75,length=4,posbase=1),
        DataSourceColumn("prin_src_payment2",label="Principal Expected Source of Payment",startpos=79,length=2,posbase=1),
        DataSourceColumn("sec_src_payment2",label="Secondary Expected Source of Payment",startpos=81,length=2,posbase=1),
        DataSourceColumn("drg",label="DRG V16.0",startpos=83,length=3,posbase=1),
        DataSourceColumn("admission_type",label="Type of admission",startpos=86,length=1,posbase=1),
        DataSourceColumn("admission_source",label="Source of admission",startpos=87,length=2,posbase=1)
    )
    return ColumnDataSource("nhds01", nhds01_columns, filename=fetch(options.scratchdir, "nhds01"), header_rows=0,label="National Hospital Discharge Survey 2001", xformpre=nhds_xform_pre, xformpost=nhds_xform_post)


def nhds02_source(options):
    nhds02_columns = (
        DataSourceColumn("year",label="Survey Year",startpos=1,length=2,posbase=1),
        DataSourceColumn("newborn_status",label="Newborn status",startpos=3,length=1,posbase=1),
        DataSourceColumn("age_units",label="Age Units",startpos=4,length=1,posbase=1),
        DataSourceColumn("raw_age",label="Raw age",startpos=5,length=2,posbase=1),
        DataSourceColumn("sex",label="Sex",startpos=7,length=1,posbase=1),
        DataSourceColumn("race2",label="Race",startpos=8,length=1,posbase=1),
        DataSourceColumn("marital_status",label="Marital Status",startpos=9,length=1,posbase=1),
        DataSourceColumn("month_of_admission",label="Month of Admission",startpos=10,length=2,posbase=1),
        DataSourceColumn("discharge_status",label="Discharge Status",startpos=12,length=1,posbase=1),
        DataSourceColumn("days_of_care",label="Days of Care",startpos=13,length=4,posbase=1),
        DataSourceColumn("los_flag",label="Length of Stay Flag",startpos=17,length=1,posbase=1),
        DataSourceColumn("geog_region",label="Geographic Region",startpos=18,length=1,posbase=1),
        DataSourceColumn("num_beds",label="Number of Beds",startpos=19,length=1,posbase=1),
        DataSourceColumn("hosp_ownership",label="Hospital Ownership",startpos=20,length=1,posbase=1),
        DataSourceColumn("analysis_wgt",label="Analysis Weight",startpos=21,length=5,posbase=1),
        DataSourceColumn("diagnosis1",label="Diagnosis Code 1",startpos=28,length=5,posbase=1),
        DataSourceColumn("diagnosis2",label="Diagnosis Code 2",startpos=33,length=5,posbase=1),
        DataSourceColumn("diagnosis3",label="Diagnosis Code 3",startpos=38,length=5,posbase=1),
        DataSourceColumn("diagnosis4",label="Diagnosis Code 4",startpos=43,length=5,posbase=1),
        DataSourceColumn("diagnosis5",label="Diagnosis Code 5",startpos=48,length=5,posbase=1),
        DataSourceColumn("diagnosis6",label="Diagnosis Code 6",startpos=53,length=5,posbase=1),
        DataSourceColumn("diagnosis7",label="Diagnosis Code 7",startpos=58,length=5,posbase=1),
        DataSourceColumn("procedure1",label="Procedure Code 1",startpos=63,length=4,posbase=1),
        DataSourceColumn("procedure2",label="Procedure Code 2",startpos=67,length=4,posbase=1),
        DataSourceColumn("procedure3",label="Procedure Code 3",startpos=71,length=4,posbase=1),
        DataSourceColumn("procedure4",label="Procedure Code 4",startpos=75,length=4,posbase=1),
        DataSourceColumn("prin_src_payment2",label="Principal Expected Source of Payment",startpos=79,length=2,posbase=1),
        DataSourceColumn("sec_src_payment2",label="Secondary Expected Source of Payment",startpos=81,length=2,posbase=1),
        DataSourceColumn("drg",label="DRG V16.0",startpos=83,length=3,posbase=1),
        DataSourceColumn("admission_type",label="Type of admission",startpos=86,length=1,posbase=1),
        DataSourceColumn("admission_source",label="Source of admission",startpos=87,length=2,posbase=1)
    )
    return ColumnDataSource("nhds02", nhds02_columns, filename=fetch(options.scratchdir, "nhds02"), header_rows=0,label="National Hospital Discharge Survey 2002", xformpre=nhds_xform_pre, xformpost=nhds_xform_post)


def get_icd9cm_fmt(datadir):
    fmt_file = os.path.join(datadir, icd9cm_fmt_file)
    if not os.path.exists(fmt_file):
        # We run the rtf parsing in a separate process as it appears the
        # regexp module is leaking serious amounts of memory.
        pid = os.fork()
        if pid:
            pid, status = os.waitpid(pid, 0)
            if status:
                sys.exit(1)
        else:
            import make_icd9cm_fmt 
            icd9cm_fmt = make_icd9cm_fmt.make_icd9cm_fmt(datadir, verbose=1)
            f = open(fmt_file, 'wb')
            try:
                cPickle.dump(icd9cm_fmt, f, -1)
            finally:
                f.close()
            os._exit(0)
    f = open(fmt_file, 'rb')
    try:
        return cPickle.load(f)
    finally:
        f.close()

def make_dataset(options):
    icd9cm_fmt = get_icd9cm_fmt(options.scratchdir)
    nhds = makedataset("nhds",
                    label="National Hospital Discharge Surveys 1996-2002",
                    weightcol='analysis_wgt')

    nhds.addcolumn("year",label="Survey Year",datatype=int,coltype="ordinal",all_value=0,all_label="All years")
    nhds.addcolumn("newborn_status",label="Newborn status",outtrans={1:"Newborn",2:"Not newborn"},datatype=int,coltype="categorical")
    nhds.addcolumn("age_units",label="Age Units",datatype=int,coltype="categorical",outtrans={1:"Years",2:"Months",3:"Days"})
    nhds.addcolumn("raw_age",label="Raw age (years, months or days)",datatype=int,coltype="scalar")
    nhds.addcolumn("sex",label="Sex",outtrans={1:"Male",2:"Female"},datatype=int,coltype="categorical",all_value=0,all_label="Persons")
    nhds.addcolumn("race1",label="Race (1996-99)",outtrans={1:"White",2:"Black",3:"American Indian/Eskimo",4:"Asian/Pacific Islander",5:"Other",9:"Not stated"},datatype=int,coltype="categorical",all_value=0,all_label="All races")
    nhds.addcolumn("race2",label="Race (2000-02)",outtrans={1:"White",2:"Black",3:"American Indian/Eskimo",4:"Asian",5:"Native Hawaiian or other Pacific Islander",6:"Other",8:"Multiple race indicated",9:"Not stated"},datatype=int,coltype="categorical",all_value=0,all_label="All races")
    nhds.addcolumn("marital_status",label="Marital Status",outtrans={1:"Married",2:"Single",3:"Widowed",4:"Divorced",5:"Separated",9:"Not stated"},datatype=int,coltype="categorical",all_value=0,all_label="All marital states")
    nhds.addcolumn("month_of_admission",label="Month of Admission/Discharge",outtrans={'01':'January','02':'February','03':'March','04':'April','05':'May','06':'June','07':'July','08':'August','09':'September','10':'October','11':'November','12':'December','99':'Missing'},datatype=str,coltype="ordinal",all_value='00',all_label="All months")
    nhds.addcolumn("discharge_status",label="Discharge Status",outtrans={1:'Routine/discharged home',2:'Left against medical advice',3:'Discharged/transferred to short-term facility',4:'Discharged/transferred to long-term care institution',5:'Alive, disposition not stated',6:'Dead',9:'Not stated or not reported'},all_label="All dispositions",all_value=0,datatype=int,coltype="categorical")
    nhds.addcolumn("days_of_care",label="Days of Care",datatype=int,coltype="scalar")
    nhds.addcolumn("los_flag",label="Length of Stay Flag",outtrans={0:'Less than 1 day',1:'One day or more'},datatype=int,coltype="categorical")
    nhds.addcolumn("geog_region",label="Geographic Region",outtrans={0:'United States',1:'Northeast',2:'Midwest',3:'South',4:'West'},datatype=int,coltype="categorical",all_value=0,all_label="All regions")
    nhds.addcolumn("num_beds",label="Number of Beds",outtrans={1:'6-99',2:'100-199',3:'200-299',4:'300-499',5:'500 and over'},datatype=int,coltype="categorical",all_value=0,all_label="All sizes")
    nhds.addcolumn("hosp_ownership",label="Hospital Ownership",outtrans={1:'Proprietary',2:'Government',3:'Nonprofit, including church'},datatype=int,coltype="categorical",all_value=0,all_label="All types")
    nhds.addcolumn("analysis_wgt",label="Analysis Weight",datatype=int,coltype="weighting")
    nhds.addcolumn("prin_src_payment1",label="Principal Expected Source of Payment (1996-97)",outtrans={1:"Worker's compensation",2:'Medicare',3:'Medicaid',4:'Other government payments',5:'Blue Cross',6:'Other private/commercial insurance',7:'Self-pay',8:'Other',9:'Not stated',0:'No charge'},datatype=int,coltype="categorical")
    nhds.addcolumn("sec_src_payment1",label="Secondary Expected Source of Payment (1996-97)",outtrans={1:"Worker's compensation",2:'Medicare',3:'Medicaid',4:'Other government payments',5:'Blue Cross',6:'Other private/commercial insurance',7:'Self-pay',8:'Other',9:'Not stated',0:'No charge'},datatype=int,coltype="categorical")
    nhds.addcolumn("prin_src_payment2",label="Principal Expected Source of Payment (1998-2002)",outtrans={'01':"Worker's compensation",'02':'Medicare','03':'Medicaid','04':'Other government','05':'Blue Cross/Blue Shield','06':'HMO/PPO','07':'Other private','08':'Self-pay','09':'No charge','10':'Other','99':'Not stated'},datatype='recode',coltype="categorical")
    nhds.addcolumn("sec_src_payment2",label="Secondary Expected Source of Payment (1998-2002)",outtrans={'01':"Worker's compensation",'02':'Medicare','03':'Medicaid','04':'Other government','05':'Blue Cross/Blue Shield','06':'HMO/PPO','07':'Other private','08':'Self-pay','09':'No charge','10':'Other','99':'Not stated'},datatype='recode',coltype="categorical")
    nhds.addcolumn("diagnosis1",label="Diagnosis Code 1",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("diagnosis2",label="Diagnosis Code 2",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("diagnosis3",label="Diagnosis Code 3",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("diagnosis4",label="Diagnosis Code 4",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("diagnosis5",label="Diagnosis Code 5",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("diagnosis6",label="Diagnosis Code 6",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("diagnosis7",label="Diagnosis Code 7",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("procedure1",label="Procedure Code 1",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("procedure2",label="Procedure Code 2",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("procedure3",label="Procedure Code 3",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("procedure4",label="Procedure Code 4",datatype='recode',coltype="ordinal",outtrans=icd9cm_fmt)
    nhds.addcolumn("drg",label="DRG V13.0-V18.0",datatype=int,coltype="categorical")
    nhds.addcolumn("diagnosis_all",label="Diagnosis codes 1-7",datatype="tuple",coltype="ordinal",outtrans=icd9cm_fmt)
#    nhds.addcolumn("diagnosis_all",label="Diagnosis codes 1-7",datatype="tuple",coltype="ordinal",multisourcecols=["diagnosis1","diagnosis2","diagnosis3","diagnosis4","diagnosis5","diagnosis6","diagnosis7"],ignorenone=1,outtrans=icd9cm_fmt)
    nhds.addcolumn("procedure_all",label="Procedure codes 1-4",datatype="tuple",coltype="ordinal",outtrans=icd9cm_fmt)
#    nhds.addcolumn("procedure_all",label="Procedure codes 1-4",datatype="tuple",coltype="ordinal",multisourcecols=["procedure1","procedure2","procedure3","procedure4"],ignorenone=1,outtrans=icd9cm_fmt)
    nhds.addcolumn("randomvalue",label="Random values",datatype=float,coltype="scalar",calculatedby=random_missing,missingvalues={999.0:None})
    nhds.addcolumn("randomdate",label="Random date",datatype="recodedate",coltype="date")
    nhds.addcolumn("admission_type",label="Type of admission (2001-02)",outtrans={1:"Emergency",2:'Urgent',3:'Elective',4:'Newborn',9:'Not available'},datatype=int,coltype="categorical")
    nhds.addcolumn("admission_source",label="Source of admission (2001-02)",outtrans={1:"Physician referral",2:'Clinical referral',3:'HMO referral',4:'Transfer from a hospital',5:'Transfer from a skilled nursing facility',6:'Transfer from other health facility',7:'Emergency room',8:'Court/law enforcement',9:'Other',99:'Not available'},datatype=int,coltype="categorical")
    if options.verbose:
        print nhds
    return nhds

def get_source(year, options):
    return globals()['nhds%02d_source' % (int(year) % 100)](options)

def all_sources(options):
    year = 1996
    while 1:
        try:
            yield get_source(year, options)
        except LookupError:
            break
        year += 1


def load_sources(nhds, options):
    """
    Load NHDS from sources (defined in nhds_source module)
    """
    nhds.initialise()
    for x in range(options.nhds_iterations):
        if options.nhds_years is None:
            sources = all_sources(options)
        else:
            years = options.nhds_years.split(',')
            sources = [get_source(year, options) for year in years]
        for source in sources:
            if options.verbose:
                print source
            nhds.loaddata(source,
                          rowlimit=options.rowlimit,
                          chunkrows=options.chunkrows)
    nhds.finalise()
    for col in nhds.get_columns():
        if getattr(col, 'calculatedby', None):
            col.calculatedby = None


def derived_cols(nhds):
    """
    Add some derived columns to the NHDS dataset.
    """

    # There should be no missing values for age in the NHDS data,
    # so don't bother checking - but this could be done and the mask
    # value set appropriately if required
    def age_years(raw_age,age_units):
            units_divisor = Numeric.choose(age_units - 1, (1.0, 12.0, 365.25))
            returnarray =  raw_age / units_divisor
            return returnarray
    print "Adding age column..."
    nhds.derivedcolumn(dername="age",dercols=("raw_age","age_units"),derfunc=age_years,coltype="scalar",datatype=float,outtrans=None,label="Age (years)")

    def age_months(raw_age,age_units):
            units_multiplier = Numeric.choose(age_units - 1, (12.0, 1.0, (1/30.5)))
            returnarray =  raw_age * units_multiplier
            return returnarray
    print "Adding age_months column..."
    nhds.derivedcolumn(dername="age_months",dercols=("raw_age","age_units"),derfunc=age_months,coltype="scalar",datatype=float,outtrans=None,label="Age (months)")

    def age_days(raw_age,age_units):
            units_multiplier = Numeric.choose(age_units - 1, (365.25, 30.5, 1.0))
            returnarray =  raw_age * units_multiplier
            return returnarray
    print "Adding age_days column..."
    nhds.derivedcolumn(dername="age_days",dercols=("raw_age","age_units"),derfunc=age_days,coltype="scalar",datatype=float,outtrans=None,label="Age (days)")

    # Add 5 year age groups
    def agegrp(age):
            agrp = MA.choose(MA.greater_equal(age,85),(age,-18.0))
            agrp = MA.choose(MA.greater_equal(agrp,80),(agrp,-17.0))
            agrp = MA.choose(MA.greater_equal(agrp,75),(agrp,-16.0))
            agrp = MA.choose(MA.greater_equal(agrp,70),(agrp,-15.0))
            agrp = MA.choose(MA.greater_equal(agrp,65),(agrp,-14.0))
            agrp = MA.choose(MA.greater_equal(agrp,60),(agrp,-13.0))
            agrp = MA.choose(MA.greater_equal(agrp,55),(agrp,-12.0))
            agrp = MA.choose(MA.greater_equal(agrp,50),(agrp,-11.0))
            agrp = MA.choose(MA.greater_equal(agrp,45),(agrp,-10.0))
            agrp = MA.choose(MA.greater_equal(agrp,40),(agrp,-9.0))
            agrp = MA.choose(MA.greater_equal(agrp,35),(agrp,-8.0))
            agrp = MA.choose(MA.greater_equal(agrp,30),(agrp,-7.0))
            agrp = MA.choose(MA.greater_equal(agrp,25),(agrp,-6.0))
            agrp = MA.choose(MA.greater_equal(agrp,20),(agrp,-5.0))
            agrp = MA.choose(MA.greater_equal(agrp,15),(agrp,-4.0))
            agrp = MA.choose(MA.greater_equal(agrp,10),(agrp,-3.0))
            agrp = MA.choose(MA.greater_equal(agrp,5),(agrp,-2.0))
            agrp = MA.choose(MA.greater_equal(agrp,0),(agrp,-1.0))
            returnarray = -agrp.astype(MA.Int)
            return returnarray

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

    nhds.derivedcolumn(dername="agegrp",dercols=("age",),derfunc=agegrp,coltype="ordinal",datatype=int,outtrans=agegrp_outtrans,label="Age Group",all_value=0,all_label="All ages")


def load(options):
    ds = make_dataset(options)
    load_sources(ds, options)
    derived_cols(ds)
    ds.save()
