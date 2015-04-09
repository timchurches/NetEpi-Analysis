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
# $Id: filters.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/tests/filters.py,v $

import unittest
from SOOMv0 import Filter, DatasetColumn, Soom, Dataset
from mx import DateTime

class DummyDataset:
    name = 'dummyds'
    backed = False
    length = 0
    generation = 0

    def __init__(self, cols):
        for i, (name, (datatype, items)) in enumerate(cols.iteritems()):
            if self.length:
                assert self.length == len(items)
            else:
                self.length = len(items)
            col = DatasetColumn.get_dataset_col(self, name, i, datatype=datatype)
            col.store_column(items)
            setattr(self, name, col)

    def get_column(self, name):
        return getattr(self, name)

    def __len__(self):
        return self.length

class filter_test(unittest.TestCase):
    words = ['adulate','adulterate', 'advocating','aesthete','afterword']

    def _test(self, dataset, filterexpr, expected_record_ids):
        filter = Filter.DatasetFilter(dataset, 'test_filter', filterexpr)
        self.assertEqual(list(filter.record_ids), expected_record_ids,
                         'expr %r returned record ids %r, expected %r' %\
                            (filterexpr, list(filter.record_ids), 
                             expected_record_ids))

    def _try_all(self, dataset, col, ops, value, expect):
        for op in ops:
            if type(value) is str:
                filterexpr = '%s %s "%s"' % (col, op, value)
            else:
                filterexpr = '%s %s %s' % (col, op, value)
            self._test(dataset, filterexpr, expect)

class filter_logical_op_test(filter_test):
    def test_eq(self):
        dummy_ds = DummyDataset({'a': (int, [1,2,1,2,-1])})
        filter = Filter.DatasetFilter(dummy_ds, 'test_filter', 'a=1')
        self.assertEqual(list(filter.record_ids), [0, 2])
        ops = '=', '==', 'equal to', 'equals', 'eq'
        self._try_all(dummy_ds, 'a', ops, 1, [0, 2])

    def test_not(self):
        dummy_ds = DummyDataset({'a': (int, [1,2,1,2,-1])})
        filter = Filter.DatasetFilter(dummy_ds, 'test_filter', 'not a=1')
        self.assertEqual(list(filter.record_ids), [1,3,4])

    def test_gt(self):
        dummy_ds = DummyDataset({'a': (int, [1,2,1,2,-1])})
        ops = 'greaterthan', 'gt', '>', 'greater than'
        self._try_all(dummy_ds, 'a', ops, 1, [1, 3])

    def test_ge(self):
        dummy_ds = DummyDataset({'a': (int, [1,2,1,2,-1])})
        ops = 'greaterthanorequalto', 'greaterequal', '>=', '=>', 'ge', \
              'greater than or equal to'
        self._try_all(dummy_ds, 'a', ops, 1, [0, 1, 2, 3])

    def test_lt(self):
        dummy_ds = DummyDataset({'a': (int, [1,2,1,2,-1])})
        ops = 'lessthan', 'lt', '<', 'less than'
        self._try_all(dummy_ds, 'a', ops, 1, [4])

    def test_le(self):
        dummy_ds = DummyDataset({'a': (int, [1,2,1,2,-1])})
        expect = [0,2,4]
        ops = 'lessthanorequalto', 'lessequal', '<=', '=<', 'le',\
              'less than or equal to'
        self._try_all(dummy_ds, 'a', ops, 1, [0,2,4])

    def test_ne(self):
        dummy_ds = DummyDataset({'a': (int, [1,2,1,2,-1])})
        ops = 'notequalto', 'notequal', '!=', '<>', 'doesnotequal', \
              'ne', '!==', '#', 'does not equal', 'not equal to'
        self._try_all(dummy_ds, 'a', ops, 1, [1,3,4])

