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
# $Id: api_demo.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/api_demo.py,v $

import os
import sys
import time
import itertools
import inspect
import traceback
import struct
import mx.DateTime
import Numeric
import MA
import optparse
from SOOMv0 import *

slow_warning = '''
    NOTE: this may take several minutes if you have the full 2 million
    NHDS records loaded.
'''

optp = optparse.OptionParser()
optp.add_option('--soompath', dest='soompath',
                help='SOOM dataset path')
optp.add_option('--writepath', dest='writepath',
                help='Dataset write path (for temporary objects, defaults '
                     'to SOOMPATH)')
optp.add_option('--nopause', dest='pause', action='store_false',
                default=True,
                help='Don\'t pause for user after each step')
optp.add_option('--nomessages', dest='messages', action='store_false',
                default=True,
                help='Don\'t generate SOOM messages')
optp.add_option('--skipto', dest='skipto',
                help='Skip to the named test')
optp.add_option('--skipslow', dest='skipslow', 
                default=False, action='store_true',
                help='Skip slow tests')
optp.add_option('--use-psyco', dest='psyco', 
                default=False, action='store_true',
                help='Enable Psyco JIT compiler')
optp.add_option('--log', dest='log',
                help='Log output to file LOG')
options, args = optp.parse_args()

if options.psyco:
    try:
        import psyco
    except ImportError:
        soom.warning('Psyco not available')
    else:
        psyco.full()

class test:
    skipto = None
    tests = []
    slow = False
    broken = False

    passed = 0
    exceptions = []
    skipped = 0
    cummulative = 0.0

    logfile = None
    if options.log:
        logfile = open(options.log, 'a')

    def __init__(self, name, text, code):
        self.name = name
        self.text = text
        self.code = code
        test.tests.append(self)
        self.run()

    def write(cls, msg):
        if cls.logfile:
            print >> cls.logfile, msg
        print msg
    write = classmethod(write)

    def prefix(self, lines, prefix):
        lines = lines.splitlines()
        for line in lines:
            self.write(prefix + line.rstrip())

    def deindent(self, lines):
        lines = lines.splitlines()
        while not lines[0]:
            del lines[0]
        first = lines[0]
        offset = len(first) - len(first.lstrip())
        lines = [line[offset:] for line in lines]
        while not lines[-1]:
            del lines[-1]
        return '\n'.join(lines)

    def run(self):
        class skip(Exception): pass
        try:
            if test.skipto:
                if test.skipto == self.name:
                    test.skipto = None
                elif self.name not in ('0a', '1'):
                    raise skip
            if self.broken:
                raise skip
            if self.slow and options.skipslow:
                raise skip
        except skip:
            test.skipped += 1
            return
        self.write('\n%s\n# test %s' % ('#' * 78, self.name))
        if self.text:
            self.prefix(self.deindent(self.text), '# ')
            if self.slow:
                self.prefix(self.deindent(slow_warning), '# ')
        if self.code:
            code = self.deindent(self.code)
            self.prefix(code, '>>> ')
            if options.pause:
                raw_input('Press Enter to execute this code\n')
            st = time.time()
            try:
                exec code in globals(), globals()
                et = time.time()
                test.cummulative += et - st
            except KeyboardInterrupt:
                test.skipto = 'end'
            except:
                test.exceptions.append(self.name)
                exc_type, exc_value, exc_tb = sys.exc_info()
                try:
                    while exc_tb:
                        if exc_tb.tb_frame.f_code.co_filename == '<string>':
                            exc_tb = exc_tb.tb_next
                            break
                        exc_tb = exc_tb.tb_next
                    l = traceback.format_exception(exc_type, exc_value, exc_tb)
                    l.append('TEST FAILED')
                    self.prefix(''.join(l), '!!! ')
                finally:
                    del exc_type, exc_value, exc_tb
            else:
                test.passed += 1
                self.write('That took %.3f seconds' % (et - st))
        else:
            if options.pause:
                raw_input('Press Enter to continue\n')

    def report(cls):
        if cls.exceptions:
            cls.write('Tests that raised exceptions: %s' % 
                      ', '.join(cls.exceptions))
        cls.write('%d tests okay, %d tests skipped, %d tests raised exceptions'%
                  (cls.passed, cls.skipped, len(cls.exceptions)))
        cls.write('total test run time %.3f' % (cls.cummulative,))
    report = classmethod(report)

