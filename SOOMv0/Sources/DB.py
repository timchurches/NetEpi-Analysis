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
# $Id: DB.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Sources/DB.py,v $

# SOOMv0 modules
from SOOMv0.Sources.common import *

__all__ = 'DBDataSource',

class DBDataSource(DataSourceBase):
    """
    Iterable class to load DataSource into a DataSet from a DB API
    v2.0 connection.

    Note: pyPgSQL will perform faster if PgSQL.fetchReturnsList and
    PgSQL.noPostgresCursor are set to 1 (these make pyPgSQL behave
    like dumber adapters - we duplicate much of those smarts anyway).
    """

    def __init__(self, name, columns, 
                 db, table, where = None, whereargs = None, fetchcount = 1000, 
                 **kwargs):
        DataSourceBase.__init__(self, name, columns, **kwargs)
        self.db = db
        self.fetchcount = fetchcount
        self.rows = []
        colmap = {}
        dbcols = []
        for col in columns:
            if col.dbname:
                dbname = col.dbname
            else:
                dbname = col.name
            colmap[dbname.lower()] = col
            dbcols.append(dbname)
        self.type = 'database connection'
        query = 'select %s from %s' % (', '.join(dbcols), table)
        if where:
            query += ' where ' + where
        self.curs = self.db.cursor()
        if whereargs is None:
            self.curs.execute(query)
        else:
            self.curs.execute(query, whereargs)
        self.col_ord = [colmap.get(d[0].lower(), None)
                        for d in self.curs.description]

    def next_rowdict(self):
        if self.rows is None:
            raise StopIteration
        if not self.rows:
            self.rows = self.curs.fetchmany(self.fetchcount)
        try:
            row = self.rows.pop(0)
        except IndexError:
            self.rows = None
            raise StopIteration
        row_dict = {}
        for col, value in zip(self.col_ord, row):
            if col:
                row_dict[col.name] = value
        return row_dict