class filter_startswith_test(filter_test):
    def test_eq_col(self):
        dummy_ds = DummyDataset({'a': (str, self.words)})
        ops = '=:', 'starting with', '==:', 'startingwith', 'eq:'
        self._try_all(dummy_ds, 'a', ops, 'ad', [0,1,2])

    def test_ne_col(self):
        dummy_ds = DummyDataset({'a': (str, self.words)})
        ops = 'notequalto:', 'notequal:', '!=:', '<>:', 'doesnotequal:', \
              'ne:', '!==:', '#:', 'does not equal:', 'not equal to:'
        self._try_all(dummy_ds, 'a', ops, 'ad', [3,4])

    def test_lt_col(self):
        dummy_ds = DummyDataset({'a': (str, self.words)})
        ops = 'lessthan:', 'lt:', '<:', 'less than:'
        self._try_all(dummy_ds, 'a', ops, 'adv', [0, 1])

    def test_le_col(self):
        dummy_ds = DummyDataset({'a': (str, self.words)})
        ops = 'lessthanorequalto:', 'lessequal:', 'le:', '<=:', '=<:', \
              'less than or equal to:'
        self._try_all(dummy_ds, 'a', ops, 'adv', [0, 1, 2])

    def test_gt_col(self):
        dummy_ds = DummyDataset({'a': (str, self.words)})
        ops = 'greaterthan:', 'gt:', '>:', 'greater than:'
        self._try_all(dummy_ds, 'a', ops, 'adu', [2, 3, 4])

    def test_ge_col(self):
        dummy_ds = DummyDataset({'a': (str, self.words)})
        ops = 'greaterthanorequalto:', 'greaterequal:', 'ge:', '>=:', '=>:', \
              'greater than or equal to:'
        self._try_all(dummy_ds, 'a', ops, 'adu', [0, 1, 2, 3, 4])

class filter_set_test(filter_test):
    def test_in(self):
        dummy_ds = DummyDataset({'a': (int, [1,2,1,2,3])})
        ops = 'in',
        self._try_all(dummy_ds, 'a', ops, (1,2), [0, 1, 2, 3])

    def test_in_col(self):
        dummy_ds = DummyDataset({'a': (str, self.words)})
        ops = 'in:',
        self._try_all(dummy_ds, 'a', ops, ('adu', 'af') , [0, 1, 4])

    def test_not_in(self):
        dummy_ds = DummyDataset({'a': (int, [1,2,1,2,3])})
        ops = 'notin',
        self._try_all(dummy_ds, 'a', ops, (1,2), [4])

    def test_not_in_col(self):
        dummy_ds = DummyDataset({'a': (str, self.words)})
        ops = 'notin:',
        self._try_all(dummy_ds, 'a', ops, ('adu', 'af') , [2, 3])