class slowtest(test):
    def __init__(self, *args, **kw):
        self.slow = True
        test.__init__(self, *args, **kw)

class brokentest(test):
    def __init__(self, *args, **kw):
        self.broken = True
        test.__init__(self, *args, **kw)

test.skipto = options.skipto

test('0',
    '''
    SOOMv0 API demo

    Make your terminal window as wide as possible and the font as small as
    possible so that lines don't wrap.
    ''', None)

test('0a',
    'Import the SOOM module.',
    'from SOOMv0 import *')

if not options.soompath:
    options.soompath = os.path.normpath(os.path.join(os.path.dirname(__file__), 
                                                     '..', 'SOOM_objects'))
soom.setpath(options.soompath, options.writepath or options.soompath)
soom.messages = options.messages


test('1',
    'Load the nhds dataset object from disc where it is stored as a compressed pickle:',
    'nhds = dsload("nhds")')

# Currently broken
brokentest('1a',
    'Examine what datasets are currently loaded.',
    'print soom')

test('1b',
    'Examine the metadata property for the nhds dataset.',
    'print nhds.describe()')

test('1c',
    'Examine the metadata properties for all nhds columns.',
    'print nhds.describe_with_cols()')

test('2a',
    'Examine the metadata for one column',
    '''print nhds['marital_status'].describe()''')

slowtest('2b',
    '''
    Now define a further (not very useful) derived age column

    Note: you only need to derive columns once if they are permanent,
    as here.  Typically this would be done when the data is first loaded,
    but new permanent columns can still be created during analysis
    without having to re-write the entire dataset.
    ''',
    '''
    def age_hours(raw_age,age_units):
        units_multiplier = Numeric.choose(age_units - 1, (365.25, 30.5, 1.0))
        returnarray =  raw_age * 24 * units_multiplier
        returnmask = Numeric.zeros(len(returnarray))
        return returnarray, returnmask
    nhds.lock()
    nhds.derivedcolumn(dername='age_hours',dercols=('raw_age','age_units'),derfunc=age_hours,coltype='scalar',datatype=float,outtrans=None,label='Age (hours)')
    nhds.save()
    ''')

test('2c',
    'Examine the metadata for the nhds dataset again.',
    'print nhds.describe_with_cols()')

test('3a',
    'Pythonic item access on one column of the dataset',
    '''print nhds['age'][3846]''')

test('3b',
    'Pythonic item access on a date column of the dataset',
    '''print nhds['randomdate'][3846]''')

test('3c',
    'Pythonic item access on a string column of the dataset',
    '''print nhds['diagnosis1'][3846]''')

test('4a',
    'Pythonic slicing of one column of the dataset',
    '''print nhds['geog_region'][2:5]''')

test('4c',
    'Pythonic slicing of a string column of the dataset',
    '''print nhds['diagnosis1'][2:9]''')

test('5',
    'The len() function returns the number of rows in a dataset.',
    '''print len(nhds)''')

test('6a',
    '''
    Note that a slice on a column with missing values preserves them
    (denoted by '--').  The randomvalue column contains a uniform random
    variate in the interval 0 and 1 but with all values between 0.7 and
    0.8 set to missing..  
    ''',
    '''print nhds['randomvalue'][500:530]''')

brokentest('6b',
    'Same slice of nhds.randomvalue using the getcolumndata() method',
    '''print nhds.getcolumndata('randomvalue')[500:530]''')

test('7a',
    '''
    Define a function to group age into broad age groups (note use of
    Numpy array operations, not Python loops).
    ''',
    '''
    def broadagegrp(age):
        agrp = MA.choose(MA.greater_equal(age,65),(age,-6.0))
        agrp = MA.choose(MA.greater_equal(agrp,45),(agrp,-5.0))
        agrp = MA.choose(MA.greater_equal(agrp,25),(agrp,-4.0))
        agrp = MA.choose(MA.greater_equal(agrp,15),(agrp,-3.0))
        agrp = MA.choose(MA.greater_equal(agrp,5),(agrp,-2.0))
        agrp = MA.choose(MA.greater_equal(agrp,0),(agrp,-1.0))
        returnarray = -agrp.astype(MA.Int)
        returnmask = Numeric.zeros(len(returnarray))
        return returnarray, returnmask
    ''')

