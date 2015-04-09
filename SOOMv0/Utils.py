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
# $Id: Utils.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Utils.py,v $

from MA import *
import soomfunc
import textwrap  # used to wrap column headings
import errno
import os
import copy
import sets
from SOOMv0 import common

# from Python Cookbook p 4
def makedict(**kwargs):
    return kwargs

# simple pluralisation based on code by Robin Palmar:
#   http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/82102
def pluralise(text):
    postfix = 's'
    if len(text) > 2:
        vowels = 'aeiou'
        if text[-2:] in ('ch', 'sh'):
            postfix = 'es'
        elif text[-1:] == 'y':
            if text[-2:-1] in vowels:
                postfix = 's'
            else:
                postfix = 'ies'
                text = text[:-1]
        elif text[-2:] == 'is':
            postfix = 'es'
            text = text[:-2]
        elif text[-1:] in ('s','z','x'):
            postfix = 'es'
    return '%s%s' % (text, postfix)

# combinations support functions
# Based on Cookbook recipe by Ulrich Hoffmann:
#   http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/190465
# Modified by Dave Cole
def xcombinations(items, n):
    if n == 0:
        yield []
    else:
        for i in xrange(len(items)):
            for cc in xcombinations(items[i + 1:], n - 1):
                yield [items[i]] + cc

def cross(*args):
    ans = [[]]
    for arg in args:
        ans = [x + [y] for x in ans for y in arg]
    return ans

def combinations(*seqs):
    yield []
    for i in range(len(seqs)):
        for subseqs in xcombinations(seqs, i + 1):
            if len(subseqs) == 1:
                for item in subseqs[0]:
                    yield [item]
            else:
                for item in cross(*subseqs):
                    yield item

# other stuff

def isect(a,b): # redundant, I think.
    return soomfunc.intersect(vector1_val1,vector2_val2)

def standardise_cmp_op(op):
    op = op.lower()
    op = op.strip()
    if op in ("starting with", "=:", "==:", "startingwith", "eq:", "startswith", "starts with"):
        return "==:", None
    elif op in ("less than", "lessthan", "lt", "<"):
        return "<", less # Numeric.less
    elif op in ("less than:", "lessthan:", "lt:", "<:"):
        return "<:", None
    elif op in ("greater than", "greaterthan", "gt", ">"):
        return ">", greater # Numeric.greater
    elif op in ("greater than:", "greaterthan:", "gt:", ">:"):
        return ">:", None
    elif op in ("greater than or equal to", "greaterthanorequalto", "greater or equal", "greaterequal", "ge", ">=", "=>"):
        return ">=", greater_equal # Numeric.greater_equal
    elif op in ("greater than or equal to:", "greaterthanorequalto:", "greater or equal:", "greaterequal:", "ge:", ">=:", "=>:"):
        return ">=:", None
    elif op in ("less than or equal to", "lessthanorequalto", "less or equal", "lessequal", "le", "<=", "=<"):
        return "<=", less_equal # Numeric.less_equal
    elif op in ("less than or equal to:", "lessthanorequalto:", "less or equal:", "lessequal:", "le:", "<=:", "=<:"):
        return "<=:", None
    elif op in ("not equal to", "notequalto", "not equal", "notequal", "does not equal", "doesnotequal", "ne", "!=", "!==", "#", "<>"):
        return "!=", not_equal # Numeric.not_equal
    elif op in ("not equal to:", "notequalto:", "not equal:", "notequal:", "does not equal:", "doesnotequal:", "ne:", "!=:", "!==:", "#:", "<>:", "not starting with", "notstartingwith", "notstartswith", "not startswith", "not starts with"):
        return "!=:", None
    elif op in ("equal to", "equals", "equalto", "eq", "=", "=="):
        return "==", equal # Numeric.equal
    else:
        return op, None


def leftouterjoin(leftds,leftjoincols,leftdatacols,rightds,rightjoincols,rightdatacols,null_rrow):
    ljkeys = []
    for ljcol in leftjoincols:
        origcol = ljcol.split("=")[0]
        if len(ljcol.split("=")) > 1:
            newcol = ljcol.split("=")[1]
        else:
            newcol = origcol
        ljkeys.append(newcol)
    ljkeys.sort()
    rjkeys = []
    for rjcol in rightjoincols:
        origcol = rjcol.split("=")[0]
        if len(rjcol.split("=")) > 1:
            newcol = rjcol.split("=")[1]
        else:
            newcol = origcol
        rjkeys.append(newcol)
    rjkeys.sort()
    if ljkeys != rjkeys:
        raise ValueError, "Join keys don't match!"

    leftdictlist,lcols = todictlist(leftds,leftjoincols,leftdatacols)
    rightdictlist,rcols = todictlist(rightds,rightjoincols,rightdatacols)

    joinedset = {}
    for lkey in lcols + rcols:
        joinedset[lkey] = []

    # pprint.pprint(joinedset)

    ldl_keys = leftdictlist.keys()
    #print ldl_keys
    ldl_keys.sort()
    #print ldl_keys

    for lkey in ldl_keys:
        lrows = leftdictlist[lkey]
        rrows = rightdictlist.get(lkey,None)
        for lrow in lrows:
            jrow = {}
            jrow.update(lrow)
            if rrows:
                for rrow in rrows:
                    jrow.update(rrow)
                    for jkey in jrow.keys():
                        joinedset[jkey].append(jrow[jkey])
            else:
                for lrow in lrows:
                    jrow.update(null_rrow)
                    for jkey in jrow.keys():
                        joinedset[jkey].append(jrow[jkey])

    return joinedset

