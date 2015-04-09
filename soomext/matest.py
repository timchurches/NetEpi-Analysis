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
# $Id: matest.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/soomext/matest.py,v $

import MA
import Numeric
from soomarray import ArrayDict

ad = ArrayDict('blah.dat', 'r+')
a = Numeric.array([0,1,2,3,4,5,6,7,8,9],Numeric.Int)
m = Numeric.array([0,0,0,0,0,1,0,0,1,0],Numeric.Int)
ad['matest1'] = MA.array(a, mask = m)
del ad

ad = ArrayDict('blah.dat')
matest = ad['matest1']

print "matest: ", matest
print "sum of matest: ", MA.sum(matest)
print "length of matest: ", len(matest)
print "count of matest: ", MA.count(matest)
print "average of matest: ", MA.average(matest)
print "minimum of matest: ", MA.minimum(matest)
print "maximum of matest: ", MA.maximum(matest)

del ad

ad = ArrayDict('blah.dat', 'w')

a = Numeric.array(xrange(1000),Numeric.Int)
m = Numeric.array(Numeric.repeat(Numeric.array([0,1],Numeric.Int),500),Numeric.Int)
ad['matest2'] = MA.array(a, mask = m)

m = Numeric.array(Numeric.repeat(Numeric.array([1,0],Numeric.Int),500),Numeric.Int)
ad['matest3'] = MA.array(a, mask = m)
del ad

ad = ArrayDict('blah.dat')

matest2 = ad['matest2']

print "matest2: ", matest2
print "sum of matest2: ", MA.sum(matest2)
print "length of matest2: ", len(matest2)
print "count of matest2: ", MA.count(matest2)
print "average of matest2: ", MA.average(matest2)
print "minimum of matest2: ", MA.minimum(matest2)
print "maximum of matest2: ", MA.maximum(matest2)

matest3 = ad['matest3']

print "matest3: ", matest3
print "sum of matest3: ", MA.sum(matest3)
print "length of matest3: ", len(matest3)
print "count of matest3: ", MA.count(matest3)
print "average of matest3: ", MA.average(matest3)
print "minimum of matest3: ", MA.minimum(matest3)
print "maximum of matest3: ", MA.maximum(matest3)
