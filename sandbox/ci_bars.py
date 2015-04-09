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
# $Id: ci_bars.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/sandbox/ci_bars.py,v $

from rpy import *

# set up dummy test data
testdata = {
            'dsr':(1,2,3,4,5,6,7,8,9,10,0,1,2,3,4,5,6,7,8,9,
                 2,3,4,5,6,7,8,9,10,11,3,4,5,6,7,8,9,10,11,12),
            'year':(1998,1998,1998,1998,1998,1998,1998,1998,1998,1998,
                 1999,1999,1999,1999,1999,1999,1999,1999,1999,1999,
                 2000,2000,2000,2000,2000,2000,2000,2000,2000,2000,
                 2001,2001,2001,2001,2001,2001,2001,2001,2001,2001),
'geog_area':('North','South','East','West','Middle',
            'North','South','East','West','Middle',
            'North','South','East','West','Middle',
            'North','South','East','West','Middle',
            'North','South','East','West','Middle',
            'North','South','East','West','Middle',
            'North','South','East','West','Middle',
            'North','South','East','West','Middle'),
'sex':('Male','Male','Male','Male','Male',
      'Female','Female','Female','Female','Female',
      'Male','Male','Male','Male','Male',
      'Female','Female','Female','Female','Female',
      'Male','Male','Male','Male','Male',
      'Female','Female','Female','Female','Female',
      'Male','Male','Male','Male','Male',
      'Female','Female','Female','Female','Female'),
'age':('Old','Old','Old','Old','Old',
      'Young','Young','Young','Young','Young',
      'Old','Old','Old','Old','Old',
      'Young','Young','Young','Young','Young',
      'Old','Old','Old','Old','Old',
      'Young','Young','Young','Young','Young',
      'Old','Old','Old','Old','Old',
      'Young','Young','Young','Young','Young')
      }

testdata['year'] = [str(x) for x in testdata['year']]

# add dummy lower and upper confidence limits
testdata['dsr_ll'] = [x - 0.7 for x in testdata['dsr']]
testdata['dsr_ul'] = [x + 0.5 for x in testdata['dsr']]

r.library('lattice')

