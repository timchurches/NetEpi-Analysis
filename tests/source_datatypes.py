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
import unittest
from mx.DateTime import DateTime, Time
import SOOMv0
from SOOMv0 import SourceDataTypes

class TestSourceDataTypes(unittest.TestCase):
    def test_int1(self):
        conv = SourceDataTypes.get_conversion('int')
        self.assertEqual(conv('123'), 123)
        self.assertRaises(TypeError, conv, None)
        self.assertRaises(ValueError, conv, '123.4')
        self.assertRaises(ValueError, conv, 'abc')
        self.assertRaises(ValueError, conv, '12 3')

    def test_int2(self):
        conv = SourceDataTypes.get_conversion('int')
        self.assertEqual(conv('-123'), -123)
        self.assertRaises(ValueError, conv, '-123.4')
        self.assertRaises(ValueError, conv, '12,3')

    def test_int3(self):
        conv = SourceDataTypes.get_conversion('int')
        self.assertEqual(conv('1234567890'), 1234567890)

    def test_int4(self):
        conv = SourceDataTypes.get_conversion('int')
        self.assertEqual(conv('12345678901234567890123456789012345678901234567890'), 12345678901234567890123456789012345678901234567890)

    def test_long1(self):
        conv = SourceDataTypes.get_conversion('long')
        self.assertEqual(conv('123'), 123)
        self.assertRaises(TypeError, conv, None)
        self.assertRaises(ValueError, conv, '123.4')
        self.assertRaises(ValueError, conv, 'abc')
        self.assertRaises(ValueError, conv, '12 3')
        self.assertRaises(ValueError, conv, '-123.4')
        self.assertRaises(ValueError, conv, '12,3')

    def test_long2(self):
        conv = SourceDataTypes.get_conversion('long')
        self.assertEqual(conv('1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890'), \
                               1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890)

    def test_str(self):
        conv = SourceDataTypes.get_conversion('str')
        self.assertEqual(conv('123'), '123')
        self.assertEqual(conv(123), '123')
        self.assertEqual(conv(123.1), '123.1')
        self.assertEqual(conv(None), 'None')
        self.assertNotEqual(conv(123.45678901234567890123456789012345678901234567890), \
                             '123.45678901234567890123456789012345678901234567890')

    def test_float(self):
        conv = SourceDataTypes.get_conversion('float')
        self.assertEqual(conv('123'), 123)
        self.assertEqual(conv('123.4'), 123.4)
        self.assertEqual(conv('-123.4'), -123.4)
        self.assertEqual(conv('123.45678901234567890123456789012345678901234567890'), \
                               123.45678901234567890123456789012345678901234567890)
        self.assertRaises(TypeError, conv, None)

    def test_date(self):
        conv = SourceDataTypes.get_conversion('date')
        self.assertEqual(conv('23/12/1970'), DateTime(1970,12,23))
        self.assertEqual(conv('23/12/70'), DateTime(1970,12,23))
        self.assertEqual(conv('25/12/00'), DateTime(2000,12,25))
        self.assertEqual(conv('25/12/1900'), DateTime(1900,12,25))
        self.assertEqual(conv('25/12/900'), DateTime(900,12,25))
        self.assertEqual(conv('25/12/9'), DateTime(2009,12,25))
        self.assertEqual(conv('3/2/2004'), DateTime(2004,2,3))
        self.assertEqual(conv('3/2/04'), DateTime(2004,2,3))
        self.assertEqual(conv('03/2/04'), DateTime(2004,2,3))
        self.assertEqual(conv('3/02/04'), DateTime(2004,2,3))
        self.assertEqual(conv('03/02/04'), DateTime(2004,2,3))
        self.assertEqual(conv('29/02/04'), DateTime(2004,2,29))
        self.assertEqual(conv(None), None)
        self.assertEqual(conv(''), None)
        self.assertRaises(ValueError, conv, '2 3 04')
        self.assertRaises(ValueError, conv, '23-12-1970')
        # how to trap this error?
        # self.assertRaises(RangeError, conv, '29/02/2003')

    def test_early_date(self):
        "This test illustrates inability to handle dates earlier than 100 AD."
        conv = SourceDataTypes.get_conversion('date')
        self.assertNotEqual(conv('25/12/0000'), DateTime(0,12,25))

    def test_iso_date(self):
        conv = SourceDataTypes.get_conversion('iso-date')
        self.assertEqual(conv('1970-12-23'), DateTime(1970,12,23))
        self.assertEqual(conv('70-12-23'), DateTime(1970,12,23))
        self.assertEqual(conv('2004-2-3'), DateTime(2004,2,3))
        self.assertEqual(conv('04-2-3'), DateTime(2004,2,3))
        self.assertEqual(conv('00-12-25'), DateTime(2000,12,25))
        self.assertEqual(conv('1900-12-25'), DateTime(1900,12,25))
        self.assertEqual(conv('900-12-25'), DateTime(900,12,25))
        self.assertEqual(conv('9-12-25'), DateTime(2009,12,25))
        self.assertEqual(conv('04-2-03'), DateTime(2004,2,3))
        self.assertEqual(conv('04-02-3'), DateTime(2004,2,3))
        self.assertEqual(conv('04-02-03'), DateTime(2004,2,3))
        self.assertEqual(conv('04-02-29'), DateTime(2004,2,29))
        self.assertEqual(conv(None), None)
        self.assertEqual(conv(''), None)
        self.assertRaises(ValueError, conv, '2 3 04')
        self.assertRaises(ValueError, conv, '1970/12/23')
        # how to trap this error?
        # self.assertRaises(RangeError, conv, '2003-02-29')

    def test_us_date(self):
        conv = SourceDataTypes.get_conversion('us-date')
        self.assertEqual(conv('12/23/1970'), DateTime(1970,12,23))
        self.assertEqual(conv('12/23/70'), DateTime(1970,12,23))
        self.assertEqual(conv('12/25/00'), DateTime(2000,12,25))
        self.assertEqual(conv('12/25/1900'), DateTime(1900,12,25))
        self.assertEqual(conv('12/25/900'), DateTime(900,12,25))
        self.assertEqual(conv('12/25/9'), DateTime(2009,12,25))
        self.assertEqual(conv('2/3/2004'), DateTime(2004,2,3))
        self.assertEqual(conv('2/3/04'), DateTime(2004,2,3))
        self.assertEqual(conv('2/03/04'), DateTime(2004,2,3))
        self.assertEqual(conv('02/3/04'), DateTime(2004,2,3))
        self.assertEqual(conv('02/03/04'), DateTime(2004,2,3))
        self.assertEqual(conv('02/29/04'), DateTime(2004,2,29))
        self.assertEqual(conv(None), None)
        self.assertEqual(conv(''), None)
        self.assertRaises(ValueError, conv, '3 2 04')
        self.assertRaises(ValueError, conv, '12-23-1970')
        # how to trap this error?
        # self.assertRaises(RangeError, conv, '02/29/2003')

    def test_iso_time(self):
        conv = SourceDataTypes.get_conversion('iso-time')
        self.assertEqual(conv('01:12:23.34'), Time(1,12,23.34))
        self.assertEqual(conv('1:12:23.4'), Time(1,12,23.4))
        self.assertEqual(conv('1:2:3.4'), Time(1,2,3.4))
        self.assertEqual(conv('01:02:03.4'), Time(1,2,3.4))
        self.assertEqual(conv(None), None)
        self.assertEqual(conv(''), None)

    def test_iso_time_leap_seconds(self):
        """Err, shouldn't some of these throw errors, even allowing for leap seconds?"""
        conv = SourceDataTypes.get_conversion('iso-time')
        self.assertEqual(conv('01:02:60.4'), Time(1,2,60.4))
        self.assertEqual(conv('01:02:61.4'), Time(1,2,61.4))
        self.assertEqual(conv('01:02:62.4'), Time(1,2,62.4))

    def test_iso_datetime(self):
        conv = SourceDataTypes.get_conversion('iso-datetime')
        self.assertEqual(conv('1970-12-23 01:12:23.34'), 
                         DateTime(1970,12,23,1,12,23.34))
        self.assertEqual(conv('1970-12-23   01:12:23.34'), 
                         DateTime(1970,12,23,1,12,23.34))
        self.assertEqual(conv('70-12-23 1:12:23.4'), 
                         DateTime(1970,12,23,1,12,23.4))
        self.assertEqual(conv('70-12-23 1:2:3.4'), 
                         DateTime(1970,12,23,1,2,3.4))
        self.assertEqual(conv(None), None)
        self.assertEqual(conv(''), None)

    def test_time_optional_seconds(self):
        conv = SourceDataTypes.get_format('time', 'HH:MM')
        self.assertEqual(conv('12:23'), Time(12,23))
        self.assertEqual(conv('12:23'), Time(12,23,0.0))

if __name__ == '__main__':
    unittest.main()
