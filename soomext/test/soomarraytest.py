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
# $Id: soomarraytest.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/soomext/test/soomarraytest.py,v $

import os
import unittest
import soomarray
import tempfile
from mx.DateTime import DateTime, Date, Time
import MA, Numeric

class TempFile:
    def __init__(self, name):
        self.tempdir = tempfile.mkdtemp()
        self.tempfilename = os.path.join(self.tempdir, name)

    def fn(self):
        return self.tempfilename

    def done(self):
        try:
            os.unlink(self.tempfilename)
        except OSError:
            pass
        os.rmdir(self.tempdir)

    def __del__(self):
        try:
            self.done()
        except:
            pass


class ArrayDictTest(unittest.TestCase):
    # This also tests MmapArray
    def test_arraydict(self):
        def _check(a):
            self.assertEqual(a['na'], na)
            self.assertEqual(a['maa'], maa)
            self.assertEqual(a['na'][500:-500], na[500:-500])
            self.assertEqual(a['maa'][500:-500], maa[500:-500])
            scatter = Numeric.array(xrange(0, len(na), 3))
            self.assertEqual(a['na'].take(scatter), Numeric.take(na, scatter))
            self.assertEqual(Numeric.take(a['na'],scatter), 
                             Numeric.take(na, scatter))
            self.assertEqual(MA.take(a['maa'], scatter), MA.take(maa, scatter))

        tmpfile = TempFile('soomtestarray_tmpfile')
        try:
            a = soomarray.ArrayDict(tmpfile.fn(), 'w')
            self.assertEqual(len(a), 0)
            self.assertRaises(KeyError, a.__getitem__, 'not_found')
            na = Numeric.arrayrange(10000)
            a['na'] = na
            na[1000] = -2222
            # MmapArray __setitem__
            a['na'][1000] = -2222

            maa = MA.arrayrange(10000)
            for i in xrange(0, len(maa), 5):
                maa[i] = MA.masked
            a['maa'] = maa
            maa[1000] = -2222
            a['maa'][1000] = -2222

            _check(a)
            del a

            a = soomarray.ArrayDict(tmpfile.fn(), 'r')
            _check(a)
        finally:
            try: del a
            except UnboundLocalError: pass
            tmpfile.done()

            
class _BSDDB_Base(unittest.TestCase):
    def _test_array(self, cls, data):
        def _set(a, data):
            # __setitem__
            for i, d in enumerate(data):
                a[i] = d
            # catch bad type assignment?
            self.assertRaises(TypeError, a.__setitem__, 0, object)

        def _check(a, data):
            # __len__ method
            self.assertEqual(len(a), len(data))
            # __getitem__
            for i, d in enumerate(data):
                self.assertEqual(a[i], d)
            # iteration (if supported)
            self.assertEqual(list(a), data)
            # slices
            self.assertEqual(a[-2:], data[-2:])

        # Disk backed
        tempfile = TempFile('soomarraytest_tmpfile')
        try:
            a=cls(tempfile.fn())
            _set(a, data)
            _check(a, data)
            del a
            a=cls(tempfile.fn())
            _check(a, data)
        finally:
            try: del a
            except UnboundLocalError: pass
            tempfile.done()
        
        # Unbacked
        a=cls()
        _set(a, data)
        _check(a, data)
        del a


class TupleString(_BSDDB_Base):
    def test_tuple(self):
        data = ['', 'qsl', 'rst', 'qrm', 'qsy']
        self._test_array(soomarray.ArrayString, data)


class TupleTest(_BSDDB_Base):
    def test_tuple(self):
        data = [(), ('abc', 'def'), ('pqr',), ('qsl', 'rst', 'qrm', 'qsy')]
        self._test_array(soomarray.ArrayTuple, data)


class DateTimeTest(_BSDDB_Base):
    def test_datetime(self):
        data = [DateTime(2004,1,1,0,0), 
                DateTime(1900,12,31,23,59,59), 
                DateTime(2050,2,28),
                None]
        self._test_array(soomarray.ArrayDateTime, data)

    def test_date(self):
        data = [Date(2004,1,1), 
                Date(1900,12,31), 
                Date(2050,2,28),
                None]
        self._test_array(soomarray.ArrayDate, data)

    def test_time(self):
        data = [Time(0,0), 
                Time(23,59,59), 
                Time(12,0,0),
                None]
        self._test_array(soomarray.ArrayTime, data)


class RecodeArray(unittest.TestCase):
    def _check_data(self, r):
        self.assertEqual(list(r), ['def', None, None, 'abc'])
        self.assertEqual(list(r[2:]), [None, 'abc'])
        self.assertEqual(r[0], 'def')
        self.assertEqual(r[3], 'abc')
        self.assertEqual(r[-1], 'abc')

    def _test_array(self, r):
        self.assertEqual(list(r), [None] * 4)
        self.assertEqual(r[0], None)
        self.assertEqual(r[3], None)
        self.assertRaises(IndexError, r.__getitem__, 4)
        r[3] = 'abc'
        r[0] = 'def'
        self._check_data(r)

    def test_numeric_array(self):
        self._test_array(soomarray.RecodeNumericArray(4))

    def test_blobstore_array(self):
        tempfile = TempFile('recode_array_tmpfile')
        try:
            self._test_array(soomarray.RecodeBlobArray(4, tempfile.fn(), 'w'))
            self._check_data(soomarray.RecodeBlobArray(4, tempfile.fn()))
        finally:
            tempfile.done()

if __name__ == '__main__':
    unittest.main()
