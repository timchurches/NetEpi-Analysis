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

# $Id: common.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Sources/common.py,v $

import sys
import os
from SOOMv0.Soom import soom
from SOOMv0.DataSourceColumn import DataSourceColumn

class DataSourceBase:
    """
    Definitions of sources of data. 

    Arguments:
        name            name of data source definition
        columns         list of DataSourceColumns
        type            ?
        label           data source label [I]
        desc            descriptive label [I]

    Key: 
        [I] inherited by the DataSet(s) created from this data
            source definition.

    Subclasses are intended to be iterable.
    """

    def __init__(self, name, columns, 
                 type = None, label = None, desc = None,
                 missing = None,
                 xformpre = None, xformpost = None):
        soom.check_name_ok(name, 'DataSource')
        self.name = name
        self.type = type
        self.label = label
        self.desc = desc
        self.missing = missing
        self.col_dict = dict([(c.name, c) for c in columns])
        self.columns = columns
        self.xformpre = xformpre
        self.xformpost = xformpost

    def register_dataset_types(self, dataset_cols):
        """
        The Dataset tells us what columns and datatypes it's
        expecting before it starts.
        """
        self.columns = []
        for ds_col in dataset_cols:
            try:
                datatype = ds_col.datatype.name
            except AttributeError:
                continue
            try:
                column = self.col_dict[ds_col.name]
            except KeyError:
                column = DataSourceColumn(ds_col.name, ds_col.label)
                self.col_dict[ds_col.name] = column
            column.set_datatype(datatype)
            self.columns.append(column)

    def __str__(self):
        """
        String method to print out the definition of a DataSource
        including the DataSourceColumns contained in it.
        """
        # TO DO: improve the layout of the definition print out
        m = [""]
        m.append("DataSource definition: %s" % self.name)
        if self.label != None:
            m.append("    Label: %s" % self.label)
        if self.desc != None:
            m.append("    Description: %s" % self.desc)
        m.append("    Type: %s" % self.type)
        m.append("    Containing the following DataSourceColumns:")
        for col in self.columns:
            # column definitions know how to print themselves
            m.extend([' ' * 8 + l for l in str(col).split('\n')])
        return '\n'.join(m)

    def __iter__(self):
        return self

    def next(self):
        while 1:
            rowdict = self.next_rowdict()
            if not rowdict:
                continue
            if self.xformpre:
                rowdict = self.xformpre(rowdict)
                if rowdict is None:
                    continue
            for col in self.columns:
                v = rowdict.get(col.name)
                if v is not None:
                    if v == '' or self.missing == v:
                        v = None
                    else:
                        try:
                            v = col.conversion(v)
                        except (TypeError, ValueError):
                            exc = sys.exc_info()
                            try:
                                raise exc[0], 'column "%s": %s, value was "%r", datatype "%s"' % (col.name, exc[1], v, col.datatype), exc[2]
                                
                            finally:
                                del exc
                    rowdict[col.name] = v
            if self.xformpost:
                rowdict = self.xformpost(rowdict)
                if rowdict is None:
                    continue
            return rowdict

class TextDataSourceBase(DataSourceBase):
    """
    Hold common methods for accessing text file DataSources.  Note:
    opens file in constructor.

    As well as the arguments supported by DataSourceBase, TextDataSourceBase
    subclasses also support the following:

        filename        name of file which contains source data
        path            path to file which contains source data
        header_rows     number of rows to skip in source data file
                        before actual data starts

    TODO: other sources such as XML and DBMS data in future.
    """

    def __init__(self, name, columns, filename, path = None,
                 header_rows = 0, **kwargs):
        DataSourceBase.__init__(self, name, columns, **kwargs)
        self.filename = filename
        self.path = path
        self.header_rows = header_rows
        self.type = 'text file'
        if self.path:
            self.filepath = os.path.join(self.path, self.filename)
        else:
            self.filepath = self.filename

    def __str__(self):
        return '%s\n    Filename: %s' % \
            (DataSourceBase.__str__(self), self.filepath)

    def get_file_iter(self):
        def _zipiter(filepath, member=None):
            try:
                import zipfile
            except ImportError:
                raise IOError, '%s: zip support not available' % self.filename
            f = zipfile.ZipFile(filepath)
            if member is None:
                if len(f.namelist()) != 1:
                    raise IOError('%s: zip file member not specified' %
                                        self.filename)
                member = f.namelist()[0]
            try:
                return iter(f.read(member).splitlines())
            finally:
                f.close()
            
        if self.filename.endswith('.gz'):
            try:
                import gzip
            except ImportError:
                raise IOError, '%s: gzip support not available' % self.filename
            return iter(gzip.GzipFile(self.filepath))
        elif self.filename.endswith('.zip'):
            return _zipiter(self.filepath)
        else:
            dirname = os.path.dirname(self.filename)
            if dirname.endswith('.zip'):
                return _zipiter(dirname, os.path.basename(self.filename))
            else:
                return iter(open(self.filepath))

    def skip_header_rows(self, i):
        if self.header_rows:
            for n in range(self.header_rows):
                i.next()
