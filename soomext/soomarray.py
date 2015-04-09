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
# $Id: soomarray.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/soomext/soomarray.py,v $

import cPickle
import string
import blobstore
import mmaparray
import MA
import Numeric
import types
import mx.DateTime
import struct
import bsddb
import types

class Error(Exception):
    pass


class MmapArray:
    def __init__(self, blob):
        self.blob = blob
        array = blob.as_array()
        self.shape = array.shape
        self._typecode = array.typecode()
        self.name = string.split(str(self.__class__))[0]

    def append(self, a):
        self.blob.append_array(a)
        self.shape = self.blob.as_array().shape

    def __repr__(self):
        return repr(self.blob.as_array())

    def __array__(self,t=None):
        if t:
            return Numeric.asarray(self.blob.as_array(),t)
        return Numeric.asarray(self.blob.as_array())

    def __float__(self):
        return float(Numeric.asarray(self.blob.as_array()))

    # Array as sequence
    def __len__(self):
        return len(self.blob.as_array())

    def __getitem__(self, index): 
        return self.blob.as_array()[index]

    def take(self, rows):
        array = self.blob.as_array()
        if MA.isMaskedArray(array):
            return MA.take(array, rows)
        else:
            return Numeric.take(array, rows)

#    __getslice__ is deprecated - slice object passed as index to __getitem__
#    def __getslice__(self, i, j): 
#        return self.blob.as_array()[i:j]

    def __setitem__(self, index, value):
        self.blob.as_array()[index] = Numeric.asarray(value,self._typecode)

    def __setslice__(self, i, j, value):
        self.blob.as_array()[i:j] = Numeric.asarray(value,self._typecode)

    def __abs__(self):
        return Numeric.absolute(self.blob.as_array())

    def __neg__(self):
        return -self.blob.as_array()

    def __add__(self, other): 
        return self.blob.as_array()+Numeric.asarray(other)
    __radd__ = __add__

    def __sub__(self, other): 
        return self.blob.as_array()-Numeric.asarray(other)

    def __rsub__(self, other): 
        return Numeric.asarray(other)-self.blob.as_array()

    def __mul__(self, other): 
        return Numeric.multiply(self.blob.as_array(),Numeric.asarray(other))
    __rmul__ = __mul__

    def __div__(self, other): 
        return Numeric.divide(self.blob.as_array(),Numeric.asarray(other))

    def __rdiv__(self, other): 
        return Numeric.divide(Numeric.asarray(other),self.blob.as_array())

    def __pow__(self,other): 
        return Numeric.power(self.blob.as_array(),Numeric.asarray(other))

    def __rpow__(self,other): 
        return Numeric.power(Numeric.asarray(other),self.blob.as_array())

    def __sqrt__(self): 
        return Numeric.sqrt(self.blob.as_array())

    def tostring(self):
        return self.blob.as_array().tostring()

    def byteswapped(self):
        return self.blob.as_array().byteswapped()

    def astype(self, typecode):
        return self.blob.as_array().astype(typecode)

    def typecode(self):
        return self._typecode

    def itemsize(self):
        return self.blob.as_array().itemsize()

    def iscontiguous(self):
        return self.blob.as_array().iscontiguous()

    def __setattr__(self,attr,value):
        if attr=='shape':
            self.blob.as_array().shape=value
        self.__dict__[attr]=value

    def __getattr__(self,attr):
        # for .attributes for example, and any future attributes
        return getattr(self.blob.as_array(), attr)


class ArrayFile(MmapArray):
    def __init__(self, filename, array = None):
        if array is not None:
            mmaparray.write(filename, array)
        blob = mmaparray.read(filename)
        MmapArray.__init__(self, blob)


BLOB_DICT = 0
BLOB_ARRAY = 1
BLOB_FILLED = 2
BLOB_MASK = 3
BLOB_STRING = 4

