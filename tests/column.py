# vim: set ts=4 sw=4 et:
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
# $Id: column.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/tests/column.py,v $

import os, shutil
import errno
import unittest
import SOOMv0
import soomfunc
import array

class column_basic_test(unittest.TestCase):
    data = [3,1,4,1,5,9,2,6,5,4]

    def test_00_instanciate(self):
        ds = SOOMv0.Dataset('testds')
        col = ds.addcolumn('test')

    def test_01_badargs(self):
        ds = SOOMv0.Dataset('testds')
        self.assertRaises(SOOMv0.Error, ds.addcolumn, '!test')    # Bad name
        self.assertRaises(SOOMv0.Error, ds.addcolumn,
                          'test', coltype='UnknownColType')
        self.assertRaises(SOOMv0.Error, ds.addcolumn,
                          'test', datatype='UnknownDataType')
        self.assertRaises(SOOMv0.Error, ds.addcolumn,
                          'test', datatype=int, all_value='BadValue')

    def test_02_data(self):
        ds = SOOMv0.Dataset('testds')
        ds.addcolumnfromseq('test', self.data)
        self.assertEqual(list(ds['test']), self.data)
        self.assertEqual(len(ds['test']), len(self.data))
        self.assertEqual(str(ds['test']), '''\
Ordinal  test
-------  ----
      0  3   
      1  1   
      2  4   
      3  1   
      4  5   
      5  9   
      6  2   
      7  6   
      8  5   
      9  4   ''')
        self.assertEqual(list(ds['test'][2:5]), self.data[2:5])

    def test_03_cardinality(self):
        ds = SOOMv0.Dataset('testds')
        ds.addcolumnfromseq('test', self.data)
        self.assertEqual(ds['test'].cardinality(), 7)

class dataset_mixin_base:
    def _asserts(self, ds, expect):
        self.assertEqual(list(ds['test']), list(expect))
        self.assertEqual(len(ds['test']), len(expect))
        self.assertEqual(list(ds['row_ordinal']), range(len(expect)))
        self.assertEqual(len(ds['row_ordinal']), len(expect))

class non_persistent_dataset_mixin(dataset_mixin_base):
    def _test(self, data, expect = None, **kwargs):
        if expect == None:
            expect = data
        ds = SOOMv0.Dataset('testds', backed = False)
        ds.addcolumnfromseq('test', data, **kwargs)
        self._asserts(ds, expect)
        return ds['test']

class persistent_dataset_mixin(dataset_mixin_base):
    def setUp(self):
        SOOMv0.dsunload('testds')
        self.path = os.path.join(os.path.dirname(__file__), 'test_objects')
        self.saved_writepath, SOOMv0.soom.writepath = \
            SOOMv0.soom.writepath, self.path

    def _test(self, data, expect = None, **kwargs):
        if expect == None:
            expect = data
        ds = SOOMv0.makedataset('testds', path=self.path, backed = True)
        ds.writepath = self.path
        ds.addcolumnfromseq('test', data, **kwargs)
        self._asserts(ds, expect)
        ds.save()
        ds.unload()
        ds = SOOMv0.dsload('testds')
        self._asserts(ds, expect)
        return ds['test']

    def tearDown(self):
        if hasattr(self, 'path') and self.path:
            SOOMv0.soom.writepath = self.saved_writepath
            try:
                shutil.rmtree(self.path)
            except OSError, (eno, estr):
                if eno != errno.ENOENT:
                    raise