class filter_combinational_test(filter_test):
    def _test_ds(self):
        return DummyDataset({'a': (int, [1,2,3,4,5]), 
                             'b': (str, ['a','b','c','d','e']),
                             'c': (str, ['one','two','three','four','five']),
                             'd': (int, [1,2,1,2,-1]),
                             'e': (int, [1,2,-3,4,5]), 
                             'f': (float, [1.2,3.45678,-9.34,0.1,0.321]),
                             'g': (int, [1,1,2,1,1]), 
                             'h': (str, ['a','a','b','a','a']),
                             'i': (str, ['one','one','two','one','one'])})

    def test_and(self):
        self._test(self._test_ds(), 'd=1 and b="c"', [2])

    def test_or(self):
        self._test(self._test_ds(), 'd=1 or b="d"', [0,2,3])

    def test_andnot(self):
        self._test(self._test_ds(), 'd=1 and not b="c"', [0])

    def test_ornot(self):
        self._test(self._test_ds(), 'd=1 or not b="c"', [0,1,2,3,4])

    def test_andor(self):
        ds = self._test_ds()
        self._test(ds, 'd=1 or (b="d" and d=2)', [0,2,3])
        self._test(ds, 'b="d" and d=2 or d=1', [0,2,3]) 
        self._test(ds, 'd=1 or d=2 and b="d"', [0,2,3]) 

    def test_oror(self):
        ds = self._test_ds()
        self._test(ds, 'a=1 or b="c" or c="five"', [0,2,4])
        self._test(ds, 'a=1 or b="a" or c="one"', [0])
        self._test(ds, 'a=1 or b="a" or c="five"', [0,4])
        self._test(ds, 'a=1 or b="f" or c="five"', [0,4])

    def test_andand(self):
        ds = self._test_ds()
        self._test(ds, 'a=1 and b="a" and c="one"', [0])
        self._test(ds, 'a=1 and b="a" and c="two"', [])
        self._test(ds, 'a=1 and b="b" and c="two"', [])
        self._test(ds, 'a=1 and b="b" and c="three"', [])
        self._test(ds, 'g=1 and h="a" and i="one"', [0,1,3,4])
        self._test(ds, 'g=1 and h="b" and i="one"', [])
        self._test(ds, 'g=1 and h="a" and i="two"', [])
        self._test(ds, 'g=1 and h="a" and i="three"', [])
        self._test(ds, 'g=11 and h="z" and i="fred"', [])
        self._test(ds, 'g=11 and h="z" and i=3', [])

    def test_andandnot(self):
        ds = self._test_ds()
        self._test(ds, 'a=1 and b="a" and not c="one"', [])
        self._test(ds, 'a=1 and b="a" and not c="one"', [])
        self._test(ds, 'a=1 and b="a" and not c="two"', [0])
        self._test(ds, 'a=1 and not b="a" and c="one"', [])
        self._test(ds, 'a=1 and not b="b" and c="one"', [0])

    def test_andnotandnot(self):
        ds = self._test_ds()
        self._test(ds, 'a=1 and not b="a" and not c="one"', [])
        self._test(ds, 'a=1 and not b="b" and not c="three"', [0])
        self._test(ds, 'a=1 and not b="a" and not c="three"', [])
        self._test(ds, 'a=4 and not b="z" and not c="eight"', [3])

    def test_notandnotandnot(self):
        ds = self._test_ds()
        self._test(ds, 'not a=4 and not b="z" and not c="eight"', [0,1,2,4])
        self._test(ds, 'not a=9 and not b="z" and not c="eight"', [0,1,2,3,4])
        self._test(ds, 'not a=1 and not b="a" and not c="one"', [1,2,3,4])
        self._test(ds, 'not a=1 and not b="b" and not c="three"', [3,4])

    def test_ornotornot(self):
        ds = self._test_ds()
        self._test(ds, 'a=1 or not b="a" or not c="one"', [0,1,2,3,4])

    def test_notornotornot(self):
        ds = self._test_ds()
        self._test(ds, 'not a=1 or not b="a" or not c="one"', [1,2,3,4])
        self._test(ds, 'not a=1 or not b="b" or not c="three"', [0,1,2,3,4])
        self._test(ds, 'not a=1 or not a=2 or not a=3', [0,1,2,3,4])

    def test_notandnotornot(self):
        ds = self._test_ds()
        self._test(ds, 'not a=1 and not b="a" or not c="one"', [1,2,3,4])
        self._test(ds, 'not a=1 or not b="b" and not c="three"', [0,1,2,3,4])

    def test_andin(self):
        ds = self._test_ds()
        self._test(ds, 'a in (1,3,5) and b in ("b","d")', [])
        self._test(ds, 'a in (1,3,5) and b in ("b","d") '
                       'or c in ("four","eleven")', [3])
        self._test(ds, 'a in (1,3,5) and b in ("b","d") '
                       'or c in ("fourth","eleven")', [])
        self._test(ds, 'a in (1,3,4) and b in ("b","d") '
                       'or c in: ("fourth","eleven")', [3])

    def test_orin(self):
        ds = self._test_ds()
        self._test(ds, 'a in (1,3,5) or b in ("b","d") or '
                       'c in ("fourth","eleven")', [0,1,2,3,4])

    def test_notinnotin(self):
        ds = self._test_ds()
        self._test(ds, 'a notin (1,3,5) and b notin ("b","d")', [])

    def test_notnotinnotnotin(self):
        ds = self._test_ds()
        self._test(ds, 'not a notin (1,3,5) and not b notin ("b","d")', [])
        self._test(ds, 'not a notin (1,3,5) and not b notin ("a","c") '
                       'and not c notin ("three","five")', [2])

    def test_notinnotnotin(self):
        ds = self._test_ds()
        self._test(ds, 'a notin (1,3,5) and not b notin ("b","d")', [1,3])

    def test_negnums1(self):
        ds = self._test_ds()
        self._test(ds, 'e=-3 and f=-9.34', [2])
        self._test(ds, 'e=-3 and f=-9.34 and c startingwith "th"', [2])

