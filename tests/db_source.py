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
# $Id: db_source.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/tests/db_source.py,v $

import unittest
import SOOMv0
from SOOMv0 import DataSourceColumn
from SOOMv0.Sources.DB import DBDataSource

class DummyCursor:
    def __init__(self, rows):
        self.rows = rows
        self.description = [('a_col',), ('b_col',)]

    def execute(self, cmd, *args, **kwargs):
        pass

    def fetchmany(self, count):
        try:
            return self.rows[:count]
        finally:
            self.rows = self.rows[count:]

class DummyDB:
    def __init__(self, rows):
        self.rows = rows

    def cursor(self):
        return DummyCursor(self.rows[:])

class DummyDataType:
    def __init__(self, name):
        self.name = name

class DummyCol:
    def __init__(self, name, datatype):
        self.name = name
        self.datatype = DummyDataType(datatype)

class db_data_source_test(unittest.TestCase):
    def test_source(self):
        rows = zip(range(30), range(29,-1,-1))
        columns = [
            DataSourceColumn('a_col', label='A Column'),
            DataSourceColumn('b_col', label='B Column'),
        ]
        dummy_dataset = [
            DummyCol('a_col', 'int'),
            DummyCol('b_col', 'int'),
        ]
        source = DBDataSource('test', columns, 
                              db=DummyDB(rows), table='', 
                              fetchcount=5)
        source.register_dataset_types(dummy_dataset)
        for db_row in source:
            row = rows.pop(0)
            self.assertEqual(db_row, {'a_col': row[0], 'b_col': row[1]})
        self.failIf(rows)

if __name__ == '__main__':
    unittest.main()
