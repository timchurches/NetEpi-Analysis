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
Column datatype specific functionality

Object hierarchy is:

    _BaseDataType
        _NumericBaseDataType
            _IntBaseDataType
                IntDataType
                LongDataType
            FloatDataType
        StrDataType
        TupleDataType
        RecodeDataType
        _DateTimeBaseDataType
            DateDataType
            TimeDataType
            DateTimeDataType

    Classes implement the following attributes and methods:

    pytype              Python type, if applicable
    default_all_value   For discrete columns, default all_value
    default_coltype     If not specified by user, gives column
                        type: categorical, ordinal or scalar
    masked_value        Types that use numpy for storage use this
                        for rows with no value.
    soomarray_type      Types that use soomarray for storage use the
                        given soomarray class.
    file_extension      Extension used on persistent data files.

    get_array(filename, size) 
                        Return an array-like object of the appropriate type.
    get_mask(size)      Return a numpy mask, for types that use numpy
    as_pytype(value)    Cast value to an appropriate pytype or 
                        raise ValueError
    store_data(data, mask, filename)
                        If filename is not None, write data (and mask)
                        to permanent storage, return pointer to 
                        persistent storage object
    load_data(filename) return pointer to persistent storage object
    take(data, want)    extract the values associated with record ids in
                        "want" list.

