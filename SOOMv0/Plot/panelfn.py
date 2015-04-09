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
# $Id: panelfn.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Plot/panelfn.py,v $

from rpy import *

panel_macros = {
    'barchart':
    '''\
    function(x, y, ..., box.ratio=1, subscripts, groups=NULL, horizontal=TRUE) 
    {
        panel.barchart(x, y, box.ratio=box.ratio, 
                    subscripts=subscripts, groups=groups, 
                    horizontal=horizontal, ...)

        if (is.null(groups)) {
            COL_ll <- plotframe$COL.ll[subscripts]
            COL_ul <- plotframe$COL.ul[subscripts]
            ticks <- as.numeric(TICKAXIS)
            ARROWS
        }
        else {
            TICKAXIS <- as.numeric(TICKAXIS)
            groupSub <- function(groups, subscripts, ...) groups[subscripts]
            groups <- as.numeric(groups)
            vals <- sort(unique(groups))
            nvals <- length(vals)
            groups <- groupSub(groups, subscripts, ...)
            width <- box.ratio/(1 + nvals * box.ratio)
            for (i in unique(TICKAXIS)) {
                ok <- TICKAXIS == i
                ticks <- (i + width * (groups[ok] - (nvals + 1)/2)) 
                COL_ll <- plotframe$COL.ll[subscripts][ok]
                COL_ul <- plotframe$COL.ul[subscripts][ok]
                ARROWS
            }
        }
    }
    ''',

    'xyplot':
    '''\
    function(x, y, ..., subscripts, groups=NULL) 
    {
        COL_ll <- plotframe$COL.ll[subscripts]
        COL_ul <- plotframe$COL.ul[subscripts]
        ticks <- as.numeric(TICKAXIS)
        ARROWS
        if (is.null(groups))
            panel.xyplot(x, y, subscripts, ...)
        else
            panel.superpose(x, y, subscripts, groups, ...)
    }
    ''',

    'dotplot':
    '''\
    function(x, y, ..., subscripts, groups=NULL) 
    {
        COL_ll <- plotframe$COL.ll[subscripts]
        COL_ul <- plotframe$COL.ul[subscripts]
        ticks <- as.numeric(TICKAXIS)
        ARROWS
        panel.dotplot(x, y, subscripts=subscripts, groups=groups, ...)
    }
    ''',
}


def ci_panel(colname, rmethod, axis, grouping):
    try:
        macro = panel_macros[rmethod]
    except KeyError:
        raise PlotError('%r plot method does not support confidence intervals')

    macro = macro.replace('COL', colname)

    if axis == 'x':
        args = [colname+'_ll', 'ticks', colname+'_ul', 'ticks']
        macro = macro.replace('TICKAXIS', 'y')
    else:
        args = ['ticks', colname+'_ll', 'ticks', colname+'_ul']
        macro = macro.replace('TICKAXIS', 'x')
    args.extend([
        'length=0.02', 
        'code=3', 
        'angle=90', 
        "col='red'", 
        'lwd=2',
    ]) 
    arrows = 'panel.arrows(%s)' % ',\n            '.join(args)
    macro = macro.replace('ARROWS', arrows)

#    print macro
    return r(macro)

def violin_panel():
    return r('''\
        function(..., box.ratio) {
            dots <- c(list(...), list(col = "transparent",
                      box.ratio = box.ratio))
            dots$varwidth = FALSE
            do.call("panel.violin", dots)
            panel.bwplot(..., fill = NULL, box.ratio = .1)
        }
    ''')