def errorbar_macro(plottype='lineplot',datadict=None,measure=None,measure_lower_limits=None,measure_upper_limits=None,
                   condcols=None,groups=None,horizontal=None,origin=0):

    if horizontal is None:
        if plottype == 'lineplot':
            horizontal = True
        else:
            horizontal = False

    if not horizontal:
        formula = measure + ' ~ ' + condcols[0]
    else:
        formula = condcols[0] + ' ~ ' + measure 
    if len(condcols) > 1:
        formula += ' | ' + condcols[1]
    if len(condcols) > 2:
        formula += ' + ' + ' + '.join(condcols[2:])
        
    rparameters = dict(formulastring=formula, ll=measure_lower_limits, ul=measure_upper_limits, groups=groups, origin=float(origin))    

    try:
        r.remove('errorbardataframe')
        r.remove('errorbarplot')
    except:
        pass

    rdataframe = with_mode(NO_CONVERSION,r.as_data_frame)(datadict)
    r.assign('errorbardataframe',rdataframe)

    if plottype == 'barchart' and not horizontal:
        rplotcode = """
        errorbarplot <- with(errorbardataframe,barchart(%(formulastring)s,
                      origin = %(origin)f,
                      dsr_ll = %(ll)s,
                      dsr_ul = %(ul)s,
                      panel = function(x, y, ..., dsr_ll, dsr_ul, subscripts) {
                          panel.barchart(x, y, subscripts, ...)
                          dsr_ll <- dsr_ll[subscripts]
                          dsr_ul <- dsr_ul[subscripts]
                          panel.segments(as.numeric(x),
                                         dsr_ll,
                                         as.numeric(x),
                                         dsr_ul,
                                         col = 'red', lwd = 2)
                      }))
        """
    elif plottype == 'barchart' and horizontal:
        rplotcode = """
        errorbarplot <- with(errorbardataframe,barchart(%(formulastring)s,
                      origin = %(origin)f,
                      dsr_ll = %(ll)s,
                      dsr_ul = %(ul)s,
                      panel = function(x, y, ..., dsr_ll, dsr_ul, subscripts) {
                          panel.barchart(x, y, subscripts, ...)
                          dsr_ll <- dsr_ll[subscripts]
                          dsr_ul <- dsr_ul[subscripts]
                          panel.segments(dsr_ll,
                                         as.numeric(y),
                                         dsr_ul,
                                         as.numeric(y),
                                         col = 'red', lwd = 2)
                      }))
        """

    elif plottype == 'lineplot' and not horizontal:
        rplotcode = "errorbarplot <- with(errorbardataframe,xyplot(%(formulastring)s,"
        if groups is not None:
            rplotcode += "groups= %(groups)s,"
        rplotcode += """
                      pch = 16, type = 'b',
                      auto.key=TRUE,
                      origin = %(origin)f,
                      dsr_ll = %(ll)s,
                      dsr_ul = %(ul)s,
                      panel.groups =
                      function(x, y, ..., dsr_ll, dsr_ul, subscripts) {
                          dsr_ll <- dsr_ll[subscripts]
                          dsr_ul <- dsr_ul[subscripts]
                          panel.segments(as.numeric(x),
                                         dsr_ll,
                                         as.numeric(x),
                                         dsr_ul,
                                        ...)
                 panel.xyplot(x, y, ...)
                 }))
        """
    elif plottype == 'lineplot' and horizontal:
        rplotcode = "errorbarplot <- with(errorbardataframe,xyplot(%(formulastring)s,"
        if groups is not None:
            rplotcode += "groups= %(groups)s,"
        rplotcode += """
                      pch = 16, type = 'b',
                      auto.key=TRUE,
                      origin = %(origin)f,
                      dsr_ll = %(ll)s,
                      dsr_ul = %(ul)s,
                      panel.groups =
                      function(x, y, ..., dsr_ll, dsr_ul, subscripts) {
                          dsr_ll <- dsr_ll[subscripts]
                          dsr_ul <- dsr_ul[subscripts]
                          panel.segments(dsr_ll,
                                         as.numeric(y),
                                         dsr_ul,
                                         as.numeric(y),
                                        ...)
                 panel.xyplot(x, y, ...)
                 }))
        """
    elif plottype == 'dotplot' and not horizontal:
        rplotcode = "errorbarplot <- with(errorbardataframe,dotplot(%(formulastring)s,"
        if groups is not None:
            rplotcode += "groups= %(groups)s,"
        rplotcode += """pch = 16,
                     auto.key=TRUE,
                     dsr_ll = %(ll)s,
                     dsr_ul = %(ul)s,
                     panel.groups =
                     function(x, y, ..., dsr_ll, dsr_ul, subscripts) {
                         dsr_ll <- dsr_ll[subscripts]
                         dsr_ul <- dsr_ul[subscripts]
                         panel.segments(as.numeric(x),
                                        dsr_ll,
                                        as.numeric(x),
                                        dsr_ul,
                                        ...)
                         panel.xyplot(x, y, ...)
                     }))
        """
    elif plottype == 'dotplot' and horizontal:
        rplotcode = "errorbarplot <- with(errorbardataframe,dotplot(%(formulastring)s,"
        if groups is not None:
            rplotcode += "groups= %(groups)s,"
        rplotcode += """pch = 16,
                     auto.key=TRUE,
                     dsr_ll = %(ll)s,
                     dsr_ul = %(ul)s,
                     panel.groups =
                     function(x, y, ..., dsr_ll, dsr_ul, subscripts) {
                         dsr_ll <- dsr_ll[subscripts]
                         dsr_ul <- dsr_ul[subscripts]
                          panel.segments(dsr_ll,
                                         as.numeric(y),
                                         dsr_ul,
                                         as.numeric(y),
                                        ...)
                         panel.xyplot(x, y, ...)
                     }))
        """


    print rplotcode % rparameters
    errorbarplot = with_mode(NO_CONVERSION,r)(rplotcode % rparameters)
    r.remove('errorbardataframe')
    return errorbarplot
    
