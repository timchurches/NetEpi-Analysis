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
# $Id: summ.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/tests/summ.py,v $

from SOOMv0 import *
import MA
import unittest

def _get_ds():
    ds = Dataset('apples')
    ds.addcolumnfromseq('variety', label='Variety',
                        coltype='categorical', datatype='int',
                        all_value=-1,
                        data=[1, 1, 2, 3, 4, 1, 2, 5],
                        use_outtrans=True, outtrans={
                            1: 'Granny Smith',
                            2: 'Golden Delicious',
                            3: 'Fuji',
                            4: 'Braeburn',
                            5: 'Pink Lady',
                        })
    ds.addcolumnfromseq('grade', label='Grade',
                        coltype='categorical', datatype='int',
                        all_value=-1,
                        data=[1, 3, 2, 1, 1, 1, 3, 0],
                        use_outtrans=True, outtrans={
                            0: 'Extra Fine',
                            1: 'Fine',
                            2: 'Good',
                            3: 'Poor',
                        })
    ds.addcolumnfromseq('size', label='Size (in cm)',
                        coltype='scalar', datatype='float',
                        data=[6.0, 8.4, 6.5, 6.6, 9.2, 6.8, 9.2, 6.5])
    ds.addcolumnfromseq('supplier', label='Supplier',
                        coltype='categorical', datatype='int',
                        data=[1, 1, 0, 0, 2, 2, 1, 0],
                        missingvalues={0: None},
                        use_outtrans=True, outtrans={
                            0: 'No',
                            1: 'Mistyvale',
                            2: 'Moss Glen',
                        })
    ds.addcolumnfromseq('weighting', label='Statistical weighting',
                        coltype='scalar', datatype='float',
                        data=[8.9, 1.7, 2.8, 2.2, 4.1, 3.7, 7.1, 7.6])
    return ds

