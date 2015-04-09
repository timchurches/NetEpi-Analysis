import math
from time import time
from SOOMv0 import *
from SOOMv0.Utils import combinations
from soomfunc import intersect

ds = dsload('nhds', path='../SOOM_objects')

cols = (
    'geog_region','sex','discharge_status','marital_status',
    'hosp_ownership','num_beds'
)

st = time()
values = []
for col in cols:
    values.append(ds[col].inverted.items())

class stats:
    def __init__(self, name):
        self.name = name
        self.buckets = [0] * 1000
        self.total = 0

    def add(self, n):
        self.total += n
        bucket = 0
        if n > 0:
            bucket = int(math.log(n, 10)) + 1
        self.buckets[bucket] += 1

    def report(self):
        print self.name, 'total:', self.total
        for v, c in enumerate(self.buckets):
            if c:
                print "  >%8d: %d" % (pow(10, v) - 1, c)
        

if 1:
    calls = 0
    result = []
    vl = stats('vector length distribution')
    cvl = stats('cache vector length distribution')
    for veckey in combinations(*values):
        if len(veckey) > 0:
            values, rows = zip(*veckey)
            if len(rows) == 1:
                rows = rows[0]
            else:
                calls += 1
                rows = intersect(*rows)
                vl.add(len(rows))
            if len(values) > 1 and len(values) < len(cols):
                cvl.add(len(rows))
#            result.append((values, rows))
    elapsed = time() - st
    print '%d intersect calls, %.3f sec, %.3f sec per call' % (
        calls, elapsed, elapsed / calls)
    vl.report()
    cvl.report()

if 0:
    calls = 0
    cache = {}
    for veckey in combinations(*values):
        if len(veckey) > 0:
            values, rows = zip(*veckey)
            if len(rows) == 1:
                rows = rows[0]
            else:
                calls += 1
                partial = cache.get(values[:-1], None)
                if partial:
                    rows = intersect(partial, rows[-1])
                else:
                    rows = intersect(*rows)
                if len(values) > 1 and len(values) < len(cols):
                    cache[values] = rows
    elapsed = time() - st
    print '%d intersect calls, %.3f sec, %.3f sec per call' % (
        calls, elapsed, elapsed / calls)
