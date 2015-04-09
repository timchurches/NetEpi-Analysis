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
Test package modules

The module files must have a function "suite" which returns
an instance of unittest.TestSuite or unittest.TestCase.

$Id: all.py 2626 2007-03-09 04:35:54Z andrewm $
$Source: /usr/local/cvsroot/NSWDoH/SOOMv0/soomext/test/all.py,v $
"""

import unittest

class AllTestSuite(unittest.TestSuite):
    all_tests = [
        "soomfunctest",
    ]

    def __init__(self):
        unittest.TestSuite.__init__(self)
        for module_name in self.all_tests:
            module = __import__(module_name, globals())
            self.addTest(module.suite())

if __name__ == '__main__':
    unittest.main(defaultTest='AllTestSuite')