class datatypes_test_mixin:
    def test_int(self):
        data = [3,1,4,1,5,9,2,6,5,4]
        self._test(data, datatype=int)

    def test_float(self):
        data = [0.16, 0.78, 0.34, 0.85, 0.87, 0.10, 0.79, 0.28, 
                0.14, 0.95, 0.47, 0.71, 0.35, 0.65, 0.34, 0.01]
        self._test(data, datatype=float)

    def test_str(self):
        data = ['pickle', 'cheese', 'salami', 'pickle', 
                'cheese', 'cheese', 'salami', 'salami']
        self._test(data, datatype=str)

    def test_tuple(self):
        data = [
            ('285.9', '285.9'),
            ('276.7', '285.9', '009.2'),
            ('250.01',),
            ('009.2',),
            ('276.7', '244.9'),
            ('250.00', '276.7', '285.9'),
            ('276.7', '079.9', '079.9', '276.7'),
            ('250.01',),
            (),
        ]
        col = self._test(data, datatype=tuple)
        self.assertEqual(col.cardinality(), 7)
        self.assertEqual(list(col.inverted['276.7']), [1,4,5,6])

    def test_recode(self):
        data = [None, 1, 2.3, 'A', 'A', 1, None]
        col = self._test(data, datatype='recode')
        self.assertEqual(col.cardinality(), 4)
        self.assertEqual(list(col), data)

    def test_missing(self):
        data = [3,None,1,4,1,5,9,2,6,5,4]
        expect = [3,0,1,0,1,5,9,2,6,5,0]
        self._test(data, expect=expect, datatype=int, missingvalues = {4: True})

class column_datatypes_persistent_test(datatypes_test_mixin,
                                       persistent_dataset_mixin,
                                       unittest.TestCase):
    pass

class column_datatypes_non_persistent_test(datatypes_test_mixin,
                                           non_persistent_dataset_mixin,
                                           unittest.TestCase):
    pass

class column_calculatedby(unittest.TestCase):
    def test_calculatedby(self):
        realdata = [3,1,4,1,5,9,2,6,5,4]
        data = [None] * len(realdata)
        fn = iter(realdata).next
        ds = SOOMv0.Dataset('testds')
        ds.addcolumnfromseq('test', data, datatype='int', calculatedby=fn)
        self.assertEqual(list(ds['test']), list(realdata))
        self.assertEqual(len(ds['test']), len(realdata))

    def test_calculatedby_witharg(self):
        def fn(arg):
            return arg.next()
        realdata = [3,1,4,1,5,9,2,6,5,4]
        data = [None] * len(realdata)
        ds = SOOMv0.Dataset('testds')
        ds.addcolumnfromseq('test', data, datatype='int', 
                            calculatedby=fn, calculatedargs=(iter(realdata),))
        self.assertEqual(list(ds['test']), list(realdata))
        self.assertEqual(len(ds['test']), len(realdata))