test('7b',
    'Define an output transformation dictionary for these broad age groups',
    '''
    broadagegrp_outtrans = { 
        1:'0 - 4 yrs',
        2:'5 - 14 yrs',
        3:'15 - 24 yrs',
        4:'25 - 44 yrs',
        5:'45 - 64 yrs',
        6:'65+ yrs'
    }
    ''')

slowtest('7c',
    'Now define and create the derived broad age group column.',
    '''
    nhds.lock()
    nhds.derivedcolumn(dername='broadagegrp',dercols=('age',),derfunc=broadagegrp,coltype='ordinal',datatype=int,outtrans=broadagegrp_outtrans,label='Broad Age Group',all_value=0,all_label='All ages')
    nhds.save()
    ''')

test('7d',
    'Let\'s look at the first 30 values of the derived broadagegrp column.',
    '''print  nhds['broadagegrp'][0:29]''')

slowtest('7e',
    'Now define a tuple column, which allows multiple values per record (row).',
    '''
    nhds.lock()
    nhds.derivedcolumn(dername='test_tuples',dercols=('age','sex','geog_region'),derfunc=itertools.izip,coltype='categorical',datatype=tuple,label='Test tuples',all_value=(),all_label='All test tuples')
    nhds.save()
    ''')

test('7f',
    'Now let us see the results.',
    '''
    print nhds['test_tuples'].describe()
    print nhds['test_tuples'][0:29]
    ''')

test('8a',
    'Define a function to take the logs of a column with missing values',
    '''
    def log10random(randomvalue):
        return MA.log10(randomvalue), MA.log10(randomvalue).mask()
    ''')

slowtest('8b',
    'Use that function to create a derived column',
    '''
    nhds.lock()
    nhds.derivedcolumn(dername='lograndomvalue',dercols=('randomvalue',),derfunc=log10random,coltype='scalar',datatype=float)
    nhds.save()
    ''')

test('8c',
    '''
    Look at the first 50 values of the new column - note that missing
    values are propagated correctly.
    ''',
    '''
    print nhds['lograndomvalue'][0:49]
    print 'Length of slice is %i' % len(nhds['lograndomvalue'][0:49])
    ''')

test('9a',
    '''
    We can specify which columns we want in each row when performing
    slicing on the whole dataset, rather than when slicing on a particular
    column.
    ''',
    '''
    nhds['age'].outtrans = None
    nhds.printcols = ('sex','marital_status','age','agegrp','randomvalue')
    ''')

test('9b',
    '''
    Get a whole row - a bit slow the first time because each column has
    to be memory-mapped.
    ''',
    'print nhds[3]')

test('9c',
    '''
    Much faster to get whole rows once the required columns are
    memory-mapped/instantiated.
    ''',
    'print nhds[-20:]')

test('10a',
    '''
    Define a filter and create a filterd versio of the nhds dataset using
    it.  A filter is like the resolved result of an SQL WHERE clause,
    but it can be stored and re-used, at least while the underlying
    dataset remians unchanged. One or more filters can be temporarily
    assigned to a dataset in order to filter all subsequent operations.
    ''',
    '''
    nhds.makefilter('testa',expr='sex = 2')
    nhds.makefilter('testb',expr='agegrp = 15')
    nhds_testa = nhds.filter(name='testa')
    ''')

test('10b1',
    'Note that slicing now honours the filtering.',
    'print nhds_testa[-20:]')

test('10b2',
    'Make a different filtered view of the dataset using the other filter.',
    '''
    nhds_testb = nhds.filter(name='testb')
    print nhds_testb[-20:]
    ''')

test('10c',
    '''
    Define another filter based on a scalar (continuous) column and make
    a filtered view of the dataset using it.
    ''',
    '''
    nhds.makefilter('testc',expr='age ge 23 and age le 24')
    nhds_testc = nhds.filter(name='testc')
    ''')

test('10d',
    '''
    Note that slicing now honours the new filtering only 23 and 24 yr
    olds are displayed.
    ''',
    'print nhds_testc[-20:]')

test('11a',
    'Print the simplest possible summary of the nhds dataset.',
    'print nhds.summ()')

test('11b',
    '''
    Add some statistical measures. This is similar to the SQL:
        select count(*), avg(age), min(age), max(age) from nhds;
    ''',
    '''
    print nhds.summ(mean('age'),minimum('age'),maximum('age'))
    ''')

