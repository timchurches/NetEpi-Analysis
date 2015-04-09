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
# $Id: nhds_population.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/loaders/nhds_population.py,v $

# Python standard modules
import csv
import time
import os
import sys
import random
import optparse

# 3rd Party Modules
# http://www.egenix.com/files/python/eGenix-mx-Extensions.html
from mx.DateTime import DateTime
# http://www.pfdubois.com/numpy/
import Numeric, MA

# SOOM modules
from SOOMv0 import *

#########################################################################
# The following code loads some population datasets for the 1997 NHDS data.
# Unfortunately, these data files are only available in Lotus 123 spreadsheet
# format, so you need to open them in a spreadsheet package and save them as
# CSV files for the following code to work. With some more work we may be
# able to automatically download and convert these files - or we could ask
# NCHS to make CSV files available instead.
#########################################################################
# Now load some population datasets for 1997
csv_reader = csv.reader(file(os.path.join(rawdatapath, "appc_b97.csv")))
fo = open(os.path.join(rawdatapath, "popsgeog97.dat"), "w")

def agegrp_transform(text):
    text = text.strip()
    if text == 'All ages' or text == 'All Ages': return '0'
    elif text == '0-4':   return '1'
    elif text == '5-9':   return '2'
    elif text == '10-14': return '3'
    elif text == '15-19': return '4'
    elif text == '20-24': return '5'
    elif text == '25-29': return '6'
    elif text == '30-34': return '7'
    elif text == '35-39': return '8'
    elif text == '40-44': return '9'
    elif text == '45-49': return '10'
    elif text == '50-54': return '11'
    elif text == '55-59': return '12'
    elif text == '60-64': return '13'
    elif text == '65-69': return '14'
    elif text == '70-74': return '15'
    elif text == '75-79': return '16'
    elif text == '80-84': return '17'
    elif text == '85+':   return '18'
    else: return text   
    
def writeline(filehandle,sex,otherattrib,popindex):
    outline = agegrp_transform(cleanline[0])
    outline += ',' + str(sex)
    outline += ',' + str(otherattrib)
    outline += ',' + str(int(cleanline[popindex]) * 1000)
    outline += '\n'
    filehandle.write(outline)

for line_no, parsed_line in enumerate(csv_reader):
    if parsed_line is not None and line_no in [11] + range(13,31):
        cleanline = []
        for item in parsed_line:
            item = item.strip().replace(",","")
            try:
                cleanline.append(int(item))
            except:
                cleanline.append(item)
        writeline(fo,0,0,1)
        writeline(fo,1,0,2)
        writeline(fo,2,0,3)
                    
        writeline(fo,0,1,4)
        writeline(fo,1,1,5)
        writeline(fo,2,1,6)
        
        writeline(fo,0,2,7)
        writeline(fo,1,2,8)
        writeline(fo,2,2,9)

        writeline(fo,0,3,10)
        writeline(fo,1,3,11)
        writeline(fo,2,3,12)

        writeline(fo,0,4,13)
        writeline(fo,1,4,14)
        writeline(fo,2,4,15)

fo.close()

popsgeog97data_columns = (
        DataSourceColumn("agegrp",label="5 yr age group",coltype="ordinal",ordinalpos=0,posbase=0),
        DataSourceColumn("sex",label="Sex",coltype="categorical",ordinalpos=1,posbase=0),
        DataSourceColumn("geog_region",label="Geographical Region",coltype="categorical",ordinalpos=2,posbase=0),
        DataSourceColumn("pop",label="Population estimate",coltype="scalar",ordinalpos=3,posbase=0)
)
popsgeog97data = CSVDataSource("popsgeog97data", popsgeog97data_columns, filename=os.path.join(rawdatapath, "popsgeog97.dat"), header_rows=0, label="Transformed appc_b97.wk1")


popsgeog97 = makedataset("popsgeog97",label="Populations by 5 yr age group, sex and geographical region, 1997")

popsgeog97.addcolumn("sex",label="Sex",outtrans={0:"Persons",1:"Male",2:"Female"},datatype=int,coltype="categorical")
popsgeog97.addcolumn("geog_region",label="Geographic Region",outtrans={0:'United States',1:'Northeast',2:'Midwest',3:'South',4:'West'},datatype=int,coltype="categorical")
popsgeog97.addcolumn("pop",label="Population estimate",datatype=int,coltype="scalar")
agegrp_outtrans = { 0:"All ages",
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
popsgeog97.addcolumn("agegrp",label="Age group",coltype="ordinal",datatype=int,outtrans=agegrp_outtrans)
            
popsgeog97.initialise()
popsgeog97.loaddata(popsgeog97data,rowlimit=None)
popsgeog97.finalise()
popsgeog97.save()

###################################################
# Repeat for racial groups populations

csv_reader = csv.reader(file(os.path.join(rawdatapath, "appc_c97.csv")))
fo = open(os.path.join(rawdatapath, "popsrace97.dat"), "w")

for line_no, parsed_line in enumerate(csv_reader):
    if parsed_line is not None and line_no in [11,13,20,27,34,41,48,55,62,69,76,83,90,97,104,111,118,125,166]:
        cleanline = []
        for item in parsed_line:
            item = item.strip().replace(",","")
            try:
                cleanline.append(int(item))
            except:
                cleanline.append(item)
        print "line_no %s, parsed_line %s" % (line_no, parsed_line)
        writeline(fo,0,0,1)
        writeline(fo,1,0,2)
        writeline(fo,2,0,3)
                    
        writeline(fo,0,1,4)
        writeline(fo,1,1,5)
        writeline(fo,2,1,6)
        
        writeline(fo,0,2,7)
        writeline(fo,1,2,8)
        writeline(fo,2,2,9)

        writeline(fo,0,3,10)
        writeline(fo,1,3,11)
        writeline(fo,2,3,12)

fo.close()

popsrace97_columns = (
        DataSourceColumn("agegrp",label="5 yr age group",coltype="ordinal",ordinalpos=0,posbase=0),
        DataSourceColumn("sex",label="Sex",coltype="categorical",ordinalpos=1,posbase=0),
        DataSourceColumn("racialgroup",label="Racial group",coltype="categorical",ordinalpos=2,posbase=0),
        DataSourceColumn("pop",label="Population estimate",coltype="scalar",ordinalpos=3,posbase=0)
)
popsrace97data = CSVDataSource("popsrace97data", popsrace97_columns, filename=os.path.join(rawdatapath, "popsrace97.dat"),header_rows=0,label="Transformed appc_c97.wk1")

popsrace97 = makedataset("popsrace97",label="Populations by 5 yr age group, sex and grouped race, 1997")

popsrace97.addcolumn("sex",label="Sex",outtrans={0:"Persons",1:"Male",2:"Female"},datatype=int,coltype="categorical")
popsrace97.addcolumn("racialgroup",label="Racial group",outtrans={0:'All races',1:'White',2:'Black',3:'Others'},datatype=int,coltype="categorical")
popsrace97.addcolumn("pop",label="Population estimate",datatype=int,coltype="scalar")
popsrace97.addcolumn("agegrp",label="Age group",coltype="ordinal",datatype=int,outtrans=agegrp_outtrans)
            
popsrace97.initialise()
popsrace97.loaddata(popsrace97data,rowlimit=None)
popsrace97.finalise()
popsrace97.save()