a = errorbar_macro(plottype='lineplot',datadict=testdata,
                   measure = "dsr",
                   measure_lower_limits='dsr_ll',
                   measure_upper_limits='dsr_ul',
                   condcols=['year','geog_area'],
                   groups='sex')
# r.print_(a)

b = errorbar_macro(plottype='lineplot',datadict=testdata,
                   measure = "dsr",
                   measure_lower_limits='dsr_ll',
                   measure_upper_limits='dsr_ul',
                   condcols=['year','geog_area'],
                   groups='sex',
                   horizontal=False)
# r.print_(b)

c = errorbar_macro(plottype='dotplot',datadict=testdata,
                   measure = "dsr",
                   measure_lower_limits='dsr_ll',
                   measure_upper_limits='dsr_ul',
                   condcols=['year','geog_area'],
                   groups='sex')
# r.print_(c)

d = errorbar_macro(plottype='dotplot',datadict=testdata,
                   measure = "dsr",
                   measure_lower_limits='dsr_ll',
                   measure_upper_limits='dsr_ul',
                   condcols=['year','geog_area'],
                   groups='sex',
                   horizontal=True)
# r.print_(d)

e = errorbar_macro(plottype='barchart',datadict=testdata,
                   measure = "dsr",
                   measure_lower_limits='dsr_ll',
                   measure_upper_limits='dsr_ul',
                   condcols=['year','geog_area','sex'])
# r.print_(e)

f = errorbar_macro(plottype='barchart',datadict=testdata,
                   measure = "dsr",
                   measure_lower_limits='dsr_ll',
                   measure_upper_limits='dsr_ul',
                   condcols=['year','geog_area','sex'],
                   horizontal=True)
# r.print_(f)

# Note that this fails because barcharts with error bars can't handle
# groups, and without groups (or a second level of panelling), the dataset
# needs further summarisation. This should not be a problem in SOOM.
g = errorbar_macro(plottype='barchart',datadict=testdata,
                   measure = "dsr",
                   measure_lower_limits='dsr_ll',
                   measure_upper_limits='dsr_ul',
                   condcols=['year','geog_area'])

r.print_(a)
x = raw_input("Hit enter for next graph")
r.print_(b)
x = raw_input("Hit enter for next graph")
r.print_(c)
x = raw_input("Hit enter for next graph")
r.print_(d)
x = raw_input("Hit enter for next graph")
r.print_(e)
x = raw_input("Hit enter for next graph")
r.print_(f)
x = raw_input("Hit enter for next graph - which is known not to look right")
r.print_(g)

