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
Test soomfuncs

$Id: soomfunctest.py 2626 2007-03-09 04:35:54Z andrewm $
$Source: /usr/local/cvsroot/NSWDoH/SOOMv0/soomext/test/soomfunctest.py,v $
"""

import unittest

import Numeric
import RandomArray
import soomfunc


class _soomfuncTest(unittest.TestCase):
    def _test_soomfunc(self, fn, want, *args):
        args = [Numeric.array(a, typecode='l') for a in args]
        result = fn(*args)
        self.assertEqual(result.typecode(), 'l')
        self.assertEqual(list(result), want)

    def _test_soomfunc_bothways(self, fn, want, *args):
        args = [Numeric.array(a, typecode='l') for a in args]
        result = fn(*args)
        self.assertEqual(result.typecode(), 'l')
        self.assertEqual(list(result), want)

        args.reverse()
        result = fn(*args)
        self.assertEqual(result.typecode(), 'l')
        self.assertEqual(list(result), want)

class uniqueCase(_soomfuncTest):
    def test_dups(self):
        self._test_soomfunc(soomfunc.unique,
                           [5, 6, 7, 8, 9], [5, 6, 6, 7, 8, 8, 8, 8, 9])
    def test_nodups(self):
        self._test_soomfunc(soomfunc.unique,
                           [5, 6, 7, 8, 9], [5, 6, 7, 8, 9])
    def test_one(self):
        self._test_soomfunc(soomfunc.unique,
                           [4], [4])
    def test_empty(self):
        self._test_soomfunc(soomfunc.unique,
                           [], [])

class uniqueSuite(unittest.TestSuite):
    test_list = (
        "test_dups",
        "test_nodups",
        "test_one",
        "test_empty",
    )
    def __init__(self):
        unittest.TestSuite.__init__(self, map(uniqueCase, self.test_list))


class intersectCase(_soomfuncTest):
    def test_dense(self):
        self._test_soomfunc_bothways(soomfunc.intersect,
                            [0, 2, 3, 5, 8],
                            [0, 2, 3, 4, 5, 7, 8, 9],
                            [0, 1, 2, 3, 5, 6, 8])

    def test_sparse(self):
        self._test_soomfunc_bothways(soomfunc.intersect,
                            [1,  5, 16],
                            [0, 1, 3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19],
                            [1, 5, 8, 16])
    def test_dups(self):
        self._test_soomfunc_bothways(soomfunc.intersect,
                            [1,  5, 16],
                            [0, 1, 3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19],
                            [1, 5, 5, 5, 8, 8, 16])
    def test_nointersect(self):
        self._test_soomfunc_bothways(soomfunc.intersect,
                            [],
                            [0, 1, 3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19],
                            [2, 4, 8, 18])
    def test_one(self):
        self._test_soomfunc_bothways(soomfunc.intersect,
                            [5],
                            [5],
                            [5])
    def test_empty(self):
        self._test_soomfunc_bothways(soomfunc.intersect,
                            [],
                            [],
                            [])

    def test_sparse_vs_dense(self):
        RandomArray.seed(0)             # For reproducability
        for s, l in (100, 100000), (10000, 100000), (100000, 100000):
            small = Numeric.sort(RandomArray.randint(0, 100000, (s,)))
            large = Numeric.sort(RandomArray.randint(0, 100000, (l,)))

            sparse1 = soomfunc.sparse_intersect(small, large)
            sparse2 = soomfunc.sparse_intersect(large, small)
            dense1 = soomfunc.dense_intersect(small, large)
            dense2 = soomfunc.dense_intersect(large, small)

            self.assertEqual(sparse1, sparse2)
            self.assertEqual(dense1, dense2)
            self.assertEqual(sparse1, dense1)



class intersectSuite(unittest.TestSuite):
    test_list = (
        "test_dense",
        "test_sparse",
        "test_dups",
        "test_nointersect",
        "test_one",
        "test_empty",
        "test_sparse_vs_dense",
    )
    def __init__(self):
        unittest.TestSuite.__init__(self, map(intersectCase, self.test_list))


class outersectCase(_soomfuncTest):
    def test_simple(self):
        self._test_soomfunc_bothways(soomfunc.outersect,
                            [1, 4, 6, 7, 9],
                            [0, 2, 3, 4, 5, 7, 8, 9],
                            [0, 1, 2, 3, 5, 6, 8])

    def test_dups(self):
        self._test_soomfunc_bothways(soomfunc.outersect,
                            [1, 4, 6, 7, 9],
                            [0, 2, 3, 3, 4, 4, 5, 7, 8, 9],
                            [0, 1, 2, 3, 3, 5, 6, 8, 8])
    def test_nooutersect(self):
        self._test_soomfunc_bothways(soomfunc.outersect,
                            [],
                            [0, 1, 2, 3, 5, 6, 8],
                            [0, 1, 2, 3, 5, 6, 8, 8])
    def test_one(self):
        self._test_soomfunc_bothways(soomfunc.outersect,
                            [],
                            [5],
                            [5])
    def test_empty(self):
        self._test_soomfunc_bothways(soomfunc.outersect,
                            [],
                            [],
                            [])

class outersectSuite(unittest.TestSuite):
    test_list = (
        "test_simple",
        "test_dups",
        "test_nooutersect",
        "test_one",
        "test_empty",
    )
    def __init__(self):
        unittest.TestSuite.__init__(self, map(outersectCase, self.test_list))


class unionCase(_soomfuncTest):
    def test_simple(self):
        self._test_soomfunc_bothways(soomfunc.union,
                            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                            [0, 2, 3, 4, 5, 7, 8, 9],
                            [0, 1, 2, 3, 5, 6, 8])

    def test_one(self):
        self._test_soomfunc_bothways(soomfunc.union,
                            [5],
                            [],
                            [5])
    def test_empty(self):
        self._test_soomfunc_bothways(soomfunc.union,
                            [],
                            [],
                            [])

class unionSuite(unittest.TestSuite):
    test_list = (
        "test_simple",
        "test_one",
        "test_empty",
    )
    def __init__(self):
        unittest.TestSuite.__init__(self, map(unionCase, self.test_list))


class differenceCase(_soomfuncTest):
    def test_simple(self):
        self._test_soomfunc(soomfunc.difference,
                            [4, 7, 9],
                            [0, 2, 3, 4, 5, 7, 8, 9],
                            [0, 1, 2, 3, 5, 6, 8])
    def test_more(self):
        self._test_soomfunc(soomfunc.difference,
                            [4, 7, 9],
                            [0, 2, 3, 4, 5, 7, 8, 9],
                            [0, 1, 2, 3],
                            [5, 6, 8])

    def test_one(self):
        self._test_soomfunc(soomfunc.difference,
                           [], [], [5])
        self._test_soomfunc(soomfunc.difference,
                           [5], [5], [])
    def test_empty(self):
        self._test_soomfunc_bothways(soomfunc.difference,
                            [],
                            [],
                            [])

class differenceSuite(unittest.TestSuite):
    test_list = (
        "test_simple",
        "test_more",
        "test_one",
        "test_empty",
    )
    def __init__(self):
        unittest.TestSuite.__init__(self, map(differenceCase, self.test_list))


class valueposCase(_soomfuncTest):
    def test_simple(self):
        self._test_soomfunc(soomfunc.valuepos,
                            [1, 2, 3, 4, 8],
                            [0, 2, 3, 3, 5, 7, 7, 7, 8, 9],
                            [1, 2, 3, 5, 6, 8])

    def test_one(self):
        self._test_soomfunc(soomfunc.valuepos,
                            [], [], [5])
        self._test_soomfunc(soomfunc.valuepos,
                            [], [5], [])

    def test_empty(self):
        self._test_soomfunc_bothways(soomfunc.valuepos,
                            [],
                            [],
                            [])

class valueposSuite(unittest.TestSuite):
    test_list = (
        "test_simple",
        "test_one",
        "test_empty",
    )
    def __init__(self):
        unittest.TestSuite.__init__(self, map(valueposCase, self.test_list))


class stripwordCase(unittest.TestCase):
    def test_empty(self):
		self.assertEqual(soomfunc.strip_word(""), "")

    def test_upper(self):
		self.assertEqual(soomfunc.strip_word("hello"), "HELLO")

    def test_quote(self):
		self.assertEqual(soomfunc.strip_word("'START"), "START")
		self.assertEqual(soomfunc.strip_word("END'"), "END")
		self.assertEqual(soomfunc.strip_word("DON'T"), "DONT")
		self.assertEqual(soomfunc.strip_word("CAN''T"), "CANT")
		self.assertEqual(soomfunc.strip_word("'''"), "")

    def test_both(self):
		self.assertEqual(soomfunc.strip_word("don't"), "DONT")
		self.assertEqual(soomfunc.strip_word("'confusion'"), "CONFUSION")

class stripwordSuite(unittest.TestSuite):
    test_list = (
        "test_empty",
        "test_upper",
        "test_quote",
        "test_both",
    )
    def __init__(self):
        unittest.TestSuite.__init__(self, map(stripwordCase, self.test_list))


class soomfuncSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(uniqueSuite())
        self.addTest(intersectSuite())
        self.addTest(outersectSuite())
        self.addTest(unionSuite())
        self.addTest(differenceSuite())
        self.addTest(valueposSuite())
        self.addTest(stripwordSuite())

def suite():
    return soomfuncSuite()

if __name__ == '__main__':
    unittest.main(hiccupaultTest='soomfuncSuite')