class searchabletext_coltype(persistent_dataset_mixin, unittest.TestCase):
    def _assertword(self, col, word, positions):
        w=col._get_occurrences(soomfunc.strip_word(word))
        if positions is not None:
            pos = []
            for line, word in positions:
                pos.append(line)
                pos.append(word)
            want = array.array('L')
            want.fromlist(pos)
        else:
            want = None
        self.assertEquals(w, want)

    def _assertrows(self, col, query, rows, message = None):
        sexpr = SOOMv0.soomparse.parse('sgoal', query)
        result = list(col.op_contains(sexpr, None))
        self.assertEqual(result, rows, message)

    def test_basics(self):
        data = [
                'this would be line one', 
                'and this is another line',
                " ".join(["amphibian"] * 50),
                'one more line',
                " ".join(["zog"] * 100),
                " ".join(["amphibian"] * 50),
            ]
        col = self._test(data, datatype='str', coltype='searchabletext')
        self._assertword(col, 'line', [(0, 3), (1, 4), (3, 2)])
        self._assertword(col, 'one', [(0, 4), (3, 0)])
        self._assertword(col, 'missing', None)
        # these test words which should take up more than one block in the index file
        self._assertword(col, 'amphibian', [ (2, x) for x in range(50) ] + [ (5, x) for x in range(50) ])
        self._assertword(col, 'zog', [ (4, x) for x in range(100) ])

    def test_query(self):
        data = """
Sir Walter Elliot, of Kellynch Hall, in Somersetshire, was a man who,
for his own amusement, never took up any book but the Baronetage;
there he found occupation for an idle hour, and consolation in a
distressed one; there his faculties were roused into admiration and
respect, by contemplating the limited remnant of the earliest patents;
there any unwelcome sensations, arising from domestic affairs
changed naturally into pity and contempt as he turned over
the almost endless creations of the last century; and there,
if every other leaf were powerless, he could read his own history
with an interest which never failed.  This was the page at which
the favourite volume always opened:

           "ELLIOT OF KELLYNCH HALL.

"Walter Elliot, born March 1, 1760, married, July 15, 1784, Elizabeth,
daughter of James Stevenson, Esq. of South Park, in the county of
Gloucester, by which lady (who died 1800) he has issue Elizabeth,
born June 1, 1785; Anne, born August 9, 1787; a still-born son,
November 5, 1789; Mary, born November 20, 1791."

Precisely such had the paragraph originally stood from the printer's hands;
but Sir Walter had improved it by adding, for the information of
himself and his family, these words, after the date of Mary's birth--
"Married, December 16, 1810, Charles, son and heir of Charles
Musgrove, Esq. of Uppercross, in the county of Somerset,"
and by inserting most accurately the day of the month on which
he had lost his wife.

Then followed the history and rise of the ancient and respectable family,
in the usual terms; how it had been first settled in Cheshire;
how mentioned in Dugdale, serving the office of high sheriff,
representing a borough in three successive parliaments,
exertions of loyalty, and dignity of baronet, in the first year
of Charles II, with all the Marys and Elizabeths they had married;
forming altogether two handsome duodecimo pages, and concluding with
the arms and motto:--"Principal seat, Kellynch Hall, in the county
of Somerset," and Sir Walter's handwriting again in this finale:--

"Heir presumptive, William Walter Elliot, Esq., great grandson of
the second Sir Walter."

Vanity was the beginning and the end of Sir Walter Elliot's character;
vanity of person and of situation.  He had been remarkably handsome
in his youth; and, at fifty-four, was still a very fine man.
Few women could think more of their personal appearance than he did,
nor could the valet of any new made lord be more delighted with
the place he held in society.  He considered the blessing of beauty
as inferior only to the blessing of a baronetcy; and the Sir Walter Elliot,
who united these gifts, was the constant object of his warmest respect
and devotion.
            """.strip().split("\n\n")
        col = self._test(data, datatype='str', coltype='searchabletext')
        self._assertrows(col, 'elliot', [0, 1, 2, 5, 6])
        self._assertrows(col, 'eliot', [])
        self._assertrows(col, 'elliot baronetage', [0])
        self._assertrows(col, 'elliot baronetcy', [6])
        self._assertrows(col, 'elliot Kellynch', [0, 1])
        self._assertrows(col, 'elliot Cheshire', [])
        self._assertrows(col, 'elliot | Cheshire', [0, 1, 2, 4, 5, 6])
        self._assertrows(col, 'in the', [0, 2, 3, 4, 6])
        self._assertrows(col, 'the in', [0, 2, 3, 4, 6])
        self._assertrows(col, 'in ~ the', [2, 3, 4, 6])
        self._assertrows(col, 'the ~ in', [2, 3, 4, 6])
        self._assertrows(col, '"in the"', [2, 3, 4])
        self._assertrows(col, '"the in"', [])
        self._assertrows(col, '"sir walter elliot"', [0, 6])
        self._assertrows(col, 'in ~[11] the', [2, 3, 4, 6])
        self._assertrows(col, 'in ~[12] the', [0, 2, 3, 4, 6])
        self._assertrows(col, 'elliot < kellynch', [0, 1])
        self._assertrows(col, 'elliot > kellynch', [])
        self._assertrows(col, 'in < the', [2, 3, 4, 6])
        self._assertrows(col, 'in > the', [4, 6])
        self._assertrows(col, 'elliot walter', [0, 2, 5, 6])
        self._assertrows(col, 'elliot walter', [0, 2, 5, 6])
        self._assertrows(col, 'son', [2, 3])
        self._assertrows(col, '*son', [2, 3, 5, 6])
        self._assertrows(col, 'person*', [6])

if __name__ == '__main__':
    unittest.main()
