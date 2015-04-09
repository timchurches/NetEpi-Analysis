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
# $Id: stats.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/tests/stats.py,v $

import unittest
from SOOMv0 import Stats
try:
    from SOOMv0 import Cstats
except ImportError:
    import sys
    sys.stderr.write('WARNING - Cstats module not available - tests skipped\n')
    Cstats = None
rpy_tests = True
if not rpy_tests:
    sys.stderr.write('WARNING - R-based stat method tests disabled\n')
import Numeric, MA

empty_numeric = Numeric.array([])
empty_ma = MA.array([],mask=[])
populated_numeric = Numeric.array([1,2,3,3,5])
populated_ma = MA.array([1,2,3,3,5],mask=[0,0,0,0,0])
null_mask = MA.array([1,2,3,5,3], mask=[0,0,0,0,0])
full_mask = MA.array([1,2,3,5,3], mask=[1,1,1,1,1])
partial_mask = MA.array([1,2,3,5,3], mask=[1,0,1,0,1])
two_elements_numeric = Numeric.array([2,5])
two_elements_ma = MA.array([2,5],mask=[0,0])
one_element_numeric = Numeric.array([2])
one_element_ma = MA.array([2],mask=[0])
one_masked_element_ma = MA.array([2],mask=[1])
one_neg_element_numeric = Numeric.array([-2])
one_neg_element_ma = MA.array([-2],mask=[0])
all_neg_numeric = Numeric.array([-3,-4,-5,-2,-76])
all_neg_ma = MA.array([-3,-4,-5,-2,-76],mask=[0,0,0,0,0])
twenty_ele = Numeric.array([4, 5, 14, 19, 17, 13, 12, 9, 8, 0, 
                            15, 18, 2, 1, 16, 6, 7, 10, 11, 3])

n1001_nomissing_numpy = Numeric.arrayrange(990, -11, -1, typecode=Numeric.Int)
w1001_nomissing_numpy = Numeric.arrayrange(990, -11, -1,
                                           typecode=Numeric.Float) / 3.0
n1006_nomissing_numpy = Numeric.arrayrange(995, -11, -1, typecode=Numeric.Int)
w1006_nomissing_numpy = Numeric.arrayrange(995, -11, -1,
                                           typecode=Numeric.Float) / 3.0
n1001_nomissing_MA = MA.array(range(990, -11, -1),
                              typecode=MA.Int, mask=Numeric.zeros(1001))
w1001_nomissing_MA = MA.array(range(990, -11, -1),
                              typecode=MA.Float, mask=Numeric.zeros(1001)) / 3.0
n1006_nomissing_MA = MA.array(range(995, -11, -1),
                              typecode=MA.Int, mask=Numeric.zeros(1006))
w1006_nomissing_MA = MA.array(range(995, -11, -1),
                              typecode=MA.Float, mask=Numeric.zeros(1006)) / 3.0

def makemask(n, mmod):
    mmask = []
    for z in range(n, -11, -1):
        if (z % mmod == 0 and mmod == 7 and z < 500) or \
           (z % mmod == 0 and mmod == 13 and z > 500):
            mmask.append(1)
        else:
            mmask.append(0)
    return Numeric.array(mmask, typecode=Numeric.Int)

n1001_missing = MA.array(range(990, -11, -1),
                         typecode=MA.Int, mask=makemask(990, 7))
w1001_missing = MA.array(range(990, -11, -1),
                         typecode=MA.Int, mask=makemask(990, 13)) / 3.0
n1006_missing = MA.array(range(995, -11, -1),
                         typecode=MA.Int, mask=makemask(995, 7))
w1006_missing = MA.array(range(995, -11, -1),
                         typecode=MA.Int, mask=makemask(995, 13)) / 3.0

