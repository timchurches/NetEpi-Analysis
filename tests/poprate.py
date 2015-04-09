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
# $Id: poprate.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/tests/poprate.py,v $

from SOOMv0 import *
from SOOMv0 import Analysis
import unittest
import MA

# The following data and results are originally from  Selvin, S. Statistical Analysis of
# Epidemiologic Data (Monographs in Epidemiology and Biostatistics, V. 35), Oxford University Press;
# 3rd edition (May 1, 2004), via the EpiTools pacakge for R (see http://www.medepi.net/epitools/ )

agegrp_outtrans = {1:"<1",2:"1-4",3:"5-14",4:"15-24",5:"25-34",6:"35-44",7:"45-54",
                   8:"55-64",9:"65-74",10:"75-84",11:"85+"}

def _get_ds1():
    ds = Dataset('deaths')
    ds.addcolumnfromseq('agegrp', label='Age Group',
                        coltype='categorical', datatype='int',outtrans=agegrp_outtrans,
                        data=[1,2,3,4,5,6,7,8,9,10,11,1,2,3,4,5,6,7,8,9,10,11])
    ds.addcolumnfromseq('_freq_', label='Frequency',
                        coltype='scalar', datatype='int',
                        data=[141,926,1253,1080,1869,4891,14956,30888,41725,26501,5928,
                               45,201,320,670,1126,3160,9723,17935,22179,13461,2238])
    ds.addcolumnfromseq('year', label='Year',
                        coltype='ordinal', datatype='int',
                        data=[1960]*11 + [1940]*11)
    return ds

def _get_pop_ds1():
    ds = Dataset('pops')
    ds.addcolumnfromseq('agegrp', label='Age Group',
                        coltype='categorical', datatype='int',outtrans=agegrp_outtrans,
                        data=[1,2,3,4,5,6,7,8,9,10,11,1,2,3,4,5,6,7,8,9,10,11])
    ds.addcolumnfromseq('_freq_', label='Frequency',
                        coltype='scalar', datatype='int',
                        data=[1784033,7065148,15658730,10482916,9939972,10563872,
                              9114202,6850263,4702482,1874619,330915,
                              906897,3794573,10003544,10629526,9465330,8249558,
                              7294330,5022499,2920220,1019504,142532])
    ds.addcolumnfromseq('year', label='Year',
                        coltype='ordinal', datatype='int',
                        data=[1960]*11 + [1940]*11)
    return ds

def _get_ds1_40():
    ds = Dataset('deaths40')
    ds.addcolumnfromseq('agegrp', label='Age Group',
                        coltype='categorical', datatype='int',outtrans=agegrp_outtrans,
                        data=[1,2,3,4,5,6,7,8,9,10,11])
    ds.addcolumnfromseq('_freq_', label='Frequency',
                        coltype='scalar', datatype='int',
                        data=[45,201,320,670,1126,3160,9723,17935,22179,13461,2238])
    ds.addcolumnfromseq('year', label='Year',
                        coltype='ordinal', datatype='int',
                        data=[1940]*11)
    return ds

def _get_pop_ds1_40():
    ds = Dataset('pops40')
    ds.addcolumnfromseq('agegrp', label='Age Group',
                        coltype='categorical', datatype='int',outtrans=agegrp_outtrans,
                        data=[1,2,3,4,5,6,7,8,9,10,11])
    ds.addcolumnfromseq('_freq_', label='Frequency',
                        coltype='scalar', datatype='int',
                        data=[906897,3794573,10003544,10629526,9465330,8249558,
                              7294330,5022499,2920220,1019504,142532])
    ds.addcolumnfromseq('year', label='Year',
                        coltype='ordinal', datatype='int',
                        data=[1940]*11)
    return ds

def _get_ds1_60():
    ds = Dataset('deaths60')
    ds.addcolumnfromseq('agegrp', label='Age Group',
                        coltype='categorical', datatype='int',outtrans=agegrp_outtrans,
                        data=[1,2,3,4,5,6,7,8,9,10,11])
    ds.addcolumnfromseq('_freq_', label='Frequency',
                        coltype='scalar', datatype='int',
                        data=[141,926,1253,1080,1869,4891,14956,30888,41725,26501,5928])
    ds.addcolumnfromseq('year', label='Year',
                        coltype='ordinal', datatype='int',
                        data=[1960]*11)
    return ds

def _get_pop_ds1_60():
    ds = Dataset('pops60')
    ds.addcolumnfromseq('agegrp', label='Age Group',
                        coltype='categorical', datatype='int',outtrans=agegrp_outtrans,
                        data=[1,2,3,4,5,6,7,8,9,10,11])
    ds.addcolumnfromseq('_freq_', label='Frequency',
                        coltype='scalar', datatype='int',
                        data=[1784033,7065148,15658730,10482916,9939972,10563872,
                              9114202,6850263,4702482,1874619,330915])
    ds.addcolumnfromseq('year', label='Year',
                        coltype='ordinal', datatype='int',
                        data=[1960]*11)
    return ds