$Id: DataTypes.py 2626 2007-03-09 04:35:54Z andrewm $
$Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/DataTypes.py,v $
"""

import sys
import os
import mx
import math
# implements memory-mapped Numpy arrays stored in BLOBs
from soomarray import ArrayDict, ArrayFile, ArrayString, ArrayTuple,\
                      ArrayDateTime, ArrayDate, ArrayTime, get_recode_array
import Numeric
import MA
from SOOMv0 import common

class _BaseDataType:
    pytype = None
    default_all_value = '_all_'
    default_coltype = 'categorical'
    masked_value = None
    soomarray_type = None
    default_format_str = '%s'
    is_numeric = False
    is_datetime = False
    is_multivalue = False

    def get_array(self, filename, size):
        if filename:
            try:
                os.unlink(filename)
            except OSError:
                pass
            return self.soomarray_type(filename, 'w')
        else:
            return [None] * size

    def get_mask(self, size):
        return None                     # No mask needed for this type

    def as_pytype(self, value):
        if self.pytype is None:
            return value
        else:
            return self.pytype(value)

    def do_format(self, v, format_str):
        if v is None:
            return str(None)
        else:
            try:
                return format_str % v
            except TypeError:
                return str(v)
            except ValueError, e:
                raise ValueError('%r %% %r: %s' % (format_str, v, e))

    def derive_format_str(self, data):
        return None

    def store_data(self, data, mask, filename = None):
        if filename:
            return None                 # Flag load on demand
        else:
            return data

    def load_data(self, filename):
        return self.soomarray_type(filename, 'r')

    def take(self, data, want):
        if hasattr(data, 'take'):
            return data.take(want)
        else:
            return [data[i] for i in want]

    def __str__(self):
        return self.name                # Historical

class _NumericBaseDataType(_BaseDataType):
    file_extension = 'SOOMblobstore'
    masked_value = 0
    is_numeric = True

    def get_array(self, filename, size):
        return Numeric.zeros(size, typecode=self.numeric_type)

    def get_mask(self, size):
        return Numeric.zeros(size, typecode=MA.MaskType)

    def store_data(self, data, mask, filename = None):
        if mask is None:
            data = Numeric.array(data, typecode=self.numeric_type)
        else:
            data = MA.array(data, typecode=self.numeric_type, mask=mask)
        if filename:
            try:
                os.unlink(filename)
            except OSError:
                pass
            data_blob = ArrayDict(filename, 'w+')
            data_blob['data'] = data
            del data_blob               # this writes the data to disc - 
                                        # we really need a .sync() method...
            return None                 # Flag for load on demand
        else:
            return data

    def load_data(self, filename):
        return ArrayDict(filename, 'r')['data']

    def take(self, data, want):
        if type(data) is MA.MaskedArray:
            return MA.take(data, want)
        elif type(data) is Numeric.ArrayType:
            return Numeric.take(data, want)
        else:
            return _BaseDataType.take(self, data, want)

class _IntBaseDataType(_NumericBaseDataType):
    pytype = int
    default_all_value = -sys.maxint
    default_coltype = 'categorical'
    numeric_type = Numeric.Int
    default_format_str = '%d'

    def as_pytype(self, value):
        try:
            return self.pytype(value)
        except ValueError:
            return self.pytype(round(float(value)))

class IntDataType(_IntBaseDataType):
    name = 'int'

class LongDataType(_IntBaseDataType):
    name = 'long'

class FloatDataType(_NumericBaseDataType):
    name = 'float'
    pytype = float
    default_all_value = float(-sys.maxint)             # AM - ewww
    default_coltype = 'scalar'
    masked_value = 0.0
    numeric_type = Numeric.Float
    default_format_str = '%10.10g'

    def derive_format_str(self, data):
        if len(data) == 0:
            return self.default_format_str
        width = 10
        max = MA.maximum(MA.absolute(data))
        if max > 0:
            decimals = width - math.log(max, 10) - 2
            if decimals < 0:
                decimals = 0
        elif max >= 0.00001:
            decimals = 8
        else:
            return '%10.10g'
        return '%%%d.%df' % (width, decimals)

class StrDataType(_BaseDataType):
    name = 'str'
    masked_value = ''
    soomarray_type = ArrayString
    file_extension = 'SOOMstringarray'

class TupleDataType(_BaseDataType):
    name = 'tuple'
    pytype = None
    masked_value = ()
    soomarray_type = ArrayTuple
    file_extension = 'SOOMtuplearray'
    is_multivalue = True

class RecodeDataType(_BaseDataType):
    name = 'recode'
    file_extension = 'SOOMrecodearray'

    def get_array(self, filename, size):
        return get_recode_array(size, filename, 'w')

    def load_data(self, filename):
        return get_recode_array(0, filename)

class _DateTimeBaseDataType(_BaseDataType):
    pytype = mx.DateTime.DateTimeType
    default_all_value = mx.DateTime.DateTime(0,1,1,0,0,0.0)
    default_coltype = 'ordinal'
    is_datetime = True

    def as_pytype(self, value):
        if type(value) == self.pytype:
            return value
        raise ValueError('bad data type')

    def do_format(self, v, format_str):
        try:
            return v.strftime(format_str)
        except AttributeError:
            return str(v)

class DateDataType(_DateTimeBaseDataType):
    name = 'date'
    soomarray_type = ArrayDate
    file_extension = 'SOOMdatearray'
    default_format_str = '%Y-%m-%d'

class TimeDataType(_DateTimeBaseDataType):
    name = 'time'
    soomarray_type = ArrayTime
    file_extension = 'SOOMtimearray'
    default_format_str = '%H:%M:%S'

class DateTimeDataType(_DateTimeBaseDataType):
    name = 'datetime'
    soomarray_type = ArrayDateTime
    file_extension = 'SOOMdatetimearray'
    default_coltype = 'scalar'
    default_format_str = '%Y-%m-%d %H:%M:%S'

class RecodeDateDataType(DateDataType):
    name = 'recodedate'
    file_extension = 'SOOMrecodearray'

    def get_array(self, filename, size):
        return get_recode_array(size, filename, 'w')

    def load_data(self, filename):
        return get_recode_array(0, filename)

class Datatypes(list):
    def _display_hook(self):
        for dt in self:
            print '%-12r: pytype %r, file extension: %r' %\
                         (dt.name, dt.pytype, dt.file_extension)
            print '%12s  default coltype: %r' %\
                         ('', dt.default_coltype)

datatypes = Datatypes((
    IntDataType, LongDataType, FloatDataType, 
    StrDataType, TupleDataType, RecodeDataType,
    DateDataType, TimeDataType, DateTimeDataType, RecodeDateDataType,
))

datatype_by_name = dict([(c.name, c) for c in datatypes])

def get_datatype_by_name(datatype):
    if type(datatype) is type:
        datatype = datatype.__name__            # Historical bumph.
    elif isinstance(datatype, _BaseDataType):
        return datatype.__class__()
    try:
        return datatype_by_name[datatype.lower()]()
    except KeyError:
        raise common.Error('%r is not a valid column data type' % datatype)
