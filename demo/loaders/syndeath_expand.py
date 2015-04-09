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
#   Define and load new WHO World Standard Population data
#
# $Id: syndeath_expand.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/loaders/syndeath_expand.py,v $

# Python standard modules
import os
import sys
import csv
import gzip
import random
import itertools

def intreader(f):
    for row in csv.reader(f):
        yield tuple([int(f) for f in row])

def minmax_iter(minmax):
    this, rest = minmax[0], minmax[1:]
    for n in xrange(minmax[0][0], minmax[0][1]+1):
        if rest:
            for v in minmax_iter(rest):
                yield (n,) + v
        else:
            yield (n,)

def pairwise(i, n=2):
    while i:
        yield i[:n]
        i = i[n:]

def syndeath_expand(datadir, scratchdir, verbose=False):
    srcfile = os.path.join(datadir, 'synthetic_deaths_comp.gz')
    dstfile = os.path.join(scratchdir, 'synthetic_deaths.csv.gz')
    if (os.path.exists(dstfile) and 
        os.path.getmtime(srcfile) <= os.path.getmtime(dstfile)):
        return
    if verbose:
        print 'Expanding %r' % srcfile
    src = gzip.open(srcfile, 'rb')
    try:
        reader = intreader(src)
        minf = reader.next()
        maxf = reader.next()
        count = 0
        minmax = zip(minf, maxf)
        lines = []
        for v, row in itertools.izip(minmax_iter(minmax), reader):
            for cod, freq in pairwise(row):
                for n in xrange(freq):
                    lines.append((random.random(),) + v + (cod,))
            if verbose:
                c = len(lines) / 10000
                if c != count:
                    count = c
                    print '\r%s' % len(lines),
                    sys.stdout.flush()
    finally:
        if verbose:
            print
        src.close()
    lines.sort()
    dst = gzip.open(dstfile, 'wb', 9)
    okay = False
    if verbose:
        print 'Writing %r' % dstfile
    try:
        writer = csv.writer(dst)
        writer.writerow('agegrp,sex,region,year,causeofdeath'.split(','))
        for row in lines:
            writer.writerow(row[1:])
        okay = True
    finally:
        dst.close()
        if not okay:
            os.unlink(dstfile)

if __name__ == '__main__':
    dir = os.path.dirname(__file__)
    syndeath_expand(os.path.join(dir, '..', 'rawdata'))