test('11c',
    '''
    Note that missing data is handled correctly - the randomvalue column
    contains random values in the interval 0 to 1.0, but all values 0.7
    to 0.8 are set to missing (masked).  In SQL you would need to use
    a subquery to count nulls?
    ''',
    '''
    print nhds.summ(nonmissing('randomvalue'),missing('randomvalue'),mean('randomvalue'),minimum('randomvalue'),maximum('randomvalue'))
    ''')

test('11d',
    'Compare to same query but using the age column (no missing values)',
    '''
    print nhds.summ(nonmissing('age'),missing('age'),mean('age'),minimum('age'),maximum('age'))
    ''')

brokentest('11e',
    '''
    Note that intelligence can be built into the  objects: try to
    calculate statistics on a categorical integer column and it gives
    an error message since that makes no sense.
    ''',
    '''
    print nhds.summ(nonmissing('geog_region'),missing('geog_region'),mean('geog_region'),minimum('geog_region'),maximum('geog_region'))
    ''')

test('12',
    '''
    Check the cardinality of a categorical column.
    Similar to SQL: select distinct geog_region from nhds;
    ''',
    '''
    print nhds['geog_region'].cardinality()
    ''')

test('13a',
    '''
    Now for a univariate contingency table.
    Same as SQL: select count(*) from nhds group by geog_region;
    ''',
    '''
    print nhds.summ('geog_region')
    ''')

test('13b',
    '''
    Same again, but adding a marginal total to the table.
    Same as SQL: select count(*) from nhds group by geog_region union select count(*) from nhds;
    Note the SQL union subclause to calculate marginal totals will be omitted henceforth for brevity.
    ''',
    '''
    print nhds.summ('geog_region',allcalc=True)
    ''')

test('13c',
    '''
    Same again, but adding proportions to the table
    Um, the SQL for this would be quite horrible...
    ''',
    '''
    print nhds.summ('geog_region',proportions=True)
    ''')

test('14a',
    '''
    Add some more statistics based on the (scalar) days_of_care column.
    Same as SQL: select count(*), avg(days_of_care), max(days_of_care), min(days_of_care) from nhds group by geog_region;
    ''',
    '''
    print nhds.summ('geog_region',mean('days_of_care'),maximum('days_of_care'),minimum('days_of_care'),allcalc=True)
    ''')

test('14b',
    '''
    Now calculate these statistics on multiple columns at once.
    Same as SQL: select count(*), avg(days_of_care), max(days_of_care), min(days_of_care), avg(age), max(age), min(age) from nhds group by geog_region;'
    ''',
    '''
    print nhds.summ('geog_region',mean('days_of_care'),mean('age'),maximum('days_of_care'),maximum('age'),minimum('days_of_care'),minimum('age'),allcalc=True)
    ''')

test('15a',
    '''
    How about quantiles, based on the days_of_care column?
    Relatively few SQL database do quantiles (percentiles).
    ''',
    '''
    print nhds.summ('geog_region',p25('days_of_care'),median('days_of_care'),p75('days_of_care'),allcalc=True)
    ''')

test('16a',
    '''
    Now a two-way contingency table.
    Same as SQL: select count(*) from nhds group by geog_region, sex;
    ''',
    '''
    print nhds.summ('geog_region','sex')
    ''')

test('16b',
    '''Add some marginal totals and proportions.''',
    '''
    print nhds.summ('geog_region','sex',proportions=True)
    ''')

test('16c',
    '''Show only intermediate summary levels.''',
    '''
    print nhds.summ('geog_region','sex',levels=[1])
    ''')

test('17a',
    '''
    Now a three-way contingency table
    Same as SQL: select count(*) from nhds group by geog_region, sex, marital_status;
    ''',
    '''
    print nhds.summ('geog_region','sex','marital_status',allcalc=True)
    ''')

test('17b',
    '''
    Add proportions for a greater than two-dimensional table (a unique
    feature - even stats' packages don't do this!) - note the helpful
    column labelling (although needs more work...).
    ''',
    '''
    print nhds.summ('geog_region','sex','marital_status',proportions=True)
    ''')

test('18a',
    '''
    And now a four-way contingency table.
    Same as SQL: select count(*) from nhds group by geog_region, sex, discharge_status, marital_status;'
    ''',
    '''
    print nhds.summ('geog_region','sex','discharge_status','marital_status',allcalc=True)
    ''')