def _get_std_ds1():
    ds = Dataset('std')
    ds.addcolumnfromseq('agegrp', label='Age Group',
                        coltype='categorical', datatype='int',outtrans=agegrp_outtrans,
                        data=[1,2,3,4,5,6,7,8,9,10,11])
    data=[1784033,7065148,15658730,10482916,9939972,10563872,
          9114202,6850263,4702482,1874619,330915]
    ds.addcolumnfromseq('_stdpop_', label='Standard population',
                        coltype='scalar', datatype='int',
                        data=data)
    return ds

class dir_indir_std_rate_test1(unittest.TestCase):

    def assertListNear(self, first, second, prec=2):
        def ma_fmt(v, prec):
            if v is None:
                return 'None'
            return '%.*f' % (prec, v)
        first = ', '.join([ma_fmt(v, prec) for v in first])
        second = ', '.join([ma_fmt(v, prec) for v in second])
        self.assertEqual(first, second, '[%s] != [%s]' % (first, second))

    def test_dsr_and_cr(self):
        ds = _get_ds1()
        pop = _get_pop_ds1()
        std = _get_std_ds1()
        results = Analysis.calc_directly_std_rates(ds, pop, std)
        self.assertListNear(results['dsr'], [139.25054, 166.08744])
        self.assertListNear(results['dsr_ll'], [138.21410, 165.18636])
        self.assertListNear(results['dsr_ul'], [140.29275, 166.99223])
        self.assertListNear(results['cr'], [119.52864, 166.08744])
        self.assertListNear(results['cr_ll'], [118.65139, 165.18636])
        self.assertListNear(results['cr_ul'], [120.41077, 166.99223])

    # AM - disabled because test is broken
    def XXX_test_isr(self):
        ds = _get_ds1()
        pop = _get_pop_ds1()
        #ds.makefilter('d40',expr='year == 1940')
        #ds.makefilter('d60',expr='year == 1960')
        #pop.makefilter('p40',expr='year == 1940')
        #pop.makefilter('p60',expr='year == 1960')
        #dths40 = ds.filter(name='d40')
        #dths60 = ds.filter(name='d60')
        #pops40 = pop.filter(name='p40')
        #pops60 = pop.filter(name='p60')

        dths40 = _get_ds1_40()
        dths60 = _get_ds1_60()
        pops40 = _get_pop_ds1_40()
        pops60 = _get_pop_ds1_60()
        
        dthsumm40 = dths40.summ(SummaryStats.asum('_freq_'))
        
        if 0:
            print dths40
            print dthsumm40
            print dthsumm40.describe_with_cols()
            print dths60
            print pops40
            print pops60
                
        results = Analysis.calc_indirectly_std_ratios(dths40, pops40, dths60, pops60,
                                             popset_popcol='_freq_', stdpopset_popcol='_freq_')
        if 0:
            print results
        #self.assertListNear(results['dsr'], [139.25054, 166.08744])
        #self.assertListNear(results['dsr_ll'], [138.21410, 165.18636])
        #self.assertListNear(results['dsr_ul'], [140.29275, 166.99223])
        #self.assertListNear(results['cr'], [119.52864, 166.08744])
        #self.assertListNear(results['cr_ll'], [118.65139, 165.18636])
        #self.assertListNear(results['cr_ul'], [120.41077, 166.99223])

# The following are synthethic tests data - counts and populations are 
# arbitrarily chosen numbers. Results checked against those produced by
# known-good SAS macros written and used by the Centre for Epidemiology
# and Research, NSW Dept of Health - see 
# http://www.health.nsw.gov.au/public-health/chorep/toc/app_methods.htm#3.2

