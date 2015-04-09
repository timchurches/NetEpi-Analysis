# vim: set ts=4 sw=4 et:
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
# $Id: DatasetColumn.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/DatasetColumn.py,v $

from SOOMv0.common import *
from SOOMv0.DataTypes import get_datatype_by_name

from SOOMv0.ColTypes.base import is_dataset_col
from SOOMv0.ColTypes.RowOrdinal import RowOrdinalColumn
from SOOMv0.ColTypes.SearchableText import SearchableTextDatasetColumn
from SOOMv0.ColTypes.Identity import IdentityDatasetColumn
from SOOMv0.ColTypes.Scalar import ScalarDatasetColumn, WeightingDatasetColumn
from SOOMv0.ColTypes.Discrete import CategoricalDatasetColumn, OrdinalDatasetColumn


column_types = [
    IdentityDatasetColumn, CategoricalDatasetColumn, OrdinalDatasetColumn, 
    ScalarDatasetColumn, WeightingDatasetColumn, SearchableTextDatasetColumn,
]

coltype_by_name = dict([(c.coltype, c) for c in column_types])
coltype_by_name['noncategorical'] = coltype_by_name['identity']

def get_coltype(coltype):
    try:
        return coltype_by_name[coltype]
    except KeyError:
        raise Error('%r is not a valid column type' % coltype)

def get_dataset_col(*args, **kwargs):
    """
    Factory to produce appropriate dataset column instance, given coltype.
    """
    datatype = get_datatype_by_name(kwargs.get('datatype', 'str'))
    coltype = kwargs.pop('coltype', None)
    if coltype is None or coltype in ('date', 'time', 'datetime'):
        coltype = datatype.default_coltype
    coltype = get_coltype(coltype)
    kwargs['datatype'] = datatype
    return coltype(*args, **kwargs)