"""

# this works as expected, but not sure what teh error messages mean
with(testdata,barchart(geog_area ~ dsr | year + sex,
              origin = 0,
              dsr_ul = dsr_ul,
              dsr_ll = dsr_ll,
              panel = function(x, y, ..., dsr_ll, dsr_ul, subscripts) {
                  panel.barchart(x, y, subscripts, ...)
                  dsr_ll <- dsr_ll[subscripts]
                  dsr_ul <- dsr_ul[subscripts]
                  panel.segments(dsr_ll,
                                 as.numeric(y),
                                 dsr_ul,
                                 as.numeric(y),
                                 col = 'red', lwd = 2)}
              ))

# no idea what I am doing wrong here, but there is not one bar per group... something
# to do with panel.groups???
with(testdata,barchart(geog_area ~ dsr | year, groups=sex,
              origin = 0,
              dsr_ul = dsr_ul,
              dsr_ll = dsr_ll,
              panel = function(x, y, ..., dsr_ll, dsr_ul, subscripts, groups) {
                  panel.barchart(x, y, subscripts, groups, ...)
                  dsr_ll <- dsr_ll[subscripts]
                  dsr_ul <- dsr_ul[subscripts]
                  panel.segments(dsr_ll,
                                 as.numeric(y),
                                 dsr_ul,
                                 as.numeric(y),
                                 col = 'red', lwd = 2)}
              ))

# successfully does dotplots with groups
with(testdata,
     dotplot(geog_area ~ dsr | year,
             groups=sex, pch = 16,
             dsr_ul = dsr_ul,
             dsr_ll = dsr_ll,
             panel.groups =
             function(x, y, ..., 
                      dsr_ll, dsr_ul,
                      subscripts) {
                 dsr_ll <- dsr_ll[subscripts]
                 dsr_ul <- dsr_ul[subscripts]
                 panel.segments(dsr_ll,
                                as.numeric(y),
                                dsr_ul,
                                as.numeric(y),
                                ...)
                 panel.xyplot(x, y, ...)
             }))

# with two levels of panelling
with(testdata,
     dotplot(geog_area ~ dsr | year + age,
             groups=sex, pch = 16,
             dsr_ul = dsr_ul,
             dsr_ll = dsr_ll,
             panel.groups =
             function(x, y, ..., 
                      dsr_ll, dsr_ul,
                      subscripts) {
                 dsr_ll <- dsr_ll[subscripts]
                 dsr_ul <- dsr_ul[subscripts]
                 panel.segments(dsr_ll,
                                as.numeric(y),
                                dsr_ul,
                                as.numeric(y),
                                ...)
                 panel.xyplot(x, y, ...)
             }))

# with no panelling
with(testdata,
     dotplot(geog_area ~ dsr , 
             groups=sex, pch = 16,
             dsr_ul = dsr_ul,
             dsr_ll = dsr_ll,
             panel.groups =
             function(x, y, ..., 
                      dsr_ll, dsr_ul,
                      subscripts) {
                 dsr_ll <- dsr_ll[subscripts]
                 dsr_ul <- dsr_ul[subscripts]
                 panel.segments(dsr_ll,
                                as.numeric(y),
                                dsr_ul,
                                as.numeric(y),
                                ...)
                 panel.xyplot(x, y, ...)
             }))

# vertical - note need to swap x and y in the panel.segments function, though.
with(testdata,
     dotplot(dsr ~ geog_area | year,
             groups=sex, pch = 16, auto.key=TRUE,
             dsr_ul = dsr_ul,
             dsr_ll = dsr_ll,
             panel.groups =
             function(x, y, ..., 
                      dsr_ll, dsr_ul,
                      subscripts) {
                 dsr_ll <- dsr_ll[subscripts]
                 dsr_ul <- dsr_ul[subscripts]
                 panel.segments(as.numeric(x),
                                dsr_ll,
                                as.numeric(x),
                                dsr_ul,
                                ...)
                 panel.xyplot(x, y, ...)
             }))

# using horizontal=TRUE - unable to get this to work...
with(testdata,
     dotplot(dsr ~ geog_area | year,
             groups=sex, pch = 16, horizontal=TRUE,
             dsr_ul = dsr_ul,
             dsr_ll = dsr_ll,
             panel.groups =
             function(x, y, ..., 
                      dsr_ll, dsr_ul,
                      subscripts, horizontal) {
                 dsr_ll <- dsr_ll[subscripts]
                 dsr_ul <- dsr_ul[subscripts]
                 panel.segments(dsr_ll,
                                as.numeric(y),
                                dsr_ul,
                                as.numeric(y),
                                ...)
                 panel.xyplot(x, y, ...)
             }))


# lineplot 
with(testdata,
     xyplot(dsr ~ year | geog_area,
             groups=sex, pch = 16, type="b",
             auto.key=TRUE,
             dsr_ul = dsr_ul,
             dsr_ll = dsr_ll,
             panel.groups =
             function(x, y, ..., 
                      dsr_ll, dsr_ul,
                      subscripts) {
                 dsr_ll <- dsr_ll[subscripts]
                 dsr_ul <- dsr_ul[subscripts]
                 panel.segments(as.numeric(x),
                                dsr_ll,
                                as.numeric(x),
                                dsr_ul,
                                ...)
                 panel.xyplot(x, y, ...)

             }))
"""