slowtest('18b',
    '''Add mean and median age to 18a above.''',
    '''
    print nhds.summ('geog_region','sex','discharge_status','marital_status',mean('age'),median('age'),weightcol=None,allcalc=True)
    ''')

# TODO: the weighted median function throws an exception with this - must
# investigate
brokentest('18c',
    '''Same again but with weighted mean and count.''',
    '''
    print nhds.summ('geog_region','sex','discharge_status','marital_status',mean('age'),median('age'),weightcol='analysis_wgt',allcalc=True)
    ''')

test('18d',
    '''The acid test - can it handle 5 columns?''',
    '''
    print nhds.summ('geog_region','sex','discharge_status','marital_status','hosp_ownership',allcalc=True,weightcol=False)
    ''')

test('18e',
    '''
    The alkali test - can it handle 6 columns? Note that this takes
    quite a while to run.
    ''',
    '''
    print nhds.summ('geog_region','sex','discharge_status','marital_status','hosp_ownership','num_beds',weightcol=False)
    ''')

test('18f',
    '''
    The litmus test - can it handle 6 columns with all levels? Note
    that this produces very lengthy output, so we will just calculate
    the summary dataset, but not print it (which takes ages).
    ''',
    '''
    sixways = nhds.summ('geog_region','sex','discharge_status','marital_status','hosp_ownership','num_beds',weightcol=False,allcalc=True)
    ''')

test('19a',
    '''
    Demonstration of coalescing values on-the-fly.
    Here is the un-coalesced hospital ownership, both unformatted and
    formatted.
    ''',
    '''
    nhds['hosp_ownership'].use_outtrans=0
    print nhds.summ('hosp_ownership')
    nhds['hosp_ownership'].use_outtrans=1
    print nhds.summ('hosp_ownership')
    ''')

test('19b',
    'Now coalesce values 1 and 3',
    '''
    print nhds.summ(condcol('hosp_ownership',coalesce(1,3,label='Private incl. non-profit')))
    ''')

test('19d',
    '''
    This on-the-fly aggregation also works for higher-order contingency tables.
    ''',
    '''
    print nhds.summ('geog_region',condcol('hosp_ownership',coalesce(1,3,label='Private incl. non-profit')),allcalc=True)
    ''')

test('19e',
    '''
    Note the on-the-fly coalescing can also be done by a function -
    this function truncates ICD9CM codes to 3 digits.
    ''',
    '''
    def icd9cm_truncate(icd9cm_code):
            return icd9cm_code[0:3]
    ''')

# AM - changing coltype is not longer supported (July '05)
test('19f',
    '''
    Let's override the column type for diagnosis1 so it is presented in
    sorted order.
    ''',
    '''
    nhds['diagnosis1'].coltype = 'ordinal'
    ''')

test('19g',
    'Et voila aussi!',
    '''
    print nhds.summ(condcol('diagnosis1',coalesce(icd9cm_truncate)),filterexpr='diagnosis1 startingwith "2"')
    ''')

# TODO - try the following with weightcol='analsysis_wgt' - seems to tickle errors in Stats.py
test('20a',
    '''
    Let's explore 'lambda' (unnamed, on-the-fly) filters.
    ''',
    '''
    print nhds.summ('geog_region','sex','discharge_status','marital_status',mean('age'),filterexpr='geog_region = 2 and discharge_status = 1',weightcol=None,allcalc=True)
    ''')

test('20b',
    '''Use a second filter to filter the dataset.''',
    '''
    print nhds.summ('geog_region','sex','discharge_status','marital_status',mean('age'),filterexpr='sex = 2',weightcol=None,allcalc=True)
    ''')

test('20c',
    '''Use the first filter again for an overall summary.''',
    '''
    print nhds.summ(mean('age'),filterexpr='geog_region = 2 and discharge_status = 1',weightcol=None,allcalc=True)
    ''')

test('21a',
    '''
    Yet another filter - note the 'startingwith' operator, like the SQL
    'like' operator.
    ''',
    '''
    print nhds.summ('diagnosis1', filterexpr='diagnosis1 startingwith "250"')
    ''')

test('21b',
    '''You can turn off the output formatting.''',
    '''
    nhds['diagnosis1'].use_outtrans=False
    print nhds.summ('diagnosis1', filterexpr='diagnosis1 startingwith "250"')
    nhds['diagnosis1'].use_outtrans=True
    ''')

