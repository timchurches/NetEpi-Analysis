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
# $Id: CSV.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Sources/CSV.py,v $

# Standard modules
import csv

# SOOMv0 modules
from SOOMv0.Sources.common import *

__all__ = 'CSVDataSource', 'HeaderCSVDataSource'

class CSVDataSource(TextDataSourceBase):
    """
    Iterable class to load DataSource into a DataSet from a CSV file
    """

    def __init__(self, name, columns, filename, **kwargs):
        # Separate csv.reader args from data source args:
        readerkw = {}
        for arg in dir(csv.Dialect):
            if arg.startswith('_') or arg not in kwargs:
                continue
            readerkw[arg] = kwargs.pop(arg)
        TextDataSourceBase.__init__(self, name, columns, filename, **kwargs)
        self.type = 'comma-separated values text file'
        self.csv_reader = csv.reader(self.get_file_iter(), **readerkw)
        self.skip_header_rows(self.csv_reader)

    def next_rowdict(self):
        """Method to read a row from an initialised csv data source"""
        # read a line
        fields = self.csv_reader.next()
        rowdict = {}
        if fields:
            for col in self.columns:
                if col.ordinalpos is not None:
                    i = col.ordinalpos - col.posbase
                    try:
                        rowdict[col.name] = fields[i]
                    except IndexError, e:
                        raise IndexError('%s: %s (want %d, have %d fields)' % 
                                        (col.name, e, i, len(fields)))
        return rowdict

class HeaderCSVDataSource(CSVDataSource):
    """
    Iterable class to load DataSource into a DataSet from a CSV
    file where the first line of the csv file defines column names.
    """

    def __init__(self, name, columns = [], **kwargs):
        CSVDataSource.__init__(self, name, columns, **kwargs)
        self.col_map = None

    def next_rowdict(self):
        """Method to read a row from an initialised csv data source"""
        # read a line
        if self.col_map is None:
            self.col_map = self.csv_reader.next()
        fields = self.csv_reader.next()
        return dict(zip(self.col_map, fields))
