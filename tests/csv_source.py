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
# $Id: csv_source.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/tests/csv_source.py,v $

import os, sys
import unittest
import SOOMv0
from SOOMv0 import DataSourceColumn
from SOOMv0.Sources.CSV import CSVDataSource

def data_dir():
    return os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'data')

class DummyDataType:
    def __init__(self, name):
        self.name = name

class DummyCol:
    def __init__(self, name, datatype):
        self.name = name
        self.datatype = DummyDataType(datatype)

class csv_data_source_test(unittest.TestCase):
    def test_source(self):
        columns = [
            DataSourceColumn('a_col', label='A Col', ordinalpos=1, posbase=1),
            DataSourceColumn('b_col', label='B Col', ordinalpos=2, posbase=1),
        ]
        dummy_dataset = [
            DummyCol('a_col', 'str'),
            DummyCol('b_col', 'str'),
        ]
        source = CSVDataSource('test', columns, 
                               path=data_dir(),
                               filename='csv_data')
        source.register_dataset_types(dummy_dataset)
        expect = [
            ('1', '2'),
            ('a,b', 'c'),
            ('d','e\nf'),
        ]
        for db_row in source:
            row_expect = dict(zip(('a_col', 'b_col'), expect.pop(0)))
            self.assertEqual(db_row, row_expect)
        self.failIf(expect)

if __name__ == '__main__':
    unittest.main()