test('21c',
    '''
    Define another filter (filter) using the 'in' operator.
    ''',
    '''
    print nhds.summ('diagnosis1',filteexpr="diagnosis1 in ('250.12','250.13','250.21')")
    ''')

test('21d',
    '''
    Define another filter (filter) using the 'in:' operator ('in' plus 'startingwith')
    ''',
    '''
    nhds['diagnosis1'].coltype = 'ordinal'
    print nhds.summ('diagnosis1',filterexpr="diagnosis1 in: ('250*','01','410.1')")
    ''')

test('22a',
    '''
    Date/time values are supported.
    ''',
    '''
    print nhds.summ('randomdate',filterexpr='year = 1996',allcalc=True)
    ''')

test('22b',
    '''
    You can change the date output format - fulldate is a function object defined in the SOOMv0 module.'
    ''',
    '''
    from SOOMv0.Utils import fulldate
    nhds['randomdate'].outtrans = fulldate
    print nhds.summ('randomdate',filterexpr='year = 1996',allcalc=True)
    ''')

test('22c',
    '''
    You can filter on dates - this is currently rather slow, but it does work.
    ''',
    '''
    print nhds.summ('sex','geog_region',filterexpr='randomdate = date(1996,3,12)')
    ''')

test('22d',
    '''Date range filtering.''',
    '''
    print nhds.summ('randomdate', 'sex', filterexpr='randomdate between (date(1996,10,12),date(1996,11,12))')
    ''')

test('22e',
    '''
    One more test of date ranges, this time using 'not'.
    ''',
    '''
    print nhds.summ('randomdate','sex',filterexpr='randomdate >= date(1996,10,1) and randomdate <= date(1996,11,1) and not randomdate = date(1996,10,15)')
    ''')

# AM - There appears to be a problem with summarising multivalue columns after
# filtering.
brokentest('23a',
    '''
    Demonstration of multivalue columns (no SQL equivalent - needs a join
    between two tables - but perfect for association rule data mining).
    Use a where clause because the cardinality of the diagnosis (ICD9CM)
    columns is rather large.
    ''',
    '''
    print nhds.summ('diagnosis1',filterexpr='diagnosis1 startingwith "250"',allcalc=True)
    print nhds.summ('diagnosis_all',filterexpr='diagnosis_all startingwith "250"',allcalc=True)
    ''')

# This feature no longer exists, but may be re-instated in future versions
# print '#24a. Demonstration of partial result caching.'
# print '#     We can precalculate a particular summary or contingency table.'
# print '>>> nhds.precalculate(var1='sex',var2='geog_region',var3='drg')'
# t = ex()
# nhds.precalculate(var1='sex',var2='geog_region',var3='drg')
# pause(t)

# print '#24b. Now turn on use of the cache and create a summary (but don't print it out - too big).'
# print '>>> soom.use_cache=1'
# print '>>> res = nhds.summ('sex','geog_region','drg',allcalc=True)'
# t = ex()
# soom.use_cache=1
# soom.messages=0
# res = nhds.summ('sex','geog_region','drg',allcalc=True)
# soom.messages=1
# soom.use_cache=1
# res = nhds.summ('sex','geog_region','drg',allcalc=True)
# pause(t)

# print '#24c. Now turn off use of the cache and create the same summary - should be slower.'
# print '>>> soom.use_cache=0'
# print '>>> res = nhds.summ('sex','geog_region','drg',allcalc=True)'
# t = ex()
# soom.use_cache=0
# res = nhds.summ('sex','geog_region','drg',allcalc=True)
# pause(t)

# AM - Subsetting is currently not functional. Filtered Datasets should
# largely replace them. At some future point, the ability to deep copy 
# datasets will be added (but first we need per-user workspaces).
brokentest('25',
    '''
    Physical dataset subsetting (as opposed to filtering) is also
    possible.  This is still a bit slow when rebuilding the indexes
    on the subset and there needs to be work done on accelerating the
    indexing loop, which could be parallelised with possible speed gains
    (but not linear gains).
    ''', None)

brokentest('25a',
    'First create a filter containing a random sample of rows.',
    '''
    nhds.makefilter('randomsample', expr='randomvalue < 0.1')
    ''')

brokentest('25b',
    '''
    Then physically subset the nhds dataset, keeping only a few columns.
    ''',
    '''
    subnhds = subset(nhds,subsetname='subnhds',label=None,filtername='randomsample',\
                    keepcols=('geog_region','sex','days_of_care','age','randomvalue'))
    ''')