def _get_ds2():
    ds = Dataset('visits')
    ds.addcolumnfromseq('sex', label='Sex',
                        coltype='categorical', datatype='int',
                        all_value=-1,
                        data=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                              2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,])
    ds.addcolumnfromseq('agegrp', label='Age Group',
                        coltype='categorical', datatype='int',
                        data=[ 1, 2, 3, 4, 5, 6, 7, 8, 9,
                              10,11,12,13,14,15,16,17,18, 
                               1, 2, 3, 4, 5, 6, 7, 8, 9,
                              10,11,12,13,14,15,16,17,18,])
    ds.addcolumnfromseq('_freq_', label='Frequency',
                        coltype='scalar', datatype='int',
                        data=[659,146,102,140,221,177,268,302,276,
                              240,207,163,143,117, 94, 65, 43, 38,
                              549, 97, 93,248,299,300,288,292,231,
                              168,149,149,180,144,132,128, 67, 85,])
    ds.addcolumnfromseq('freq_wgtd_by_wgt', label='Statistical weighting',
                        coltype='scalar', datatype='float',
                        data=[ 19380,  3831,  2592,  3624,  5676,  4522,
                                6836,  7783,  7186,  6195,  5358,  4239,
                                3628,  2950,  2401,  1634,  1108,   954, 
                               16419,  2566,  2337,  6512,  7907,  7808,
                                7597,  7690,  6008,  4274,  3736,  3901, 
                                4707,  3723,  3420,  3256,  1676,  2151,])
    return ds

def _get_pop_ds2():
    ds = Dataset('pop')
    ds.addcolumnfromseq('agegrp', label='Age Group',
                        coltype='categorical', datatype='int',
                        data=[1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 
                              3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 
                              5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 
                              7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 
                              9, 9, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 
                             11, 11, 11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 
                             13, 13, 13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 
                             15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 
                             17, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18])
    ds.addcolumnfromseq('race', label='Race',
                        coltype='categorical', datatype='int',
                        data=[1,1,2,2,5,5,1,1,2,2,5,5,1,1,2,2,5,5,
                              1,1,2,2,5,5,1,1,2,2,5,5,1,1,2,2,5,5,
                              1,1,2,2,5,5,1,1,2,2,5,5,1,1,2,2,5,5,
                              1,1,2,2,5,5,1,1,2,2,5,5,1,1,2,2,5,5,
                              1,1,2,2,5,5,1,1,2,2,5,5,1,1,2,2,5,5,
                              1,1,2,2,5,5,1,1,2,2,5,5,1,1,2,2,5,5,])
    ds.addcolumnfromseq('sex', label='Sex',
                        coltype='categorical', datatype='int',
                        data=[1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,
                              1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,
                              1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,
                              1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,
                              1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,
                              1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,])
    ds.addcolumnfromseq('_freq_', label='Population',
                        coltype='scalar', datatype='int',
                        data=
     [7995000,7592000,1584000,1540000, 566000, 548000,8162000,7759000,1703000,
      1654000, 548000, 519000,7910000,7497000,1591000,1542000, 530000, 509000,
      7938000,7450000,1567000,1539000, 506000, 483000,7208000,6916000,1282000,
      1378000, 510000, 478000,7757000,7650000,1267000,1440000, 572000, 571000,
      8541000,8425000,1355000,1504000, 520000, 566000,9420000,9307000,1386000,
      1550000, 510000, 553000,8945000,8905000,1247000,1409000, 465000, 523000,
      7767000,7845000, 984000,1154000, 387000, 444000,6386000,6578000, 670000,
       820000, 290000, 318000,4870000,5142000, 527000, 672000, 217000, 236000,
      4116000,4482000, 428000, 567000, 168000, 197000,3905000,4535000, 398000,
       529000, 129000, 171000,3396000,4318000, 289000, 418000, 101000, 135000,
      2628000,3683000, 208000, 327000,  67000,  91000,1558000,2632000, 111000,
       212000,  39000,  52000, 986000,2443000,  83000, 199000,  28000,  44000,])
    return ds

if 0:
    # Test broken by API changes
    class popn_rate_test(unittest.TestCase):

        def assertListNear(self, first, second, prec=2):
            def ma_fmt(v, prec):
                if v is None:
                    return 'None'
                return '%.*f' % (prec, v)
            first = ', '.join([ma_fmt(v, prec) for v in first])
            second = ', '.join([ma_fmt(v, prec) for v in second])
            self.assertEqual(first, second, '[%s] != [%s]' % (first, second))

        def test_simple(self):
            ds = _get_ds1()
            pop = _get_pop_ds1()
            Analysis.calc_directly_std_rates(ds, pop)
            # AM - This result has not be verified at this time...
            self.assertListNear(ds['pop_rate_wgtd_by_wgt'],
                [0.001910, 0.000368, 0.000258, 0.000362, 0.000631, 0.000471, 
                0.000656, 0.000688, 0.000674, 0.000678, 0.000729, 0.000755, 
                0.000770, 0.000666, 0.000634, 0.000563, 0.000649, 0.000870, 
                0.001696, 0.000258, 0.000245, 0.000687, 0.000901, 0.000808, 
                0.000724, 0.000674, 0.000554, 0.000453, 0.000484, 0.000645, 
                0.000897, 0.000711, 0.000702, 0.000794, 0.000579, 0.000801],
                prec=5)


if __name__ == '__main__':
    unittest.main()