class ArrayDict:
    def __init__(self, filename, mode = 'r'):
        self.dict_dirty = 0
        self.store = blobstore.open(filename, mode)
        if len(self.store) > 0:
            blob = self.store[0]
            self.dict = cPickle.loads(blob.as_str())
        else:
            self.dict_dirty = 1
            self.store.append()
            self.dict = {}

    def __del__(self):
        if self.dict_dirty:
            blob = self.store[0]
            blob.type = BLOB_DICT
            blob.save_str(cPickle.dumps(self.dict))

    def __getitem__(self, key):
        index = self.dict[key]
        blob = self.store[index]
        if blob.type == BLOB_ARRAY:
            return MmapArray(blob)
        elif blob.type == BLOB_FILLED:
            data = MmapArray(blob)
            blob = self.store[blob.other]
            mask = MmapArray(blob)
            return MA.array(data, mask = mask)
        elif blob.type == BLOB_STRING:
            return blob.as_str()
        else:
            raise Error('bad BLOB type %s in index' % blob.type)

    def __setitem__(self, key, a):
        index = self.dict.get(key)
        if index is None:
            if MA.isMaskedArray(a):
                index = self._save_new_masked(a)
            elif type(a) == Numeric.ArrayType:
                index = self._save_new_array(a)
            elif type(a) == types.StringType:
                index = self._save_new_str(a)
            else:
                index = self._save_new_str(repr(a))
            self.dict[key] = index
            self.dict_dirty = 1
        else:
            if MA.isMaskedArray(a):
                self._save_masked(index, a)
            elif type(a) == Numeric.ArrayType:
                self._save_array(index, a)
            elif type(a) == types.StringType:
                self._save_str(index, a)
            else:
                index = self._save_str(index, repr(a))

    def __delitem__(self, key):
        index = self.dict.get(key)
        if index is None:
            raise KeyError, key
        blob = self.store[index]
        if blob.type == BLOB_FILLED:
            self.store.free(blob.other)
        self.store.free(index)
        del self.dict[key]
        self.dict_dirty = 1

    def __getslice__(self, i, j): 
        slice = []
        if j > len(self):
            j = len(self)
        for s in range(i,j):
            slice.append(self[s])
        return slice

    def clear(self):
        for key in self.dict.keys():
            del self[key]

    def get(self, key, default = None):
        if self.dict.has_key(key):
            return self[key]
        return default

    def has_key(self, key):
        return self.dict.has_key(key)

    def keys(self):
        return self.dict.keys()

    def values(self):
        values = []
        for key in self.dict.keys():
            values.append(self[key])
        return values

    def items(self):
        items = []
        for key in self.dict.keys():
            items.append((key, self[key]))
        return items

    def _save_new_masked(self, a):
        index = self.store.append()
        blob = self.store[index]
        blob.type = BLOB_FILLED
        blob.save_array(a.filled())
        blob.other = self.store.append()
        blob = self.store[blob.other]
        blob.type = BLOB_MASK
        blob.save_array(a.mask())
        blob.other = index
        return index

    def _save_new_array(self, a):
        index = self.store.append()
        blob = self.store[index]
        blob.type = BLOB_ARRAY
        blob.save_array(a)
        return index

    def _save_new_str(self, a):
        index = self.store.append()
        blob = self.store[index]
        blob.type = BLOB_STRING
        blob.save_str(str(a))
        return index

    def _save_masked(self, index, a):
        blob = self.store[index]
        if blob.type == BLOB_FILLED:
            blob.save_array(a.filled())
            blob = self.store[blob.other]
            blob.save_array(a.mask())
        elif blob.type == BLOB_ARRAY:
            blob.type = BLOB_FILLED
            blob.save_array(a.filled())
            blob.other = self.store.append()
            blob = self.store[blob.other]
            blob.type = BLOB_MASK
            blob.save_array(a.mask())
        else:
            raise Error('unexpected BLOB type %s in index' % blob.type)

    def _save_array(self, index, a):
        blob = self.store[index]
        if blob.type == BLOB_FILLED:
            blob.type = BLOB_ARRAY
            blob.save_array(a)
            self.store.free(blob.other)
            blob.other = 0
        elif blob.type == BLOB_ARRAY:
            blob.save_array(a)
        else:
            raise Error('unexpected BLOB type %s in index' % blob.type)

    def _save_str(self, index, a):
        blob = self.store[index]
        if blob.type == BLOB_STRING:
            blob.save_str(a)
        else:
            raise Error('unexpected BLOB type %s in index' % blob.type)

    def __len__(self):
        return len(self.dict)


class ArrayString:
    def __init__(self, filename=None, mode='c'):
        self.store = bsddb.rnopen(filename, mode)

    def __del__(self):
        try:
            self.store.close()
        except AttributeError:
            pass

    def __setitem__(self, i, a):
        if a is None:
            self.store[i+1] = ''
        elif type(a) is str:
            self.store[i+1] = a
        else:
            raise TypeError('Cannot store a non-string in an ArrayString: %r' % a)

    def __getitem__(self, i):
        if type(i) is slice:
            return [self.store[s+1] for s in xrange(*i.indices(len(self)))]
        else:
            try:
                return self.store[i+1]
            except KeyError:
                raise IndexError('index %d out of range' % i)

    def __delitem__(self, i):
        del self.store[i+1]

    def __len__(self):
        stat = self.store.db.stat()
        return stat['ndata']

#    def __getslice__(self, i, j):
#        slice = []
#        for s in range(i, j):
#            item = self.store[s+1]
#            slice.append(item)
#        return slice    