class filter_paren_test(filter_test):
    def _test_ds(self):
        ds = Dataset('paren')
        for name in 'abcdefghij':
            ds.addcolumnfromseq(name, datatype='int', data=range(10))
        return ds

    def test_parentheses(self):
        ds = self._test_ds()
        self._test(ds, 'a=0 or b=0 and c=1 or d=1 and e=2 '
                       'or f=2 and g=3 or h=3 and i=4 or j=4', [0,4])

        self._test(ds, '(a=0 or b=0) and (c=1 or d=1) and '
                       '(e=2 or f=2) and (g=3 or h=3) and (i=4 or j=4)', [])

        self._test(ds, 'a=0 and b=0 or c=1 and d=1 or e=2 and f=2 '
                       'or g=3 and h=3 or i=4 and j=4', [0,1,2,3,4])

        self._test(ds, 'a=0 and (b=0 or c=1) and (d=1 or e=2) and '
                       '(f=2 or g=3) and (h=3 or i=4) and j=4', [])

        self._test(ds, 'a=0 and (b=0 or c=1) and (d=0 or e=2) '
                       'and (f=0 or g=3) and (h=0 or i=4) and j=0', [0])

        self._test(ds, '(a=0 and b=0) or (c=1 and d=0) or (((e=2 and '
                       'f=0 or g=3) and (h=0 or i=4)) or j=3)', [0,3])

        self._test(ds, '(a=2 and (b=0 or (c=2 and (d in (2,3) and (e=2 or '
                       '(f=3 and (g=3 or (h=4 and (i=3 or j=4)))))))))', [2])

        self._test(ds, '(((((((((a=2 and b=0) or c=2) and d in (2,3)) and e=2)'
                       'or f=3) and g=3) or h=4) and i=3) or j=4)', [3,4])

    def test_manyin(self):
        ds = self._test_ds()
        self._test(ds, 
                   'a in (1,2,3,4,5,6,7,8,9) and b in (0,2,3,4,5,6,7,8,9) and '
                   'c in (0,1,3,4,5,6,7,8,9) and d in (0,1,2,4,5,6,7,8,9) and '
                   'e in (0,1,2,3,5,6,7,8,9) and f in (0,1,2,3,4,6,7,8,9) and '
                   'g in (0,1,2,3,4,5,7,8,9) and h in (0,1,2,3,4,5,6,8,9) and '
                   'i in (0,1,2,3,4,5,6,7,9) and j in (0,1,2,3,4,5,6,7,8)',
                   [])

        self._test(ds, 
                   'a in (1,2,3,4,5,6,7,8,9) and b in (0,2,3,4,5,6,7,8,9) and '
                   'c in (0,1,3,4,5,6,7,8,9) and d in (0,1,2,3,5,6,7,8,9) and '
                   'e in (0,1,2,3,5,6,7,8,9) and f in (0,1,2,3,4,6,7,8,9) and '
                   'g in (0,1,2,3,4,5,7,8,9) and h in (0,1,2,3,4,5,6,8,9) and '
                   'i in (0,1,2,3,4,5,6,7,9) and j in (0,1,3,4,5,6,7,8,9)',
                   [3,9])

        self._test(ds, 
                   'a in (11) and b in (0,2,3,4,5,6,7,8,9) and '
                   'c in (0,1,3,4,5,6,7,8,9) and d in (0,1,2,3,5,6,7,8,9) and '
                   'e in (0,1,2,3,5,6,7,8,9) and f in (0,1,2,3,4,6,7,8,9) and '
                   'g in (0,1,2,3,4,5,7,8,9) and h in (0,1,2,3,4,5,6,8,9) and '
                   'i in (0,1,2,3,4,5,6,7,9) and j in (0,1,3,4,5,6,7,8,9)',
                   [])

        self._test(ds, 
                   'a notin (0,1,2,4,5,6,7,8) and b notin (0,2,8) and '
                   'c notin (0,4,5,6,7,8) and d notin (0,1,2,5,6,7) and '
                   'e notin (0,1,2,5,6,7,8) and f notin (0,8,8,8,8,8,8,8) and '
                   'g notin (0,1,2,4,5,7,8) and h notin (4,5,6,8) and '
                   'i notin (0,6,7) and j notin (0,1,4,5,6,7,8)',
                   [3,9])

