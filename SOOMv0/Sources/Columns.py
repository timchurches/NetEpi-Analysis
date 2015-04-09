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
# $Id: Columns.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Sources/Columns.py,v $

# SOOMv0 modules
from SOOMv0.Sources.common import *

__all__ = 'ColumnDataSource',

class ColumnDataSource(TextDataSourceBase):
    def __init__(self, name, columns, **kwargs):
        TextDataSourceBase.__init__(self, name, columns, **kwargs)
        self.type = 'columnar text file'
        self.file_iter = self.get_file_iter()
        self.skip_header_rows(self.file_iter)
        self.columns = columns

    def next_rowdict(self):
        """Method to read a row from an initialised data source"""
        line = self.file_iter.next()
        if line == chr(26):
            raise StopIteration
        row = {}
        for col in self.columns:
            if col.startpos is not None:
                startpos = col.startpos - col.posbase
                val = line[startpos:startpos + col.length]
                if val.lstrip():
                    row[col.name] = val
                else:
                    row[col.name] = col.blankval
        return row

