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
# $Id: SOOM_demo_data_load.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/SOOM_demo_data_load.py,v $

# Python standard modules
import time
import os
import sys
import random
import optparse

try:
    import psyco
except ImportError:
    pass
else:
#    psyco.log('/tmp/psyco.log')
    psyco.full()

# SOOM modules
from SOOMv0 import *

# following code used to generate random values for a calculated column for
# testing purposes
random.seed(123)

datasets = 'nhds', 'whopop', 'whotext', 'syndeath', 'epitools'

def main():
    optp = optparse.OptionParser()
    optp.add_option('--datasets', dest='datasets',
                    default='all',
                    help='datasets to load - %s, default "all"' % ', '.join(datasets))
    optp.add_option('-S', '--soompath', dest='soompath',
                    help='SOOM dataset write path')
    optp.add_option('--nhds-years', dest='nhds_years',
                    help='NHDS years to load')
    optp.add_option('-N', '--rowlimit', dest='rowlimit', type='int',
                    help='stop loading datasets after ROWLIMIT rows')
    optp.add_option('--nhds-iterations', dest='nhds_iterations', type='int',
                    help='number of iterations of NHDS data to load (default=1)',
                    default=1)
    optp.add_option('-C', '--chunkrows', dest='chunkrows', type='int',
                    default=5000,
                    help='read sources in CHUNKROWS blocks (default 5000)')
    optp.add_option('-q', '--quiet', dest='verbose', action='store_false',
                    default=True,
                    help='quieter operation')
    options, args = optp.parse_args()
    options.datasets = options.datasets.split(',')
    if 'all' in options.datasets:
        options.datasets = datasets
    else:
        for dsname in options.datasets:
            if dsname not in datasets:
                optp.error('Unknown dataset %r' % dsname)
    moduledir = os.path.dirname(__file__)
    options.datadir = os.path.join(moduledir, 'rawdata')
    options.scratchdir = os.path.join(moduledir, 'scratch')
    if not options.soompath:
        options.soompath = os.path.normpath(os.path.join(moduledir, '..', 'SOOM_objects'))
    soom.messages = options.verbose
    soom.setpath(options.soompath, options.soompath)

    loadstart = time.time()

    for dsname in options.datasets:
        mod = __import__('loaders.' + dsname, globals(), locals(), [dsname])
        if options.verbose:
            print 'Using %r loader from %r' % (dsname, mod.__file__)
        mod.load(options)

    elapsed = time.time() - loadstart
    print "Loading of demo data took %.3f seconds" % elapsed

if __name__ == '__main__':
    main()
