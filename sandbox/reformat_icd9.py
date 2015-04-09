import psyco
psyco.full()
from time import time
import re

def A(data):
    if data and len(data) == 5:
        if data[3] == "-":
            return data[0:3]
        elif data[4] == "-":
            if data[0] == "E":
                return data[0:4]
            else:
                return ".".join((data[0:3],data[3]))
        else:
            if data[0] == "E":
                return ".".join((data[0:4],data[4]))
            else:
                # return data[0:3] + "." + data[3:5]
                return ".".join((data[0:3],data[3]))
    else:
        return data

def B(data):
    if data and len(data) == 5:
        if data[3] == "-":
            return data[:3]
        elif data[4] == "-":
            if data[0] == "E":
                return data[:4]
            else:
                return data[:3] + '.' + data[3]
        else:
            if data[0] == "E":
                return data[:4] + '.' + data[4]
            else:
                return data[:3] + '.' + data[3]
    else:
        return data

data = [l.strip() for l in open('/tmp/x', 'U')]

map(A, data)
map(B, data)

st = time()
a = map(A, data)
print "A", time() - st

st = time()
b = map(B, data)
print "B", time() - st

print "A == B", a == b
