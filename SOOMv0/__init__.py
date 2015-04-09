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
# SOOMv0.py
# SOOM Proof-of-concept implementation Version 0
# Written by Tim Churches April-November 2001
# Substantially revised by Tim Churches and Ben Golding, April-May 2003
# Extensive further work by Tim Churches and Andrew McNamara, May 2003-...

# $Id: __init__.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/__init__.py,v $

# Module imports
#from MA import * # Masked Arrays, part of NumPy, used to support missing values
#from soomfunc import * # fast C version of Numpy array intersections etc
#from SOOMv0.Utils import *     # AM - don't really need this here?
from SOOMv0.Soom import soom
from SOOMv0.DataSourceColumn import DataSourceColumn
from SOOMv0.Dataset import *
from SOOMv0.DatasetSummary import suppress, retain, order, reversed, \
                                  coalesce, condcol, numcmp
from SOOMv0.SummaryStats import *
from SOOMv0.SummaryProp import propn_names_and_labels, extract_propn_cols
from SOOMv0.Filter import filtered_ds, sampled_ds, sliced_ds
from SOOMv0.Datasets import Datasets
from SOOMv0.DataTypes import datatypes
from SOOMv0.PlotRegistry import plot
from SOOMv0.common import *              # Exceptions, constants, etc
import SOOMv0.interactive_hook          # Interactive friendliness
#from SOOMv0.TransformFN import *

#try:
#    import psyco
#except ImportError:
#    pass
#else:
#    psyco.log('/tmp/soompsyco.log', 'a')
#    psyco.bind(Dataset)
#    psyco.bind(DatasetColumn)
#    psyco.bind(DatasetFilter)
##    psyco.full()

datasets = Datasets()
dsload = datasets.dsload
dsunload = datasets.dsunload
makedataset = datasets.makedataset
subset = datasets.subset
