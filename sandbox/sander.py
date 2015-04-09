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
# $Id: sander.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/sandbox/sander.py,v $

from Numeric import *
import math

import math

def factgen():
    n = 1
    t = 1
    while True:
        t = t * n
        n += 1
        yield t

def fact(x):
    fg = factgen()
    f = 1
    for t in xrange(int(x)):
        f = fg.next()
    return f

def logfact(x):
    fg = factgen()
    f = 1
    for t in xrange(int(x)):
        f = fg.next()
    return math.log(f)

def exact(a, b, c, d, names=None):
    _clevel = 0.95
    _criter = 0.0001
    _maxit = 1000
    _midp = 1
    _oflow = 708
    _rrt = 1.0
    if len(b) != len(a) or len(c) != len(a) or len(d) != len(a):
        raise ValueError, "All input vectors must be same length"
    if innerproduct(a,d) == 0 and innerproduct(b,c) == 0:
        raise ValueError, "No tables with non-zero diagonal or off-diagonal products are allowed."
    if names:
        print "Exact 2x2 analysis of association of %s and %s." % (names[0], names[1])
        print "Crude table:"
        print sum(a), sum(b)
        print sum(c), sum(d)
    print 'original a,b,c,d:', a,b,c,d
    # margins
    m1 = (a + b != 0) and (a + c != 0) and (b + d != 0) and (c + d != 0)
    print 'm1 non-zero margin mask:', m1
    # delete any strata with a zero margin
    a = compress(m1,a)
    b = compress(m1,b)
    c = compress(m1,c)
    d = compress(m1,d)
    print 'a,b,c,d after compress:', a,b,c,d
    # reverse sort the strata
    st = argsort(a+b+c+d).tolist()
    print "st = ", st, type(st)
    st.reverse()
    print "st = ", st, type(st)
    a = take(a, st)
    b = take(b, st)
    c = take(c, st)
    d = take(d, st)
    print '"a,b,c,d after sort:', a,b,c,d
    # flip tables if necessary
    if sum(a) > sum(d):
        d, a = a, d    
    if sum(b) > sum(c):
        c, b = b, c    
    sw = sum(a) > sum(b) # sw also used for flow control later!
    if sw:
        b, a = a, b
        d, c = c, d
        _rrt = 1.0 / _rrt
    # number of strata
    ns = len(a)
    print "ns = ", ns
    # overflow cntrol constant
    oflow = -_oflow / float(ns)
    # marginal case totals
    m1 = a + b
    print "a, b:", a,b
    print 'm1:', m1
    ms = sum(m1)
    # marginal exposure totals
    n1 = a + c
    n0 = b + d
    print "m1, ms, n1, n0:", m1, ms, n1, n0
    # bounds of stratum-specific "a" cells
    l = maximum(0, m1 - n0)
    u = minimum(m1, n1)
    print "l = ", l
    print "u = ", u
    cl = concatenate((array([0.0]), cumsum(l)))
    cu = concatenate((array([0.0]), cumsum(u)))    
    print 'cl = ', cl
    print 'cu = ', cu
    # "a" cell total
    as = sum(a)
    # compute network co-efficients
    # initialise recursively defined co-efficient matrix
    mm = zeros((cu[ns]+1,ns+1),typecode=Float32)
    mm[0,0] = 1
    print mm
    print "l=", l
    print "u=", u
    print "cl=", cl
    print "cu=", cu
    # print "range for k:", 0,ns-1
    k = -1
    # for k in range(ns):
    while True:
        k += 1
        j = int(cl[k+1])
        i = j - 1
        # print "range for i:", j-1, cu[k+1] - 1
        # for i in range(int(j-1),int(cu[k+1])):
        while True:
            i += 1
            r = int(max(l[k], i - cu[k])) - 1
            # print "range for r:", max(l[k], i - cu[k]) - 1, min(u[k], i-cl[k]) - 1
            # print "actual range for r:", range(int(max(l[k], i - cu[k]) - 1), int(min(u[k], i-cl[k])))
            # for r in range(int(max(l[k], i - cu[k]) - 1), int(min(u[k], i-cl[k]))):
            while True:
                r += 1
                print "k, j, i, r", k, j, i, r
                print "[i, k]:", i, k
                print "mm[i,k]", mm[i,k]
                print "[i-r,k]:", i-r, k
                print "mm[i-r,k]", mm[i-r,k] 
                #print "oflow", oflow
                #print "n1[k], logfact(n1[k])", n1[k], logfact(n1[k])
                #print "n1[k] - r, logfact(n1[k] - r)", n1[k] - r, logfact(n1[k] - r)
                #print "r, logfact(r)", r, logfact(r)
                #print "n0[k], logfact(n0[k])", n0[k], logfact(n0[k])
                #print "n0[k] - m1[k] + r, logfact(n0[k] - m1[k] + r)", n0[k] - m1[k] + r, logfact(n0[k] - m1[k] + r)
                #print "m1[k] - r, logfact(m1[k] - r)", m1[k] - r, logfact(m1[k] - r)
                print (mm[i,k] + mm[i-r,k] * exp(oflow + \
                logfact(n1[k]) - logfact(n1[k] - r) - logfact(r) + \
                logfact(n0[k]) - logfact(n0[k] - m1[k] + r) - \
                logfact(m1[k] - r)))
                print (exp(oflow + \
                logfact(n1[k]) - logfact(n1[k] - r) - logfact(r) + \
                logfact(n0[k]) - logfact(n0[k] - m1[k] + r) - \
                logfact(m1[k] - r)))
                mm[i,k] = (mm[i,k] + mm[i-r,k] * exp(oflow + \
                logfact(n1[k]) - logfact(n1[k] - r) - logfact(r) + \
                logfact(n0[k]) - logfact(n0[k] - m1[k] + r) - \
                logfact(m1[k] - r)))
                print mm
                print '--------------'
                if r >= int(min(u[k], i-cl[k])):
                    break
            print "==============="
            if i >= cu[k+1]:
                break
        print "*****************"
        if k >= ns-1:
            break
    cl = int(cl[ns])
    cu = int(cu[ns])
    print cl, cu, ns
    print "mm:", mm
    print mm[cl:cu, ns] # debug
    print transpose(mm[cl:cu, ns]) # debug
    lc = log(transpose(mm[cl:cu, ns]))
    lc = lc - max(lc)
    # compute p-values for testing _rrt
    s = arrayrange(cl, cu - cl + 2) # double check this!
    # null probs from 0 to as
    p = exp(lc + log(_rrt)*s) 
    p = p / float(sum(p))
    # Fisher p-values
    ip = as - cl + 1
    plf = sum(p[0:ip-1])
    puf = 1.0 - plf + p[ip-1]
    # 2-sided mid-p
    pm = plf - p[ip-1]/2.0
    pm = 2.0*minimum(pm, 1.- pm)
    pf = 2.0*minimum(plf,puf)
    if sw:
        _rrt = 1.0/_rrt
    if names: # print p-values
        print "Two-sided p-values for testing OR = %d" % _rrt
        print "(from doubling the smaller of the lower and upper p) --:"
        print "                   Fisher: %d   mid-p: %d" % (pf, pm)
    # Find confidence limits
    rr = array([-1.0, -1.0, -1.0])
    namerr = ["Lower CL", "estimate", "Upper CL"]
    # Alpha level for CL
    alpha = (1.0 - _clevel) / 2.0
    alpha = array([1.0 - alpha, 0.5, alpha])
    zedu = innerproduct(a, d) == 0
    zedl = innerproduct(b, c) == 0
    
    if zedu or zedl:
        # Add a small constant to a and find only one limit.
        n = n1 + n0
        a = (n*a + n1*m1/n)/(n + 1)
        b = m1 - a
        c = n1 - a
        d = n0 - b
    i = 2.0 * zedu
    while i < (3.0 - 2.0*zedl):
        i += 1
        if _midp:
            m = 0.5
        else:
            m = (3.0 - i) / 2.0
        targ = alpha[i-1]
        # use bisection on log odds ratio
        # upper and lower bracketting values
        bh = lrr + (i - 2.0)*rad + 1.0
        bl = bh - 2.0
        # pv is hypergeometric terms, sh, sl, sm are p-vals
        pv = exp(lc + bh*s) 
        sh = (sum(pv[0:ip-1])  - m*pv[ip-1]) / float(sum(pv))
        pv = exp(lc + bl*s) 
        sl = (sum(pv[0:ip-1]) - m*pv[ip-1]) / float(sum(pv))
        cnv = 0
        iter = 0
        while not cnv and iter < _maxit:
            iter += 1
            if sl < targ:
                # decrememt bl and try again
                bl -= 1
                pv = exp(lc + bl*s) 
                sl = (sum(pv[0:ip-1]) - m*pv[ip-1]) / float(sum(pv))
                continue
            elif sh > targ:
                # increment bh and try again
                bh += 1
                pv = exp(lc + bh*s) 
                sh = (sum(pv[0:ip-1]) - m*pv[ip-1]) / float(sum(pv))
                continue
            bm = (bh + bl) / 2.0
            pv = exp(lc + bm*s) 
            sm = (sum(pv[0:ip-1]) - m*pv[ip-1]) / float(sum(pv)) 
            if ((sm - targ) >= 0) == ((sl - targ) >= 0):
                # push up bl
                bl = bm
                sl = sm
            else:
                # push down bh
                bh = bm
                sh = sm
            cnv = abs(bh - bl) < _criter and abs(sm - targ) < _criter / 10.0
        if not cnv:
            print "No convergence for %s after %i iteractions." % (namerr[i-1], iter)
        else:
            rr[i-1] = exp(bm)
    if sw:
        sw = (rr == 0)
        rr = (1.0 - sw) / (array([rr[2],rr[1],rr[0]]) + sw)
        i = 4 - i
    return (rr[1], rr[0], rr[2], plf, puf, pm)

a = array([3,2,1,1,4,4,5,4,3,8,5,8,5,4,4,7,4,5])
b = array([5,4,4,5,1,5,3,4,2,1,1,1,3,1,2,1,2,3])
c = array([1,1,1,0,1,1,1,1,1,0,1,1,1,1,1,1,0,1])
d = array([0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,1,0])
names = ['crying','treated','strata']

a = array([3,2],typecode=Float32)
b = array([5,4],typecode=Float32)
c = array([1,1],typecode=Float32)
d = array([2,3],typecode=Float32)

print exact(a,b,c,d,names=names)