brokentest('25c',
    '''Demonstrate that the subsetting has occured..''',
    '''
    print subnhds.summ('geog_region',allcalc=True)
    ''')

brokentest('25d',
    '''And compare with parent...''',
    '''
    print nhds.summ('geog_region',allcalc=True)
    ''')

brokentest('25e',
    None,
    '''
    print subnhds.summ('sex',minimum('randomvalue'),mean('randomvalue'),maximum('randomvalue'),allcalc=True)
    print subnhds.describe_with_cols()
    ''')

# Causes a memory allocation error on large datasets (33 million rows)
brokentest('26a',
    '''
    Note that all the summary methods and function don't just print out
    results, they can return the results as data objects (in this case
    as a dataset instance).
    ''',
    '''
    sex_by_geog_region = nhds.summ('sex','geog_region',mean('age'),allcalc=True)
    print sex_by_geog_region.describe_with_cols()
    print sex_by_geog_region[:]
    ''')

# TODO: re-instate this for next version
brokentest('26b',
    '''
    Thus we can further manipulate the summary datasets. Let's summarise
    by age group, sex and geographical region, for 1997 only, and join
    it with appropriate populations and calculate age/sex-specific rates.
    ''',
    '''
    soom.messages=0
    popsgeog97 = dsload('popsgeog97')
    pops = popsgeog97.sum('sex','agegrp','geog_region',cellcols='pop',options=[s.sum])
    nhds.makefilter('only97',expr='year eq 97')
    counts = nhds.sum('sex','agegrp','geog_region',filtername='only97',cellcols='days_of_care',options=[s.wgtfreq],wgtcol='analysis_wgt')
    print counts.metadata
    counts_and_pops = leftouterjoin(counts,('geog_region','sex','agegrp'),('_freq_wgtd_by_analysis_wgt',),pops,('geog_region','sex','agegrp'),('sum_of_pop=pop',),None)
    counts = counts_and_pops['_freq_wgtd_by_analysis_wgt']
    pops = counts_and_pops['pop']
    rates = []
    for i in range(len(counts_and_pops['sex'])):
            rates.append((float(counts[i]) / pops[i])*100000)
    counts_and_pops['rates'] = rates
    rr = makedataset('regional_rates',label='1997 regional age/sex-sepecific hospitalisation rates')
    rr.addcolumnfromseq(name='agegrp',data=counts_and_pops['agegrp'],mask=None,label='Age Group',datatype=int,coltype='ordinal',outtrans=nhds.agegrp.outtrans)
    rr.addcolumnfromseq(name='sex',data=counts_and_pops['sex'],mask=None,label='Sex',coltype='categorical',datatype=int,outtrans=nhds.sex.outtrans)
    rr.addcolumnfromseq(name='geog_region',data=counts_and_pops['geog_region'],mask=None,label='Geographical Region',coltype='categorical',datatype=int,outtrans=nhds.geog_region.outtrans)
    rr.addcolumnfromseq(name='count',data=counts_and_pops['_freq_wgtd_by_analysis_wgt'],mask=None,label='Weighted count',coltype='scalar',datatype=int)
    rr.addcolumnfromseq(name='pop',data=counts_and_pops['pop'],mask=None,label='Popn.',coltype='scalar',datatype=int)
    rr.addcolumnfromseq(name='rate',data=counts_and_pops['rates'],mask=None,label='Rate per 100,000',coltype='scalar',datatype=float)
    soom.messages=1
    print rr
    ''')

brokentest('27',
    '''
    Support for association rules is under development. Here we form
    all maximal frequent sets from a multivalued column (diagnosis_all)
    which contains all diagnosis codes (1 to 7) for each admission
    to hospital. Note that a minor extension to the SOOM data model is
    needed to support formation of frequent sets from heterogenous columns
    (eg sex, age group and diagnoses). Work on formation of association
    rules from teh frequent sets is also proceeding. One advantage of
    the SOOM approach is that the row ordinals (record IDs) of all rows
    which participate in each frequent set are stored as the sets are
    created, making subsequent manipulation of those records possible
    and swift. The following derives all maximal frequent sets with
    support of ).1% or more, and prints those with 2 or more elements
    in them. Easily parallelised!
    ''',
    '''
    nhds.maximal_frequent_sets('diagnosis_all',minsup=0.001,min_set_size_to_print=2)
    ''')

test.report()
