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
# $Id: rconv.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Plot/rconv.py,v $

# 3rd Party modules
from rpy import *
import MA, Numeric
from mx import DateTime

# SOOM bits
from SOOMv0.common import *
from SOOMv0 import DataTypes

r_datefmt = '%Y-%m-%d %H:%M:%S'
MissingDate = DateTime.DateTime(0).strftime(r_datefmt)

def rname(name):
    """ 
    Make a Python symbol name safe as an R symbol name
    """
    return name.replace('_', '.').replace('-', '.')

def MA_to_R(data):
    """
    Given an MA array, return an R array with "missing" values
    """
    mask = data.mask()
    if mask is None:
        return data.filled()
    try:
        # We have to do this within R because the assignment to is.na is a
        # very strange beast, and there is no obvious way to do it directly
        # via rpy.
        r.assign('mask', Numeric.nonzero(mask) + 1)
        r.assign('data', data.filled())
        r('is.na(data)<-mask')
        return r('data')
    finally:
        r.remove('data')
        r.remove('mask')

def Date_to_R(data):
    return r.strptime([d.strftime(r_datefmt) for d in data], r_datefmt)

def Missing_Date_to_R(data):
    """
    Given an array (list) of mx.DateTime or None objects, return 
    an R time array with missing values.
    """
    dates = []
    mask = []
    for i in xrange(len(data)):
        d = data[i]
        if d is None:
            mask.append(i+1)
            dates.append(MissingDate)
        else:
            dates.append(d.strftime(r_datefmt))
    try:
        r.assign('mask', mask)
        r.assign('data', r.strptime(dates, r_datefmt))
        r('is.na(data)<-mask')
        return r('data')
    finally:
        r.remove('data')
        r.remove('mask')

def rwrap(text, cex=1):
    lines = []
    rmode = get_default_mode()
    try:
        set_default_mode(BASIC_CONVERSION)
        for line in text.splitlines():
            words = line.split()
            wordwidth = r.strwidth(words, units='fig')
            if not isinstance(wordwidth, list):
                wordwidth = [wordwidth]
            partial = []
            partial_width = 0
            for word, width in zip(words, wordwidth):
                if partial_width + width * cex >= 0.8:
                    lines.append(' '.join(partial))
                    partial = []
                    partial_width = 0
                partial.append(word)
                partial_width += width * cex
            if partial:
                lines.append(' '.join(partial))
    finally:
        set_default_mode(rmode)
    return '\n'.join(lines)

def summ_to_array(ds, measure, debug=False):
    from SOOMv0.CrossTab import CrossTab

    ct = CrossTab.from_summset(ds)
    data = ct[measure].data
    if MA.isMaskedArray(data):
        data = data.filled()    # Dealing with frequencies, so this is valid.
    data = data.astype(Numeric.Float64)
    if debug: print type(data)
    if debug: print data
    array = r.as_array(data)
    dimnames = []
    labels = []
    for axis in ct.axes:
        dimnames.append([axis.col.do_outtrans(v) for v in axis.values])
        labels.append(axis.col.label or axis.col.name)
    dimnames = r.list(*dimnames)
    dimnames = r.names__(dimnames, labels)
    array = r.dimnames__(array, dimnames)
    if debug: r.print_(array)
    return array
