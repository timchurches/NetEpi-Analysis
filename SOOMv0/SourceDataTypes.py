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
Support for converting data from source files into python types
"""
# $Id: SourceDataTypes.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/SourceDataTypes.py,v $

import re
import mx.DateTime

__all__ = 'add_datatype', 'is_valid_datatype', 'convert_datatype', \
          'DateConvert'

datatypes = {}

def add_datatype(name, conversion_fn):
    """
    Register a datatype "name"

    The supplied conversion function should accept a single
    argument, being the data in source type, and return a python
    type (in particular, a type supported by soomarray - the basic
    python types int, float, str, tuple, list and dict, as well as
    mx.DateTime types.
    """
    datatypes[name] = conversion_fn

def is_valid_datatype(name):
    if not datatypes.has_key(name):
        raise ValueError, 'invalid datatype: %s' % name

def convert_datatype(datatype, value):
    try:
        cnvt = datatypes[datatype]
    except KeyError:
        raise TypeError, 'Unknown datatype: %s' % datatype
    else:
        return cnvt(value)

def get_conversion(datatype):
    return datatypes[datatype]

def no_conversion(value):
    return value

add_datatype('int', int)
add_datatype('long', long)
add_datatype('str', str)
add_datatype('float', float)
add_datatype('tuple', tuple)
add_datatype('recode', no_conversion)

class DateTimeMagicBase:
    rewrite_re = re.compile(r'(d+|m+|y+|H+|M+|S+|U+)')
    def __init__(self, fmt):
        def repl(match):
            s = match.group(0)
            return r'(?P<%s>\d{1,%d})' % (s[0], len(s))
        self.fmt = fmt
        self.extract_re = self.rewrite_re.sub(repl, self.fmt)
        self.extract_re_c = re.compile('^' + self.extract_re)

    def extract(self, s):
        match = self.extract_re_c.match(s)
        if not match:
            raise ValueError, \
                'unable to parse date/time "%s" with format %s' % (s, self.fmt)
        return match

class DateConvert(DateTimeMagicBase):
    def __call__(self, s):
        if not s:
            return None
        if isinstance(s, mx.DateTime.DateTimeType):
            return s
        match = self.extract(s)
        day, month, year = [int(match.group(f)) for f in 'dmy']
        if year < 50:
            year += 2000
        elif year < 100:
            year += 1900
        return mx.DateTime.Date(year, month, day)

class DateTimeConvert(DateTimeMagicBase):
    def __call__(self, s):
        if not s:
            return None
        if isinstance(s, mx.DateTime.DateTimeType):
            return s
        match = self.extract(s)
        day, month, year, hour, minute = [int(match.group(f)) for f in 'dmyHM']
        try:
            msec = '.' + match.group('U')
        except IndexError:
            msec = ''
        try:
            second = float(match.group('S') + msec)
        except IndexError:
            second = 0.0
        if year < 50:
            year += 2000
        elif year < 100:
            year += 1900
        return mx.DateTime.DateTime(year, month, day, hour, minute, second)

class TimeConvert(DateTimeMagicBase):
    def __call__(self, s):
        if not s:
            return None
        if isinstance(s, mx.DateTime.DateTimeType):
            return s
        match = self.extract(s)
        hour, minute = int(match.group('H')), int(match.group('M'))
        try:
            msec = '.' + match.group('U')
        except IndexError:
            msec = ''
        try:
            second = float(match.group('S') + msec)
        except IndexError:
            second = 0.0
        return mx.DateTime.Time(hour, minute, second)

def get_format(datatype, format):
    ctor_map = {
        'date': DateConvert, 
        'datetime': DateTimeConvert, 
        'time': TimeConvert,
    }
    try:
        return datatypes[format]
    except KeyError:
        datatypes[format] = conversion = ctor_map[datatype](format)
        return conversion

add_datatype('date', DateConvert('dd/mm/yyyy'))
add_datatype('datetime', DateConvert('dd/mm/yyyy HH:MM:SS'))
add_datatype('recodedate', DateConvert('dd/mm/yyyy'))
add_datatype('iso-date', DateConvert('yyyy-mm-dd'))
add_datatype('us-date', DateConvert('mm/dd/yyyy'))
add_datatype('iso-datetime', DateTimeConvert(r'yyyy-mm-dd\s+HH:MM:SS.UU'))
add_datatype('iso-time', TimeConvert('HH:MM:SS.UU'))

# AM - I thought the performance cost of the magic above might be too much, so
# I tried the following - the difference was barely measurable.
#
#def simpledate(value):
#    day, month, year = value.split('/')
#    return mx.DateTime.Date(int(year), int(month), int(day))
#add_datatype('date', simpledate)
