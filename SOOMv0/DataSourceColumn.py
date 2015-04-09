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
Classes and functions for loading SOOM datasets from external
sources.  Currently data is loaded from one or more instances of
the DataSource class - defined below Each DataSource object contains
a number of DataSourceColumn instances
"""

# $Id: DataSourceColumn.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/DataSourceColumn.py,v $

import os
from SOOMv0.Soom import soom
from SOOMv0 import SourceDataTypes

__all__ = 'DataSourceColumn',

class DataSourceColumn:
    """
    Column definition class for DataSource class

    Attributes:

        name            Column name [I]
        datatype        FIXME XXX this seems to be unused XXX
        coltype         See Soom.py coltypes
        desc            longer description [I]
        label           column label [I][P]
        blankval        character(s) used to represent missing 
                        values in source data
        errorval        character(s) used to represent error values
                        in source data

    For column formatted ASCII files:
        posbase         column positions are zero-based or one-based
        startpos        starting column position for this column
                        of data
        length          length of this column

    For CSV ascii files:
        ordinalpos      the ordinal position of the column (zero
                        or one based)

    For DB queries:
        dbname         if database column name differs from "name"

    Key: [I] inherited by DatasetColumn
         [P] used for presentation of data
    """

    def __init__(self,
                 name,
                 label = None,
#                 datatype = 'str',
                 coltype = 'categorical',
                 posbase = 0,
                 desc = None,
                 startpos = None,
                 length = None,
                 blankval = None,
                 errorval = None,
                 ordinalpos = None,
                 dbname = None,
                 format = None):
        # make sure the new DataSourceColumn has a name
        soom.check_name_ok(name, 'DataSourceColumn')
                                    # DatasetColumn definitions
        # validate some keyword arguments
# Rules are more complicated than they used to be - fix this later
#        if coltype not in soom.coltypes:
#            raise ValueError, '%s is not a valid column type' % coltype

        if posbase < 0 or posbase > 1:
            raise ValueError, '%s - posbase must be 0 or 1' % posbase

        self.name = name
        self.coltype = coltype
        self.posbase = posbase
        self.desc = desc
        self.label = label
        self.startpos = startpos
        self.length = length
        self.blankval = blankval
        self.errorval = errorval
        self.ordinalpos = ordinalpos
        self.dbname = dbname
        self.format = format

    def set_datatype(self, datatype):
        self.datatype = datatype
        if self.format and self.datatype in ('date', 'datetime', 'time'):
            self.conversion = SourceDataTypes.get_format(self.datatype,
                                                         self.format)
        else:
            self.conversion = SourceDataTypes.get_conversion(self.datatype)

    def __str__(self):
        """
        String method to print the definition of a DataSourceColumn
        """
        rep = []
        rep.append("DataSourceColumn definition: %s" % self.name)
        if self.label is not None:
            rep.append("    Label: %s" % self.label)
        if self.desc is not None:
            rep.append("    Description: %s" + self.desc)
        if self.startpos is not None:
            rep.append("    Starting at column position: %s (%s-based)" % \
                (self.startpos, self.posbase))
        if self.length is not None:
            rep.append("    Extending for: %s bytes" % self.length)
        if self.ordinalpos is not None:
            rep.append("    Ordinal position: %s" % self.ordinalpos)
        rep.append("    Column Type: %s" % self.coltype)
        return os.linesep.join(rep)
