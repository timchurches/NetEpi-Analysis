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

# Compare our calc_indirectly_std_ratios with verified SAS results see:
# tests/SAS/indirect_std_check.sas and the data files tests/data/smr_results*

import sys, os
import unittest
import csv
import itertools
import Numeric

import SOOMv0
from SOOMv0.Sources.CSV import CSVDataSource
from SOOMv0.DataSourceColumn import DataSourceColumn
from SOOMv0.Analysis import calc_indirectly_std_ratios as calc_ind
from SOOMv0.CrossTab import CrossTab

thisdir = os.path.abspath(os.path.dirname(__file__))
soomobj = os.path.join(thisdir, '..', '..', 'SOOM_objects')

try:
    event_ds = SOOMv0.dsload('syndeath', path=soomobj)
    pop_ds = SOOMv0.dsload('synpop', path=soomobj)
    skip = 0
except SOOMv0.DatasetNotFound:
    sys.stderr.write('WARNING - %s tests skipped because syndeath datasets '                         'were not found\n' % __file__)
    skip = 1


colnames = [ 'observed', 'expected', 'isr', 'isr_ll', 'isr_ul', ]

if not skip:
    class CSVCols(SOOMv0.Dataset):
        def __init__(self, filename):
            SOOMv0.Dataset.__init__(self, filename)
            f = open(filename, 'rb')
            ds
            try:
                reader = csv.reader(f)
                self.colmap = dict([(c, i) 
                                    for i, c in enumerate(reader.next())])
                self.cols = []
                for i in xrange(len(self.colmap)):
                    self.cols.append([])
                for row in reader:
                    for i, v in enumerate(row):
                        if v:
                            v = float(v)
                        self.cols[i].append(v)
            finally:
                f.close()

        def __getitem__(self, col):
            return self.cols[self.colmap[col]]

    def csv_to_ds(filename):
        name = os.path.basename(filename).replace('.', '_')
        SOOMv0.soom.writepath = '/tmp'      # XXX
        ds = SOOMv0.Dataset(name, summary=True, path='/tmp')
        ds.addcolumn('sex', datatype='int', coltype='categorical')
        ds.addcolumn('region', datatype='int', coltype='categorical')
        ds.addcolumn('observed', datatype='float', coltype='scalar')
        ds.addcolumn('expected', datatype='float', coltype='scalar')
        ds.addcolumn('isr', datatype='float', coltype='scalar')
        ds.addcolumn('isr_ll', datatype='float', coltype='scalar')
        ds.addcolumn('isr_ul', datatype='float', coltype='scalar')
        cols = [
            DataSourceColumn('region', ordinalpos=0),
            DataSourceColumn('sex', ordinalpos=1),
            DataSourceColumn('observed', ordinalpos=4),
            DataSourceColumn('expected', ordinalpos=5),
            DataSourceColumn('isr', ordinalpos=6),
            DataSourceColumn('isr_ll', ordinalpos=7),
            DataSourceColumn('isr_ul', ordinalpos=8),
        ]
        source = CSVDataSource(name, cols, filename, header_rows=1)
        ds.lock()
        ds.loaddata(source, initialise=1, finalise=1)
        return ds


    class _BaseIndirectSAS(unittest.TestCase):
        def basetest(self):
            sasdata = csv_to_ds(os.path.join(thisdir, self.sasresults_file))
            summset = event_ds.summ('sex', 'region', zeros=True,
                                    filterexpr=self.e_filterexpr)
            stdsumset = event_ds.summ('agegrp', 'sex', zeros=True,
                                    filterexpr=self.s_filterexpr)
            ind = calc_ind(summset, pop_ds, stdsumset, pop_ds,
                        conflev=self.conflev, 
                        popset_popcol='pop', stdpopset_popcol='pop')
            sasct = CrossTab.from_summset(sasdata)
            indct = CrossTab.from_summset(ind, shaped_like=sasct)
            for colname in colnames:
                a = sasct[colname].data
                b = indct[colname].data.filled(0)
                if not Numeric.allclose(a, b):
                    if 0:
                        print
                        print ind
                        print a
                        print b
                    self.fail('%s not equal' % colname)

    class test_37_37_90(_BaseIndirectSAS):
        sasresults_file = 'data/smr_results_37_37_CL0.90.csv'
        s_filterexpr = 'causeofdeath = 37'
        e_filterexpr = 'causeofdeath = 37'
        conflev = 0.90
        test = _BaseIndirectSAS.basetest

    class test_37_37_99(_BaseIndirectSAS):
        sasresults_file = 'data/smr_results_37_37_CL0.99.csv'
        s_filterexpr = 'causeofdeath = 37'
        e_filterexpr = 'causeofdeath = 37'
        conflev = 0.99
        test = _BaseIndirectSAS.basetest

    class test_37_95_90(_BaseIndirectSAS):
        sasresults_file = 'data/smr_results_37_95_CL0.90.csv'
        s_filterexpr = 'causeofdeath = 37'
        e_filterexpr = 'causeofdeath = 95'
        conflev = 0.90
        test = _BaseIndirectSAS.basetest

    class test_37_95_99(_BaseIndirectSAS):
        sasresults_file = 'data/smr_results_37_95_CL0.99.csv'
        s_filterexpr = 'causeofdeath = 37'
        e_filterexpr = 'causeofdeath = 95'
        conflev = 0.99
        test = _BaseIndirectSAS.basetest

    class test_95_37_90(_BaseIndirectSAS):
        sasresults_file = 'data/smr_results_95_37_CL0.90.csv'
        s_filterexpr = 'causeofdeath = 95'
        e_filterexpr = 'causeofdeath = 37'
        conflev = 0.90
        test = _BaseIndirectSAS.basetest

    class test_95_37_99(_BaseIndirectSAS):
        sasresults_file = 'data/smr_results_95_37_CL0.99.csv'
        s_filterexpr = 'causeofdeath = 95'
        e_filterexpr = 'causeofdeath = 37'
        conflev = 0.99
        test = _BaseIndirectSAS.basetest

    class test_95_95_90(_BaseIndirectSAS):
        sasresults_file = 'data/smr_results_95_95_CL0.90.csv'
        s_filterexpr = 'causeofdeath = 95'
        e_filterexpr = 'causeofdeath = 95'
        conflev = 0.90
        test = _BaseIndirectSAS.basetest

    class test_95_95_99(_BaseIndirectSAS):
        sasresults_file = 'data/smr_results_95_95_CL0.99.csv'
        s_filterexpr = 'causeofdeath = 95'
        e_filterexpr = 'causeofdeath = 95'
        conflev = 0.99
        test = _BaseIndirectSAS.basetest


if __name__ == '__main__':
    unittest.main()