def innerjoin(leftds,leftjoincols,leftdatacols,rightds,rightjoincols,rightdatacols):
    ljkeys = []
    for ljcol in leftjoincols:
        origcol = ljcol.split("=")[0]
        if len(ljcol.split("=")) > 1:
            newcol = ljcol.split("=")[1]
        else:
            newcol = origcol
        ljkeys.append(newcol)
    ljkeys.sort()
    rjkeys = []
    for rjcol in rightjoincols:
        origcol = rjcol.split("=")[0]
        if len(rjcol.split("=")) > 1:
            newcol = rjcol.split("=")[1]
        else:
            newcol = origcol
        rjkeys.append(newcol)
    rjkeys.sort()
    if ljkeys != rjkeys:
        raise ValueError, "Join keys don't match!"

    leftdictlist,lcols = todictlist(leftds,leftjoincols,leftdatacols)
    rightdictlist,rcols = todictlist(rightds,rightjoincols,rightdatacols)

    joinedset = {}
    for lkey in lcols + rcols:
        joinedset[lkey] = []

    # pprint.pprint(joinedset)

    ldl_keys = leftdictlist.keys()
    #print ldl_keys
    ldl_keys.sort()
    #print ldl_keys

    for lkey in ldl_keys:
        lrows = leftdictlist[lkey]
        rrows = rightdictlist.get(lkey,None)
        for lrow in lrows:
            jrow = {}
            jrow.update(lrow)
            if rrows:
                for rrow in rrows:
                    jrow.update(rrow)
                    for jkey in jrow.keys():
                        joinedset[jkey].append(jrow[jkey])
    return joinedset

# functions for rates
# this whole area of how datasets are joined needs reworking - principles are OK, details need revision.

"""
def todictlist(summaryset,joincols,datacols):
    # print summaryset.keys()
    dictlist = {}
    allcols = []
    for col in list(joincols) + list(datacols):
        if col not in allcols:
            allcols.append(col)
    for i in xrange(len(summaryset[joincols[0]])):
        joinkeylist = []
        for jcol in joincols:
            joinkeylist.append(summaryset[jcol.split("=")[0]][i])
        joinkey = tuple(joinkeylist)
        rowdict = {}
        cols = []
        for col in allcols:
            origcol = col.split("=")[0]
            if len(col.split("=")) > 1:
                newcol = col.split("=")[1]
            else:
                newcol = origcol
            rowdict[newcol] = summaryset[origcol][i]
            cols.append(newcol)
        if dictlist.has_key(joinkey):
            dictlist[joinkey].append(rowdict)
        else:
            dictlist[joinkey] = [rowdict]
    return dictlist, cols
"""

def todictlist(sumset,joincols,datacols):
    # print summaryset.keys()
    dictlist = {}
    allcols = []
    for col in list(joincols) + list(datacols):
        if col not in allcols:
            allcols.append(col)
    for i in xrange(len(getattr(sumset,joincols[0]).data)):
        joinkeylist = []
        for jcol in joincols:
            joinkeylist.append(getattr(sumset,jcol.split("=")[0]).data[i])
        joinkey = tuple(joinkeylist)
        rowdict = {}
        cols = []
        for col in allcols:
            origcol = col.split("=")[0]
            if len(col.split("=")) > 1:
                newcol = col.split("=")[1]
            else:
                newcol = origcol
            rowdict[newcol] = getattr(sumset,origcol).data[i]
            cols.append(newcol)
        if dictlist.has_key(joinkey):
            dictlist[joinkey].append(rowdict)
        else:
            dictlist[joinkey] = [rowdict]
    return dictlist, cols

# define some date output transformations
# move to soomutilfuncs.py probably
def ddmmyyyy(indatetime,sep="/"):
    if indatetime is None:
        return "All date/times"
    else:
        fmt = "%d" + sep + "%m" + sep + "%Y"
        return indatetime.strftime(fmt)

def fulldate(indatetime):
    if indatetime is None:
        return "All date/times"
    else:
        fmt = "%A, %d %B %Y"
        return indatetime.strftime(fmt)

def helpful_mkdir(path):
    try:
        os.makedirs(path)
    except OSError, (eno, estr):
        if eno != errno.EEXIST:
            raise OSError(eno, '%s: mkdir %s' % (estr, path))

def assert_args_exhausted(args = None, kwargs = None):
    if args is not None and args:
        raise common.Error('Unknown argument(s): %s' % 
                               ', '.join([repr(arg) for arg in args]))
    if kwargs is not None and kwargs:
            raise common.Error('Unknown keyword argument(s): %s' % 
                               ', '.join(kwargs.keys()))