class StatsTests(unittest.TestCase):
    def _test(self, fn, data, expect, **kwargs):
        if type(data) is tuple:
            result = fn(*data,**kwargs)
        else:
            result = fn(data,**kwargs)
        if result is MA.masked or expect is MA.masked:
            ok = result is expect
        elif type(result) in (float, int) or type(expect) in (float, int):
            ok = round(result, 4) == round(expect, 4)
        else:
            ok = result == expect
        self.failUnless(ok, '%s(%s) - expected %s, got %s' % 
                                (fn.__name__, data, expect, result))

    def _stricttest(self, fn, data, expect, **kwargs):
        if type(data) is tuple:
            result = fn(*data,**kwargs)
        else:
            result = fn(data,**kwargs)
        if result is MA.masked or expect is MA.masked:
            ok = result is expect
        elif type(result) in (float, int) or type(expect) in (float, int):
            ok = round(result, 7) == round(expect, 7)
        elif type(result) in (tuple, list) or type(expect) in (tuple, list):
            oks = []
            for i in range(len(result)):
                r_val = result[i]
                e_val = expect[i]
                if e_val is None or r_val is None:
                    oks.append(r_val == e_val)
                else:                
                    oks.append(round(r_val, 7) == round(e_val, 7))
            ok = True
            for r in oks:
                if not r:
                    ok = False
        else:
            ok = result == expect
        self.failUnless(ok, '%s(%s) - expected %s, got %s' % 
                                (fn.__name__, data, expect, result))

    def test_wn_misc(self):
        self._test(Stats.wn, (empty_numeric,), 0) 
        self._test(Stats.wn, (empty_ma,), 0)
        self._test(Stats.wn, (populated_numeric,), 14)
        self._test(Stats.wn, (populated_ma,), 14)
        self._test(Stats.wn, (full_mask,), 0)
        self._test(Stats.wn, (null_mask,), 14)
        self._test(Stats.wn, (partial_mask,), 7)
        self._test(Stats.wn, (two_elements_numeric,), 7)
        self._test(Stats.wn, (two_elements_ma,), 7)
        self._test(Stats.wn, (one_element_numeric,), 2)
        self._test(Stats.wn, (one_element_ma,), 2)
        self._test(Stats.wn, (one_neg_element_numeric,), 0)
        self._test(Stats.wn, (one_neg_element_ma,), 0)
        self._test(Stats.wn, (one_masked_element_ma,), 0)
        self._test(Stats.wn, (all_neg_numeric,), 0)
        self._test(Stats.wn, (all_neg_ma,), 0)

    def test_wn_misc_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wn, (empty_numeric,), 0,exclude_nonpositive_weights=True) 
        self._test(Stats.wn, (empty_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (populated_numeric,), 14, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (populated_ma,), 14, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (full_mask,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (null_mask,), 14, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (partial_mask,), 7, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (two_elements_numeric,), 7, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (two_elements_ma,), 7, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (one_element_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (one_element_ma,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (one_neg_element_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (one_neg_element_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (one_masked_element_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (all_neg_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (all_neg_ma,), 0, exclude_nonpositive_weights=True)

    def test_wn_1001(self):
        # now with 1001 element arrays
        self._test(Stats.wn, (w1001_nomissing_numpy,), 163515)
        self._test(Stats.wn, (w1001_nomissing_MA,), 163515)
        self._test(Stats.wn, (w1001_missing,), 154046.66666667)

    def test_wn_1001_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wn, (w1001_nomissing_numpy,), 163515, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (w1001_nomissing_MA,), 163515, exclude_nonpositive_weights=True)
        self._test(Stats.wn, (w1001_missing,), 154046.66666667, exclude_nonpositive_weights=True)
    
    def test_nonmissing_misc(self):
        self._test(Stats.nonmissing, empty_numeric, 0)
        self._test(Stats.nonmissing, empty_ma, 0)
        self._test(Stats.nonmissing, populated_numeric, 5)
        self._test(Stats.nonmissing, populated_ma, 5)
        self._test(Stats.nonmissing, null_mask, 5)
        self._test(Stats.nonmissing, full_mask, 0)
        self._test(Stats.nonmissing, partial_mask, 2)
        self._test(Stats.nonmissing, two_elements_numeric, 2)
        self._test(Stats.nonmissing, two_elements_ma, 2)
        self._test(Stats.nonmissing, one_element_numeric, 1)
        self._test(Stats.nonmissing, one_element_ma, 1)
        self._test(Stats.nonmissing, one_neg_element_numeric, 1)
        self._test(Stats.nonmissing, one_neg_element_ma, 1)
        self._test(Stats.nonmissing, one_masked_element_ma, 0)
        self._test(Stats.nonmissing, all_neg_numeric, 5)
        self._test(Stats.nonmissing, all_neg_ma, 5)

    def test_nonmissing_1001(self):
        self._test(Stats.nonmissing, n1001_nomissing_numpy, 1001)
        self._test(Stats.nonmissing, n1001_nomissing_MA, 1001)
        self._test(Stats.nonmissing, n1001_missing, 928)
        self._test(Stats.nonmissing, n1006_nomissing_numpy, 1006)
        self._test(Stats.nonmissing, n1006_nomissing_MA, 1006)
        self._test(Stats.nonmissing, n1006_missing, 933)

    def test_wnonmissing_misc(self):
        self._test(Stats.wnonmissing, (empty_numeric,empty_numeric), 0)
        self._test(Stats.wnonmissing, (empty_ma,empty_numeric), 0)
        self._test(Stats.wnonmissing, (empty_numeric,empty_ma), 0)
        self._test(Stats.wnonmissing, (empty_ma,empty_ma), 0)
        self._test(Stats.wnonmissing, (populated_numeric,populated_numeric), 5)
        self._test(Stats.wnonmissing, (populated_ma,populated_numeric), 5)
        self._test(Stats.wnonmissing, (populated_numeric,populated_ma), 5)
        self._test(Stats.wnonmissing, (populated_ma,populated_ma), 5)
        self._test(Stats.wnonmissing, (populated_numeric,full_mask), 0)
        self._test(Stats.wnonmissing, (populated_ma,full_mask), 0)
        self._test(Stats.wnonmissing, (null_mask,null_mask), 5)
        self._test(Stats.wnonmissing, (null_mask,partial_mask), 2)
        self._test(Stats.wnonmissing, (null_mask,full_mask), 0)
        self._test(Stats.wnonmissing, (partial_mask,null_mask), 2)
        self._test(Stats.wnonmissing, (partial_mask,partial_mask), 2)
        self._test(Stats.wnonmissing, (partial_mask,full_mask), 0)
        self._test(Stats.wnonmissing, (full_mask,null_mask), 0)
        self._test(Stats.wnonmissing, (full_mask,partial_mask), 0)
        self._test(Stats.wnonmissing, (full_mask,full_mask), 0)
        self._test(Stats.wnonmissing, (two_elements_numeric,two_elements_numeric), 2)
        self._test(Stats.wnonmissing, (two_elements_ma,two_elements_numeric), 2)
        self._test(Stats.wnonmissing, (one_element_numeric,one_element_numeric), 1)
        self._test(Stats.wnonmissing, (one_element_ma,one_element_ma), 1)
        self._test(Stats.wnonmissing, (one_element_ma,one_element_numeric), 1)
        self._test(Stats.wnonmissing, (one_element_numeric,one_element_ma), 1)
        self._test(Stats.wnonmissing, (one_element_numeric,one_neg_element_numeric), 1)
        self._test(Stats.wnonmissing, (one_element_ma,one_neg_element_numeric), 1)
        self._test(Stats.wnonmissing, (one_element_numeric,one_neg_element_ma), 1)
        self._test(Stats.wnonmissing, (one_element_ma,one_neg_element_ma), 1)
        self._test(Stats.wnonmissing, (one_masked_element_ma,one_element_ma), 0)
        self._test(Stats.wnonmissing, (one_masked_element_ma,one_neg_element_numeric), 0)
        self._test(Stats.wnonmissing, (one_element_ma,one_masked_element_ma), 0)
        self._test(Stats.wnonmissing, (all_neg_numeric,all_neg_numeric), 5)
        self._test(Stats.wnonmissing, (all_neg_numeric,all_neg_ma), 5)
        self._test(Stats.wnonmissing, (all_neg_ma,all_neg_numeric), 5)
        self._test(Stats.wnonmissing, (all_neg_ma,all_neg_ma), 5)

    def test_wnonmissing_misc_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wnonmissing, (empty_numeric,empty_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (empty_ma,empty_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (empty_numeric,empty_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (empty_ma,empty_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (populated_numeric,populated_numeric,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (populated_ma,populated_numeric,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (populated_numeric,populated_ma,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (populated_ma,populated_ma,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (populated_numeric,full_mask,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (populated_ma,full_mask,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (null_mask,null_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (null_mask,partial_mask,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (null_mask,full_mask,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (partial_mask,null_mask,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (partial_mask,partial_mask,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (partial_mask,full_mask,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (full_mask,null_mask,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (full_mask,partial_mask,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (full_mask,full_mask,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (two_elements_numeric,two_elements_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (two_elements_ma,two_elements_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_element_numeric,one_element_numeric,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_element_ma,one_element_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_element_ma,one_element_numeric,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_element_numeric,one_element_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_element_numeric,one_neg_element_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_element_ma,one_neg_element_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_element_numeric,one_neg_element_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_element_ma,one_neg_element_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_masked_element_ma,one_element_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_masked_element_ma,one_neg_element_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (one_element_ma,one_masked_element_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (all_neg_numeric,all_neg_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (all_neg_numeric,all_neg_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (all_neg_ma,all_neg_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (all_neg_ma,all_neg_ma,), 0, exclude_nonpositive_weights=True)

    def test_wnonmissing_1001(self):
        # now with 1001 element arrays
        self._test(Stats.wnonmissing, (n1001_nomissing_numpy,w1001_nomissing_numpy), 1001)
        self._test(Stats.wnonmissing, (n1001_nomissing_MA,w1001_nomissing_numpy), 1001)
        self._test(Stats.wnonmissing, (n1001_nomissing_numpy,w1001_nomissing_MA), 1001)
        self._test(Stats.wnonmissing, (n1001_nomissing_MA,w1001_nomissing_MA), 1001)
        self._test(Stats.wnonmissing, (n1001_missing,w1001_nomissing_numpy), 928)
        self._test(Stats.wnonmissing, (n1001_missing,w1001_nomissing_MA), 928)
        self._test(Stats.wnonmissing, (n1001_nomissing_numpy,w1001_missing), 963)
        self._test(Stats.wnonmissing, (n1001_nomissing_MA,w1001_missing), 963)
        self._test(Stats.wnonmissing, (n1001_missing,w1001_missing), 890)

    def test_wnonmissing_1001_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wnonmissing, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (n1001_nomissing_MA,w1001_nomissing_numpy,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (n1001_nomissing_numpy,w1001_nomissing_MA,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (n1001_nomissing_MA,w1001_nomissing_MA,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (n1001_missing,w1001_nomissing_numpy,), 919, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (n1001_missing,w1001_nomissing_MA,), 919, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (n1001_nomissing_numpy,w1001_missing,), 952, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (n1001_nomissing_MA,w1001_missing,), 952, exclude_nonpositive_weights=True)
        self._test(Stats.wnonmissing, (n1001_missing,w1001_missing,), 881, exclude_nonpositive_weights=True)

    def test_missing_misc(self):
        self._test(Stats.missing, empty_numeric, 0)
        self._test(Stats.missing, empty_ma, 0)
        self._test(Stats.missing, populated_numeric, 0)
        self._test(Stats.missing, populated_ma, 0)
        self._test(Stats.missing, null_mask, 0)
        self._test(Stats.missing, full_mask, 5)
        self._test(Stats.missing, partial_mask, 3)
        self._test(Stats.missing, two_elements_numeric, 0)
        self._test(Stats.missing, two_elements_ma, 0)
        self._test(Stats.missing, one_element_numeric, 0)
        self._test(Stats.missing, one_element_ma, 0)
        self._test(Stats.missing, one_neg_element_numeric, 0)
        self._test(Stats.missing, one_neg_element_ma, 0)
        self._test(Stats.missing, one_masked_element_ma, 1)
        self._test(Stats.missing, all_neg_numeric, 0)
        self._test(Stats.missing, all_neg_ma, 0)

    def test_wmissing_misc(self):
        self._test(Stats.wmissing, (empty_numeric,empty_numeric), 0)
        self._test(Stats.wmissing, (empty_ma,empty_numeric), 0)
        self._test(Stats.wmissing, (empty_numeric,empty_ma), 0)
        self._test(Stats.wmissing, (empty_ma,empty_ma), 0)
        self._test(Stats.wmissing, (populated_numeric,populated_numeric), 0)
        self._test(Stats.wmissing, (populated_ma,populated_numeric), 0)
        self._test(Stats.wmissing, (populated_numeric,populated_ma), 0)
        self._test(Stats.wmissing, (populated_ma,populated_ma), 0)
        self._test(Stats.wmissing, (populated_numeric,full_mask), 5)
        self._test(Stats.wmissing, (populated_ma,full_mask), 5)
        self._test(Stats.wmissing, (null_mask,null_mask), 0)
        self._test(Stats.wmissing, (null_mask,partial_mask), 3)
        self._test(Stats.wmissing, (null_mask,full_mask), 5)
        self._test(Stats.wmissing, (partial_mask,null_mask), 3)
        self._test(Stats.wmissing, (partial_mask,partial_mask), 3)
        self._test(Stats.wmissing, (partial_mask,full_mask), 5)
        self._test(Stats.wmissing, (full_mask,null_mask), 5)
        self._test(Stats.wmissing, (full_mask,partial_mask), 5)
        self._test(Stats.wmissing, (full_mask,full_mask), 5)
        self._test(Stats.wmissing, (two_elements_numeric,two_elements_numeric), 0)
        self._test(Stats.wmissing, (two_elements_ma,two_elements_numeric), 0)
        self._test(Stats.wmissing, (one_element_numeric,one_element_numeric), 0)
        self._test(Stats.wmissing, (one_element_ma,one_element_ma), 0)
        self._test(Stats.wmissing, (one_element_ma,one_element_numeric), 0)
        self._test(Stats.wmissing, (one_element_numeric,one_element_ma), 0)
        self._test(Stats.wmissing, (one_element_numeric,one_neg_element_numeric), 0)
        self._test(Stats.wmissing, (one_element_ma,one_neg_element_numeric), 0)
        self._test(Stats.wmissing, (one_element_numeric,one_neg_element_ma), 0)
        self._test(Stats.wmissing, (one_element_ma,one_neg_element_ma), 0)
        self._test(Stats.wmissing, (one_masked_element_ma,one_neg_element_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_ma,one_masked_element_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (all_neg_numeric,all_neg_numeric), 0)
        self._test(Stats.wmissing, (all_neg_numeric,all_neg_ma), 0)
        self._test(Stats.wmissing, (all_neg_ma,all_neg_numeric), 0)
        self._test(Stats.wmissing, (all_neg_ma,all_neg_ma), 0)

    # note that the results of wmissing() with exclude_nonpositive_weights=True differ from those
    # returned by SAS. This is because SAS distinguishes between excluded observations (excluded because they
    # have non-positive weights) and missing values. Thus, in SAS, with the EXCLNPWGTS option set,
    # the number of missing plus the number of non-missing observations does not equal the total number
    # of observations (because some are "excluded"). In NetEpi SOOOM, we don't distinguish between
    # missing and "excluded", or rather, we exclude observations by setting the data value to missing.
    
    def test_wmissing_misc_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wmissing, (empty_numeric,empty_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (empty_ma,empty_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (empty_numeric,empty_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (empty_ma,empty_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (populated_numeric,populated_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (populated_ma,populated_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (populated_numeric,populated_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (populated_ma,populated_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (populated_numeric,full_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (populated_ma,full_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (null_mask,null_mask,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (null_mask,partial_mask,), 3, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (null_mask,full_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (partial_mask,null_mask,), 3, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (partial_mask,partial_mask,), 3, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (partial_mask,full_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (full_mask,null_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (full_mask,partial_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (full_mask,full_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (two_elements_numeric,two_elements_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (two_elements_ma,two_elements_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_numeric,one_element_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_ma,one_element_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_ma,one_element_numeric,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_numeric,one_element_ma,), 0, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_numeric,one_neg_element_numeric,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_ma,one_neg_element_numeric,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_numeric,one_neg_element_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_ma,one_neg_element_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_masked_element_ma,one_neg_element_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (one_element_ma,one_masked_element_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (all_neg_numeric,all_neg_numeric,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (all_neg_numeric,all_neg_ma,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (all_neg_ma,all_neg_numeric,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (all_neg_ma,all_neg_ma,), 5, exclude_nonpositive_weights=True)

    def test_missing_1001(self):
        self._test(Stats.missing, n1001_nomissing_numpy, 0)
        self._test(Stats.missing, n1001_nomissing_MA, 0)
        self._test(Stats.missing, n1001_missing, 73)

    def test_missing_1006(self):
        self._test(Stats.missing, n1006_nomissing_numpy, 0)
        self._test(Stats.missing, n1006_nomissing_MA, 0)
        self._test(Stats.missing, n1006_missing, 73)

    def test_wmissing_1001(self):
        # now with 1001 element arrays
        self._test(Stats.wmissing, (n1001_nomissing_numpy,w1001_nomissing_numpy), 0)
        self._test(Stats.wmissing, (n1001_nomissing_MA,w1001_nomissing_numpy), 0)
        self._test(Stats.wmissing, (n1001_nomissing_numpy,w1001_nomissing_MA), 0)
        self._test(Stats.wmissing, (n1001_nomissing_MA,w1001_nomissing_MA), 0)
        self._test(Stats.wmissing, (n1001_missing,w1001_nomissing_numpy), 73)
        self._test(Stats.wmissing, (n1001_missing,w1001_nomissing_MA), 73)
        self._test(Stats.wmissing, (n1001_nomissing_numpy,w1001_missing), 38)
        self._test(Stats.wmissing, (n1001_nomissing_MA,w1001_missing), 38)
        self._test(Stats.wmissing, (n1001_missing,w1001_missing), 111)

    def test_wmissing_1001_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wmissing, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 11, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (n1001_nomissing_MA,w1001_nomissing_numpy,), 11, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (n1001_nomissing_numpy,w1001_nomissing_MA,), 11, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (n1001_nomissing_MA,w1001_nomissing_MA,), 11, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (n1001_missing,w1001_nomissing_numpy,), 82, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (n1001_missing,w1001_nomissing_MA,), 82, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (n1001_nomissing_numpy,w1001_missing,), 49, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (n1001_nomissing_MA,w1001_missing,), 49, exclude_nonpositive_weights=True)
        self._test(Stats.wmissing, (n1001_missing,w1001_missing,), 120, exclude_nonpositive_weights=True)

    def test_aminimum_misc(self):
        self._test(Stats.aminimum, empty_numeric, None)
        self._test(Stats.aminimum, empty_ma, None)
        self._test(Stats.aminimum, populated_numeric, 1)
        self._test(Stats.aminimum, populated_ma, 1)
        self._test(Stats.aminimum, null_mask, 1)
        self._test(Stats.aminimum, full_mask, None)
        self._test(Stats.aminimum, partial_mask, 2)
        self._test(Stats.aminimum, two_elements_numeric, 2)
        self._test(Stats.aminimum, two_elements_ma, 2)
        self._test(Stats.aminimum, one_element_numeric, 2)
        self._test(Stats.aminimum, one_element_ma, 2)
        self._test(Stats.aminimum, one_masked_element_ma, None)
        self._test(Stats.aminimum, one_neg_element_numeric, -2)
        self._test(Stats.aminimum, one_neg_element_ma, -2)
        self._test(Stats.aminimum, all_neg_numeric, -76)
        self._test(Stats.aminimum, all_neg_ma, -76)

    def test_wminimum_misc(self):
        self._test(Stats.wminimum, (empty_numeric,empty_numeric), None)
        self._test(Stats.wminimum, (empty_ma,empty_numeric), None)
        self._test(Stats.wminimum, (empty_numeric,empty_ma), None)
        self._test(Stats.wminimum, (empty_ma,empty_ma), None)
        self._test(Stats.wminimum, (populated_numeric,populated_numeric), 1)
        self._test(Stats.wminimum, (populated_ma,populated_numeric), 1)
        self._test(Stats.wminimum, (populated_numeric,populated_ma), 1)
        self._test(Stats.wminimum, (populated_ma,populated_ma), 1)
        self._test(Stats.wminimum, (populated_numeric,full_mask), None)
        self._test(Stats.wminimum, (populated_ma,full_mask), None)
        self._test(Stats.wminimum, (null_mask,null_mask), 1)
        self._test(Stats.wminimum, (null_mask,partial_mask), 2)
        self._test(Stats.wminimum, (null_mask,full_mask), None)
        self._test(Stats.wminimum, (partial_mask,null_mask), 2)
        self._test(Stats.wminimum, (partial_mask,partial_mask), 2)
        self._test(Stats.wminimum, (partial_mask,full_mask), None)
        self._test(Stats.wminimum, (full_mask,null_mask), None)
        self._test(Stats.wminimum, (full_mask,partial_mask), None)
        self._test(Stats.wminimum, (full_mask,full_mask), None)
        self._test(Stats.wminimum, (two_elements_numeric,two_elements_numeric), 2)
        self._test(Stats.wminimum, (two_elements_ma,two_elements_numeric), 2)
        self._test(Stats.wminimum, (one_element_numeric,one_element_numeric), 2)
        self._test(Stats.wminimum, (one_element_ma,one_element_ma), 2)
        self._test(Stats.wminimum, (one_element_ma,one_element_numeric), 2)
        self._test(Stats.wminimum, (one_element_numeric,one_element_ma), 2)
        self._test(Stats.wminimum, (one_element_numeric,one_neg_element_numeric), 2)
        self._test(Stats.wminimum, (one_element_ma,one_neg_element_numeric), 2)
        self._test(Stats.wminimum, (one_element_numeric,one_neg_element_ma), 2)
        self._test(Stats.wminimum, (one_element_ma,one_neg_element_ma), 2)
        self._test(Stats.wminimum, (one_masked_element_ma,one_neg_element_ma), None)
        self._test(Stats.wminimum, (one_element_ma,one_masked_element_ma), None)
        self._test(Stats.wminimum, (all_neg_numeric,all_neg_numeric), -76)
        self._test(Stats.wminimum, (all_neg_numeric,all_neg_ma), -76)
        self._test(Stats.wminimum, (all_neg_ma,all_neg_numeric), -76)
        self._test(Stats.wminimum, (all_neg_ma,all_neg_ma), -76)

    def test_wminimum_misc_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wminimum, (empty_numeric,empty_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (empty_ma,empty_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (empty_numeric,empty_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (empty_ma,empty_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (populated_numeric,populated_numeric,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (populated_ma,populated_numeric,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (populated_numeric,populated_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (populated_ma,populated_ma,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (populated_numeric,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (populated_ma,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (null_mask,null_mask,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (null_mask,partial_mask,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (null_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (partial_mask,null_mask,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (partial_mask,partial_mask,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (partial_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (full_mask,null_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (full_mask,partial_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (full_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_element_numeric,one_element_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_element_ma,one_element_ma,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_element_ma,one_element_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_element_numeric,one_element_ma,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_element_numeric,one_neg_element_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_element_ma,one_neg_element_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_element_numeric,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_element_ma,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_masked_element_ma,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (one_element_ma,one_masked_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (two_elements_numeric,two_elements_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (two_elements_ma,two_elements_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (all_neg_numeric,all_neg_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (all_neg_numeric,all_neg_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (all_neg_ma,all_neg_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (all_neg_ma,all_neg_ma,), None, exclude_nonpositive_weights=True)

    def test_aminimum_1001(self):
        self._test(Stats.aminimum, n1001_nomissing_numpy, -10)
        self._test(Stats.aminimum, n1001_nomissing_MA, -10)
        self._test(Stats.aminimum, n1001_missing, -10)

    def test_aminimum_1006(self):
        self._test(Stats.aminimum, n1006_nomissing_numpy, -10)
        self._test(Stats.aminimum, n1006_nomissing_MA, -10)
        self._test(Stats.aminimum, n1006_missing, -10)

    def test_wminimum_1001(self):
        # now with 1001 element arrays
        self._test(Stats.wminimum, (n1001_nomissing_numpy,w1001_nomissing_numpy), -10)
        self._test(Stats.wminimum, (n1001_nomissing_MA,w1001_nomissing_numpy), -10)
        self._test(Stats.wminimum, (n1001_nomissing_numpy,w1001_nomissing_MA), -10)
        self._test(Stats.wminimum, (n1001_nomissing_MA,w1001_nomissing_MA), -10)
        self._test(Stats.wminimum, (n1001_missing,w1001_nomissing_numpy), -10)
        self._test(Stats.wminimum, (n1001_missing,w1001_nomissing_MA), -10)
        self._test(Stats.wminimum, (n1001_nomissing_numpy,w1001_missing), -10)
        self._test(Stats.wminimum, (n1001_nomissing_MA,w1001_missing), -10)
        self._test(Stats.wminimum, (n1001_missing,w1001_missing), -10)

    def test_wminimum_1001_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wminimum, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (n1001_nomissing_MA,w1001_nomissing_numpy,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (n1001_nomissing_numpy,w1001_nomissing_MA,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (n1001_nomissing_MA,w1001_nomissing_MA,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (n1001_missing,w1001_nomissing_numpy,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (n1001_missing,w1001_nomissing_MA,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (n1001_nomissing_numpy,w1001_missing,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (n1001_nomissing_MA,w1001_missing,), 1, exclude_nonpositive_weights=True)
        self._test(Stats.wminimum, (n1001_missing,w1001_missing,), 1, exclude_nonpositive_weights=True)

    def test_amaximum_misc(self):
        self._test(Stats.amaximum, empty_numeric, None)
        self._test(Stats.amaximum, empty_ma, None)
        self._test(Stats.amaximum, populated_numeric, 5)
        self._test(Stats.amaximum, populated_ma, 5)
        self._test(Stats.amaximum, null_mask, 5)
        self._test(Stats.amaximum, full_mask, None)
        self._test(Stats.amaximum, partial_mask, 5)
        self._test(Stats.amaximum, two_elements_numeric, 5)
        self._test(Stats.amaximum, two_elements_ma, 5)
        self._test(Stats.amaximum, one_element_numeric, 2)
        self._test(Stats.amaximum, one_element_ma, 2)
        self._test(Stats.amaximum, one_masked_element_ma, None)
        self._test(Stats.amaximum, one_neg_element_numeric, -2)
        self._test(Stats.amaximum, one_neg_element_ma, -2)
        self._test(Stats.amaximum, all_neg_numeric, -2)
        self._test(Stats.amaximum, all_neg_ma, -2)

    def test_wmaximum_misc(self):
        self._test(Stats.wmaximum, (empty_numeric,empty_numeric), None)
        self._test(Stats.wmaximum, (empty_ma,empty_numeric), None)
        self._test(Stats.wmaximum, (empty_numeric,empty_ma), None)
        self._test(Stats.wmaximum, (empty_ma,empty_ma), None)
        self._test(Stats.wmaximum, (populated_numeric,populated_numeric), 5)
        self._test(Stats.wmaximum, (populated_ma,populated_numeric), 5)
        self._test(Stats.wmaximum, (populated_numeric,populated_ma), 5)
        self._test(Stats.wmaximum, (populated_ma,populated_ma), 5)
        self._test(Stats.wmaximum, (populated_numeric,full_mask), None)
        self._test(Stats.wmaximum, (populated_ma,full_mask), None)
        self._test(Stats.wmaximum, (null_mask,null_mask), 5)
        self._test(Stats.wmaximum, (null_mask,partial_mask), 5)
        self._test(Stats.wmaximum, (null_mask,full_mask), None)
        self._test(Stats.wmaximum, (partial_mask,null_mask), 5)
        self._test(Stats.wmaximum, (partial_mask,partial_mask), 5)
        self._test(Stats.wmaximum, (partial_mask,full_mask), None)
        self._test(Stats.wmaximum, (full_mask,null_mask), None)
        self._test(Stats.wmaximum, (full_mask,partial_mask), None)
        self._test(Stats.wmaximum, (full_mask,full_mask), None)
        self._test(Stats.wmaximum, (two_elements_numeric,two_elements_numeric), 5)
        self._test(Stats.wmaximum, (two_elements_ma,two_elements_numeric), 5)
        self._test(Stats.wmaximum, (one_element_numeric,one_element_numeric), 2)
        self._test(Stats.wmaximum, (one_element_ma,one_element_ma), 2)
        self._test(Stats.wmaximum, (one_element_ma,one_element_numeric), 2)
        self._test(Stats.wmaximum, (one_element_numeric,one_element_ma), 2)
        self._test(Stats.wmaximum, (one_element_numeric,one_neg_element_numeric), 2)
        self._test(Stats.wmaximum, (one_element_ma,one_neg_element_numeric), 2)
        self._test(Stats.wmaximum, (one_element_numeric,one_neg_element_ma), 2)
        self._test(Stats.wmaximum, (one_element_ma,one_neg_element_ma), 2)
        self._test(Stats.wmaximum, (one_masked_element_ma,one_neg_element_ma), None)
        self._test(Stats.wmaximum, (one_element_ma,one_masked_element_ma), None)
        self._test(Stats.wmaximum, (all_neg_numeric,all_neg_numeric), -2)
        self._test(Stats.wmaximum, (all_neg_numeric,all_neg_ma), -2)
        self._test(Stats.wmaximum, (all_neg_ma,all_neg_numeric), -2)
        self._test(Stats.wmaximum, (all_neg_ma,all_neg_ma), -2)

    def test_wmaximum_misc_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wmaximum, (empty_numeric,empty_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (empty_ma,empty_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (empty_numeric,empty_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (empty_ma,empty_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (populated_numeric,populated_numeric,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (populated_ma,populated_numeric,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (populated_numeric,populated_ma,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (populated_ma,populated_ma,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (populated_numeric,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (populated_ma,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (null_mask,null_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (null_mask,partial_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (null_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (partial_mask,null_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (partial_mask,partial_mask,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (partial_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (full_mask,null_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (full_mask,partial_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (full_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (two_elements_numeric,two_elements_numeric,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (two_elements_ma,two_elements_numeric,), 5, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_element_numeric,one_element_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_element_ma,one_element_ma,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_element_ma,one_element_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_element_numeric,one_element_ma,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_element_numeric,one_neg_element_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_element_ma,one_neg_element_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_element_numeric,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_element_ma,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_masked_element_ma,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (one_element_ma,one_masked_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (all_neg_numeric,all_neg_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (all_neg_numeric,all_neg_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (all_neg_ma,all_neg_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (all_neg_ma,all_neg_ma,), None, exclude_nonpositive_weights=True)

    def test_amaximum_1001(self):
        self._test(Stats.amaximum, n1001_nomissing_numpy, 990)
        self._test(Stats.amaximum, n1001_nomissing_MA, 990)
        self._test(Stats.amaximum, n1001_missing, 990)

    def test_amaximum_1006(self):
        self._test(Stats.amaximum, n1006_nomissing_numpy, 995)
        self._test(Stats.amaximum, n1006_nomissing_MA, 995)
        self._test(Stats.amaximum, n1006_missing, 995)

    def test_wmaximum_1001(self):
        # now with 1001 element arrays
        self._test(Stats.wmaximum, (n1001_nomissing_numpy,w1001_nomissing_numpy), 990)
        self._test(Stats.wmaximum, (n1001_nomissing_MA,w1001_nomissing_numpy), 990)
        self._test(Stats.wmaximum, (n1001_nomissing_numpy,w1001_nomissing_MA), 990)
        self._test(Stats.wmaximum, (n1001_nomissing_MA,w1001_nomissing_MA), 990)
        self._test(Stats.wmaximum, (n1001_missing,w1001_nomissing_numpy), 990)
        self._test(Stats.wmaximum, (n1001_missing,w1001_nomissing_MA), 990)
        self._test(Stats.wmaximum, (n1001_nomissing_numpy,w1001_missing), 990)
        self._test(Stats.wmaximum, (n1001_nomissing_MA,w1001_missing), 990)
        self._test(Stats.wmaximum, (n1001_missing,w1001_missing), 990)

    def test_wmaximum_1001_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wmaximum, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (n1001_nomissing_MA,w1001_nomissing_numpy,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (n1001_nomissing_numpy,w1001_nomissing_MA,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (n1001_nomissing_MA,w1001_nomissing_MA,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (n1001_missing,w1001_nomissing_numpy,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (n1001_missing,w1001_nomissing_MA,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (n1001_nomissing_numpy,w1001_missing,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (n1001_nomissing_MA,w1001_missing,), 990, exclude_nonpositive_weights=True)
        self._test(Stats.wmaximum, (n1001_missing,w1001_missing,), 990, exclude_nonpositive_weights=True)

    def test_asum_misc(self):
        self._test(Stats.asum, empty_numeric, None)
        self._test(Stats.asum, empty_ma, None)
        self._test(Stats.asum, populated_numeric, 14)
        self._test(Stats.asum, populated_ma, 14)
        self._test(Stats.asum, null_mask, 14)
        self._test(Stats.asum, full_mask, None)
        self._test(Stats.asum, partial_mask, 7)
        self._test(Stats.asum, two_elements_numeric, 7)
        self._test(Stats.asum, two_elements_ma, 7)
        self._test(Stats.asum, one_element_numeric, 2)
        self._test(Stats.asum, one_element_ma, 2)
        self._test(Stats.asum, one_masked_element_ma, None)
        self._test(Stats.asum, one_neg_element_numeric, -2)
        self._test(Stats.asum, one_neg_element_ma, -2)
        self._test(Stats.asum, all_neg_numeric, -90)
        self._test(Stats.asum, all_neg_ma, -90)

    def test_wsum_misc(self):
        self._test(Stats.wsum, (empty_numeric,empty_numeric), None)
        self._test(Stats.wsum, (empty_ma,empty_numeric), None)
        self._test(Stats.wsum, (empty_numeric,empty_ma), None)
        self._test(Stats.wsum, (empty_ma,empty_ma), None)
        self._test(Stats.wsum, (populated_numeric,populated_numeric), 48)
        self._test(Stats.wsum, (populated_ma,populated_numeric), 48)
        self._test(Stats.wsum, (populated_numeric,populated_ma), 48)
        self._test(Stats.wsum, (populated_ma,populated_ma), 48)
        self._test(Stats.wsum, (populated_numeric,full_mask), None)
        self._test(Stats.wsum, (populated_ma,full_mask), None)
        self._test(Stats.wsum, (null_mask,null_mask), 48)
        self._test(Stats.wsum, (null_mask,partial_mask), 29)
        self._test(Stats.wsum, (null_mask,full_mask), None)
        self._test(Stats.wsum, (partial_mask,null_mask), 29)
        self._test(Stats.wsum, (partial_mask,partial_mask), 29)
        self._test(Stats.wsum, (partial_mask,full_mask), None)
        self._test(Stats.wsum, (full_mask,null_mask), None)
        self._test(Stats.wsum, (full_mask,partial_mask), None)
        self._test(Stats.wsum, (full_mask,full_mask), None)
        self._test(Stats.wsum, (two_elements_numeric,two_elements_numeric), 29)
        self._test(Stats.wsum, (two_elements_ma,two_elements_numeric), 29)
        self._test(Stats.wsum, (one_element_numeric,one_element_numeric), 4)
        self._test(Stats.wsum, (one_element_ma,one_element_ma), 4)
        self._test(Stats.wsum, (one_element_ma,one_element_numeric), 4)
        self._test(Stats.wsum, (one_element_numeric,one_element_ma), 4)
        self._test(Stats.wsum, (one_element_numeric,one_neg_element_numeric), 0)
        self._test(Stats.wsum, (one_element_ma,one_neg_element_numeric), 0)
        self._test(Stats.wsum, (one_element_numeric,one_neg_element_ma), 0)
        self._test(Stats.wsum, (one_element_ma,one_neg_element_ma), 0)
        self._test(Stats.wsum, (one_masked_element_ma,one_neg_element_ma), None)
        self._test(Stats.wsum, (one_element_ma,one_masked_element_ma), None)
        self._test(Stats.wsum, (all_neg_numeric,all_neg_numeric), 0)
        self._test(Stats.wsum, (all_neg_numeric,all_neg_ma), 0)
        self._test(Stats.wsum, (all_neg_ma,all_neg_numeric), 0)
        self._test(Stats.wsum, (all_neg_ma,all_neg_ma), 0)

    def test_wsum_misc_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wsum, (empty_numeric,empty_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (empty_ma,empty_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (empty_numeric,empty_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (empty_ma,empty_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (populated_numeric,populated_numeric,), 48, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (populated_ma,populated_numeric,), 48, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (populated_numeric,populated_ma,), 48, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (populated_ma,populated_ma,), 48, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (populated_numeric,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (populated_ma,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (null_mask,null_mask,), 48, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (null_mask,partial_mask,), 29, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (null_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (partial_mask,null_mask,), 29, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (partial_mask,partial_mask,), 29, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (partial_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (full_mask,null_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (full_mask,partial_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (full_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (two_elements_numeric,two_elements_numeric,), 29, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (two_elements_ma,two_elements_numeric,), 29, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (one_element_numeric,one_element_numeric,), 4, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (one_element_ma,one_element_ma,), 4, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (one_element_ma,one_element_numeric,), 4, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (one_element_numeric,one_element_ma,), 4, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (one_element_numeric,one_neg_element_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (one_element_ma,one_neg_element_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (one_element_numeric,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (one_element_ma,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (one_masked_element_ma,one_neg_element_ma), None)
        self._test(Stats.wsum, (one_element_ma,one_masked_element_ma), None)
        self._test(Stats.wsum, (all_neg_numeric,all_neg_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (all_neg_numeric,all_neg_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (all_neg_ma,all_neg_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (all_neg_ma,all_neg_ma,), None, exclude_nonpositive_weights=True)

    def test_asum_1001(self):
        self._test(Stats.asum, n1001_nomissing_numpy, 490490)
        self._test(Stats.asum, n1001_nomissing_MA, 490490)
        self._test(Stats.asum, n1001_missing, 472605)

    def test_asum_1006(self):
        self._test(Stats.asum, n1006_nomissing_numpy, 495455)
        self._test(Stats.asum, n1006_nomissing_MA, 495455)
        self._test(Stats.asum, n1006_missing, 477570)

    def test_wsum_1001(self):
        # now with 1001 element arrays
        self._test(Stats.wsum, (n1001_nomissing_numpy,w1001_nomissing_numpy), 107974405)
        self._test(Stats.wsum, (n1001_nomissing_MA,w1001_nomissing_numpy), 107974405)
        self._test(Stats.wsum, (n1001_nomissing_numpy,w1001_nomissing_MA), 107974405)
        self._test(Stats.wsum, (n1001_nomissing_MA,w1001_nomissing_MA), 107974405)
        self._test(Stats.wsum, (n1001_missing,w1001_nomissing_numpy), 105984417)
        self._test(Stats.wsum, (n1001_missing,w1001_nomissing_MA), 105984417)
        self._test(Stats.wsum, (n1001_nomissing_numpy,w1001_missing), 100639410.6667)
        self._test(Stats.wsum, (n1001_nomissing_MA,w1001_missing), 100639410.6667)
        self._test(Stats.wsum, (n1001_missing,w1001_missing), 98649422.6667)

    def test_wsum_1001_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wsum, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 107974405, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (n1001_nomissing_MA,w1001_nomissing_numpy,), 107974405, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (n1001_nomissing_numpy,w1001_nomissing_MA,), 107974405, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (n1001_nomissing_MA,w1001_nomissing_MA,), 107974405, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (n1001_missing,w1001_nomissing_numpy,), 105984417, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (n1001_missing,w1001_nomissing_MA,), 105984417, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (n1001_nomissing_numpy,w1001_missing,), 100639410.6667, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (n1001_nomissing_MA,w1001_missing,), 100639410.6667, exclude_nonpositive_weights=True)
        self._test(Stats.wsum, (n1001_missing,w1001_missing,), 98649422.6667, exclude_nonpositive_weights=True)

    def test_amean_misc(self):
        self._test(Stats.amean, empty_numeric, None)
        self._test(Stats.amean, empty_ma, None)
        self._test(Stats.amean, populated_numeric, 2.8)
        self._test(Stats.amean, populated_ma, 2.8)
        self._test(Stats.amean, null_mask, 2.8)
        self._test(Stats.amean, full_mask, None)
        self._test(Stats.amean, partial_mask, 3.5)
        self._test(Stats.amean, two_elements_numeric, 3.5)
        self._test(Stats.amean, two_elements_ma, 3.5)
        self._test(Stats.amean, one_element_numeric, 2)
        self._test(Stats.amean, one_element_ma, 2)
        self._test(Stats.amean, one_masked_element_ma, None)
        self._test(Stats.amean, one_neg_element_numeric, -2)
        self._test(Stats.amean, one_neg_element_ma, -2)
        self._test(Stats.amean, all_neg_numeric, -18)
        self._test(Stats.amean, all_neg_ma, -18)

    def test_wamean_misc(self):
        self._test(Stats.wamean, (empty_numeric,empty_numeric), None)
        self._test(Stats.wamean, (empty_ma,empty_numeric), None)
        self._test(Stats.wamean, (empty_numeric,empty_ma), None)
        self._test(Stats.wamean, (empty_ma,empty_ma), None)
        self._test(Stats.wamean, (populated_numeric,populated_numeric), 3.42857142857)
        self._test(Stats.wamean, (populated_ma,populated_numeric), 3.42857142857)
        self._test(Stats.wamean, (populated_numeric,populated_ma), 3.42857142857)
        self._test(Stats.wamean, (populated_ma,populated_ma), 3.42857142857)
        self._test(Stats.wamean, (populated_numeric,full_mask), None)
        self._test(Stats.wamean, (populated_ma,full_mask), None)
        self._test(Stats.wamean, (null_mask,null_mask), 3.42857142857)
        self._test(Stats.wamean, (null_mask,partial_mask), 4.142857142)
        self._test(Stats.wamean, (null_mask,full_mask), None)
        self._test(Stats.wamean, (partial_mask,null_mask), 4.142857142)
        self._test(Stats.wamean, (partial_mask,partial_mask), 4.142857142)
        self._test(Stats.wamean, (partial_mask,full_mask), None)
        self._test(Stats.wamean, (full_mask,null_mask), None)
        self._test(Stats.wamean, (full_mask,partial_mask), None)
        self._test(Stats.wamean, (full_mask,full_mask), None)
        self._test(Stats.wamean, (two_elements_numeric,two_elements_numeric), 4.142857142)
        self._test(Stats.wamean, (two_elements_ma,two_elements_numeric), 4.142857142)
        self._test(Stats.wamean, (one_element_numeric,one_element_numeric), 2)
        self._test(Stats.wamean, (one_element_ma,one_element_ma), 2)
        self._test(Stats.wamean, (one_element_ma,one_element_numeric), 2)
        self._test(Stats.wamean, (one_element_numeric,one_element_ma), 2)
        self._test(Stats.wamean, (one_element_numeric,one_neg_element_numeric), None)
        self._test(Stats.wamean, (one_element_ma,one_neg_element_numeric), None)
        self._test(Stats.wamean, (one_element_numeric,one_neg_element_ma), None)
        self._test(Stats.wamean, (one_element_ma,one_neg_element_ma), None)
        self._test(Stats.wamean, (one_masked_element_ma,one_neg_element_ma), None)
        self._test(Stats.wamean, (one_element_ma,one_masked_element_ma), None)
        self._test(Stats.wamean, (all_neg_numeric,all_neg_numeric), None)
        self._test(Stats.wamean, (all_neg_numeric,all_neg_ma), None)
        self._test(Stats.wamean, (all_neg_ma,all_neg_numeric), None)
        self._test(Stats.wamean, (all_neg_ma,all_neg_ma), None)

    def test_wamean_misc_exclnpwgts(self):
        # repeat with exclude_nonpositive_weights=True
        self._test(Stats.wamean, (empty_numeric,empty_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (empty_ma,empty_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (empty_numeric,empty_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (empty_ma,empty_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (populated_numeric,populated_numeric,), 3.42857142857, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (populated_ma,populated_numeric,), 3.42857142857, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (populated_numeric,populated_ma,), 3.42857142857, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (populated_ma,populated_ma,), 3.42857142857, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (populated_numeric,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (populated_ma,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (null_mask,null_mask,), 3.42857142857, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (null_mask,partial_mask,), 4.142857142, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (null_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (partial_mask,null_mask,), 4.142857142, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (partial_mask,partial_mask,), 4.142857142, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (partial_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (full_mask,null_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (full_mask,partial_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (full_mask,full_mask,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (two_elements_numeric,two_elements_numeric,), 4.142857142, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (two_elements_ma,two_elements_numeric,), 4.142857142, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_element_numeric,one_element_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_element_ma,one_element_ma,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_element_ma,one_element_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_element_numeric,one_element_ma,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_element_numeric,one_neg_element_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_element_ma,one_neg_element_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_element_numeric,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_element_ma,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_masked_element_ma,one_neg_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (one_element_ma,one_masked_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (all_neg_numeric,all_neg_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (all_neg_numeric,all_neg_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (all_neg_ma,all_neg_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (all_neg_ma,all_neg_ma,), None, exclude_nonpositive_weights=True)

    def test_amean_1001(self):
        self._test(Stats.amean, n1001_nomissing_numpy, 490.0)
        self._test(Stats.amean, n1001_nomissing_MA, 490.0)
        self._test(Stats.amean, n1001_missing, 509.272629)

    def test_amean_1006(self):
        self._test(Stats.amean, n1006_nomissing_numpy, 492.5)
        self._test(Stats.amean, n1006_nomissing_MA, 492.5)
        self._test(Stats.amean, n1006_missing, 511.865)

    def test_ameancl_1001(self):
        self._stricttest(Stats.ameancl, n1001_nomissing_numpy, (490.0,472.0684723242,507.9315276758))
        self._stricttest(Stats.ameancl, n1001_nomissing_MA, (490.0,472.0684723242,507.9315276758))
        self._stricttest(Stats.ameancl, n1001_missing, (509.2726293103,490.6730245555,527.8722340652))

    def test_ameancl_1006(self):
        self._stricttest(Stats.ameancl, n1006_nomissing_numpy, (492.5,474.5238970310,510.4761029690))
        self._stricttest(Stats.ameancl, n1006_nomissing_MA, (492.5,474.5238970310,510.4761029690))
        self._stricttest(Stats.ameancl, n1006_missing, (511.8649517686,493.2264201498,530.5034833872))

    def test_wamean_1001(self):
        # now with 1001 element arrays
        self._test(Stats.wamean, (n1001_nomissing_numpy,w1001_nomissing_numpy), 660.3333)
        self._test(Stats.wamean, (n1001_nomissing_MA,w1001_nomissing_numpy), 660.3333)
        self._test(Stats.wamean, (n1001_nomissing_numpy,w1001_nomissing_MA), 660.3333)
        self._test(Stats.wamean, (n1001_nomissing_MA,w1001_nomissing_MA), 660.3333)
        self._test(Stats.wamean, (n1001_missing,w1001_nomissing_numpy), 672.699107)
        self._test(Stats.wamean, (n1001_missing,w1001_nomissing_MA), 672.699107)
        self._test(Stats.wamean, (n1001_nomissing_numpy,w1001_missing), 653.304695547)
        self._test(Stats.wamean, (n1001_nomissing_MA,w1001_missing), 653.304695547)
        self._test(Stats.wamean, (n1001_missing,w1001_missing),  666.1780537)

    def test_wamean_1001_exclnpwgts(self):
        # repeat with, exclude_nonpositive_weights=True 
        self._test(Stats.wamean, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 660.3333, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (n1001_nomissing_MA,w1001_nomissing_numpy,), 660.3333, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (n1001_nomissing_numpy,w1001_nomissing_MA,), 660.3333, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (n1001_nomissing_MA,w1001_nomissing_MA,), 660.3333, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (n1001_missing,w1001_nomissing_numpy,), 672.699107, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (n1001_missing,w1001_nomissing_MA,), 672.699107, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (n1001_nomissing_numpy,w1001_missing,), 653.304695547, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (n1001_nomissing_MA,w1001_missing,), 653.304695547, exclude_nonpositive_weights=True)
        self._test(Stats.wamean, (n1001_missing,w1001_missing,),  666.1780537, exclude_nonpositive_weights=True)

    # Note that the following values have NOT been checked against SAS because SAS v8.2 does not produce conf limits
    # for weighted means (despite the SAS documentation giving the formula to be used). However, the values appear to
    # be correct, at least nominally. They have been checked against SAS PROC SURVEYMEANS using no CLASS or STRATA
    # and the confidence limits are very nearly the same, but not identical (at the third decimal place) - probably
    # due to computation issues due to the use of taylor series expansion to calculate the standard error in 
    # PROC SURVEYMEANS.
    def test_wameancl_1001(self):
        # now with 1001 element arrays
        self._stricttest(Stats.wameancl, (n1001_nomissing_numpy,w1001_nomissing_numpy), (660.33333333332018, 645.84588892710951, 674.82077773953085))
        self._stricttest(Stats.wameancl, (n1001_nomissing_MA,w1001_nomissing_numpy), (660.33333333332018, 645.84588892710951, 674.82077773953085))
        self._stricttest(Stats.wameancl, (n1001_nomissing_numpy,w1001_nomissing_MA), (660.33333333332018, 645.84588892710951, 674.82077773953085))
        self._stricttest(Stats.wameancl, (n1001_nomissing_MA,w1001_nomissing_MA), (660.33333333332018, 645.84588892710951, 674.82077773953085))
        self._stricttest(Stats.wameancl, (n1001_missing,w1001_nomissing_numpy), (672.69910695583076, 658.02179536228903, 687.37641854937249))
        self._stricttest(Stats.wameancl, (n1001_missing,w1001_nomissing_MA), (672.69910695583076, 658.02179536228903, 687.37641854937249))
        self._stricttest(Stats.wameancl, (n1001_nomissing_numpy,w1001_missing), (653.30469554679121, 638.35896025595366, 668.25043083762876))
        self._stricttest(Stats.wameancl, (n1001_nomissing_MA,w1001_missing), (653.30469554679121, 638.35896025595366, 668.25043083762876))
        self._stricttest(Stats.wameancl, (n1001_missing,w1001_missing),  (666.17805369972359, 650.9948410875752, 681.36126631187199))

    def test_ameancl_misc(self):
        self._stricttest(Stats.ameancl, empty_numeric, (None,None,None))
        self._stricttest(Stats.ameancl, empty_ma, (None,None,None))
        self._stricttest(Stats.ameancl, populated_numeric, (2.8,0.9583146670,4.6416853330))
        self._stricttest(Stats.ameancl, populated_ma, (2.8,0.9583146670,4.6416853330))
        self._stricttest(Stats.ameancl, null_mask, (2.8,0.9583146670,4.6416853330))
        self._stricttest(Stats.ameancl, full_mask, (None,None,None))
        self._stricttest(Stats.ameancl, partial_mask, (3.5,-15.5593071043,22.5593071043))
        self._stricttest(Stats.ameancl, two_elements_numeric, (3.5,-15.5593071043,22.5593071043))
        self._stricttest(Stats.ameancl, two_elements_ma, (3.5,-15.5593071043,22.5593071043))
        self._stricttest(Stats.ameancl, one_element_numeric, (2,None,None))
        self._stricttest(Stats.ameancl, one_element_ma, (2,None,None))
        self._stricttest(Stats.ameancl, one_masked_element_ma, (None,None,None))
        self._stricttest(Stats.ameancl, one_neg_element_numeric, (-2,None,None))
        self._stricttest(Stats.ameancl, one_neg_element_ma, (-2,None,None))
        self._stricttest(Stats.ameancl, all_neg_numeric, (-18,-58.2823817862,22.2823817862))
        self._stricttest(Stats.ameancl, all_neg_ma, (-18,-58.2823817862,22.2823817862))

    def test_wameancl_misc(self):
        self._stricttest(Stats.wameancl, (empty_numeric,empty_numeric), (None,None,None))
        self._stricttest(Stats.wameancl, (empty_ma,empty_numeric), (None,None,None))
        self._stricttest(Stats.wameancl, (empty_numeric,empty_ma), (None,None,None))
        self._stricttest(Stats.wameancl, (empty_ma,empty_ma), (None,None,None))
        self._stricttest(Stats.wameancl, (populated_numeric,populated_numeric), (3.4285714285714284, 1.6327300183955371, 5.2244128387473197))
        self._stricttest(Stats.wameancl, (populated_ma,populated_numeric), (3.4285714285714284, 1.6327300183955371, 5.2244128387473197))
        self._stricttest(Stats.wameancl, (populated_numeric,populated_ma), (3.4285714285714284, 1.6327300183955371, 5.2244128387473197))
        self._stricttest(Stats.wameancl, (populated_ma,populated_ma), (3.4285714285714284, 1.6327300183955371, 5.2244128387473197))
        self._stricttest(Stats.wameancl, (populated_numeric,full_mask), (None,None,None))
        self._stricttest(Stats.wameancl, (populated_ma,full_mask), (None,None,None))
        self._stricttest(Stats.wameancl, (null_mask,null_mask), (3.4285714285714284, 1.6327300183955371, 5.2244128387473197))
        self._stricttest(Stats.wameancl, (null_mask,partial_mask), (4.1428571428571432, -13.077377449741839, 21.363091735456123))
        self._stricttest(Stats.wameancl, (null_mask,full_mask), (None,None,None))
        self._stricttest(Stats.wameancl, (partial_mask,null_mask),(4.1428571428571432, -13.077377449741839, 21.363091735456123) )
        self._stricttest(Stats.wameancl, (partial_mask,partial_mask), (4.1428571428571432, -13.077377449741839, 21.363091735456123))
        self._stricttest(Stats.wameancl, (partial_mask,full_mask), (None,None,None))
        self._stricttest(Stats.wameancl, (full_mask,null_mask), (None,None,None))
        self._stricttest(Stats.wameancl, (full_mask,partial_mask), (None,None,None))
        self._stricttest(Stats.wameancl, (full_mask,full_mask), (None,None,None))
        self._stricttest(Stats.wameancl, (two_elements_numeric,two_elements_numeric), (4.1428571428571432, -13.077377449741839, 21.363091735456123))
        self._stricttest(Stats.wameancl, (two_elements_ma,two_elements_numeric), (4.1428571428571432, -13.077377449741839, 21.363091735456123))
        self._stricttest(Stats.wameancl, (one_element_numeric,one_element_numeric), (2,None,None))
        self._stricttest(Stats.wameancl, (one_element_ma,one_element_ma), (2,None,None))
        self._stricttest(Stats.wameancl, (one_element_ma,one_element_numeric), (2,None,None))
        self._stricttest(Stats.wameancl, (one_element_numeric,one_element_ma), (2,None,None))
        self._stricttest(Stats.wameancl, (one_element_numeric,one_neg_element_numeric), (None,None,None))
        self._stricttest(Stats.wameancl, (one_element_ma,one_neg_element_numeric), (None,None,None))
        self._stricttest(Stats.wameancl, (one_element_numeric,one_neg_element_ma), (None,None,None))
        self._stricttest(Stats.wameancl, (one_element_ma,one_neg_element_ma), (None,None,None))
        self._stricttest(Stats.wameancl, (one_masked_element_ma,one_neg_element_ma), (None,None,None))
        self._stricttest(Stats.wameancl, (one_element_ma,one_masked_element_ma), (None,None,None))
        self._stricttest(Stats.wameancl, (all_neg_numeric,all_neg_numeric), (None,None,None))
        self._stricttest(Stats.wameancl, (all_neg_numeric,all_neg_ma), (None,None,None))
        self._stricttest(Stats.wameancl, (all_neg_ma,all_neg_numeric), (None,None,None))
        self._stricttest(Stats.wameancl, (all_neg_ma,all_neg_ma), (None,None,None))

    # To-Do: test for arange and wrange required!

    # To-Do: more tests for geomean are required here.
    def test_geomean(self):
        self._test(Stats.geomean, empty_numeric, None)
        self._test(Stats.geomean, empty_ma, None)
        self._test(Stats.geomean, populated_numeric, 2.4595)
        self._test(Stats.geomean, populated_ma, 2.4595)
        self._test(Stats.geomean, null_mask, 2.4595)
        self._test(Stats.geomean, full_mask, None)
        self._test(Stats.geomean, partial_mask, 3.1623)

    def test_median_empty(self):
        # with exclude_nonpositive_weights = False
        self._test(Stats.median, (empty_numeric,1), None)
        self._test(Stats.median, (empty_numeric,2), None)
        self._test(Stats.median, (empty_numeric,3), None)
        self._test(Stats.median, (empty_numeric,4), None)
        self._test(Stats.median, (empty_numeric,5), None)

        self._test(Stats.median, (empty_ma,1), None)
        self._test(Stats.median, (empty_ma,2), None)
        self._test(Stats.median, (empty_ma,3), None)
        self._test(Stats.median, (empty_ma,4), None)
        self._test(Stats.median, (empty_ma,5), None)

    def test_wmedian_empty(self):
        self._test(Stats.wmedian, (empty_numeric,empty_numeric)  , None)
        self._test(Stats.wmedian, (empty_numeric,empty_ma)  , None)
        self._test(Stats.wmedian, (empty_ma,empty_numeric)  , None)
        self._test(Stats.wmedian, (empty_ma,empty_ma)  , None)

        self._test(Stats.wmedian, (populated_numeric,full_mask)  , None)
        self._test(Stats.wmedian, (populated_ma,full_mask)  , None)

        self._test(Stats.wmedian, (populated_numeric,all_neg_numeric)  , None)
        self._test(Stats.wmedian, (populated_numeric,all_neg_numeric)  , None)

    def test_median_misc(self):
        self._test(Stats.median, (one_element_numeric,1), 2)
        self._test(Stats.median, (one_element_ma,1), 2)
        self._test(Stats.median, (one_masked_element_ma,1), None)
        self._test(Stats.median, (one_neg_element_numeric,1), -2)
        self._test(Stats.median, (one_neg_element_ma,1), -2)

        self._test(Stats.median, (one_element_numeric,2), 2)
        self._test(Stats.median, (one_element_ma,2), 2)
        self._test(Stats.median, (one_masked_element_ma,2), None)
        self._test(Stats.median, (one_neg_element_numeric,2), -2)
        self._test(Stats.median, (one_neg_element_ma,2), -2)

        self._test(Stats.median, (one_element_numeric,3), 2)
        self._test(Stats.median, (one_element_ma,3), 2)
        self._test(Stats.median, (one_masked_element_ma,3), None)
        self._test(Stats.median, (one_neg_element_numeric,3), -2)
        self._test(Stats.median, (one_neg_element_ma,3), -2)

        self._test(Stats.median, (one_element_numeric,4), 2)
        self._test(Stats.median, (one_element_ma,4), 2)
        self._test(Stats.median, (one_masked_element_ma,4), None)
        self._test(Stats.median, (one_neg_element_numeric,4), -2)
        self._test(Stats.median, (one_neg_element_ma,4), -2)

        self._test(Stats.median, (one_element_numeric,5), 2)
        self._test(Stats.median, (one_element_ma,5), 2)
        self._test(Stats.median, (one_masked_element_ma,5), None)
        self._test(Stats.median, (one_neg_element_numeric,5), -2)
        self._test(Stats.median, (one_neg_element_ma,5), -2)

    def test_median_misc_exclnpwgts(self):
        self._test(Stats.median, (one_element_numeric,1,), 2)
        self._test(Stats.median, (one_element_ma,1,), 2)
        self._test(Stats.median, (one_masked_element_ma,1,), None)
        self._test(Stats.median, (one_neg_element_numeric,1,), -2)
        self._test(Stats.median, (one_neg_element_ma,1,), -2)

        self._test(Stats.median, (one_element_numeric,2,), 2)
        self._test(Stats.median, (one_element_ma,2,), 2)
        self._test(Stats.median, (one_masked_element_ma,2,), None)
        self._test(Stats.median, (one_neg_element_numeric,2,), -2)
        self._test(Stats.median, (one_neg_element_ma,2,), -2)

        self._test(Stats.median, (one_element_numeric,3,), 2)
        self._test(Stats.median, (one_element_ma,3,), 2)
        self._test(Stats.median, (one_masked_element_ma,3,), None)
        self._test(Stats.median, (one_neg_element_numeric,3,), -2)
        self._test(Stats.median, (one_neg_element_ma,3,), -2)

        self._test(Stats.median, (one_element_numeric,4,), 2)
        self._test(Stats.median, (one_element_ma,4,), 2)
        self._test(Stats.median, (one_masked_element_ma,4,), None)
        self._test(Stats.median, (one_neg_element_numeric,4,), -2)
        self._test(Stats.median, (one_neg_element_ma,4,), -2)

        self._test(Stats.median, (one_element_numeric,5,), 2)
        self._test(Stats.median, (one_element_ma,5,), 2)
        self._test(Stats.median, (one_masked_element_ma,5,), None)
        self._test(Stats.median, (one_neg_element_numeric,5,), -2)
        self._test(Stats.median, (one_neg_element_ma,5,), -2)

    def test_wmedian_misc(self):
        self._test(Stats.wmedian, (one_element_numeric,one_element_numeric), 2)
        self._test(Stats.wmedian, (one_element_ma,one_element_numeric), 2)
        self._test(Stats.wmedian, (one_element_numeric,one_element_ma), 2)
        self._test(Stats.wmedian, (one_element_ma,one_element_ma), 2)
        self._test(Stats.wmedian, (one_masked_element_ma,one_element_numeric), None)
        self._test(Stats.wmedian, (one_masked_element_ma,one_element_ma), None)
        self._test(Stats.wmedian, (one_masked_element_ma,one_masked_element_ma), None)
        self._test(Stats.wmedian, (one_neg_element_numeric,one_element_ma), -2)
        self._test(Stats.wmedian, (one_neg_element_numeric,one_element_numeric), -2)
        self._test(Stats.wmedian, (one_neg_element_ma,one_element_ma), -2)
        self._test(Stats.wmedian, (one_neg_element_ma,one_element_numeric), -2)
        self._test(Stats.wmedian, (one_neg_element_ma,one_neg_element_ma), -2)

    def test_wmedian_misc_exclnpwgts(self):
        self._test(Stats.wmedian, (one_element_numeric,one_element_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_element_ma,one_element_numeric,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_element_numeric,one_element_ma,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_element_ma,one_element_ma,), 2, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_masked_element_ma,one_element_numeric,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_masked_element_ma,one_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_masked_element_ma,one_masked_element_ma,), None, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_neg_element_numeric,one_element_ma,), -2, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_neg_element_numeric,one_element_numeric,), -2, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_neg_element_ma,one_element_ma,), -2, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_neg_element_ma,one_element_numeric,), -2, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (one_neg_element_ma,one_neg_element_ma,), None, exclude_nonpositive_weights=True)

    def test_median_nonmissing_odd(self):
        self._test(Stats.median, (n1001_nomissing_numpy,1)  , 489.5)
        self._test(Stats.median, (n1001_nomissing_numpy,2)  , 489.0)
        self._test(Stats.median, (n1001_nomissing_numpy,3)  , 490.0)
        self._test(Stats.median, (n1001_nomissing_numpy,4)  , 490.0)
        self._test(Stats.median, (n1001_nomissing_numpy,5)  , 490.0)

        self._test(Stats.median, (n1001_nomissing_MA,1)  , 489.5)
        self._test(Stats.median, (n1001_nomissing_MA,2)  , 489.0)
        self._test(Stats.median, (n1001_nomissing_MA,3)  , 490.0)
        self._test(Stats.median, (n1001_nomissing_MA,4)  , 490.0)
        self._test(Stats.median, (n1001_nomissing_MA,5)  , 490.0)

    def test_wmedian_nonmissing_odd(self):
        self._test(Stats.wmedian, (n1001_nomissing_numpy,w1001_nomissing_numpy)  , 700.0)
        self._test(Stats.wmedian, (n1001_nomissing_numpy,w1001_nomissing_MA)  , 700.0)
        self._test(Stats.wmedian, (n1001_nomissing_numpy,w1001_missing)  , 693.0)
        self._test(Stats.wmedian, (n1001_nomissing_MA,w1001_nomissing_numpy)  , 700.0)
        self._test(Stats.wmedian, (n1001_nomissing_MA,w1001_nomissing_MA)  , 700.0)
        self._test(Stats.wmedian, (n1001_nomissing_MA,w1001_missing)  , 693.0)

    def test_median_nonmissing_even(self):
        self._test(Stats.median, (n1006_nomissing_numpy,1)  , 492.0)
        self._test(Stats.median, (n1006_nomissing_numpy,2)  , 492.0)
        self._test(Stats.median, (n1006_nomissing_numpy,3)  , 492.0)
        self._test(Stats.median, (n1006_nomissing_numpy,4)  , 492.5)
        self._test(Stats.median, (n1006_nomissing_numpy,5)  , 492.5)

        self._test(Stats.median, (n1006_nomissing_MA,1)  , 492.0)
        self._test(Stats.median, (n1006_nomissing_MA,2)  , 492.0)
        self._test(Stats.median, (n1006_nomissing_MA,3)  , 492.0)
        self._test(Stats.median, (n1006_nomissing_MA,4)  , 492.5)
        self._test(Stats.median, (n1006_nomissing_MA,5)  , 492.5)

    def test_wmedian_nonmissing_even(self):
        self._test(Stats.wmedian, (n1006_nomissing_numpy,w1006_nomissing_numpy)  , 704.0)
        self._test(Stats.wmedian, (n1006_nomissing_numpy,w1006_nomissing_MA)  , 704.0)
        self._test(Stats.wmedian, (n1006_nomissing_numpy,w1006_missing)  , 696.0)
        self._test(Stats.wmedian, (n1006_nomissing_MA,w1006_nomissing_numpy)  , 704.0)
        self._test(Stats.wmedian, (n1006_nomissing_MA,w1006_nomissing_MA)  , 704.0)
        self._test(Stats.wmedian, (n1006_nomissing_MA,w1006_missing)  , 696.0)

    def test_median_nonmissing_odd(self):
        self._test(Stats.median, (n1001_missing,1)  , 526.0)
        self._test(Stats.median, (n1001_missing,2)  , 526.0)
        self._test(Stats.median, (n1001_missing,3)  , 526.0)
        self._test(Stats.median, (n1001_missing,4)  , 526.5)
        self._test(Stats.median, (n1001_missing,5)  , 526.5)

    def test_median_nonmissing_even(self):
        self._test(Stats.median, (n1006_missing,1)  , 528.5)
        self._test(Stats.median, (n1006_missing,2)  , 528.0)
        self._test(Stats.median, (n1006_missing,3)  , 529.0)
        self._test(Stats.median, (n1006_missing,4)  , 529.0)
        self._test(Stats.median, (n1006_missing,5)  , 529.0)

    def test_wmedian_nonmissing_odd(self):
        self._test(Stats.wmedian, (n1001_missing,w1001_nomissing_numpy)  , 713.0)
        self._test(Stats.wmedian, (n1001_missing,w1001_nomissing_MA)  , 713.0)
        self._test(Stats.wmedian, (n1001_missing,w1001_missing)  , 707.0)

    def test_wmedian_nonmissing_even(self):
        self._test(Stats.wmedian, (n1006_missing,w1006_nomissing_numpy)  , 717.0)
        self._test(Stats.wmedian, (n1006_missing,w1006_nomissing_MA)  , 717.0)
        self._test(Stats.wmedian, (n1006_missing,w1006_missing)  , 710.0)

        # with exclude_nonpositive_weights = True
    def test_wmedian_nonmissing_odd_exclnpwgts(self):
        self._test(Stats.wmedian, (n1001_nomissing_numpy,w1001_nomissing_numpy,)  , 700.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1001_nomissing_numpy,w1001_nomissing_MA,)  , 700.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1001_nomissing_numpy,w1001_missing,)  , 693.0, exclude_nonpositive_weights=True)

        self._test(Stats.wmedian, (n1001_nomissing_MA,w1001_nomissing_numpy,)  , 700.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1001_nomissing_MA,w1001_nomissing_MA,)  , 700.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1001_nomissing_MA,w1001_missing,)  , 693.0, exclude_nonpositive_weights=True)

    def test_wmedian_nonmissing_even_exclnpwgts(self):
        self._test(Stats.wmedian, (n1006_nomissing_numpy,w1006_nomissing_numpy,)  , 704.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1006_nomissing_numpy,w1006_nomissing_MA,)  , 704.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1006_nomissing_numpy,w1006_missing,)  , 696.0, exclude_nonpositive_weights=True)

        self._test(Stats.wmedian, (n1006_nomissing_MA,w1006_nomissing_numpy,)  , 704.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1006_nomissing_MA,w1006_nomissing_MA,)  , 704.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1006_nomissing_MA,w1006_missing,)  , 696.0, exclude_nonpositive_weights=True)

    def test_wmedian_missing_odd_exclnpwgts(self):
        self._test(Stats.wmedian, (n1001_missing,w1001_nomissing_numpy,)  , 713.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1001_missing,w1001_nomissing_MA,)  , 713.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1001_missing,w1001_missing,)  , 707.0, exclude_nonpositive_weights=True)

    def test_wmedian_missing_even_exclnpwgts(self):
        self._test(Stats.wmedian, (n1006_missing,w1006_nomissing_numpy,)  , 717.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1006_missing,w1006_nomissing_MA,)  , 717.0, exclude_nonpositive_weights=True)
        self._test(Stats.wmedian, (n1006_missing,w1006_missing,)  , 710.0, exclude_nonpositive_weights=True)

    def test_quantile_p0_odd_nonmissing(self):
        # 0th percentile
        self._test(Stats.quantile, (n1001_nomissing_numpy,), -10.0, p=0.0, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , -10.0, p=0.0, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , -10.0, p=0.0, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , -10.0, p=0.0, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , -10.0, p=0.0, defn=5)

        self._test(Stats.quantile, (n1001_nomissing_MA,), -10.0, p=0.0, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , -10.0, p=0.0, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , -10.0, p=0.0, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , -10.0, p=0.0, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , -10.0, p=0.0, defn=5)

    def test_quantile_p0_even_nonmissing(self):
        # 0th percentile
        self._test(Stats.quantile, (n1006_nomissing_numpy,), -10.0, p=0.0, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , -10.0, p=0.0, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , -10.0, p=0.0, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , -10.0, p=0.0, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , -10.0, p=0.0, defn=5)

        self._test(Stats.quantile, (n1006_nomissing_MA,), -10.0, p=0.0, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , -10.0, p=0.0, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , -10.0, p=0.0, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , -10.0, p=0.0, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , -10.0, p=0.0, defn=5)

    def test_quantile_p1_odd_nonmissing(self):
        # 1st percentile
        self._test(Stats.quantile, (n1001_nomissing_numpy,), -0.99, p=0.01, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , -1.0, p=0.01, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 0.0, p=0.01, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , -0.98, p=0.01, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 0.0, p=0.01, defn=5)

        self._test(Stats.quantile, (n1001_nomissing_MA,)  , -0.99, p=0.01, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , -1.0, p=0.01, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 0.0, p=0.01, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , -0.98, p=0.01, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 0.0, p=0.01, defn=5)

    def test_wquantile_p1_odd_nonmissing(self):
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_numpy,)  , 99.0, p=0.01)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_MA,)  , 99.0, p=0.01)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_missing,)  , 96.0, p=0.01)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_numpy,)  , 99.0, p=0.01)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_MA,)  , 99.0, p=0.01)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_missing,)  , 96.0, p=0.01)

    def test_quantile_p1_even_nonmissing(self):
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , -0.94, p=0.01, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , -1.0, p=0.01, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 0.0, p=0.01, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , -0.93, p=0.01, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 0.0, p=0.01, defn=5)

        self._test(Stats.quantile, (n1006_nomissing_MA,)  , -0.94, p=0.01, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , -1.0, p=0.01, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 0.0, p=0.01, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , -0.93, p=0.01, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 0.0, p=0.01, defn=5)

    def test_wquantile_p1_even_nonmissing(self):
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_numpy,)  , 100.0, p=0.01)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_MA,)  , 100.0, p=0.01)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_missing,)  , 97.0, p=0.01)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_numpy,)  , 100.0, p=0.01)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_MA,)  , 100.0, p=0.01)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_missing,)  , 97.0, p=0.01)

    def test_quantile_p1_odd_missing(self):
        self._test(Stats.quantile, (n1001_missing,)  , -0.44, p=0.01, defn=1)
        self._test(Stats.quantile, (n1001_missing,)  , -1.0, p=0.01, defn=2)
        self._test(Stats.quantile, (n1001_missing,)  , 1.0, p=0.01, defn=3)
        self._test(Stats.quantile, (n1001_missing,)  , -0.42, p=0.01, defn=4)
        self._test(Stats.quantile, (n1001_missing,)  , 1.0, p=0.01, defn=5)

    def test_quantile_p1_even_missing(self):
        self._test(Stats.quantile, (n1006_missing,)  , -0.34, p=0.01, defn=1)
        self._test(Stats.quantile, (n1006_missing,)  , -1.0, p=0.01, defn=2)
        self._test(Stats.quantile, (n1006_missing,)  , 1.0, p=0.01, defn=3)
        self._test(Stats.quantile, (n1006_missing,)  , -0.32, p=0.01, defn=4)
        self._test(Stats.quantile, (n1006_missing,)  , 1.0, p=0.01, defn=5)

    def test_wquantile_p1_odd_missing(self):
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_numpy,)  , 106.0, p=0.01)
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_MA,)  , 106.0, p=0.01)
        self._test(Stats.wquantile, (n1001_missing,w1001_missing,)  , 102.0, p=0.01)

    def test_wquantile_p1_even_missing(self):
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_numpy,)  , 106.0, p=0.01)
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_MA,)  , 106.0, p=0.01)
        self._test(Stats.wquantile, (n1006_missing,w1006_missing,)  , 102.0, p=0.01)

        # with exclude_nonpositive_weights = True
    def test_wquantile_p1_odd_nonmissing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_numpy)  , 99.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_MA)  , 99.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_missing)  , 96.0, exclude_nonpositive_weights=True, p=0.01)

        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_numpy)  , 99.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_MA)  , 99.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_missing)  , 96.0, exclude_nonpositive_weights=True, p=0.01)

    def test_wquantile_p1_even_nonmissing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_numpy)  , 100.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_MA)  , 100.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_missing)  , 97.0, exclude_nonpositive_weights=True, p=0.01)

        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_numpy)  , 100.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_MA)  , 100.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_missing)  , 97.0, exclude_nonpositive_weights=True, p=0.01)

    def test_wquantile_p1_odd_missing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_numpy)  , 106.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_MA)  , 106.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1001_missing,w1001_missing)  , 102.0, exclude_nonpositive_weights=True, p=0.01)

    def test_wquantile_p1_even_nonmissing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_numpy)  , 106.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_MA)  , 106.0, exclude_nonpositive_weights=True, p=0.01)
        self._test(Stats.wquantile, (n1006_missing,w1006_missing)  , 102.0, exclude_nonpositive_weights=True, p=0.01)

    # 100th percentile
    def test_quantile_p100_odd_nonmissing(self):
        self._test(Stats.quantile, (n1001_nomissing_numpy,), 990.0, p=1.0, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 990.0, p=1.0, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 990.0, p=1.0, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 990.0, p=1.0, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 990.0, p=1.0, defn=5)

        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 990.0, p=1.0, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 990.0, p=1.0, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 990.0, p=1.0, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 990.0, p=1.0, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 990.0, p=1.0, defn=5)

    def test_quantile_p100_even_nonmissing(self):
        self._test(Stats.quantile, (n1006_nomissing_numpy,), 995.0, p=1.0, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 995.0, p=1.0, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 995.0, p=1.0, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 995.0, p=1.0, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 995.0, p=1.0, defn=5)

        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 995.0, p=1.0, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 995.0, p=1.0, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 995.0, p=1.0, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 995.0, p=1.0, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 995.0, p=1.0, defn=5)

    def test_wquantile_p100_odd_nonmissing(self):
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_numpy,)  , 990.0, p=1.0)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_MA,)  , 990.0, p=1.0)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_missing,)  , 990.0, p=1.0)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_numpy,)  , 990.0, p=1.0)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_MA,)  , 990.0, p=1.0)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_missing,)  , 990.0, p=1.0)

    def test_wquantile_p100_even_nonmissing(self):
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_numpy,)  , 995.0, p=1.0)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_MA,)  , 995.0, p=1.0)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_missing,)  , 995.0, p=1.0)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_numpy,)  , 995.0, p=1.0)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_MA,)  , 995.0, p=1.0)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_missing,)  , 995.0, p=1.0)

    # 99th percentile
    def test_quantile_p99_odd_nonmissing(self):
        self._test(Stats.quantile, (n1001_nomissing_numpy,), 979.99, p=0.99, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 980.0, p=0.99, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 980.0, p=0.99, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 980.98, p=0.99, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 980.0, p=0.99, defn=5)

        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 979.99, p=0.99, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 980.0, p=0.99, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 980.0, p=0.99, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 980.98, p=0.99, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 980.0, p=0.99, defn=5)

    def test_wquantile_p99_odd_nonmissing(self):
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_numpy,)  , 986.0, p=0.99)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_MA,)  , 986.0, p=0.99)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_missing,)  , 985.0, p=0.99)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_numpy,)  , 986.0, p=0.99)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_MA,)  , 986.0, p=0.99)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_missing,)  , 985.0, p=0.99)

    def test_quantile_p99_even_nonmissing(self):
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 984.94, p=0.99, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 985.0, p=0.99, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 985.0, p=0.99, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 985.93, p=0.99, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 985.0, p=0.99, defn=5)

        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 984.94, p=0.99, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 985.0, p=0.99, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 985.0, p=0.99, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 985.93, p=0.99, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 985.0, p=0.99, defn=5)

    def test_wquantile_p99_even_nonmissing(self):
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_numpy,)  , 991.0, p=0.99)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_MA,)  , 991.0, p=0.99)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_missing,)  , 991.0, p=0.99)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_numpy,)  , 991.0, p=0.99)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_MA,)  , 991.0, p=0.99)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_missing,)  , 991.0, p=0.99)

    def test_wquantile_p99_odd_missing(self):
        self._test(Stats.quantile, (n1001_missing,)  , 980.72, p=0.99, defn=1)
        self._test(Stats.quantile, (n1001_missing,)  , 981.0, p=0.99, defn=2)
        self._test(Stats.quantile, (n1001_missing,)  , 981.0, p=0.99, defn=3)
        self._test(Stats.quantile, (n1001_missing,)  , 981.71, p=0.99, defn=4)
        self._test(Stats.quantile, (n1001_missing,)  , 981.0, p=0.99, defn=5)

    def test_wquantile_p99_even_missing(self):
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_numpy,)  , 986.0, p=0.99)
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_MA,)  , 986.0, p=0.99)
        self._test(Stats.wquantile, (n1001_missing,w1001_missing,)  , 985.0, p=0.99)

    def test_quantile_p99_even_missing(self):
        self._test(Stats.quantile, (n1006_missing,)  , 985.67, p=0.99, defn=1)
        self._test(Stats.quantile, (n1006_missing,)  , 986.0, p=0.99, defn=2)
        self._test(Stats.quantile, (n1006_missing,)  , 986.0, p=0.99, defn=3)
        self._test(Stats.quantile, (n1006_missing,)  , 986.66, p=0.99, defn=4)
        self._test(Stats.quantile, (n1006_missing,)  , 986.0, p=0.99, defn=5)

    def test_wquantile_p99_even_missing(self):
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_numpy,)  , 991.0, p=0.99)
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_MA,)  , 991.0, p=0.99)
        self._test(Stats.wquantile, (n1006_missing,w1006_missing,)  , 991.0, p=0.99)

        # with exclude_nonpositive_weights = True
    def test_wquantile_p99_odd_nonmissing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_numpy)  , 986.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_MA)  , 986.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_missing)  , 985.0, exclude_nonpositive_weights=True, p=0.99)

        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_numpy)  , 986.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_MA)  , 986.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_missing)  , 985.0, exclude_nonpositive_weights=True, p=0.99)

    def test_wquantile_p99_even_nonmissing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_numpy)  , 991.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_MA)  , 991.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_missing)  , 991.0, exclude_nonpositive_weights=True, p=0.99)

        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_numpy)  , 991.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_MA)  , 991.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_missing)  , 991.0, exclude_nonpositive_weights=True, p=0.99)

    def test_wquantile_p99_odd_missing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_numpy)  , 986.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_MA)  , 986.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1001_missing,w1001_missing)  , 985.0, exclude_nonpositive_weights=True, p=0.99)

    def test_wquantile_p99_even_missing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_numpy)  , 991.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_MA)  , 991.0, exclude_nonpositive_weights=True, p=0.99)
        self._test(Stats.wquantile, (n1006_missing,w1006_missing)  , 991.0, exclude_nonpositive_weights=True, p=0.99)

        # 75th percentile
    def test_quantile_p75_odd_nonmissing(self):
        self._test(Stats.quantile, (n1001_nomissing_numpy,), 739.75, p=0.75, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 740.0, p=0.75, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 740.0, p=0.75, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 740.5, p=0.75, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_numpy,)  , 740.0, p=0.75, defn=5)

        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 739.75, p=0.75, defn=1)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 740.0, p=0.75, defn=2)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 740.0, p=0.75, defn=3)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 740.5, p=0.75, defn=4)
        self._test(Stats.quantile, (n1001_nomissing_MA,)  , 740.0, p=0.75, defn=5)

    def test_wquantile_p75_odd_nonmissing(self):
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_numpy,)  , 858.0, p=0.75)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_MA,)  , 858.0, p=0.75)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_missing,)  , 854.0, p=0.75)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_numpy,)  , 858.0, p=0.75)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_MA,)  , 858.0, p=0.75)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_missing,)  , 854.0, p=0.75)

    def test_quantile_p75_even_nonmissing(self):
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 743.5, p=0.75, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 743.0, p=0.75, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 744.0, p=0.75, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 744.25, p=0.75, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_numpy,)  , 744.0, p=0.75, defn=5)

        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 743.5, p=0.75, defn=1)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 743.0, p=0.75, defn=2)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 744.0, p=0.75, defn=3)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 744.25, p=0.75, defn=4)
        self._test(Stats.quantile, (n1006_nomissing_MA,)  , 744.0, p=0.75, defn=5)

    def test_wquantile_p75_even_nonmissing(self):
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_numpy,)  , 862.0, p=0.75)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_MA,)  , 862.0, p=0.75)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_missing,)  , 860.0, p=0.75)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_numpy,)  , 862.0, p=0.75)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_MA,)  , 862.0, p=0.75)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_missing,)  , 860.0, p=0.75)

    def test_quantile_p75_odd_missing(self):
        self._test(Stats.quantile, (n1001_missing,)  , 758.0, p=0.75, defn=1)
        self._test(Stats.quantile, (n1001_missing,)  , 758.0, p=0.75, defn=2)
        self._test(Stats.quantile, (n1001_missing,)  , 758.0, p=0.75, defn=3)
        self._test(Stats.quantile, (n1001_missing,)  , 758.75, p=0.75, defn=4)
        self._test(Stats.quantile, (n1001_missing,)  , 758.5, p=0.75, defn=5)

    def test_wquantile_p75_odd_missing(self):
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_numpy,)  , 863.0, p=0.75)
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_MA,)  , 863.0, p=0.75)
        self._test(Stats.wquantile, (n1001_missing,w1001_missing,)  , 860.0, p=0.75)

    def test_quantile_p75_even_missing(self):
        self._test(Stats.quantile, (n1006_missing,)  , 761.75, p=0.75, defn=1)
        self._test(Stats.quantile, (n1006_missing,)  , 762.0, p=0.75, defn=2)
        self._test(Stats.quantile, (n1006_missing,)  , 762.0, p=0.75, defn=3)
        self._test(Stats.quantile, (n1006_missing,)  , 762.5, p=0.75, defn=4)
        self._test(Stats.quantile, (n1006_missing,)  , 762.0, p=0.75, defn=5)

    def test_wquantile_p75_even_missing(self):
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_numpy,)  , 867.0, p=0.75)
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_MA,)  , 867.0, p=0.75)
        self._test(Stats.wquantile, (n1006_missing,w1006_missing,)  , 865.0, p=0.75)

        # with exclude_nonpositive_weights = True
    def test_wquantile_p75_odd_nonmissing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_numpy)  , 858.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_nomissing_MA)  , 858.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1001_nomissing_numpy,w1001_missing)  , 854.0, exclude_nonpositive_weights=True, p=0.75)

        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_numpy)  , 858.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_nomissing_MA)  , 858.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1001_nomissing_MA,w1001_missing)  , 854.0, exclude_nonpositive_weights=True, p=0.75)

    def test_wquantile_p75_even_nonmissing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_numpy)  , 862.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_nomissing_MA)  , 862.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1006_nomissing_numpy,w1006_missing)  , 860.0, exclude_nonpositive_weights=True, p=0.75)

        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_numpy)  , 862.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_nomissing_MA)  , 862.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1006_nomissing_MA,w1006_missing)  , 860.0, exclude_nonpositive_weights=True, p=0.75)

    def test_wquantile_p75_odd_missing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_numpy)  , 863.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1001_missing,w1001_nomissing_MA)  , 863.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1001_missing,w1001_missing)  , 860.0, exclude_nonpositive_weights=True, p=0.75)

    def test_wquantile_p75_even_missing_exclnpwgts(self):
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_numpy)  , 867.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1006_missing,w1006_nomissing_MA)  , 867.0, exclude_nonpositive_weights=True, p=0.75)
        self._test(Stats.wquantile, (n1006_missing,w1006_missing)  , 865.0, exclude_nonpositive_weights=True, p=0.75)

    def test_quantile_p25_misc(self):
        self._test(Stats.quantile, (empty_numeric,), None, p=0.25)
        self._test(Stats.quantile, (empty_ma,), None, p=0.25)
        self._test(Stats.quantile, (populated_numeric,), 2.0, p=0.25)
        self._test(Stats.quantile, (populated_ma,), 2.0, p=0.25)
        self._test(Stats.quantile, (null_mask,), 2.0, p=0.25)
        self._test(Stats.quantile, (full_mask,), None, p=0.25)
        self._test(Stats.quantile, (partial_mask,), 2.0, p=0.25)
        self._test(Stats.quantile, (two_elements_numeric,), 2.0, p=0.25)
        self._test(Stats.quantile, (two_elements_ma,), 2.0, p=0.25)
        self._test(Stats.quantile, (twenty_ele,), 4.5, p=0.25)
        self._test(Stats.quantile, (twenty_ele,), 14.5, p=0.75)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=0.75)
        self._test(Stats.quantile, one_element_ma, 2.0, p=0.25)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=0.75)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=0.25)

    def test_quantile_p0_p100_misc_def5(self):
        self._test(Stats.quantile, (empty_numeric,), None, p=1.0,defn=5)
        self._test(Stats.quantile, (empty_ma,), None, p=1.0,defn=5)
        self._test(Stats.quantile, (empty_numeric,), None, p=0.0,defn=5)
        self._test(Stats.quantile, (empty_ma,), None, p=0.0,defn=5)
        self._test(Stats.quantile, (populated_numeric,), 5.0, p=1.0,defn=5)
        self._test(Stats.quantile, (populated_ma,), 5.0, p=1.0,defn=5)
        self._test(Stats.quantile, (populated_numeric,), 1.0, p=0.0,defn=5)
        self._test(Stats.quantile, (populated_ma,), 1.0, p=0.0,defn=5)
        self._test(Stats.quantile, (null_mask,), 5.0, p=1.0,defn=5)
        self._test(Stats.quantile, (full_mask,), None, p=1.0,defn=5)
        self._test(Stats.quantile, (null_mask,), 1.0, p=0.0,defn=5)
        self._test(Stats.quantile, (full_mask,), None, p=0.0,defn=5)
        self._test(Stats.quantile, (partial_mask,), 5.0, p=1.0,defn=5)
        self._test(Stats.quantile, (partial_mask,), 2.0, p=0.0,defn=5)
        self._test(Stats.quantile, (two_elements_numeric,), 5.0, p=1.0,defn=5)
        self._test(Stats.quantile, (two_elements_ma,), 5.0, p=1.0,defn=5)
        self._test(Stats.quantile, (two_elements_numeric,), 2.0, p=0.0,defn=5)
        self._test(Stats.quantile, (two_elements_ma,), 2.0, p=0.0,defn=5)
        self._test(Stats.quantile, (twenty_ele,), 19.0, p=1.0,defn=5)
        self._test(Stats.quantile, (twenty_ele,), 0.0, p=0.0,defn=5)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=1.0,defn=5)
        self._test(Stats.quantile, one_element_ma, 2.0, p=1.0,defn=5)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=0.0,defn=5)
        self._test(Stats.quantile, one_element_ma, 2.0, p=0.0,defn=5)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=1.0,defn=5)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=1.0,defn=5)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=0.0,defn=5)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=0.0,defn=5)

    def test_quantile_p0_p100_misc_def4(self):
        self._test(Stats.quantile, (empty_numeric,), None, p=1.0,defn=4)
        self._test(Stats.quantile, (empty_ma,), None, p=1.0,defn=4)
        self._test(Stats.quantile, (empty_numeric,), None, p=0.0,defn=4)
        self._test(Stats.quantile, (empty_ma,), None, p=0.0,defn=4)
        self._test(Stats.quantile, (populated_numeric,), 5.0, p=1.0,defn=4)
        self._test(Stats.quantile, (populated_ma,), 5.0, p=1.0,defn=4)
        self._test(Stats.quantile, (populated_numeric,), 1.0, p=0.0,defn=4)
        self._test(Stats.quantile, (populated_ma,), 1.0, p=0.0,defn=4)
        self._test(Stats.quantile, (null_mask,), 5.0, p=1.0,defn=4)
        self._test(Stats.quantile, (full_mask,), None, p=1.0,defn=4)
        self._test(Stats.quantile, (null_mask,), 1.0, p=0.0,defn=4)
        self._test(Stats.quantile, (full_mask,), None, p=0.0,defn=4)
        self._test(Stats.quantile, (partial_mask,), 5.0, p=1.0,defn=4)
        self._test(Stats.quantile, (partial_mask,), 2.0, p=0.0,defn=4)
        self._test(Stats.quantile, (two_elements_numeric,), 5.0, p=1.0,defn=4)
        self._test(Stats.quantile, (two_elements_ma,), 5.0, p=1.0,defn=4)
        self._test(Stats.quantile, (two_elements_numeric,), 2.0, p=0.0,defn=4)
        self._test(Stats.quantile, (two_elements_ma,), 2.0, p=0.0,defn=4)
        self._test(Stats.quantile, (twenty_ele,), 19.0, p=1.0,defn=4)
        self._test(Stats.quantile, (twenty_ele,), 0.0, p=0.0,defn=4)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=1.0,defn=4)
        self._test(Stats.quantile, one_element_ma, 2.0, p=1.0,defn=4)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=0.0,defn=4)
        self._test(Stats.quantile, one_element_ma, 2.0, p=0.0,defn=4)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=1.0,defn=4)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=1.0,defn=4)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=0.0,defn=4)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=0.0,defn=4)

    def test_quantile_p0_p100_misc_def3(self):
        self._test(Stats.quantile, (empty_numeric,), None, p=1.0,defn=3)
        self._test(Stats.quantile, (empty_ma,), None, p=1.0,defn=3)
        self._test(Stats.quantile, (empty_numeric,), None, p=0.0,defn=3)
        self._test(Stats.quantile, (empty_ma,), None, p=0.0,defn=3)
        self._test(Stats.quantile, (populated_numeric,), 5.0, p=1.0,defn=3)
        self._test(Stats.quantile, (populated_ma,), 5.0, p=1.0,defn=3)
        self._test(Stats.quantile, (populated_numeric,), 1.0, p=0.0,defn=3)
        self._test(Stats.quantile, (populated_ma,), 1.0, p=0.0,defn=3)
        self._test(Stats.quantile, (null_mask,), 5.0, p=1.0,defn=3)
        self._test(Stats.quantile, (full_mask,), None, p=1.0,defn=3)
        self._test(Stats.quantile, (null_mask,), 1.0, p=0.0,defn=3)
        self._test(Stats.quantile, (full_mask,), None, p=0.0,defn=3)
        self._test(Stats.quantile, (partial_mask,), 5.0, p=1.0,defn=3)
        self._test(Stats.quantile, (partial_mask,), 2.0, p=0.0,defn=3)
        self._test(Stats.quantile, (two_elements_numeric,), 5.0, p=1.0,defn=3)
        self._test(Stats.quantile, (two_elements_ma,), 5.0, p=1.0,defn=3)
        self._test(Stats.quantile, (two_elements_numeric,), 2.0, p=0.0,defn=3)
        self._test(Stats.quantile, (two_elements_ma,), 2.0, p=0.0,defn=3)
        self._test(Stats.quantile, (twenty_ele,), 19.0, p=1.0,defn=3)
        self._test(Stats.quantile, (twenty_ele,), 0.0, p=0.0,defn=3)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=1.0,defn=3)
        self._test(Stats.quantile, one_element_ma, 2.0, p=1.0,defn=3)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=0.0,defn=3)
        self._test(Stats.quantile, one_element_ma, 2.0, p=0.0,defn=3)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=1.0,defn=3)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=1.0,defn=3)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=0.0,defn=3)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=0.0,defn=3)

    def test_quantile_p0_p100_misc_def2(self):
        self._test(Stats.quantile, (empty_numeric,), None, p=1.0,defn=2)
        self._test(Stats.quantile, (empty_ma,), None, p=1.0,defn=2)
        self._test(Stats.quantile, (empty_numeric,), None, p=0.0,defn=2)
        self._test(Stats.quantile, (empty_ma,), None, p=0.0,defn=2)
        self._test(Stats.quantile, (populated_numeric,), 5.0, p=1.0,defn=2)
        self._test(Stats.quantile, (populated_ma,), 5.0, p=1.0,defn=2)
        self._test(Stats.quantile, (populated_numeric,), 1.0, p=0.0,defn=2)
        self._test(Stats.quantile, (populated_ma,), 1.0, p=0.0,defn=2)
        self._test(Stats.quantile, (null_mask,), 5.0, p=1.0,defn=2)
        self._test(Stats.quantile, (full_mask,), None, p=1.0,defn=2)
        self._test(Stats.quantile, (null_mask,), 1.0, p=0.0,defn=2)
        self._test(Stats.quantile, (full_mask,), None, p=0.0,defn=2)
        self._test(Stats.quantile, (partial_mask,), 5.0, p=1.0,defn=2)
        self._test(Stats.quantile, (partial_mask,), 2.0, p=0.0,defn=2)
        self._test(Stats.quantile, (two_elements_numeric,), 5.0, p=1.0,defn=2)
        self._test(Stats.quantile, (two_elements_ma,), 5.0, p=1.0,defn=2)
        self._test(Stats.quantile, (two_elements_numeric,), 2.0, p=0.0,defn=2)
        self._test(Stats.quantile, (two_elements_ma,), 2.0, p=0.0,defn=2)
        self._test(Stats.quantile, (twenty_ele,), 19.0, p=1.0,defn=2)
        self._test(Stats.quantile, (twenty_ele,), 0.0, p=0.0,defn=2)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=1.0,defn=2)
        self._test(Stats.quantile, one_element_ma, 2.0, p=1.0,defn=2)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=0.0,defn=2)
        self._test(Stats.quantile, one_element_ma, 2.0, p=0.0,defn=2)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=1.0,defn=2)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=1.0,defn=2)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=0.0,defn=2)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=0.0,defn=2)

    def test_quantile_p0_p100_misc_def1(self):
        self._test(Stats.quantile, (empty_numeric,), None, p=1.0,defn=1)
        self._test(Stats.quantile, (empty_ma,), None, p=1.0,defn=1)
        self._test(Stats.quantile, (empty_numeric,), None, p=0.0,defn=1)
        self._test(Stats.quantile, (empty_ma,), None, p=0.0,defn=1)
        self._test(Stats.quantile, (populated_numeric,), 5.0, p=1.0,defn=1)
        self._test(Stats.quantile, (populated_ma,), 5.0, p=1.0,defn=1)
        self._test(Stats.quantile, (populated_numeric,), 1.0, p=0.0,defn=1)
        self._test(Stats.quantile, (populated_ma,), 1.0, p=0.0,defn=1)
        self._test(Stats.quantile, (null_mask,), 5.0, p=1.0,defn=1)
        self._test(Stats.quantile, (full_mask,), None, p=1.0,defn=1)
        self._test(Stats.quantile, (null_mask,), 1.0, p=0.0,defn=1)
        self._test(Stats.quantile, (full_mask,), None, p=0.0,defn=1)
        self._test(Stats.quantile, (partial_mask,), 5.0, p=1.0,defn=1)
        self._test(Stats.quantile, (partial_mask,), 2.0, p=0.0,defn=1)
        self._test(Stats.quantile, (two_elements_numeric,), 5.0, p=1.0,defn=1)
        self._test(Stats.quantile, (two_elements_ma,), 5.0, p=1.0,defn=1)
        self._test(Stats.quantile, (two_elements_numeric,), 2.0, p=0.0,defn=1)
        self._test(Stats.quantile, (two_elements_ma,), 2.0, p=0.0,defn=1)
        self._test(Stats.quantile, (twenty_ele,), 19.0, p=1.0,defn=1)
        self._test(Stats.quantile, (twenty_ele,), 0.0, p=0.0,defn=1)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=1.0,defn=1)
        self._test(Stats.quantile, one_element_ma, 2.0, p=1.0,defn=1)
        self._test(Stats.quantile, one_element_numeric, 2.0, p=0.0,defn=1)
        self._test(Stats.quantile, one_element_ma, 2.0, p=0.0,defn=1)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=1.0,defn=1)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=1.0,defn=1)
        self._test(Stats.quantile, one_neg_element_numeric, -2.0, p=0.0,defn=1)
        self._test(Stats.quantile, one_neg_element_ma, -2.0, p=0.0,defn=1)

    def test_quantiles_p1_p99_p75_odd_nonmissing(self):
        # 1st percentile
        self._test(Stats.quantiles, (n1001_nomissing_numpy,), (-0.99000000000000021,979.99,739.75), p=(0.01,0.99,0.75), defn=1)
        self._test(Stats.quantiles, (n1001_nomissing_numpy,), (-1.0,980.0,740.0), p=(0.01,0.99,0.75), defn=2)
        self._test(Stats.quantiles, (n1001_nomissing_numpy,), (0.0,980.0,740.0), p=(0.01,0.99,0.75), defn=3)
        self._test(Stats.quantiles, (n1001_nomissing_numpy,), (-0.98000000000000043,980.98,740.5), p=(0.01,0.99,0.75), defn=4)
        self._test(Stats.quantiles, (n1001_nomissing_numpy,), (0.0,980.0,740.0), p=(0.01,0.99,0.75), defn=5)

        self._test(Stats.quantiles, (n1001_nomissing_MA,), (-0.99000000000000021,979.99,739.75), p=(0.01,0.99,0.75), defn=1)
        self._test(Stats.quantiles, (n1001_nomissing_MA,), (-1.0,980.0,740.0), p=(0.01,0.99,0.75), defn=2)
        self._test(Stats.quantiles, (n1001_nomissing_MA,), (0.0,980.0,740.0), p=(0.01,0.99,0.75), defn=3)
        self._test(Stats.quantiles, (n1001_nomissing_MA,), (-0.98000000000000043,980.98,740.5), p=(0.01,0.99,0.75), defn=4)
        self._test(Stats.quantiles, (n1001_nomissing_MA,), (0.0,980.0,740.0), p=(0.01,0.99,0.75), defn=5)

    def test_wquantiles_p1_p75_p99_even_nonmissing_exclnpwgts(self):
        self._test(Stats.wquantiles, (n1006_missing,w1006_nomissing_numpy)  , (106.0,867.0,991.0), exclude_nonpositive_weights=True, p=[0.01,0.75,0.99])
        self._test(Stats.wquantiles, (n1006_missing,w1006_nomissing_MA)  , (106.0,867.0,991.0), exclude_nonpositive_weights=True, p=(0.01,0.75,0.99))
        self._test(Stats.wquantiles, (n1006_missing,w1006_missing)  , (102.0,865.0,991.0), exclude_nonpositive_weights=True, p=[0.01,0.75,0.99])

    def test_quantiles_misc(self):
        self._test(Stats.quantiles, (empty_numeric,), (None,None,None,None), p=(0.01,0.25,0.73,1))
        self._test(Stats.quantiles, (empty_ma,), (None,None,None,None), p=(0.01,0.25,0.73,1))
        self._test(Stats.quantiles, (full_mask,), (None,None,None,None), p=(0.01,0.25,0.73,1))
        self._test(Stats.quantiles, one_element_numeric, (2.0,2.0,2.0,2.0,2.0), p=(0,0.000000001,0.01,0.1,0.75))
        self._test(Stats.quantiles, one_element_ma, (2.0,2.0,2.0,2.0,2.0), p=(0,0.000000001,0.01,0.1,0.75))
        self._test(Stats.quantiles, one_neg_element_numeric, (-2.0,-2.0,-2.0,-2.0,-2.0), p=(0,0.000000001,0.01,0.1,0.75))
        self._test(Stats.quantiles, one_neg_element_ma, (-2.0,-2.0,-2.0,-2.0,-2.0), p=(0,0.000000001,0.01,0.1,0.75))
        
    def test_samplevar_misc(self):
        self._test(Stats.samplevar, empty_numeric, None)
        self._test(Stats.samplevar, empty_ma, None)
        self._test(Stats.samplevar, populated_numeric, 2.2)
        self._test(Stats.samplevar, populated_ma, 2.2)
        self._test(Stats.samplevar, null_mask, 2.2)
        self._test(Stats.samplevar, full_mask, None)
        self._test(Stats.samplevar, partial_mask, 4.5)
        self._test(Stats.samplevar, two_elements_numeric, 4.5)
        self._test(Stats.samplevar, two_elements_ma, 4.5)
        self._test(Stats.samplevar, one_element_numeric, None)
        self._test(Stats.samplevar, one_element_ma, None)
        self._test(Stats.samplevar, one_neg_element_numeric, None)
        self._test(Stats.samplevar, one_neg_element_ma, None)
        self._test(Stats.samplevar, all_neg_numeric, 1052.50000)
        self._test(Stats.samplevar, all_neg_ma, 1052.50000)

    def test_wsamplevar_misc(self):
        self._test(Stats.wsamplevar, (empty_numeric,empty_numeric), None)
        self._test(Stats.wsamplevar, (empty_ma,empty_numeric), None)
        self._test(Stats.wsamplevar, (empty_numeric,empty_ma), None)
        self._test(Stats.wsamplevar, (empty_ma,empty_ma), None)
        self._test(Stats.wsamplevar, (populated_numeric,populated_numeric), 1.8021978022)
        self._test(Stats.wsamplevar, (populated_numeric,populated_ma), 1.8021978022)
        self._test(Stats.wsamplevar, (populated_ma,populated_numeric), 1.8021978022)
        self._test(Stats.wsamplevar, (populated_ma,populated_ma), 1.8021978022)
        self._test(Stats.wsamplevar, (null_mask,null_mask), 1.8021978022)
        self._test(Stats.wsamplevar, (full_mask,null_mask), None)
        self._test(Stats.wsamplevar, (full_mask,partial_mask), None)
        self._test(Stats.wsamplevar, (full_mask,full_mask), None)
        self._test(Stats.wsamplevar, (null_mask,full_mask), None)
        self._test(Stats.wsamplevar, (partial_mask,full_mask), None)
        self._test(Stats.wsamplevar, (full_mask,full_mask), None)
        self._test(Stats.wsamplevar, (partial_mask,partial_mask), 2.1428571429)
        self._test(Stats.wsamplevar, (two_elements_numeric,two_elements_numeric), 2.1428571429)
        self._test(Stats.wsamplevar, (two_elements_ma,two_elements_numeric), 2.1428571429)
        self._test(Stats.wsamplevar, (two_elements_numeric,two_elements_ma), 2.1428571429)
        self._test(Stats.wsamplevar, (two_elements_ma,two_elements_ma), 2.1428571429)
        self._test(Stats.wsamplevar, (one_element_numeric,one_element_numeric), 0.0)
        self._test(Stats.wsamplevar, (one_element_ma,one_element_numeric), 0.0)
        self._test(Stats.wsamplevar, (one_element_numeric,one_element_ma), 0.0)
        self._test(Stats.wsamplevar, (one_element_ma,one_element_ma), 0.0)
        self._test(Stats.wsamplevar, (one_neg_element_numeric,one_neg_element_ma), None)
        self._test(Stats.wsamplevar, (one_neg_element_ma,one_neg_element_ma), None)
        self._test(Stats.wsamplevar, (one_neg_element_numeric,one_neg_element_numeric), None)
        self._test(Stats.wsamplevar, (one_neg_element_ma,one_neg_element_numeric), None)
        self._test(Stats.wsamplevar, (all_neg_numeric,all_neg_numeric), None)
        self._test(Stats.wsamplevar, (all_neg_ma,all_neg_numeric), None)
        self._test(Stats.wsamplevar, (all_neg_numeric,all_neg_ma), None)
        self._test(Stats.wsamplevar, (all_neg_ma,all_neg_ma), None)

    def test_wsamplevar_misc_exclnpwgts(self):
        self._test(Stats.wsamplevar, (empty_numeric,empty_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (empty_ma,empty_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (empty_numeric,empty_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (empty_ma,empty_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (populated_numeric,populated_numeric), 1.8021978022, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (populated_numeric,populated_ma), 1.8021978022, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (populated_ma,populated_numeric), 1.8021978022, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (populated_ma,populated_ma), 1.8021978022, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (null_mask,null_mask), 1.8021978022, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (full_mask,null_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (full_mask,partial_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (full_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (null_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (partial_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (full_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (partial_mask,partial_mask), 2.1428571429, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (two_elements_numeric,two_elements_numeric), 2.1428571429, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (two_elements_ma,two_elements_numeric), 2.1428571429, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (two_elements_numeric,two_elements_ma), 2.1428571429, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (two_elements_ma,two_elements_ma), 2.1428571429, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (one_element_numeric,one_element_numeric), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (one_element_ma,one_element_numeric), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (one_element_numeric,one_element_ma), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (one_element_ma,one_element_ma), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (one_neg_element_numeric,one_neg_element_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (one_neg_element_ma,one_neg_element_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (one_neg_element_numeric,one_neg_element_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (one_neg_element_ma,one_neg_element_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (all_neg_numeric,all_neg_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (all_neg_ma,all_neg_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (all_neg_numeric,all_neg_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (all_neg_ma,all_neg_ma), None, exclude_nonpositive_weights=True)

    def test_samplevar_1001(self):
        self._test(Stats.samplevar, n1001_nomissing_numpy, 83583.5)
        self._test(Stats.samplevar, n1001_nomissing_MA, 83583.5)
        self._test(Stats.samplevar, n1001_missing, 83353.6095197)

    def test_samplevar_1006(self):
        self._test(Stats.samplevar, n1006_nomissing_numpy, 84420.1666667)
        self._test(Stats.samplevar, n1006_nomissing_MA, 84420.1666667)
        self._test(Stats.samplevar, n1006_missing,  84155.0396823)

    def test_wsamplevar_1001(self):
        self._test(Stats.wsamplevar, (n1001_nomissing_numpy,w1001_nomissing_numpy), 54505.2222235835)
        self._test(Stats.wsamplevar, (n1001_nomissing_MA,w1001_nomissing_numpy), 54505.2222235835)
        self._test(Stats.wsamplevar, (n1001_nomissing_numpy,w1001_nomissing_MA), 54505.2222235835)
        self._test(Stats.wsamplevar, (n1001_nomissing_MA,w1001_nomissing_MA), 54505.2222235835)
        self._test(Stats.wsamplevar, (n1001_missing,w1001_nomissing_numpy), 51849.4940772112)
        self._test(Stats.wsamplevar, (n1001_missing,w1001_nomissing_MA), 51849.4940772112)
        self._test(Stats.wsamplevar, (n1001_nomissing_numpy,w1001_missing), 55798.5328446147)
        self._test(Stats.wsamplevar, (n1001_nomissing_MA,w1001_missing), 55798.5328446147)
        self._test(Stats.wsamplevar, (n1001_missing,w1001_missing), 53205.0071243415)

    def test_wsamplevar_1001_exclnpwgts(self):
        self._test(Stats.wsamplevar, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 54505.2222235835, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1001_nomissing_MA,w1001_nomissing_numpy,), 54505.2222235835, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1001_nomissing_numpy,w1001_nomissing_MA,), 54505.2222235835, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1001_nomissing_MA,w1001_nomissing_MA,), 54505.2222235835, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1001_missing,w1001_nomissing_numpy,), 51849.4940772112, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1001_missing,w1001_nomissing_MA,), 51849.4940772112, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1001_nomissing_numpy,w1001_missing,), 55798.5328446147, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1001_nomissing_MA,w1001_missing,), 55798.5328446147, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1001_missing,w1001_missing,), 53205.0071243415, exclude_nonpositive_weights=True)

    def test_wsamplevar_1006(self):
        self._test(Stats.wsamplevar, (n1006_nomissing_numpy,w1006_nomissing_numpy), 55056.8888902326)
        self._test(Stats.wsamplevar, (n1006_nomissing_MA,w1006_nomissing_numpy), 55056.8888902326)
        self._test(Stats.wsamplevar, (n1006_nomissing_numpy,w1006_nomissing_MA), 55056.8888902326)
        self._test(Stats.wsamplevar, (n1006_nomissing_MA,w1006_nomissing_MA), 55056.8888902326)
        self._test(Stats.wsamplevar, (n1006_missing,w1006_nomissing_numpy), 52365.9372357347)
        self._test(Stats.wsamplevar, (n1006_missing,w1006_nomissing_MA), 52365.9372357347)
        self._test(Stats.wsamplevar, (n1006_nomissing_numpy,w1006_missing), 56418.9816615686)
        self._test(Stats.wsamplevar, (n1006_nomissing_MA,w1006_missing), 56418.9816615686)
        self._test(Stats.wsamplevar, (n1006_missing,w1006_missing), 53784.5056180943)

    def test_wsamplevar_1006_exclnpwgts(self):
        self._test(Stats.wsamplevar, (n1006_nomissing_numpy,w1006_nomissing_numpy,), 55056.8888902326, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1006_nomissing_MA,w1006_nomissing_numpy,), 55056.8888902326, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1006_nomissing_numpy,w1006_nomissing_MA,), 55056.8888902326, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1006_nomissing_MA,w1006_nomissing_MA,), 55056.8888902326, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1006_missing,w1006_nomissing_numpy,), 52365.9372357347, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1006_missing,w1006_nomissing_MA,), 52365.9372357347, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1006_nomissing_numpy,w1006_missing,), 56418.9816615686, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1006_nomissing_MA,w1006_missing,), 56418.9816615686, exclude_nonpositive_weights=True)
        self._test(Stats.wsamplevar, (n1006_missing,w1006_missing,), 53784.5056180943, exclude_nonpositive_weights=True)

    def test_populationvar_misc(self):
        self._test(Stats.populationvar, empty_numeric, None)
        self._test(Stats.populationvar, empty_ma, None)
        self._test(Stats.populationvar, populated_numeric, 1.7600000)
        self._test(Stats.populationvar, populated_ma, 1.7600000)
        self._test(Stats.populationvar, null_mask, 1.7600000)
        self._test(Stats.populationvar, full_mask, None)
        self._test(Stats.populationvar, partial_mask, 2.25000)
        self._test(Stats.populationvar, two_elements_numeric, 2.25000)
        self._test(Stats.populationvar, two_elements_ma, 2.25000)
        self._test(Stats.populationvar, one_element_numeric, 0.0)
        self._test(Stats.populationvar, one_element_ma, 0.0)
        self._test(Stats.populationvar, one_neg_element_numeric, 0.0)
        self._test(Stats.populationvar, one_neg_element_ma, 0.0)
        self._test(Stats.populationvar, all_neg_numeric, 842.00000)
        self._test(Stats.populationvar, all_neg_ma, 842.00000)

    def test_wpopulationvar_misc(self):
        self._test(Stats.wpopulationvar, (empty_numeric,empty_numeric), None)
        self._test(Stats.wpopulationvar, (empty_ma,empty_numeric), None)
        self._test(Stats.wpopulationvar, (empty_numeric,empty_ma), None)
        self._test(Stats.wpopulationvar, (empty_ma,empty_ma), None)
        self._test(Stats.wpopulationvar, (populated_numeric,populated_numeric), 1.6734693878)
        self._test(Stats.wpopulationvar, (populated_numeric,populated_ma), 1.6734693878)
        self._test(Stats.wpopulationvar, (populated_ma,populated_numeric), 1.6734693878)
        self._test(Stats.wpopulationvar, (populated_ma,populated_ma), 1.6734693878)
        self._test(Stats.wpopulationvar, (null_mask,null_mask), 1.6734693878)
        self._test(Stats.wpopulationvar, (full_mask,null_mask), None)
        self._test(Stats.wpopulationvar, (full_mask,partial_mask), None)
        self._test(Stats.wpopulationvar, (full_mask,full_mask), None)
        self._test(Stats.wpopulationvar, (null_mask,full_mask), None)
        self._test(Stats.wpopulationvar, (partial_mask,full_mask), None)
        self._test(Stats.wpopulationvar, (full_mask,full_mask), None)
        self._test(Stats.wpopulationvar, (partial_mask,partial_mask), 1.8367346939)
        self._test(Stats.wpopulationvar, (two_elements_numeric,two_elements_numeric), 1.8367346939)
        self._test(Stats.wpopulationvar, (two_elements_ma,two_elements_numeric), 1.8367346939)
        self._test(Stats.wpopulationvar, (two_elements_numeric,two_elements_ma), 1.8367346939)
        self._test(Stats.wpopulationvar, (two_elements_ma,two_elements_ma), 1.8367346939)
        self._test(Stats.wpopulationvar, (one_element_numeric,one_element_numeric), 0.0)
        self._test(Stats.wpopulationvar, (one_element_ma,one_element_numeric), 0.0)
        self._test(Stats.wpopulationvar, (one_element_numeric,one_element_ma), 0.0)
        self._test(Stats.wpopulationvar, (one_element_ma,one_element_ma), 0.0)
        self._test(Stats.wpopulationvar, (one_neg_element_numeric,one_neg_element_ma), None)
        self._test(Stats.wpopulationvar, (one_neg_element_ma,one_neg_element_ma), None)
        self._test(Stats.wpopulationvar, (one_neg_element_numeric,one_neg_element_numeric), None)
        self._test(Stats.wpopulationvar, (one_neg_element_ma,one_neg_element_numeric), None)
        self._test(Stats.wpopulationvar, (all_neg_numeric,all_neg_numeric), None)
        self._test(Stats.wpopulationvar, (all_neg_ma,all_neg_numeric), None)
        self._test(Stats.wpopulationvar, (all_neg_numeric,all_neg_ma), None)
        self._test(Stats.wpopulationvar, (all_neg_ma,all_neg_ma), None)

    def test_wpopulationvar_misc_exclnpwgts(self):
        self._test(Stats.wpopulationvar, (empty_numeric,empty_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (empty_ma,empty_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (empty_numeric,empty_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (empty_ma,empty_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (populated_numeric,populated_numeric), 1.6734693878, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (populated_numeric,populated_ma), 1.6734693878, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (populated_ma,populated_numeric), 1.6734693878, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (populated_ma,populated_ma), 1.6734693878, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (null_mask,null_mask), 1.6734693878, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (full_mask,null_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (full_mask,partial_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (full_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (null_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (partial_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (full_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (partial_mask,partial_mask), 1.8367346939, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (two_elements_numeric,two_elements_numeric), 1.8367346939, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (two_elements_ma,two_elements_numeric), 1.8367346939, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (two_elements_numeric,two_elements_ma), 1.8367346939, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (two_elements_ma,two_elements_ma), 1.8367346939, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (one_element_numeric,one_element_numeric), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (one_element_ma,one_element_numeric), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (one_element_numeric,one_element_ma), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (one_element_ma,one_element_ma), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (one_neg_element_numeric,one_neg_element_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (one_neg_element_ma,one_neg_element_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (one_neg_element_numeric,one_neg_element_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (one_neg_element_ma,one_neg_element_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (all_neg_numeric,all_neg_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (all_neg_ma,all_neg_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (all_neg_numeric,all_neg_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (all_neg_ma,all_neg_ma), None, exclude_nonpositive_weights=True)

    def test_populationvar_1001(self):
        self._test(Stats.populationvar, n1001_nomissing_numpy, 83500.0000)
        self._test(Stats.populationvar, n1001_nomissing_MA, 83500.0000)
        self._test(Stats.populationvar, n1001_missing, 83263.7888198109)

    def test_populationvar_1006(self):
        self._test(Stats.populationvar, n1006_nomissing_numpy, 84336.2500)
        self._test(Stats.populationvar, n1006_nomissing_MA, 84336.2500)
        self._test(Stats.populationvar, n1006_missing,  84064.8413546869)

    def test_wpopulationvar_1001(self):
        self._test(Stats.wpopulationvar, (n1001_nomissing_numpy,w1001_nomissing_numpy), 54504.8888888911)
        self._test(Stats.wpopulationvar, (n1001_nomissing_MA,w1001_nomissing_numpy), 54504.8888888911)
        self._test(Stats.wpopulationvar, (n1001_nomissing_numpy,w1001_nomissing_MA), 54504.8888888911)
        self._test(Stats.wpopulationvar, (n1001_nomissing_MA,w1001_nomissing_MA), 54504.8888888911)
        self._test(Stats.wpopulationvar, (n1001_missing,w1001_nomissing_numpy), 51849.1649806388)
        self._test(Stats.wpopulationvar, (n1001_missing,w1001_nomissing_MA), 51849.1649806388)
        self._test(Stats.wpopulationvar, (n1001_nomissing_numpy,w1001_missing), 55798.170622262425)
        self._test(Stats.wpopulationvar, (n1001_nomissing_MA,w1001_missing), 55798.170622262425)
        self._test(Stats.wpopulationvar, (n1001_missing,w1001_missing), 53204.6478317361)

    def test_wpopulationvar_1006(self):
        self._test(Stats.wpopulationvar, (n1006_nomissing_numpy,w1006_nomissing_numpy), 55056.5555555538)
        self._test(Stats.wpopulationvar, (n1006_nomissing_MA,w1006_nomissing_numpy), 55056.5555555538)
        self._test(Stats.wpopulationvar, (n1006_nomissing_numpy,w1006_nomissing_MA), 55056.5555555538)
        self._test(Stats.wpopulationvar, (n1006_nomissing_MA,w1006_nomissing_MA), 55056.5555555538)
        self._test(Stats.wpopulationvar, (n1006_missing,w1006_nomissing_numpy), 52365.6083163646)
        self._test(Stats.wpopulationvar, (n1006_missing,w1006_nomissing_MA), 52365.6083163646)
        self._test(Stats.wpopulationvar, (n1006_nomissing_numpy,w1006_missing), 56418.6193084682)
        self._test(Stats.wpopulationvar, (n1006_nomissing_MA,w1006_missing), 56418.6193084682)
        self._test(Stats.wpopulationvar, (n1006_missing,w1006_missing), 53784.14642265374)

    def test_wpopulationvar_1001_exclnpwgts(self):
        self._test(Stats.wpopulationvar, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 54504.8888888911, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1001_nomissing_MA,w1001_nomissing_numpy,), 54504.8888888911, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1001_nomissing_numpy,w1001_nomissing_MA,), 54504.8888888911, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1001_nomissing_MA,w1001_nomissing_MA,), 54504.8888888911, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1001_missing,w1001_nomissing_numpy,), 51849.1649806388, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1001_missing,w1001_nomissing_MA,), 51849.1649806388, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1001_nomissing_numpy,w1001_missing,), 55798.170622262425, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1001_nomissing_MA,w1001_missing,), 55798.170622262425, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1001_missing,w1001_missing,), 53204.6478317361, exclude_nonpositive_weights=True)

    def test_wpopulationvar_1006_exclnpwgts(self):
        self._test(Stats.wpopulationvar, (n1006_nomissing_numpy,w1006_nomissing_numpy,), 55056.5555555538, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1006_nomissing_MA,w1006_nomissing_numpy,), 55056.5555555538, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1006_nomissing_numpy,w1006_nomissing_MA,), 55056.5555555538, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1006_nomissing_MA,w1006_nomissing_MA,), 55056.5555555538, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1006_missing,w1006_nomissing_numpy,), 52365.6083163646, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1006_missing,w1006_nomissing_MA,), 52365.6083163646, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1006_nomissing_numpy,w1006_missing,), 56418.6193084682, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1006_nomissing_MA,w1006_missing,), 56418.6193084682, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulationvar, (n1006_missing,w1006_missing,), 53784.14642265374, exclude_nonpositive_weights=True)

    def test_sample_stddev_1001(self):
        self._test(Stats.sample_stddev, n1001_nomissing_numpy, 289.108111266)
        self._test(Stats.sample_stddev, n1001_nomissing_MA, 289.108111266)
        self._test(Stats.sample_stddev, n1001_missing, 288.710251844)

    def test_sample_stddev_1006(self):
        self._test(Stats.sample_stddev, n1006_nomissing_numpy, 290.551487118)
        self._test(Stats.sample_stddev, n1006_nomissing_MA, 290.551487118)
        self._test(Stats.sample_stddev, n1006_missing,  290.094880483)
    
    def test_wsample_stddev_1001(self):
        self._test(Stats.wsample_stddev, (n1001_nomissing_numpy,w1001_nomissing_numpy), 233.463535105)
        self._test(Stats.wsample_stddev, (n1001_nomissing_MA,w1001_nomissing_numpy), 233.463535105)
        self._test(Stats.wsample_stddev, (n1001_nomissing_numpy,w1001_nomissing_MA), 233.463535105)
        self._test(Stats.wsample_stddev, (n1001_nomissing_MA,w1001_nomissing_MA), 233.463535105)
        self._test(Stats.wsample_stddev, (n1001_missing,w1001_nomissing_numpy), 227.704839819)
        self._test(Stats.wsample_stddev, (n1001_missing,w1001_nomissing_MA), 227.704839819)
        self._test(Stats.wsample_stddev, (n1001_nomissing_numpy,w1001_missing), 236.217130718)
        self._test(Stats.wsample_stddev, (n1001_nomissing_MA,w1001_missing), 236.217130718)
        self._test(Stats.wsample_stddev, (n1001_missing,w1001_missing), 230.662105957)

    def test_wsample_stddev_1001_exclnpwgts(self):
        self._test(Stats.wsample_stddev, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 233.463535105, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_stddev, (n1001_nomissing_MA,w1001_nomissing_numpy,), 233.463535105, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_stddev, (n1001_nomissing_numpy,w1001_nomissing_MA,), 233.463535105, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_stddev, (n1001_nomissing_MA,w1001_nomissing_MA,), 233.463535105, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_stddev, (n1001_missing,w1001_nomissing_numpy,), 227.704839819, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_stddev, (n1001_missing,w1001_nomissing_MA,), 227.704839819, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_stddev, (n1001_nomissing_numpy,w1001_missing,), 236.217130718, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_stddev, (n1001_nomissing_MA,w1001_missing,), 236.217130718, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_stddev, (n1001_missing,w1001_missing,), 230.662105957, exclude_nonpositive_weights=True)

    def test_population_stddev_1001(self):
        self._test(Stats.population_stddev, n1001_nomissing_numpy, 288.963665536)
        self._test(Stats.population_stddev, n1001_nomissing_MA, 288.963665536)
        self._test(Stats.population_stddev, n1001_missing, 288.554654823)

    def test_population_stddev_1006(self):
        self._test(Stats.population_stddev, n1006_nomissing_numpy, 290.407)
        self._test(Stats.population_stddev, n1006_nomissing_MA, 290.407)
        self._test(Stats.population_stddev, n1006_missing,  289.939375309)

    def test_wpopulation_stddev_1006(self):
        self._test(Stats.wpopulation_stddev, (n1006_nomissing_numpy,w1006_nomissing_numpy), 234.64133386)
        self._test(Stats.wpopulation_stddev, (n1006_nomissing_MA,w1006_nomissing_numpy), 234.64133386)
        self._test(Stats.wpopulation_stddev, (n1006_nomissing_numpy,w1006_nomissing_MA), 234.64133386)
        self._test(Stats.wpopulation_stddev, (n1006_nomissing_MA,w1006_nomissing_MA), 234.64133386)
        self._test(Stats.wpopulation_stddev, (n1006_missing,w1006_nomissing_numpy), 228.835330131)
        self._test(Stats.wpopulation_stddev, (n1006_missing,w1006_nomissing_MA), 228.835330131)
        self._test(Stats.wpopulation_stddev, (n1006_nomissing_numpy,w1006_missing), 237.526)
        self._test(Stats.wpopulation_stddev, (n1006_nomissing_MA,w1006_missing), 237.526)
        self._test(Stats.wpopulation_stddev, (n1006_missing,w1006_missing), 231.914092773)

    def test_sample_cv_misc(self):
        self._test(Stats.sample_cv, empty_numeric, None)
        self._test(Stats.sample_cv, empty_ma, None)
        self._test(Stats.sample_cv, populated_numeric, 52.9728463364)
        self._test(Stats.sample_cv, populated_ma, 52.9728463364)
        self._test(Stats.sample_cv, null_mask, 52.9728463364)
        self._test(Stats.sample_cv, full_mask, None)
        self._test(Stats.sample_cv, partial_mask, 60.6091526731)
        self._test(Stats.sample_cv, two_elements_numeric, 60.6091526731)
        self._test(Stats.sample_cv, two_elements_ma, 60.6091526731)
        self._test(Stats.sample_cv, one_element_numeric, None)
        self._test(Stats.sample_cv, one_element_ma, None)
        self._test(Stats.sample_cv, one_neg_element_numeric, None)
        self._test(Stats.sample_cv, one_neg_element_ma, None)
        self._test(Stats.sample_cv, all_neg_numeric, -180.2347577501)
        self._test(Stats.sample_cv, all_neg_ma, -180.2347577501)

    def test_wsample_cv_misc(self):
        self._test(Stats.wsample_cv, (empty_numeric,empty_numeric), None)
        self._test(Stats.wsample_cv, (empty_ma,empty_numeric), None)
        self._test(Stats.wsample_cv, (empty_numeric,empty_ma), None)
        self._test(Stats.wsample_cv, (empty_ma,empty_ma), None)
        self._test(Stats.wsample_cv, (populated_numeric,populated_numeric), 39.1550719335)
        self._test(Stats.wsample_cv, (populated_numeric,populated_ma), 39.1550719335)
        self._test(Stats.wsample_cv, (populated_ma,populated_numeric), 39.1550719335)
        self._test(Stats.wsample_cv, (populated_ma,populated_ma), 39.1550719335)
        self._test(Stats.wsample_cv, (null_mask,null_mask), 39.1550719335)
        self._test(Stats.wsample_cv, (full_mask,null_mask), None)
        self._test(Stats.wsample_cv, (full_mask,partial_mask), None)
        self._test(Stats.wsample_cv, (full_mask,full_mask), None)
        self._test(Stats.wsample_cv, (null_mask,full_mask), None)
        self._test(Stats.wsample_cv, (partial_mask,full_mask), None)
        self._test(Stats.wsample_cv, (full_mask,full_mask), None)
        self._test(Stats.wsample_cv, (partial_mask,partial_mask), 35.3343129861)
        self._test(Stats.wsample_cv, (two_elements_numeric,two_elements_numeric), 35.3343129861)
        self._test(Stats.wsample_cv, (two_elements_ma,two_elements_numeric), 35.3343129861)
        self._test(Stats.wsample_cv, (two_elements_numeric,two_elements_ma), 35.3343129861)
        self._test(Stats.wsample_cv, (two_elements_ma,two_elements_ma), 35.3343129861)
        self._test(Stats.wsample_cv, (one_element_numeric,one_element_numeric), 0.0)
        self._test(Stats.wsample_cv, (one_element_ma,one_element_numeric), 0.0)
        self._test(Stats.wsample_cv, (one_element_numeric,one_element_ma), 0.0)
        self._test(Stats.wsample_cv, (one_element_ma,one_element_ma), 0.0)
        self._test(Stats.wsample_cv, (one_neg_element_numeric,one_neg_element_ma), None)
        self._test(Stats.wsample_cv, (one_neg_element_ma,one_neg_element_ma), None)
        self._test(Stats.wsample_cv, (one_neg_element_numeric,one_neg_element_numeric), None)
        self._test(Stats.wsample_cv, (one_neg_element_ma,one_neg_element_numeric), None)
        self._test(Stats.wsample_cv, (all_neg_numeric,all_neg_numeric), None)
        self._test(Stats.wsample_cv, (all_neg_ma,all_neg_numeric), None)
        self._test(Stats.wsample_cv, (all_neg_numeric,all_neg_ma), None)
        self._test(Stats.wsample_cv, (all_neg_ma,all_neg_ma), None)

    def test_wsample_cv_misc_exclnpwgts(self):
        self._test(Stats.wsample_cv, (empty_numeric,empty_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (empty_ma,empty_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (empty_numeric,empty_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (empty_ma,empty_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (populated_numeric,populated_numeric), 39.1550719335, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (populated_numeric,populated_ma), 39.1550719335, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (populated_ma,populated_numeric), 39.1550719335, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (populated_ma,populated_ma), 39.1550719335, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (null_mask,null_mask), 39.1550719335, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (full_mask,null_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (full_mask,partial_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (full_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (null_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (partial_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (full_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (partial_mask,partial_mask), 35.3343129861, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (two_elements_numeric,two_elements_numeric), 35.3343129861, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (two_elements_ma,two_elements_numeric), 35.3343129861, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (two_elements_numeric,two_elements_ma), 35.3343129861, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (two_elements_ma,two_elements_ma), 35.3343129861, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (one_element_numeric,one_element_numeric), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (one_element_ma,one_element_numeric), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (one_element_numeric,one_element_ma), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (one_element_ma,one_element_ma), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (one_neg_element_numeric,one_neg_element_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (one_neg_element_ma,one_neg_element_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (one_neg_element_numeric,one_neg_element_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (one_neg_element_ma,one_neg_element_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (all_neg_numeric,all_neg_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (all_neg_ma,all_neg_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (all_neg_numeric,all_neg_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (all_neg_ma,all_neg_ma), None, exclude_nonpositive_weights=True)

    def test_sample_cv_1001(self):
        self._test(Stats.sample_cv, n1001_nomissing_numpy, 59.0016553605)
        self._test(Stats.sample_cv, n1001_nomissing_MA, 59.0016553605)
        self._test(Stats.sample_cv, n1001_missing, 56.6907065543)

    def test_sample_cv_1006(self):
        self._test(Stats.sample_cv, n1006_nomissing_numpy, 58.9952258108)
        self._test(Stats.sample_cv, n1006_nomissing_MA, 58.9952258108)
        self._test(Stats.sample_cv, n1006_missing,  56.6741050507)
    
    def test_wsample_cv_1001(self):
        self._test(Stats.wsample_cv, (n1001_nomissing_numpy,w1001_nomissing_numpy), 35.3554066287)
        self._test(Stats.wsample_cv, (n1001_nomissing_MA,w1001_nomissing_numpy), 35.3554066287)
        self._test(Stats.wsample_cv, (n1001_nomissing_numpy,w1001_nomissing_MA), 35.3554066287)
        self._test(Stats.wsample_cv, (n1001_nomissing_MA,w1001_nomissing_MA), 35.3554066287)
        self._test(Stats.wsample_cv, (n1001_missing,w1001_nomissing_numpy), 33.8494339393)
        self._test(Stats.wsample_cv, (n1001_missing,w1001_nomissing_MA), 33.8494339393)
        self._test(Stats.wsample_cv, (n1001_nomissing_numpy,w1001_missing), 36.1572681672)
        self._test(Stats.wsample_cv, (n1001_nomissing_MA,w1001_missing), 36.1572681672)
        self._test(Stats.wsample_cv, (n1001_missing,w1001_missing), 34.6246930045)

    def test_wsample_cv_1001_exclnpwgts(self):
        self._test(Stats.wsample_cv, (n1001_nomissing_numpy,w1001_nomissing_numpy,), 35.3554066287, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (n1001_nomissing_MA,w1001_nomissing_numpy,), 35.3554066287, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (n1001_nomissing_numpy,w1001_nomissing_MA,), 35.3554066287, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (n1001_nomissing_MA,w1001_nomissing_MA,), 35.3554066287, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (n1001_missing,w1001_nomissing_numpy,), 33.8494339393, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (n1001_missing,w1001_nomissing_MA,), 33.8494339393, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (n1001_nomissing_numpy,w1001_missing,), 36.1572681672, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (n1001_nomissing_MA,w1001_missing,), 36.1572681672, exclude_nonpositive_weights=True)
        self._test(Stats.wsample_cv, (n1001_missing,w1001_missing,), 34.6246930045, exclude_nonpositive_weights=True)

    def test_population_cv_misc(self):
        self._test(Stats.population_cv, empty_numeric, None)
        self._test(Stats.population_cv, empty_ma, None)
        self._test(Stats.population_cv, populated_numeric, 47.3803541479)
        self._test(Stats.population_cv, populated_ma, 47.3803541479)
        self._test(Stats.population_cv, null_mask, 47.3803541479)
        self._test(Stats.population_cv, full_mask, None)
        self._test(Stats.population_cv, partial_mask, 42.8571428571)
        self._test(Stats.population_cv, two_elements_numeric, 42.8571428571)
        self._test(Stats.population_cv, two_elements_ma, 42.8571428571)
        self._test(Stats.population_cv, one_element_numeric, 0.0)
        self._test(Stats.population_cv, one_element_ma, 0.0)
        self._test(Stats.population_cv, one_neg_element_numeric, 0.0)
        self._test(Stats.population_cv, one_neg_element_ma, 0.0)
        self._test(Stats.population_cv, all_neg_numeric, -161.2068680950)
        self._test(Stats.population_cv, all_neg_ma, -161.2068680950)

    def test_wpopulation_cv_misc(self):
        self._test(Stats.wpopulation_cv, (empty_numeric,empty_numeric), None)
        self._test(Stats.wpopulation_cv, (empty_ma,empty_numeric), None)
        self._test(Stats.wpopulation_cv, (empty_numeric,empty_ma), None)
        self._test(Stats.wpopulation_cv, (empty_ma,empty_ma), None)
        self._test(Stats.wpopulation_cv, (populated_numeric,populated_numeric), 37.7307714089)
        self._test(Stats.wpopulation_cv, (populated_numeric,populated_ma), 37.7307714089)
        self._test(Stats.wpopulation_cv, (populated_ma,populated_numeric), 37.7307714089)
        self._test(Stats.wpopulation_cv, (populated_ma,populated_ma), 37.7307714089)
        self._test(Stats.wpopulation_cv, (null_mask,null_mask), 37.7307714089)
        self._test(Stats.wpopulation_cv, (full_mask,null_mask), None)
        self._test(Stats.wpopulation_cv, (full_mask,partial_mask), None)
        self._test(Stats.wpopulation_cv, (full_mask,full_mask), None)
        self._test(Stats.wpopulation_cv, (null_mask,full_mask), None)
        self._test(Stats.wpopulation_cv, (partial_mask,full_mask), None)
        self._test(Stats.wpopulation_cv, (full_mask,full_mask), None)
        self._test(Stats.wpopulation_cv, (partial_mask,partial_mask), 32.7132171742)
        self._test(Stats.wpopulation_cv, (two_elements_numeric,two_elements_numeric), 32.7132171742)
        self._test(Stats.wpopulation_cv, (two_elements_ma,two_elements_numeric), 32.7132171742)
        self._test(Stats.wpopulation_cv, (two_elements_numeric,two_elements_ma), 32.7132171742)
        self._test(Stats.wpopulation_cv, (two_elements_ma,two_elements_ma), 32.7132171742)
        self._test(Stats.wpopulation_cv, (one_element_numeric,one_element_numeric), 0.0)
        self._test(Stats.wpopulation_cv, (one_element_ma,one_element_numeric), 0.0)
        self._test(Stats.wpopulation_cv, (one_element_numeric,one_element_ma), 0.0)
        self._test(Stats.wpopulation_cv, (one_element_ma,one_element_ma), 0.0)
        self._test(Stats.wpopulation_cv, (one_neg_element_numeric,one_neg_element_ma), None)
        self._test(Stats.wpopulation_cv, (one_neg_element_ma,one_neg_element_ma), None)
        self._test(Stats.wpopulation_cv, (one_neg_element_numeric,one_neg_element_numeric), None)
        self._test(Stats.wpopulation_cv, (one_neg_element_ma,one_neg_element_numeric), None)
        self._test(Stats.wpopulation_cv, (all_neg_numeric,all_neg_numeric), None)
        self._test(Stats.wpopulation_cv, (all_neg_ma,all_neg_numeric), None)
        self._test(Stats.wpopulation_cv, (all_neg_numeric,all_neg_ma), None)
        self._test(Stats.wpopulation_cv, (all_neg_ma,all_neg_ma), None)

    def test_wpopulation_cv_misc_exclnpwgts(self):
        self._test(Stats.wpopulation_cv, (empty_numeric,empty_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (empty_ma,empty_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (empty_numeric,empty_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (empty_ma,empty_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (populated_numeric,populated_numeric), 37.7307714089, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (populated_numeric,populated_ma), 37.7307714089, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (populated_ma,populated_numeric), 37.7307714089, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (populated_ma,populated_ma), 37.7307714089, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (null_mask,null_mask), 37.7307714089, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (full_mask,null_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (full_mask,partial_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (full_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (null_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (partial_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (full_mask,full_mask), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (partial_mask,partial_mask), 32.7132171742, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (two_elements_numeric,two_elements_numeric), 32.7132171742, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (two_elements_ma,two_elements_numeric), 32.7132171742, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (two_elements_numeric,two_elements_ma), 32.7132171742, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (two_elements_ma,two_elements_ma), 32.7132171742, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (one_element_numeric,one_element_numeric), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (one_element_ma,one_element_numeric), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (one_element_numeric,one_element_ma), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (one_element_ma,one_element_ma), 0.0, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (one_neg_element_numeric,one_neg_element_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (one_neg_element_ma,one_neg_element_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (one_neg_element_numeric,one_neg_element_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (one_neg_element_ma,one_neg_element_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (all_neg_numeric,all_neg_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (all_neg_ma,all_neg_numeric), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (all_neg_numeric,all_neg_ma), None, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (all_neg_ma,all_neg_ma), None, exclude_nonpositive_weights=True)

    def test_population_cv_1001(self):
        self._test(Stats.population_cv, n1001_nomissing_numpy, 58.9721766400)
        self._test(Stats.population_cv, n1001_nomissing_MA, 58.9721766400)
        self._test(Stats.population_cv, n1001_missing, 56.6601537596)

    def test_population_cv_1006(self):
        self._test(Stats.population_cv, n1006_nomissing_numpy, 58.9658968377)
        self._test(Stats.population_cv, n1006_nomissing_MA, 58.9658968377)
        self._test(Stats.population_cv, n1006_missing,  56.6437249332)

    def test_wpopulation_cv_1006(self):
        self._test(Stats.wpopulation_cv, (n1006_nomissing_numpy,w1006_nomissing_numpy), 35.3552989241)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_MA,w1006_nomissing_numpy), 35.3552989241)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_numpy,w1006_nomissing_MA), 35.3552989241)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_MA,w1006_nomissing_MA), 35.3552989241)
        self._test(Stats.wpopulation_cv, (n1006_missing,w1006_nomissing_numpy), 33.8499398934)
        self._test(Stats.wpopulation_cv, (n1006_missing,w1006_nomissing_MA), 33.8499398934)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_numpy,w1006_missing), 36.1577798983)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_MA,w1006_missing), 36.1577798983)
        self._test(Stats.wpopulation_cv, (n1006_missing,w1006_missing), 34.6248792762)

    def test_wpopulation_cv_1006_exclnpwgts(self):
        self._test(Stats.wpopulation_cv, (n1006_nomissing_numpy,w1006_nomissing_numpy,), 35.3552989241, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_MA,w1006_nomissing_numpy,), 35.3552989241, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_numpy,w1006_nomissing_MA,), 35.3552989241, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_MA,w1006_nomissing_MA,), 35.3552989241, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (n1006_missing,w1006_nomissing_numpy,), 33.8499398934, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (n1006_missing,w1006_nomissing_MA,), 33.8499398934, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_numpy,w1006_missing,), 36.1577798983, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (n1006_nomissing_MA,w1006_missing,), 36.1577798983, exclude_nonpositive_weights=True)
        self._test(Stats.wpopulation_cv, (n1006_missing,w1006_missing,), 34.6248792762, exclude_nonpositive_weights=True)

    def test_stderr_misc(self):
        self._test(Stats.stderr, empty_numeric, None)
        self._test(Stats.stderr, empty_ma, None)
        self._test(Stats.stderr, populated_numeric, 0.6633249581)
        self._test(Stats.stderr, populated_ma, 0.6633249581)
        self._test(Stats.stderr, null_mask, 0.6633249581)
        self._test(Stats.stderr, full_mask, None)
        self._test(Stats.stderr, partial_mask, 1.5)
        self._test(Stats.stderr, two_elements_numeric, 1.5)
        self._test(Stats.stderr, two_elements_ma, 1.5)
        self._test(Stats.stderr, one_element_numeric, None)
        self._test(Stats.stderr, one_element_ma, None)
        self._test(Stats.stderr, one_neg_element_numeric, None)
        self._test(Stats.stderr, one_neg_element_ma, None)
        self._test(Stats.stderr, all_neg_numeric, 14.5086181285)
        self._test(Stats.stderr, all_neg_ma, 14.5086181285)

    def test_stderr_1001(self):
        self._test(Stats.stderr, n1001_nomissing_numpy, 9.1378334412)
        self._test(Stats.stderr, n1001_nomissing_MA, 9.1378334412)
        self._test(Stats.stderr, n1001_missing, 9.4773783249)

    def test_stderr_1006(self):
        self._test(Stats.stderr, n1006_nomissing_numpy, 9.1606040558)
        self._test(Stats.stderr, n1006_nomissing_MA, 9.1606040558)
        self._test(Stats.stderr, n1006_missing, 9.4972800124)

    def test_wstderr_1006(self):
        self._test(Stats.wstderr, (n1006_nomissing_numpy,w1006_nomissing_numpy), 7.40153)
        self._test(Stats.wstderr, (n1006_nomissing_MA,w1006_nomissing_numpy), 7.40153)
        self._test(Stats.wstderr, (n1006_nomissing_numpy,w1006_nomissing_MA), 7.40153)
        self._test(Stats.wstderr, (n1006_nomissing_MA,w1006_nomissing_MA), 7.40153)
        self._test(Stats.wstderr, (n1006_missing,w1006_nomissing_numpy), 7.49575)
        self._test(Stats.wstderr, (n1006_missing,w1006_nomissing_MA), 7.49575)
        self._test(Stats.wstderr, (n1006_nomissing_numpy,w1006_missing), 7.63832)
        self._test(Stats.wstderr, (n1006_nomissing_MA,w1006_missing), 7.63832)
        self._test(Stats.wstderr, (n1006_missing,w1006_missing), 7.75637)

    def test_wstderr_misc(self):
        self._test(Stats.wstderr, (Numeric.array([1,2,3,4,5]),Numeric.array([2,2,1,1,1])), 0.699854212224)

    def test_t_misc(self):
        self._test(Stats.t, empty_numeric, None)
        self._test(Stats.t, empty_ma, None)
        self._test(Stats.t, populated_numeric, 4.2211588241)
        self._test(Stats.t, populated_ma, 4.2211588241)
        self._test(Stats.t, null_mask, 4.2211588241)
        self._test(Stats.t, full_mask, None)
        self._test(Stats.t, partial_mask, 2.333333333)
        self._test(Stats.t, two_elements_numeric, 2.333333333)
        self._test(Stats.t, two_elements_ma, 2.333333333)
        self._test(Stats.t, one_element_numeric, None)
        self._test(Stats.t, one_element_ma, None)
        self._test(Stats.t, one_neg_element_numeric, None)
        self._test(Stats.t, one_neg_element_ma, None)
        self._test(Stats.t, all_neg_numeric, -1.2406419302)
        self._test(Stats.t, all_neg_ma, -1.2406419302)

    def test_t_1001(self):
        self._test(Stats.t, n1001_nomissing_numpy, 53.6232142061)
        self._test(Stats.t, n1001_nomissing_MA, 53.6232142061)
        self._test(Stats.t, n1001_missing, 53.7356019620)

    def test_t_1006(self):
        self._test(Stats.t, n1006_nomissing_numpy, 53.7628301585)
        self._test(Stats.t, n1006_nomissing_MA, 53.7628301585)
        self._test(Stats.t, n1006_missing, 53.8959524307)

    def test_probit(self):
        # all results calculated by SAS V8.2 on Windows probit() function, except
        # where indicated
        self._stricttest(Stats.probit,0.0000001, -5.199337582)
        self._stricttest(Stats.probit,0.000001, -4.753424309)
        self._stricttest(Stats.probit,0.00001, -4.264890794)
        self._stricttest(Stats.probit,0.0001, -3.719016485)
        self._stricttest(Stats.probit,0.001, -3.090232306)
        self._stricttest(Stats.probit,0.01, -2.326347874)
        self._stricttest(Stats.probit,0.3000007, -0.524398510595) # SAS probit(0.3000007) gives -0.524398499
        self._stricttest(Stats.probit,0.300007, -0.52438038)
        self._stricttest(Stats.probit,0.30007, -0.524199196)
        self._stricttest(Stats.probit,0.3007, -0.522388301)
        self._stricttest(Stats.probit,0.307, -0.504371986)
        self._stricttest(Stats.probit,0.37, -0.331853358115) # SAS probit(0.37) gives -0.331853346
        self._stricttest(Stats.probit,0.5000001, 2.5066283e-7)
        self._stricttest(Stats.probit,0.500001, 2.5066283e-6)
        self._stricttest(Stats.probit,0.50001, 0.0000250663)
        self._stricttest(Stats.probit,0.5001, 0.0002506628)
        self._stricttest(Stats.probit,0.501, 0.0025066309)
        self._stricttest(Stats.probit,0.51, 0.0250689083)
        self._stricttest(Stats.probit,0.8456789, 1.0180752422)
        self._stricttest(Stats.probit,0.845678, 1.01807143956) # SAS probit(0.845678) gives 1.0180714543
        self._stricttest(Stats.probit,0.84567, 1.0180377846)
        self._stricttest(Stats.probit,0.8456, 1.0177432241)
        self._stricttest(Stats.probit,0.845, 1.0152220332)
        self._stricttest(Stats.probit,0.84, 0.9944578832)
        self._stricttest(Stats.probit,0.9999999, 5.1993375823)
        self._stricttest(Stats.probit,0.999999, 4.7534243088)
        self._stricttest(Stats.probit,0.99999, 4.2648907939)
        self._stricttest(Stats.probit,0.9999, 3.7190164855)
        self._stricttest(Stats.probit,0.999, 3.0902323062)
        self._stricttest(Stats.probit,0.99, 2.326347874)
        self._stricttest(Stats.probit,0.975, 1.9599639845)
        self._stricttest(Stats.probit,0.025, -1.959963985 )
        self._stricttest(Stats.probit,0.0, -1.0e20) # SAS returns an error
        self._stricttest(Stats.probit,0.1, -1.281551566)
        self._stricttest(Stats.probit,0.2, -0.841621234)
        self._stricttest(Stats.probit,0.3, -0.524400513)
        self._stricttest(Stats.probit,0.4, -0.253347103)
        self._stricttest(Stats.probit,0.5, -4.06379E-17) # NetEpi Analysis Probit returns 0.0
        self._stricttest(Stats.probit,0.6, 0.2533471031)
        self._stricttest(Stats.probit,0.7, 0.5244005127)
        self._stricttest(Stats.probit,0.8, 0.8416212336)
        self._stricttest(Stats.probit,0.9, 1.2815515655)
        self._stricttest(Stats.probit,1.0, 1.0e20) # SAS returns an error

    def test_cdf_gauss_GL(self):
        # all results calculated by SAS V8.2 on Windows probnorm() function, except
        # where indicated
        self._stricttest(Stats.cdf_gauss_GL,-10,7.619853E-24)
        self._stricttest(Stats.cdf_gauss_GL,-9.5, 1.049452E-21)
        self._stricttest(Stats.cdf_gauss_GL,-9.0,1.128588E-19)
        self._stricttest(Stats.cdf_gauss_GL,-8.5, 9.479535E-18)
        self._stricttest(Stats.cdf_gauss_GL,-8.0,6.220961E-16)
        self._stricttest(Stats.cdf_gauss_GL,-7.5, 3.190892E-14)
        self._stricttest(Stats.cdf_gauss_GL,-7.0,1.279813E-12)
        self._stricttest(Stats.cdf_gauss_GL,-6.5, 4.016001E-11)
        self._stricttest(Stats.cdf_gauss_GL,-6.0,9.865876E-10)
        self._stricttest(Stats.cdf_gauss_GL,-5.5, 1.8989562E-8)
        self._stricttest(Stats.cdf_gauss_GL,-5.0,2.8665157E-7)
        self._stricttest(Stats.cdf_gauss_GL,-4.5, 3.3976731E-6)
        self._stricttest(Stats.cdf_gauss_GL,-4.0,0.0000316712)
        self._stricttest(Stats.cdf_gauss_GL,-3.5, 0.0002326291)
        self._stricttest(Stats.cdf_gauss_GL,-3.0,0.001349898)
        self._stricttest(Stats.cdf_gauss_GL,-2.5, 0.0062096653)
        self._stricttest(Stats.cdf_gauss_GL,-2.0,0.0227501319)
        self._stricttest(Stats.cdf_gauss_GL,-1.9, 0.0287165598)
        self._stricttest(Stats.cdf_gauss_GL,-1.8, 0.0359303191)
        self._stricttest(Stats.cdf_gauss_GL,-1.7, 0.0445654628)
        self._stricttest(Stats.cdf_gauss_GL,-1.6, 0.0547992917)
        self._stricttest(Stats.cdf_gauss_GL,-1.5, 0.0668072013)
        self._stricttest(Stats.cdf_gauss_GL,-1.4, 0.0807566592)
        self._stricttest(Stats.cdf_gauss_GL,-1.3, 0.0968004846)
        self._stricttest(Stats.cdf_gauss_GL,-1.2, 0.1150696702)
        self._stricttest(Stats.cdf_gauss_GL,-1.1, 0.1356660609)
        self._stricttest(Stats.cdf_gauss_GL,-1.0,0.1586552539)
        self._stricttest(Stats.cdf_gauss_GL,-0.9, 0.1840601253)
        self._stricttest(Stats.cdf_gauss_GL,-0.8, 0.2118553986)
        self._stricttest(Stats.cdf_gauss_GL,-0.7, 0.2419636522)
        self._stricttest(Stats.cdf_gauss_GL,-0.6, 0.2742531178)
        self._stricttest(Stats.cdf_gauss_GL,-0.5, 0.3085375387)
        self._stricttest(Stats.cdf_gauss_GL,-0.4, 0.3445782584)
        self._stricttest(Stats.cdf_gauss_GL,-0.3, 0.3820885778)
        self._stricttest(Stats.cdf_gauss_GL,-0.2, 0.4207402906)
        self._stricttest(Stats.cdf_gauss_GL,-0.1, 0.4601721627)
        self._stricttest(Stats.cdf_gauss_GL,0.0,0.5)
        self._stricttest(Stats.cdf_gauss_GL,0.1, 0.5398278373)
        self._stricttest(Stats.cdf_gauss_GL,0.2, 0.5792597094)
        self._stricttest(Stats.cdf_gauss_GL,0.3, 0.6179114222)
        self._stricttest(Stats.cdf_gauss_GL,0.4, 0.6554217416)
        self._stricttest(Stats.cdf_gauss_GL,0.5, 0.6914624613)
        self._stricttest(Stats.cdf_gauss_GL,0.6, 0.7257468822)
        self._stricttest(Stats.cdf_gauss_GL,0.7, 0.7580363478)
        self._stricttest(Stats.cdf_gauss_GL,0.8, 0.7881446014)
        self._stricttest(Stats.cdf_gauss_GL,0.9, 0.8159398747)
        self._stricttest(Stats.cdf_gauss_GL,1.0,0.8413447461)
        self._stricttest(Stats.cdf_gauss_GL,1.1, 0.8643339391)
        self._stricttest(Stats.cdf_gauss_GL,1.2, 0.8849303298)
        self._stricttest(Stats.cdf_gauss_GL,1.3, 0.9031995154)
        self._stricttest(Stats.cdf_gauss_GL,1.4, 0.9192433408)
        self._stricttest(Stats.cdf_gauss_GL,1.5, 0.9331927987)
        self._stricttest(Stats.cdf_gauss_GL,1.6, 0.9452007083)
        self._stricttest(Stats.cdf_gauss_GL,1.7, 0.9554345372)
        self._stricttest(Stats.cdf_gauss_GL,1.8, 0.9640696809)
        self._stricttest(Stats.cdf_gauss_GL,1.9, 0.9712834402)
        self._stricttest(Stats.cdf_gauss_GL,2.0,0.9772498681)
        self._stricttest(Stats.cdf_gauss_GL,2.5, 0.9937903347)
        self._stricttest(Stats.cdf_gauss_GL,3.0,0.998650102)
        self._stricttest(Stats.cdf_gauss_GL,3.5, 0.9997673709)
        self._stricttest(Stats.cdf_gauss_GL,4.0,0.9999683288)
        self._stricttest(Stats.cdf_gauss_GL,4.5, 0.9999966023)
        self._stricttest(Stats.cdf_gauss_GL,5.0,0.9999997133)
        self._stricttest(Stats.cdf_gauss_GL,5.5, 0.999999981)
        self._stricttest(Stats.cdf_gauss_GL,6.0,0.999999999)
        self._stricttest(Stats.cdf_gauss_GL,6.5, 1)
        self._stricttest(Stats.cdf_gauss_GL,7.0,1)
        self._stricttest(Stats.cdf_gauss_GL,7.5, 1)
        self._stricttest(Stats.cdf_gauss_GL,8.0,1)
        self._stricttest(Stats.cdf_gauss_GL,8.5, 1)
        self._stricttest(Stats.cdf_gauss_GL,9.0,1)
        self._stricttest(Stats.cdf_gauss_GL,9.5, 1)
        self._stricttest(Stats.cdf_gauss_GL,10.0,1 )

    def test_cdf_gauss(self):
        if Cstats is None:
            return
        # all results calculated by SAS V8.2 on Windows probnorm() function,
        # except where indicated
        self._stricttest(Cstats.cdf_gauss,-10,7.619853E-24)
        self._stricttest(Cstats.cdf_gauss,-9.5, 1.049452E-21)
        self._stricttest(Cstats.cdf_gauss,-9.0,1.128588E-19)
        self._stricttest(Cstats.cdf_gauss,-8.5, 9.479535E-18)
        self._stricttest(Cstats.cdf_gauss,-8.0,6.220961E-16)
        self._stricttest(Cstats.cdf_gauss,-7.5, 3.190892E-14)
        self._stricttest(Cstats.cdf_gauss,-7.0,1.279813E-12)
        self._stricttest(Cstats.cdf_gauss,-6.5, 4.016001E-11)
        self._stricttest(Cstats.cdf_gauss,-6.0,9.865876E-10)
        self._stricttest(Cstats.cdf_gauss,-5.5, 1.8989562E-8)
        self._stricttest(Cstats.cdf_gauss,-5.0,2.8665157E-7)
        self._stricttest(Cstats.cdf_gauss,-4.5, 3.3976731E-6)
        self._stricttest(Cstats.cdf_gauss,-4.0,0.0000316712)
        self._stricttest(Cstats.cdf_gauss,-3.5, 0.0002326291)
        self._stricttest(Cstats.cdf_gauss,-3.0,0.001349898)
        self._stricttest(Cstats.cdf_gauss,-2.5, 0.0062096653)
        self._stricttest(Cstats.cdf_gauss,-2.0,0.0227501319)
        self._stricttest(Cstats.cdf_gauss,-1.9, 0.0287165598)
        self._stricttest(Cstats.cdf_gauss,-1.8, 0.0359303191)
        self._stricttest(Cstats.cdf_gauss,-1.7, 0.0445654628)
        self._stricttest(Cstats.cdf_gauss,-1.6, 0.0547992917)
        self._stricttest(Cstats.cdf_gauss,-1.5, 0.0668072013)
        self._stricttest(Cstats.cdf_gauss,-1.4, 0.0807566592)
        self._stricttest(Cstats.cdf_gauss,-1.3, 0.0968004846)
        self._stricttest(Cstats.cdf_gauss,-1.2, 0.1150696702)
        self._stricttest(Cstats.cdf_gauss,-1.1, 0.1356660609)
        self._stricttest(Cstats.cdf_gauss,-1.0,0.1586552539)
        self._stricttest(Cstats.cdf_gauss,-0.9, 0.1840601253)
        self._stricttest(Cstats.cdf_gauss,-0.8, 0.2118553986)
        self._stricttest(Cstats.cdf_gauss,-0.7, 0.2419636522)
        self._stricttest(Cstats.cdf_gauss,-0.6, 0.2742531178)
        self._stricttest(Cstats.cdf_gauss,-0.5, 0.3085375387)
        self._stricttest(Cstats.cdf_gauss,-0.4, 0.3445782584)
        self._stricttest(Cstats.cdf_gauss,-0.3, 0.3820885778)
        self._stricttest(Cstats.cdf_gauss,-0.2, 0.4207402906)
        self._stricttest(Cstats.cdf_gauss,-0.1, 0.4601721627)
        self._stricttest(Cstats.cdf_gauss,0.0,0.5)
        self._stricttest(Cstats.cdf_gauss,0.1, 0.5398278373)
        self._stricttest(Cstats.cdf_gauss,0.2, 0.5792597094)
        self._stricttest(Cstats.cdf_gauss,0.3, 0.6179114222)
        self._stricttest(Cstats.cdf_gauss,0.4, 0.6554217416)
        self._stricttest(Cstats.cdf_gauss,0.5, 0.6914624613)
        self._stricttest(Cstats.cdf_gauss,0.6, 0.7257468822)
        self._stricttest(Cstats.cdf_gauss,0.7, 0.7580363478)
        self._stricttest(Cstats.cdf_gauss,0.8, 0.7881446014)
        self._stricttest(Cstats.cdf_gauss,0.9, 0.8159398747)
        self._stricttest(Cstats.cdf_gauss,1.0,0.8413447461)
        self._stricttest(Cstats.cdf_gauss,1.1, 0.8643339391)
        self._stricttest(Cstats.cdf_gauss,1.2, 0.8849303298)
        self._stricttest(Cstats.cdf_gauss,1.3, 0.9031995154)
        self._stricttest(Cstats.cdf_gauss,1.4, 0.9192433408)
        self._stricttest(Cstats.cdf_gauss,1.5, 0.9331927987)
        self._stricttest(Cstats.cdf_gauss,1.6, 0.9452007083)
        self._stricttest(Cstats.cdf_gauss,1.7, 0.9554345372)
        self._stricttest(Cstats.cdf_gauss,1.8, 0.9640696809)
        self._stricttest(Cstats.cdf_gauss,1.9, 0.9712834402)
        self._stricttest(Cstats.cdf_gauss,2.0,0.9772498681)
        self._stricttest(Cstats.cdf_gauss,2.5, 0.9937903347)
        self._stricttest(Cstats.cdf_gauss,3.0,0.998650102)
        self._stricttest(Cstats.cdf_gauss,3.5, 0.9997673709)
        self._stricttest(Cstats.cdf_gauss,4.0,0.9999683288)
        self._stricttest(Cstats.cdf_gauss,4.5, 0.9999966023)
        self._stricttest(Cstats.cdf_gauss,5.0,0.9999997133)
        self._stricttest(Cstats.cdf_gauss,5.5, 0.999999981)
        self._stricttest(Cstats.cdf_gauss,6.0,0.999999999)
        self._stricttest(Cstats.cdf_gauss,6.5, 1)
        self._stricttest(Cstats.cdf_gauss,7.0,1)
        self._stricttest(Cstats.cdf_gauss,7.5, 1)
        self._stricttest(Cstats.cdf_gauss,8.0,1)
        self._stricttest(Cstats.cdf_gauss,8.5, 1)
        self._stricttest(Cstats.cdf_gauss,9.0,1)
        self._stricttest(Cstats.cdf_gauss,9.5, 1)
        self._stricttest(Cstats.cdf_gauss,10.0,1 )

    if rpy_tests:
        def test_propcl_wald_openepi(self):
            # results checked against those given for OpenEpi for conflev=0.95 - see
            # http://www.openepi.com
            self._stricttest(Stats.propcl,(81,263),(0.30798479087452474,0.2521901258121082, 0.36377945593694128),method='wald')
            self._stricttest(Stats.propcl,(15,148),(0.10135135135135136,0.052730006059349958, 0.14997269664335275),method='wald')
            self._stricttest(Stats.propcl,(0,20),(0.0,0.0, 0.0),method='wald')
            self._stricttest(Stats.propcl,(1,29),(0.034482758620689655,0.0, 0.10089224371696039),method='wald')
            self._stricttest(Stats.propcl,(37,12345),(0.0029971648440664236,0.0020328784065148978, 0.003961451281617949),method='wald')
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10411773863010707, 0.054977863564014226, 0.15325761369619989),method='wald',noninteger='accept')
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10135135135135136,0.052730006059349958, 0.14997269664335275),method='wald',noninteger='truncate')
            self._stricttest(Stats.propcl,(14.65,148.3897),(0.10135135135135136,0.052730006059349958, 0.14997269664335275),method='wald',noninteger='round')

    if rpy_tests:
        def test_propcl_wilsonscore_openepi(self):
            # results checked against those given for OpenEpi for conflev=0.95 - see
            # http://www.openepi.com
            self._stricttest(Stats.propcl,(81,263),(0.30798479087452474,0.25528851952360065, 0.36620957741579707),method='wilsonscore')
            self._stricttest(Stats.propcl,(15,148),(0.10135135135135136,0.062386399313902226, 0.16048724222274599),method='wilsonscore')
            self._stricttest(Stats.propcl,(0,20),(0.0, 0.0, 0.16112515999567781),method='wilsonscore')
            self._stricttest(Stats.propcl,(1,29),(0.034482758620689655,0.0061132142310903054, 0.17175522023715417),method='wilsonscore')
            self._stricttest(Stats.propcl,(0,1234567890),(0.0, 0.0, 3.111581708121877e-09),method='wilsonscore')
            self._stricttest(Stats.propcl,(1,1234567890),(8.1000000737100002e-10,1.4298488937441067e-10, 4.5885968284487044e-09),method='wilsonscore')
            self._stricttest(Stats.propcl,(1234567889,1234567890),(0.99999999919000004,0.99999999541140339, 0.99999999985701526),method='wilsonscore')
            self._stricttest(Stats.propcl,(1234567890,1234567890),(1.0,0.99999999688841834, 1.0),method='wilsonscore')
            self._stricttest(Stats.propcl,(37,12345),(0.0029971648440664236,0.0021753177561375232, 0.004128225708659488),method='wilsonscore')
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10411773863010707,0.064573854610111614, 0.1636413093053814),method='wilsonscore',noninteger='accept')
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10135135135135136,0.062386399313902226, 0.16048724222274599),method='wilsonscore',noninteger='truncate')
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10135135135135136,0.062386399313902226, 0.16048724222274599),method='wilsonscore',noninteger='round')

    if rpy_tests:
        def test_propcl_fleiss_openepi(self):
            # results checked against those given for OpenEpi for conflev=0.95 - see
            # http://www.openepi.com
            self._stricttest(Stats.propcl,(81,263),(0.30798479087452474,0.25350868194154358, 0.36817620147624969),method='fleissquadratic')
            self._stricttest(Stats.propcl,(15,148),(0.10135135135135136,0.059778208217201693, 0.16444977986733081),method='fleissquadratic')
            self._stricttest(Stats.propcl,(0,20),(0.0, 0.0, 0.20045334688974203),method='fleissquadratic')
            self._stricttest(Stats.propcl,(1,29),(0.034482758620689655,0.001802640192242886, 0.19628175244935558),method='fleissquadratic')
            self._stricttest(Stats.propcl,(37,12345),(0.0029971648440664236,0.0021412605029732137, 0.0041751050961838752),method='fleissquadratic')
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10411773863010707,0.061959128597117254, 0.167581040827433),method='fleissquadratic',noninteger='accept')
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10135135135135136,0.059778208217201693, 0.16444977986733081),method='fleissquadratic',noninteger='truncate')
            self._stricttest(Stats.propcl,(15.45,147.8897),(0.10135135135135136,0.059778208217201693, 0.16444977986733081),method='fleissquadratic',noninteger='round')

    if rpy_tests:
        def test_propcl_exact_openepi(self):
            # results checked against those given for OpenEpi for conflev=0.95 - see
            # http://www.openepi.com
            self._stricttest(Stats.propcl,(81,263),(0.30798479087452474,0.25273674558527148, 0.36762192260135129),method='exact')
            self._stricttest(Stats.propcl,(15,148),(0.10135135135135136,0.057844010083448541, 0.16165049034947895),method='exact')
            self._stricttest(Stats.propcl,(0,20),(0.0, 0.0, 0.16843347098308536),method='exact')
            self._stricttest(Stats.propcl,(1,29),(0.034482758620689655,0.00087264688357992194, 0.17764429548872296),method='exact')
            self._stricttest(Stats.propcl,(37,12345),(0.0029971648440664236,0.0021111318528365865, 0.0041288536907305717),method='exact')
            # note that OpenEpi gives (0.0629, 0.1612) for the following, but Agresti's R code gives same answers as Stats.propcl
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10411773863010707,0.060026025569085137, 0.16482490419242998),method='exact',noninteger='accept')

    if rpy_tests:
        def test_propcl_modwald_openepi(self):
            # results checked against those given for OpenEpi for conflev=0.95 - see
            # http://www.openepi.com
            self._stricttest(Stats.propcl,(81,263),(0.30798479087452474,0.25522066483389699, 0.36627743210550062),method='modwald')
            self._stricttest(Stats.propcl,(15,148),(0.10135135135135136,0.061385974691729225, 0.16148766684491894),method='modwald')
            self._stricttest(Stats.propcl,(0,20),(0.0, 0.0, 0.18980956277351352),method='modwald')
            self._stricttest(Stats.propcl,(1,29),(0.034482758620689655,0.0, 0.18628651021203402),method='modwald')
            self._stricttest(Stats.propcl,(37,12345),(0.0029971648440664236,0.0021631574386132956, 0.0041403860261837152),method='modwald')
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10411773863010707,0.063601455596412559, 0.16461370831908045),method='modwald',noninteger='accept')
            
    if rpy_tests:
        def test_propcl_blaker_agresti(self):
            # results checked against those given by R code by Alan Agresti at 
            # http://web.stat.ufl.edu/~aa/cda/R/one_sample/R1/
            # which is a bit circular, since the NetEpi code is derived from this same R code...
            self._stricttest(Stats.propcl,(81,263),(0.30798479087452474,0.25391674558527266, 0.36647192260135014),method='blaker')
            self._stricttest(Stats.propcl,(15,148),(0.10135135135135136,0.057954010083448602, 0.16012049034947745),method='blaker')
            self._stricttest(Stats.propcl,(0,20),(0.0, 0.0, 0.16013347098307706),method='blaker')
            self._stricttest(Stats.propcl,(1,29),(0.034482758620689655,0.0017626468835799233, 0.16604429548871136),method='blaker')
            self._stricttest(Stats.propcl,(81,263),(0.30798479087452474,0.23771735816553957, 0.38513832566974371),method='blaker',conflev=0.99)
            self._stricttest(Stats.propcl,(15,148),(0.10135135135135136,0.048324559728836966, 0.181747531538276),method='blaker',conflev=0.99)
            self._stricttest(Stats.propcl,(0,20),(0.0, 0.0, 0.224209500989066),method='blaker',conflev=0.99)
            self._stricttest(Stats.propcl,(1,29),(0.034482758620689655,0.00034283133272151867, 0.22375030657503353),method='blaker',conflev=0.99)
            self._stricttest(Stats.propcl,(37,12345),(0.0029971648440664236,0.0021311318528365866, 0.004098853690730573),method='blaker')
            # the following values cause the Agresti R code to fail (probably reasonably so, as non-intger iputs aren't entirely
            # kosher, so the results are not independently checked, but are almost identical to the exact results
            self._stricttest(Stats.propcl,(15.45,148.3897),(0.10411773863010707,0.06002602556908513, 0.16482490419243001),method='blaker',noninteger='accept')

    if rpy_tests:
        def test_propcl_badinpts(self):
            # tests for bad inputs (code shared by all methods)
            self.assertRaises(ValueError, Stats.propcl,-1,20)
            self.assertRaises(ValueError, Stats.propcl,1,-20)
            self.assertRaises(ValueError, Stats.propcl,-1,-20)
            self.assertRaises(ValueError, Stats.propcl,21,20)
            self.assertRaises(ValueError, Stats.propcl,20.0000000001,20.0,noninteger='accept')
            self.assertRaises(ValueError, Stats.propcl,21,0)
            self.assertRaises(ValueError, Stats.propcl,21,42,method='humperdinck')
            self.assertRaises(ValueError, Stats.propcl,21,42,conflev=95)
            self.assertRaises(ValueError, Stats.propcl,21,42,conflev=0.45)
            self.assertRaises(ValueError, Stats.propcl,21,42,conflev=-0.95)
            self.assertRaises(ValueError, Stats.propcl,21.3,42,conflev=0.95)
            self.assertRaises(ValueError, Stats.propcl,21,42.2,conflev=0.95)
            self.assertRaises(ValueError, Stats.propcl,21.4,42.2,conflev=0.95)
            self.assertRaises(ValueError, Stats.propcl,21.4,42.2,conflev=0.95,noninteger='reject')
            self.assertRaises(ValueError, Stats.propcl,21.4,42.2,conflev=0.95,noninteger='undecided')

    if rpy_tests:
        def test_ratecl_rg_openepi(self):
            # results checked against those given for OpenEpi for conflev=0.95 - see
            # http://www.openepi.com, except for case of 123456789,123456789987654321 (and v-v) where results 
            # checked against those given by SAS V8.2 using Daly macro at 
            # http://www.listserv.uga.edu/cgi-bin/wa?A2=ind9809d&L=sas-l&F=&S=&P=17761
            self._stricttest(Stats.ratecl,(5,25),(20.0, 8.324556212833075, 48.050609518782899),method='rg',basepop=100)
            self._stricttest(Stats.ratecl,(66,2098),(3.145853194, 2.4715123437810247, 4.0041848627893932),method='rg',basepop=100)
            self._stricttest(Stats.ratecl,(66,123456789),(5.3460000486486007e-05,4.2000386849949533e-05, 6.8046317340491808e-05),method='rg',basepop=100)
            self._stricttest(Stats.ratecl,(123456789,123456789987654321),(9.9999999199999995e-08,9.9982360291405311e-08, 1.0001764045305388e-07),basepop=100,method='rg')
            self._stricttest(Stats.ratecl,(123456789987654321,123456789),(100000000800.00002,100000000242.1844, 100000001357.81537),method='rg',basepop=100)

    if rpy_tests:
        def test_ratecl_byar_openepi(self):
            # results checked against those given for OpenEpi for conflev=0.95 - see
            # http://www.openepi.com, except for case of 123456789,123456789987654321 (and v-v) where results 
            # checked against those given by SAS V8.2 using Daly macro at 
            # http://www.listserv.uga.edu/cgi-bin/wa?A2=ind9809d&L=sas-l&F=&S=&P=17761
            self._stricttest(Stats.ratecl,(5,25),(20.0, 6.4453908037658438, 46.67265670862578),method='byar',basepop=100)
            self._stricttest(Stats.ratecl,(66,2098),(3.145853194, 2.4328873947163197, 4.0023584323110661),method='byar',basepop=100)
            self._stricttest(Stats.ratecl,(66,123456789),(5.3460000486486007e-05,4.1344002184560613e-05, 6.8015279345946824e-05),method='byar',basepop=100)
            self._stricttest(Stats.ratecl,(123456789,123456789987654321),(9.9999999199999995e-08,9.9982360291405311e-08, 1.0001764045305388e-07),method='byar',basepop=100)
            self._stricttest(Stats.ratecl,(123456789987654321,123456789),(100000000800.00002,100000000242.18448, 100000001357.81552),method='byar',basepop=100)

    if rpy_tests:
        def test_ratecl_normal_openepi(self):
            # results checked against those given for OpenEpi for conflev=0.95 - see
            # http://www.openepi.com, except for case of 123456789,123456789987654321 (and v-v) where results 
            # checked against those given by SAS V8.2 using Daly macro at 
            # http://www.listserv.uga.edu/cgi-bin/wa?A2=ind9809d&L=sas-l&F=&S=&P=17761
            self._stricttest(Stats.ratecl,(5,25),(20.0, 2.4695490624761534, 37.530450937523852),method='normal',basepop=100)
            self._stricttest(Stats.ratecl,(66,2098),(3.145853194, 2.3869007246642115, 3.9048056623710594),method='normal',basepop=100)
            self._stricttest(Stats.ratecl,(66,123456789),(5.3460000486486007e-05,4.0562513903917558e-05, 6.6357487069054457e-05),method='normal',basepop=100)
            self._stricttest(Stats.ratecl,(123456789,123456789987654321),(9.9999999199999995e-08,9.9982360291405311e-08, 1.0001764045305388e-07),method='normal',basepop=100)
            self._stricttest(Stats.ratecl,(123456789987654321,123456789),(100000000800.00002,100000000242.18448, 100000001357.81555),method='normal',basepop=100)

    if rpy_tests:
        def test_ratecl_daly_openepi(self):
            # results checked against those given by SAS V8.2 using macro by Daly at 
            # http://www.listserv.uga.edu/cgi-bin/wa?A2=ind9809d&L=sas-l&F=&S=&P=17761
            self._stricttest(Stats.ratecl,(5,25),(20.0, 6.4939455604736835, 46.673328317290668),method='daly',basepop=100)
            self._stricttest(Stats.ratecl,(66,2098),(3.145853194, 2.4330026319657412, 4.0022965892520039),method='daly',basepop=100)
            self._stricttest(Stats.ratecl,(5,25),(20.0, 4.3117129626092785, 56.599037644092057),method='daly',conflev=0.99,basepop=100)
            self._stricttest(Stats.ratecl,(66,2098),(3.145853194,2.2379465861483445, 4.2877203401224167),method='daly',conflev=0.99,basepop=100)
            self._stricttest(Stats.ratecl,(66,123456789),(5.3460000486486007e-05,4.1345960503347653e-05, 6.8014228397360178e-05),method='daly',basepop=100)
            self._stricttest(Stats.ratecl,(123456789,123456789987654321),(9.9999999199999995e-08,9.9982360291405311e-08, 1.0001764045305388e-07),method='daly',basepop=100)
            self._stricttest(Stats.ratecl,(123456789987654321,123456789),(100000000800.00002,100000000242.18448, 100000001357.81554),method='daly',basepop=100)

    if rpy_tests:
        def test_ratecl_badinpts(self):
            # tests for bad inputs (code shared by all methods)
            self.assertRaises(ValueError, Stats.ratecl,-1,20)
            self.assertRaises(ValueError, Stats.ratecl,1,-20)
            self.assertRaises(ValueError, Stats.ratecl,-1,-20)
            self.assertRaises(ValueError, Stats.ratecl,21,0)
            self.assertRaises(ValueError, Stats.ratecl,21,42,method='humperdinck')
            self.assertRaises(ValueError, Stats.ratecl,21,42,conflev=95)
            self.assertRaises(ValueError, Stats.ratecl,21,42,conflev=0.45)
            self.assertRaises(ValueError, Stats.ratecl,21,42,conflev=-0.95)
            self.assertRaises(ValueError, Stats.ratecl,21,42,basepop=0)
            self.assertRaises(ValueError, Stats.ratecl,21,42,basepop=-100)

    if rpy_tests:
        def test_freqcl_byar_openepi(self):
            # results checked against those given for OpenEpi for conflev=0.95 - see
            # http://www.openepi.com, except for case of 123456789,123456789987654321 (and v-v) where results 
            # checked against those given by SAS V8.2 using Daly macro at 
            # http://www.listserv.uga.edu/cgi-bin/wa?A2=ind9809d&L=sas-l&F=&S=&P=17761
            self._stricttest(Stats.freqcl,(66,),(66.0, 51.041977541148384, 83.969479909886161),method='byar')
            self._stricttest(Stats.freqcl,(3,),(3.0, 0.602972562598596, 8.7653644442764342),method='byar')
            self._stricttest(Stats.freqcl,(123456789,),(123456789.0, 123435012.56950366, 123478568.32489048),method='byar')
            self._stricttest(Stats.freqcl,(123456789987654321,),(1.2345678998765432e+17, 1.2345678929899318e+17, 1.2345679067631546e+17),method='byar')
            self._stricttest(Stats.freqcl,(0,),(0.0, 0.0, 3.6680118656769207),method='byar')

    if rpy_tests:
        def test_freqcl_daly_openepi(self):
            # results checked against those given by SAS V8.2 using macro by Daly at 
            # http://www.listserv.uga.edu/cgi-bin/wa?A2=ind9809d&L=sas-l&F=&S=&P=17761
            self._stricttest(Stats.freqcl,(66,),(66.0, 51.044395218641284, 83.968182442506816),method='daly')
            self._stricttest(Stats.freqcl,(3,),(3.0, 0.61867212289560147, 8.7672730697423251),method='daly')
            self._stricttest(Stats.freqcl,(123456789,),(123456789.0, 123435012.5696615, 123478568.32473257),method='daly')
            self._stricttest(Stats.freqcl,(123456789987654321,),(1.2345678998765432e+17, 1.2345678929899317e+17, 1.2345679067631547e+17),method='daly')
            self._stricttest(Stats.freqcl,(0,),(0.0, 0.0, 3.6888794541139354),method='daly')
            pass
            
        def test_freqcl_badinpts(self):
            # tests for bad inputs (code shared by all methods)
            self.assertRaises(ValueError, Stats.freqcl,-1)
            self.assertRaises(ValueError, Stats.freqcl,21,method='humperdinck')
            self.assertRaises(ValueError, Stats.freqcl,21,conflev=95)
            self.assertRaises(ValueError, Stats.freqcl,21,conflev=0.45)
            self.assertRaises(ValueError, Stats.freqcl,21,conflev=-0.95)
            pass

    if rpy_tests:
        def test_wncl_misc_daly(self):
            self._stricttest(Stats.wncl, (empty_numeric,), (0.0,0.0,0.0), conflev=0.95, method='daly') 
            self._stricttest(Stats.wncl, (empty_ma,), (0.0,0.0,0.0), conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (populated_numeric,), (14.0, 4.545761892331579, 32.671329822103466), conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (populated_ma,), (14.0, 4.545761892331579, 32.671329822103466),conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (full_mask,),(0.0,0.0,0.0) ,conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (null_mask,), (14.0, 4.545761892331579, 32.671329822103466), conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (partial_mask,), (7.0, 0.84773247490387726, 25.286406837033859), conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (two_elements_numeric,), (7.0, 0.84773247490387726, 25.286406837033859), conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (two_elements_ma,), (7.0, 0.84773247490387726, 25.286406837033859), conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (one_element_numeric,), (2.0, 0.050635615968579795, 11.143286781877794), conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (one_element_ma,), (2.0, 0.050635615968579795, 11.143286781877794), conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (one_neg_element_numeric,), (0.0,0.0,0.0),conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (one_neg_element_ma,), (0.0,0.0,0.0),conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (one_masked_element_ma,), (0.0,0.0,0.0),conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (all_neg_numeric,), (0.0,0.0,0.0),conflev=0.95, method='daly')
            self._stricttest(Stats.wncl, (all_neg_ma,), (0.0,0.0,0.0),conflev=0.95, method='daly')

    if rpy_tests:
        def test_wncl_misc__daly_exclnpwgts(self):
            # repeat with exclude_nonpositive_weights=True
            #self._stricttest(Stats.wncl, (empty_numeric,), 0,exclude_nonpositive_weights=True,conflev=0.95, method='daly') 
            #self._stricttest(Stats.wncl, (empty_ma,), 0, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (populated_numeric,), 14, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (populated_ma,), 14, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (full_mask,), 0, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (null_mask,), 14, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (partial_mask,), 7, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (two_elements_numeric,), 7, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (two_elements_ma,), 7, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (one_element_numeric,), 2, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (one_element_ma,), 2, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (one_neg_element_numeric,), 0, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (one_neg_element_ma,), 0, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (one_masked_element_ma,), 0, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (all_neg_numeric,), 0, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            #self._stricttest(Stats.wncl, (all_neg_ma,), 0, exclude_nonpositive_weights=True,conflev=0.95, method='daly')
            pass

    if rpy_tests:
        def test_wncl_1001(self):
            # now with 1001 element arrays
            #self._stricttest(Stats.wncl, (w1001_nomissing_numpy,), 163515)
            #self._stricttest(Stats.wncl, (w1001_nomissing_MA,), 163515)
            #self._stricttest(Stats.wncl, (w1001_missing,), 154046.66666667)
            pass

    if rpy_tests:
        def test_wncl_1001_exclnpwgts(self):
            # repeat with exclude_nonpositive_weights=True
            #self._stricttest(Stats.wncl, (w1001_nomissing_numpy,), 163515, exclude_nonpositive_weights=True)
            #self._stricttest(Stats.wncl, (w1001_nomissing_MA,), 163515, exclude_nonpositive_weights=True)
            #self._stricttest(Stats.wncl, (w1001_missing,), 154046.66666667, exclude_nonpositive_weights=True)
            pass

if __name__ == '__main__':
    unittest.main()