class datetime_test(filter_test):
    def _get_dates_ds(self):
        ds = Dataset('dates_and_times')
        ds.addcolumnfromseq('a', label='Date 1',
                            datatype='date',
                            data=[DateTime.Date(1956,4,23),
                                  DateTime.Date(2003,9,30),
                                  DateTime.Date(2002,3,1),
                                  DateTime.Date(2000,6,21),
                                  DateTime.Date(2009,5,27),
                                  DateTime.Date(3003,9,11),
                                  DateTime.Date(1903,4,2),
                                  DateTime.Date(1803,9,9),
                                  DateTime.Date(1803,9,9),
                                  DateTime.Date(103,9,29)])                                
        ds.addcolumnfromseq('b', label='Time 1',
                            datatype='time',
                            data=[DateTime.Time(1,4,23.1),
                                  DateTime.Time(20,9,30.2),
                                  DateTime.Time(8,3,1.3),
                                  DateTime.Time(18,6,21.44),
                                  DateTime.Time(0,0,0.0),
                                  DateTime.Time(12,9,11.5),
                                  DateTime.Time(19,4,2),
                                  DateTime.Time(18,9,9.789876353663554648477647863563),
                                  DateTime.Time(18,9,9),
                                  DateTime.Time(23,59,59.9999999999999999999999)])                                
        ds.addcolumnfromseq('c', label='Datetime 1',
                            datatype='datetime',
                            data=[DateTime.DateTime(1956,4,23,23,59,59.9999999999999999999999),
                                  DateTime.DateTime(2003,9,30,18,9,9),
                                  DateTime.DateTime(2002,3,1,18,9,9.789876353663554648477647863563),
                                  DateTime.DateTime(2000,6,21,19,4,2),
                                  DateTime.DateTime(2009,5,27,12,9,11.5),
                                  DateTime.DateTime(3003,9,11,0,0,0.0),
                                  DateTime.DateTime(1903,4,2,18,6,21.44),
                                  DateTime.DateTime(1803,9,9,8,3,1.3),
                                  DateTime.DateTime(1803,9,9,20,9,30.2),
                                  DateTime.DateTime(103,9,29,1,4,23.1)])                                
        return ds

    def _get_reldate_ds(self):
        def rdt(**kwargs):
            return now + DateTime.RelativeDateTime(hour=12, **kwargs)
        now = DateTime.now()
        data = [
            rdt(days=1),                                # tomorrow
            now,
            rdt(days=-1),                               # yesterday
            rdt(days=-7),                               # last week
            rdt(days=-7, weekday=(DateTime.Monday,0)),  # Monday a week ago
            rdt(months=-1),                             # a month ago
            rdt(months=-1, day=1),                      # begining of last mnth
            rdt(years=-1),                              # a year go
            rdt(years=-1, month=DateTime.January, day=1),# begining of last year
        ]
        ds = Dataset('reldate')
        ds.addcolumnfromseq('a', label='dates relative to today',
                            datatype= 'date', data=data)
        return ds

    def test_dates_simple(self):
        ds = self._get_dates_ds()
        self._test(ds, 'a ge date(1960,1,1)', [1,2,3,4,5])
        self._test(ds, 'a ge date 1960-1-1', [1,2,3,4,5])
        self._test(ds, 'a le date(1903,4,2)', [6,7,8,9])
        self._test(ds, 'a le date 1903-4-2', [6,7,8,9])
        self._test(ds, 'a == date(3003,9,11)', [5])
        self._test(ds, 'a == date 3003-9-11', [5])
        self._test(ds, 'a > date(4000,1,1)', [])
        self._test(ds, 'a > date 4000-1-1', [])
        self._test(ds, 'a < date(103,9,29)', [])

    def test_dates_comb(self):
        ds = self._get_dates_ds()
        self._test(ds, 'a ge date(100,1,1) and a le date(200,1,1)', [9])

    def test_dates_between(self):
        ds = self._get_dates_ds()
        self._test(ds, 'a between (date(1850,1,1),date(1950,1,1))', [6])
        self._test(ds, 'a between (date(100,1,1),date(4000,1,1))', 
                   [0,1,2,3,4,5,6,7,8,9])

    def test_reldat(self):
        # Picking values for relative datetime tests is difficult - the clock
        # is running, and first-of-month (etc) change the result.
        ds = self._get_reldate_ds()
        self.assertRaises(ValueError, Filter.DatasetFilter, ds, 'test_filter',
                          'a >= reldate(days=-1, months=-1)')
        self.assertRaises(TypeError, Filter.DatasetFilter, ds, 'test_filter',
                          'a >= reldate(poo=1)')
        self.assertRaises(ValueError, Filter.DatasetFilter, ds, 'test_filter',
                          'a >= reldate(align="xxx")')
        self._test(ds, 'a >= reldate(days=+1)', [0])
        self._test(ds, 'a >= reldate()', [0, 1])
        self._test(ds, 'a >= reldate(days=0)', [0, 1])
        self._test(ds, 'a >= reldate(days=-1)', [0, 1, 2])
        if DateTime.now().day_of_week == 0:
            self._test(ds, 'a >= reldate(days=-7)', [0, 1, 2, 3, 4]) # this fails on Mondays!
        else:
            self._test(ds, 'a >= reldate(days=-7)', [0, 1, 2, 3]) # this fails on Mondays!
        self._test(ds, 'a >= reldate(days=-7, align="monday")', [0, 1, 2, 3, 4]) 
        if DateTime.now().day == 1:
            expect = [0, 1, 2, 3, 4, 5, 6]
        else:
            expect = [0, 1, 2, 3, 4, 5]
        self._test(ds, 'a >= reldate(months=-1)', expect)
        self._test(ds, 'a >= reldate(months=-1, align="bom")', [0, 1, 2, 3, 4, 5, 6])
        if DateTime.now().day == 1 and DateTime.now().month == DateTime.January:
            expect = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        else:
            expect = [0, 1, 2, 3, 4, 5, 6, 7]
        self._test(ds, 'a >= reldate(years=-1)', expect)
        self._test(ds, 'a >= reldate(years=-1, align="boy")', [0, 1, 2, 3, 4, 5, 6, 7, 8])
        if DateTime.now().day_of_week == 0:
            self._test(ds, 'a between(reldate(days=-7), reldate(days=-2))', [3, 4]) # also fails on Mondays
        else:
            self._test(ds, 'a between(reldate(days=-7), reldate(days=-2))', [3]) 

    # Note: currently no support for times or datetime in filters

if __name__ == '__main__':
    unittest.main()
