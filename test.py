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
# $Id: test.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/test.py,v $

import sys
import os
import unittest
import optparse

from SOOMv0 import soom

topdir = os.path.dirname(__file__)
sys.path.insert(0, topdir)
sys.path.insert(0, os.path.join(topdir, 'soomext'))

test_dirs = 'tests', 'soomext/test',
sys.path[0:0] = test_dirs

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbose', dest='verbosity',
                        action='count', default=1) 
    parser.add_option('-m', '--messages', dest='messages',
                        action='store_true', default=False)
    options, args = parser.parse_args()
    soom.messages = options.messages
    if options.messages:
        options.verbosity = max(2, options.verbosity)
    if args:
        tests = args
    else:
        tests = []
        for test_dir in test_dirs:
            for f in os.listdir(test_dir):
                if f.endswith('.py') and not f.startswith('.') and f != 'all.py':
                    tests.append(f[:-len('.py')])
    test_suite = unittest.defaultTestLoader.loadTestsFromNames(tests)
    test_runner = unittest.TextTestRunner(verbosity=options.verbosity)
    result = test_runner.run(test_suite)
    sys.exit(not result.wasSuccessful())
    