class ArrayTuple:
    def __init__(self, filename=None, mode='c'):
        self.store = bsddb.rnopen(filename, mode)

    def __del__(self):
        try:
            self.store.close()
        except AttributeError:
            pass


    def __setitem__(self, i, a):
        if type(a) is not tuple:
            raise TypeError('Cannot store a non-tuple in an ArrayTuple: %r' % a)
        try:
            x = hash(a)
        except:
            raise ValueError('Cannot store a non-hashable value in an ArrayTuple: %r' % a)
        self.store[i+1] = cPickle.dumps(a,-1)

    def __getitem__(self, i):
        if type(i) is slice:
            return [cPickle.loads(self.store[s+1])
                    for s in xrange(*i.indices(len(self)))]
        else:
            try:
                return cPickle.loads(self.store[i+1])
            except KeyError:
                raise IndexError('index %d out of range' % i)

    def __delitem__(self, i):
        del self.store[i+1]

    def __len__(self):
        stat = self.store.db.stat()
        return stat['ndata']
        #return len(self.store)  # why doesn't this work?
            # Works on the first call, but subseq calls return 0
        # return len(self.store.keys())

#    def __getslice__(self, i, j):
#        slice = []
#        for s in range(i, j):
#            item = cPickle.loads(self.store[s+1])
#            slice.append(item)
#        return slice    


class ArrayDateTime:
    def __init__(self, filename=None, mode='c'):
        self.store = bsddb.rnopen(filename, mode)

    def __del__(self):
        try:
            self.store.close()
        except AttributeError:
            pass

    def __setitem__(self, i, a):
        if a is None:
            self.store[i+1] = str(None)
        else:
            try:
                absdt = a.absvalues()
            except AttributeError:
                raise TypeError('ArrayDateTime values must be mx.DateTimes or None')
            self.store[i+1] = struct.pack('ld',absdt[0],absdt[1])

    def __getitem__(self, i):
        if type(i) is slice:
            res = []
            for s in xrange(*i.indices(len(self))):
                item = self.store[s+1]
                if item == str(None):
                    res.append(None)
                else:
                    absdt = struct.unpack('ld',item)
                    res.append(mx.DateTime.DateTimeFromAbsDateTime(absdt[0],absdt[1]))
            return res
        else:
            try:
                item = self.store[i+1]
            except KeyError:
                raise IndexError('index %d out of range' % i)
            if item == str(None):
                return None
            else:
                absdt = struct.unpack('ld',item)
                return mx.DateTime.DateTimeFromAbsDateTime(absdt[0],absdt[1])

    def __delitem__(self, i):   
        del self.store[i+1]

    def __len__(self):
        stat = self.store.db.stat()
        return stat['ndata']

#    def __getslice__(self, i, j):
#        slice = []
#        for s in range(i, j):
#            item = self.store[s+1]
#            if item == str(None):
#                slice.append(None)
#            else:
#                absdt = struct.unpack('ld',item)
#                slice.append(mx.DateTime.DateTimeFromAbsDateTime(absdt[0],absdt[1]))
#        return slice    


class ArrayDate:
    def __init__(self, filename=None, mode='c'):
        self.store = bsddb.rnopen(filename, mode)

    def __del__(self):
        try:
            self.store.close()
        except AttributeError:
            pass

    def __setitem__(self, i, a):
        if a is None:
            self.store[i+1] = str(None)
        else:
            try:
                absdt = a.absvalues()
            except AttributeError:
                raise TypeError('ArrayDate values must be mx.DateTimes or None')
            self.store[i+1] = struct.pack('l',absdt[0])

    def __getitem__(self, i):
        if type(i) is slice:
            res = []
            for s in xrange(*i.indices(len(self))):
                item = self.store[s+1]
                if item == str(None):
                    res.append(None)
                else:
                    absdt = struct.unpack('l',item)
                    res.append(mx.DateTime.DateTimeFromAbsDateTime(absdt[0],0))
            return res
        else:
            try:
                item = self.store[i+1]
            except KeyError:
                raise IndexError('index %d out of range' % i)
            if item == str(None):
                return None
            else:
                absdt = struct.unpack('l',item)
                return mx.DateTime.DateTimeFromAbsDateTime(absdt[0],0)

    def __delitem__(self, i):   
        del self.store[i+1]

    def __len__(self):
        stat = self.store.db.stat()
        return stat['ndata']

#    def __getslice__(self, i, j):
#        slice = []
#        for s in range(i, j):
#            item = self.store[s+1]
#            if item == str(None):
#                slice.append(None)
#            else:
#                absdt = struct.unpack('l',item)
#                slice.append(mx.DateTime.DateTimeFromAbsDateTime(absdt[0],0))
#        return slice    


