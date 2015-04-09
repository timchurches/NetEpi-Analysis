import sys, os
from time import time
demodir = os.path.join(os.path.dirname(__file__), '..', 'demo')
sys.path.insert(0, demodir)
import loaders.nhds

if 1:
    import psyco
    psyco.full()

class options:
    datadir = os.path.join(demodir, 'rawdata')

src = loaders.nhds.nhds96_source(options)
st = time()
i = 0
for line in src.get_file_iter():
    i += 1
elapsed = time() - st
print '%d total, %.3f per second, took %.3f' % (i, i / elapsed, elapsed)

src = loaders.nhds.nhds96_source(options)
st = time()
i = 0
try:
    while 1:
        d = src.next_rowdict()
        i += 1
except StopIteration:
    pass
elapsed = time() - st
print '%d total, %.3f per second, took %.3f' % (i, i / elapsed, elapsed)