class summ_test(unittest.TestCase):

    def assertListNear(self, first, second, prec=2):
        def ma_round(v, prec):
            if v is None or type(v) is MA.MaskedScalar:
                return None
            return round(v, prec)
        def ma_fmt(v, prec):
            if v is None:
                return 'None'
            return '%.*f' % (prec, v)
        first = [ma_round(v, prec) for v in first]
        second = [ma_round(v, prec) for v in second]
        first_str = ', '.join([ma_fmt(v, prec) for v in first])
        second_str = ', '.join([ma_fmt(v, prec) for v in second])
        self.assertEqual(first, second, 
                         '[%s] != [%s]' % (first_str, second_str))

    def test_simple(self):
        ds = _get_ds()
        summ = ds.summ('variety')
        self.assertEqual(list(summ['row_ordinal']), range(5))
        self.assertEqual(list(summ['variety']), range(1,6))
        self.assertEqual(list(summ['_freq_']), [3, 2, 1, 1, 1])
        self.assertEqual(list(summ['_condcols_']), [('variety',)] * 5)

    def test_two(self):
        ds = _get_ds()
        summ = ds.summ('variety', 'grade')
        self.assertEqual(list(summ['row_ordinal']), range(20))
        self.assertEqual(list(summ['variety']), [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 
                                             3, 3, 4, 4, 4, 4, 5, 5, 5, 5])
        self.assertEqual(list(summ['grade']), [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 
                                            2, 3, 0, 1, 2, 3, 0, 1, 2, 3])
        self.assertEqual(list(summ['_freq_']), [0, 2, 0, 1, 0, 0, 1, 1, 0, 1, 
                                             0, 0, 0, 1, 0, 0, 1, 0, 0, 0])
        self.assertEqual(list(summ['_condcols_']), [('variety', 'grade')] * 20)

    def test_allcalc(self):
        ds = _get_ds()
        summ = ds.summ('variety', 'grade', allcalc=True)
        self.assertEqual(list(summ['row_ordinal']), range(30))
        self.assertEqual(list(summ['variety']),
            [-1, 1, 2, 3, 4, 5, -1, -1, -1, -1, 1, 1, 1, 1, 
             2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5])
        self.assertEqual(list(summ['grade']), 
            [-1, -1, -1, -1, -1, -1, 0, 1, 2, 3, 0, 1, 2, 3, 
             0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3])
        self.assertEqual(list(summ['_freq_']), 
            [8, 3, 2, 1, 1, 1, 1, 4, 1, 2, 0, 2, 0, 1, 0, 
             0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0])
        self.assertEqual(list(summ['_condcols_']), 
            [()] + [('variety',)] * 5 + [('grade',)] * 4 + 
             [('variety', 'grade')] * 20)

    def test_stats(self):
        ds = _get_ds()
        summ = ds.summ('variety', minimum('size'), mean('size'))
        self.assertEqual(list(summ['row_ordinal']), range(5))
        self.assertEqual(list(summ['variety']), range(1,6))
        self.assertEqual(list(summ['_freq_']), [3, 2, 1, 1, 1])
        self.assertListNear(summ['minimum_of_size'], 
           [6.0, 6.5, 6.6, 9.2, 6.5])
        self.assertListNear(summ['mean_of_size'], 
           [7.07, 7.85, 6.6, 9.2, 6.5], prec=2)
        self.assertEqual(list(summ['_condcols_']), [('variety',)] * 5)

    def test_stats_percentile(self):
        ds = _get_ds()
        summ = ds.summ('variety', p25('size'), p75('size'))
        self.assertEqual(list(summ['row_ordinal']), range(5))
        self.assertEqual(list(summ['variety']), range(1,6))
        self.assertEqual(list(summ['_freq_']), [3, 2, 1, 1, 1])
        self.assertListNear(summ['p25_of_size'], 
           [6.0, 6.5, 6.6, 9.2, 6.5])
        self.assertListNear(summ['p75_of_size'], 
           [8.4, 9.2, 6.6, 9.2, 6.5])
        self.assertEqual(list(summ['_condcols_']), [('variety',)] * 5)

    def test_stats_wgtfreq1(self):
        def check():
            self.assertEqual(list(summ['row_ordinal']), range(5))
            self.assertEqual(list(summ['_freq_']), [3, 2, 1, 1, 1])
            self.assertListNear(summ['freq_wgtd_by_weighting'], 
            [14.3, 9.9, 2.2, 4.1, 7.6], prec=4)
            self.assertEqual(list(summ['_condcols_']), [('variety',)] * 5)
        ds = _get_ds()
        summ = ds.summ('variety', freq(), weightcol='weighting')
        check()
        summ = ds.summ('variety', freq(weightcol='weighting'))
        check()
        ds.weightcol = 'weighting'
        summ = ds.summ('variety', freq())
        check()

    def test_stats_wgtmean(self):
        def check():
            self.assertEqual(list(summ['row_ordinal']), range(5))
            self.assertEqual(list(summ['_freq_']), [3, 2, 1, 1, 1])
            self.assertListNear(list(summ['mean_of_size_wgtd_by_weighting']), 
            [6.49, 8.44, 6.6, 9.2, 6.5])
            self.assertEqual(list(summ['_condcols_']), [('variety',)] * 5)
        ds = _get_ds()
        summ = ds.summ('variety', mean('size'), weightcol='weighting')
        check()
        summ = ds.summ('variety', mean('size', weightcol='weighting'))
        check()
        ds.weightcol = 'weighting'
        summ = ds.summ('variety', mean('size'))
        check()

    def test_stats_applyto(self):
        ds = _get_ds()
        summ = ds.summ('variety', applyto('size', minimum, mean))
        self.assertEqual(list(summ['row_ordinal']), range(5))
        self.assertEqual(list(summ['variety']), range(1,6))
        self.assertEqual(list(summ['_freq_']), [3, 2, 1, 1, 1])
        self.assertEqual(list(summ['minimum_of_size']), 
           [6.0, 6.5, 6.6, 9.2, 6.5])
        self.assertEqual(list(summ['mean_of_size']), 
           [7.0666666666666666, 7.85, 6.6, 9.2, 6.5])
        self.assertEqual(list(summ['_condcols_']), [('variety',)] * 5)

    def test_filternamed(self):
        ds = _get_ds()
        ds.makefilter('not_delicious', expr='variety != 2', 
                      label='Not Delicious!')
        summ = ds.summ('variety', filtername='not_delicious')
        self.assertEqual(list(summ['row_ordinal']), range(4))
        self.assertEqual(list(summ['variety']), [1, 3, 4, 5])
        self.assertEqual(list(summ['_freq_']), [3, 1, 1, 1])
        self.assertEqual(list(summ['_condcols_']), [('variety',)] * 4)

    def test_filteranon(self):
        ds = _get_ds()
        summ = ds.summ('variety', 
                       filterexpr='variety != 2', filterlabel='Not Delicious!')
        self.assertEqual(list(summ['row_ordinal']), range(4))
        self.assertEqual(list(summ['variety']), [1, 3, 4, 5])
        self.assertEqual(list(summ['_freq_']), [3, 1, 1, 1])
        self.assertEqual(list(summ['_condcols_']), [('variety',)] * 4)

    def test_missing(self):
        ds = _get_ds()
        summ = ds.summ('variety', 'supplier')
        self.assertEqual(list(summ['row_ordinal']), range(15))
        self.assertEqual(list(summ['variety']), [1, 1, 1, 2, 2, 2, 3, 3, 
                                              3, 4, 4, 4, 5, 5, 5])
        self.assertEqual(list(summ['supplier']), [0, 1, 2, 0, 1, 2, 0, 1, 
                                               2, 0, 1, 2, 0, 1, 2])
        self.assertEqual(list(summ['_freq_']), [0, 2, 1, 1, 1, 0, 1, 0, 
                                             0, 0, 0, 1, 1, 0, 0])
        self.assertEqual(list(summ['_condcols_']), 
                         [('variety', 'supplier')] * 15)

    def test_proportions(self):
        def check():
            self.assertListNear(summ['_prop_of_all-grade-supplier'],
                                [ 1, 0.125, 0.5, 0.125, 0.25, 
                                  0.375, 0.375, 0.25, 0.125, 0, 
                                  0, 0.125, 0.125, 0.25, 0.125, 
                                  0, 0, 0, 0.25, 0], prec=4)
            self.assertListNear(summ['_prop_of_all-supplier'],
                                [1, 1, 1, 1, 1, 
                                 0.375, 0.375, 0.25, 1, 0, 
                                 0, 0.25, 0.25, 0.5, 1, 
                                 0, 0, 0, 1, 0], prec=4)
            self.assertListNear(summ['_prop_of_all-grade'],
                                [1, 0.125, 0.5, 0.125, 0.25, 
                                 1, 1, 1, 0.3333, 0, 
                                 0, 0.3333, 0.3333, 1, 0.3333, 
                                 0, 0, 0, 0.6667, 0], prec=4)
        ds = _get_ds()
        summ = ds.summ('grade', 'supplier', proportions=True)
        check()
        summ = ds.summ('grade', 'supplier', 
                       freq(weightcol='weighting'), proportions=True)
        check()

    def test_weighted_proportions1(self):
        def check(wgted_freq_col_name, wgted_freq_col_values):
            self.assertEqual(list(summ['row_ordinal']), range(5))
            self.assertEqual(list(summ['_freq_']), [8, 1, 4, 1, 2])
            self.assertListNear(summ[wgted_freq_col_name], 
                                wgted_freq_col_values, prec=4)
            self.assertListNear(summ['_prop_of_all-grade'], 
                                [1.0, 0.1995, 0.4961, 
                                 0.0735, 0.2310], prec=4)
            self.assertEqual(list(summ['_condcols_']), [()] + [('grade',)] * 4)

        ds = _get_ds()
        colname = 'freq_wgtd_by_weighting'
        colvalues = [38.1, 7.6, 18.9, 2.8, 8.8]
        summ = ds.summ('grade', freq(), weightcol='weighting', proportions=True)
        check(colname, colvalues)
        summ = ds.summ('grade', freq(weightcol='weighting'), 
                       weightcol='weighting', proportions=True)
        check(colname, colvalues)
        summ = ds.summ('grade', freq(), weightcol='weighting', proportions=True)
        check(colname, colvalues)
        ds.weightcol = 'weighting'
        summ = ds.summ('grade', freq(), proportions=True)
        check(colname, colvalues)
        summ = ds.summ('grade', freq(weightcol='weighting'), proportions=True)
        check(colname, colvalues)
        colname = 'freq_wgtd_by_size'
        colvalues = [59.2, 6.5, 28.6, 6.5, 17.6]
        summ = ds.summ('grade', freq(weightcol='size'), proportions=True)
        check(colname, colvalues)
        ds.weightcol = None
        summ = ds.summ('grade', freq(weightcol='size'), 
                       weightcol='weighting', proportions=True)
        check(colname, colvalues)

    def test_weighted_proportions2(self):
        def check():
            self.assertListNear(summ['_prop_of_all-grade-supplier'],
                                [1.00, 0.20, 0.50, 0.07, 0.23, 
                                 0.33, 0.46, 0.20, 0.20, 0.00, 
                                 0.00, 0.06, 0.23, 0.20, 0.07, 
                                 0.00, 0.00, 0.00, 0.23, 0.00])
            self.assertListNear(summ['_prop_of_all-supplier'],
                                [1.00, 1.00, 1.00, 1.00, 1.00, 
                                 0.33, 0.46, 0.20, 1.00, 0.00,
                                 0.00, 0.12, 0.47, 0.41, 1.00,
                                 0.00, 0.00, 0.00, 1.00, 0.00])
            self.assertListNear(summ['_prop_of_all-grade'],
                                [1.00, 0.20, 0.50, 0.07, 0.23, 
                                 1.00, 1.00, 1.00, 0.60, 0.00, 
                                 0.00, 0.17, 0.50, 1.00, 0.22, 
                                 0.00, 0.00, 0.00, 0.50, 0.00])
        ds = _get_ds()
        summ = ds.summ('grade', 'supplier', 
                       proportions=True, weightcol='weighting')
        check()
        ds.weightcol = 'weighting'
        summ = ds.summ('grade', 'supplier', 
                       proportions=True)
        check()
        summ = ds.summ('grade', 'supplier', 
                       freq(weightcol='weighting'), proportions=True )
        check()

    def test_weighted_and_filtered_proportions(self):
        ds = _get_ds()
        summ = ds.summ('grade', 'supplier', 
                       proportions=True, weightcol='weighting',
                       filterexpr='size > 6.5')
        # AM - checked these results by hand, 15-Nov-04
        self.assertListNear(summ['_prop_of_all-grade-supplier'],
                            [1.00, 0.53, 0.47, 0.12, 0.47, 0.41, 
                             0.12, 0.00, 0.41, 0.00, 0.47, 0.00])
        self.assertListNear(summ['_prop_of_all-supplier'],
                            [1.00, 1.00, 1.00, 0.12, 0.47, 0.41, 
                             0.22, 0.00, 0.78, 0.00, 1.00, 0.00])
        self.assertListNear(summ['_prop_of_all-grade'],
                            [1.00, 0.53, 0.47, 1.00, 1.00, 1.00, 
                             1.00, 0.00, 1.00, 0.00, 1.00, 0.00])

    def test_value_suppression(self):
        ds = _get_ds()
        summ = ds.summ(condcol('grade', suppress(3)), 
                       condcol('supplier', suppress(None)),
                       mean('size'))
        self.assertListNear(summ['row_ordinal'], [0, 1, 2, 3, 4, 5])
        self.assertListNear(summ['grade'], [0, 0, 1, 1, 2, 2])
        self.assertListNear(summ['supplier'], [1, 2, 1, 2, 1, 2])
        self.assertListNear(summ['mean_of_size'], 
                            [None, None, 6.0, 8.0, None, None])
        # And some boundary cases:
        summ = ds.summ(condcol('grade', suppress()), 'supplier')
        self.assertEqual(len(summ), 12)

    def test_value_suppression_and_filter(self):
        ds = _get_ds()
        summ = ds.summ(condcol('grade', suppress(3)), 
                       condcol('supplier', suppress(None)),
                       mean('size'),
                       filterexpr='supplier != 1') 
        self.assertListNear(summ['row_ordinal'], [0, 1, 2])
        self.assertListNear(summ['grade'], [0, 1, 2])
        self.assertListNear(summ['supplier'], [2, 2, 2])
        self.assertListNear(summ['mean_of_size'], [None, 8.0, None])

    def test_value_suppression_and_propn_nomt(self):
        ds = _get_ds()
        summ = ds.summ(condcol('grade', suppress(3)), 
                       condcol('supplier', suppress(None)),
                       mean('size'),
                       proportions=True, nomt=True)
        self.assertListNear(summ['grade'], [0, 0, 1, 1, 2, 2])
        self.assertListNear(summ['supplier'], [1, 2, 1, 2, 1, 2])
        self.assertListNear(summ['mean_of_size'], 
                            [None, None, 6.0, 8.0, None, None])
        self.assertListNear(summ['_prop_of_all-grade-supplier'],
                            [ 0.00, 0.00, 0.13, 0.25, 0.00, 0.00])
        self.assertListNear(summ['_prop_of_all-supplier'],
                            [ 0.00, 0.00, 0.25, 0.50, 0.00, 0.00])
        self.assertListNear(summ['_prop_of_all-grade'],
                            [ 0.00, 0.00, 0.33, 1.00, 0.00, 0.00])

    def test_coalesce(self):
        ds = _get_ds()
        summ = ds.summ(condcol('grade', coalesce(2,3), coalesce(0, 1)), 
                       'supplier',
                       mean('size'))
        self.assertListNear(summ['grade'], [0, 0, 0, 2, 2, 2])
        self.assertListNear(summ['supplier'], [None, 1, 2, None, 1, 2])
        self.assertListNear(summ['mean_of_size'], 
                            [6.55, 6.0, 8.0, 6.5, 8.8, None])


if __name__ == '__main__':
    unittest.main()