class ArrayTime:
    def __init__(self, filename=None, mode='c'):
        self.store = bsddb.rnopen(filename, mode)

    def __del__(self):
        try:
            self.store.close()
        except AttributeError:
            pass

    def __setitem__(self, i, a):
        if a is None:
            self.store[i+1] = str(None)
        else:
            try:
                absdt = a.absvalues()
            except AttributeError:
                raise TypeError('ArrayTime values must be mx.DateTimes or None')
            self.store[i+1] = struct.pack('d',absdt[1])

    def __getitem__(self, i):
        if type(i) is slice:
            res = []
            for s in xrange(*i.indices(len(self))):
                item = self.store[s+1]
                if item == str(None):
                    res.append(None)
                else:
                    absdt = struct.unpack('d',item)
                    res.append(mx.DateTime.DateTimeDeltaFromSeconds(absdt[0]))
            return res
        else:
            try:
                item = self.store[i+1]
            except KeyError:
                raise IndexError('index %d out of range' % i)
            if item == str(None):
                return None
            else:
                absdt = struct.unpack('d',item)
                return mx.DateTime.DateTimeDeltaFromSeconds(absdt[0])

    def __delitem__(self, i):   
        del self.store[i+1]

    def __len__(self):
        stat = self.store.db.stat()
        return stat['ndata']

#    def __getslice__(self, i, j):
#        slice = []
#        for s in range(i, j):
#            item = self.store[s+1]
#            if item == str(None):
#                slice.append(None)
#            else:
#                absdt = struct.unpack('d',item)
#                slice.append(mx.DateTime.DateTimeDeltaFromSeconds(absdt[0]))
#        return slice    


RECODE_META_IDX = 0
RECODE_DATA_IDX = 1

class RecodeBlobArray:
    def __init__(self, size, filename, mode='r'):
        self.dirty = False
        self.store = None
        self.store = blobstore.open(filename, mode)
        if len(self.store):
            metadata = cPickle.loads(self.store[RECODE_META_IDX].as_str())
            self.obj_to_code, self.code_to_obj, self.next_code = metadata
        else:
            self.store.append()
            self.store.append()
            self.obj_to_code = {}
            self.code_to_obj = [None]
            self.next_code = 1
            zeros = Numeric.zeros(size)
            self.store[RECODE_DATA_IDX].save_array(zeros)

    def __del__(self):
        if self.dirty:
            metadata = self.obj_to_code, self.code_to_obj, self.next_code
            self.store[0].save_str(cPickle.dumps(metadata))

    def __len__(self):
        return len(self.store[RECODE_DATA_IDX].as_array())

    def __getitem__(self, i):
        array = self.store[RECODE_DATA_IDX].as_array()
        if type(i) is slice:
            return [self.code_to_obj[v] for v in array[i]]
        else:
            return self.code_to_obj[array[i]]
    
    def take(self, rows):
        array = self.store[RECODE_DATA_IDX].as_array()
        return [self.code_to_obj[v] for v in Numeric.take(array, rows)]

    def __setitem__(self, i, v):
        code = self.obj_to_code.get(v, None)
        if code is None:
            code = self.next_code
            self.next_code += 1
            self.obj_to_code[v] = code
            self.code_to_obj.append(v)
        array = self.store[RECODE_DATA_IDX].as_array()
        array[i] = code
        self.dirty = True


class RecodeNumericArray:
    def __init__(self, size):
        self.obj_to_code = {}
        self.code_to_obj = [None]
        self.next_code = 1
        self.data = Numeric.zeros(size)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        if type(i) is slice:
            return [self.code_to_obj[v] for v in self.data[i]]
        else:
            return self.code_to_obj[self.data[i]]

    def take(self, rows):
        return [self.code_to_obj[v] for v in Numeric.take(self.data, rows)]

    def __setitem__(self, i, v):
        code = self.obj_to_code.get(v, None)
        if code is None:
            code = self.next_code
            self.next_code += 1
            self.obj_to_code[v] = code
            self.code_to_obj.append(v)
        self.data[i] = code

def get_recode_array(size, filename=None, mode='r'):
    if filename:
        return RecodeBlobArray(size, filename, mode)
    else:
        return RecodeNumericArray(size)

class ArrayVocab:
    def __init__(self, filename=None, mode='c'):
        self.store = bsddb.hashopen(filename, mode)

    def __del__(self):
        try:
            self.store.close()
        except AttributeError:
            pass

    def __setitem__(self, i, a):
        if type(a) != types.TupleType or len(a) != 2:
            raise TypeError('value must be a 2-element tuple')
        try:
            v = struct.pack(">LL", *map(int, a))
        except ValueError:
            raise TypeError('values must be integers')
        self.store[str(i)] = v

    def __getitem__(self, i):
        return struct.unpack(">LL", self.store[i])

    def get(self, i, default):
        try:
            return self.__getitem__(i)
        except KeyError:
            return default
            
    def __delitem__(self, i):   
        del self.store[i]

    def keys(self):
        return self.store.keys()

    def __len__(self):
        stat = self.store.db.stat()
        return stat['ndata']

    def sync(self):
        self.store.sync()

