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
# $Id: twobytwo.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/output/twobytwo.py,v $

import Numeric

import SOOMv0

from libsoomexplorer.output.base import OutputBase

class _AxisLabel:
    def __init__(self, label, values):
        self.label = label
        self.values = values

class _XTab:
    def __init__(self, label, data):
        self.label = label
        self.data = data.copy()
        self.htot = Numeric.add.reduce(self.data, 1)
        self.vtot = Numeric.add.reduce(self.data, 0)
        self.tot = Numeric.add.reduce(self.data.flat)

class TwoByTwoDisplay:
    """
    A bit silly - we need this "display" class to attach the twobytwo
    analysis object to, because the "output" class gets pickled,
    and the twobytwo analysis doesn't like this.
    """
    def __init__(self, summaryset, measurecol, conflev=None):
        from SOOMv0 import Analysis
        def add_stratum(a, label):
            self.analysis.add_stratum(a[0,0], a[1,0], a[0,1], a[1,1], 
                                      label=label)
            self.xtabs.append(_XTab(label, a))
            
        # CrossTab object
        self.ct = summaryset.crosstab()
        # Counts array
        self.freq = self.ct[measurecol].data.filled()
        # TwoByTwo analysis object and _XTab objects
        analargs = {}
        if conflev is not None:
            analargs['conflev'] = conflev
        self.analysis = Analysis.twobytwotable(**analargs)
        self.xtabs = []
        if len(self.freq.shape) == 2:
            add_stratum(self.freq, '')
        else:
            axis = self.ct.axes[2]
            labels = ['%s: %s' % (axis.label, axis.col.do_outtrans(v))
                      for v in axis.values]
            for i in range(self.freq.shape[2]):
                add_stratum(self.freq[:,:,i], labels[i])
            self.xtabs.append(_XTab('Unstratified (crude)', 
                                    Numeric.add.reduce(self.freq, 2)))

        # TwoByTwo report object
        sections = list(Analysis.twobytwotable.sections)
        sections.remove('counts')
        self.report = list(self.analysis.report(sections))
        # _XTab labels
        self.axislabels = []
        for axis in self.ct.axes[:2]:
            values = [axis.col.do_format(axis.col.do_outtrans(v))
                      for v in axis.values]
            self.axislabels.append(_AxisLabel(axis.label, values))

class TwoByTwoOut(OutputBase):
    inline = True
    markup = 'twobytwo'

    def __init__(self):
        super(TwoByTwoOut, self).__init__()
        self.summaryset = None
        self.title = ''
        self.footer = ''

    def clear(self):
        super(TwoByTwoOut, self).clear()
        self.summaryset = None

    def plotstart(self):
        f, path = self.tempfile('png')
        SOOMv0.plot.output('PNG', file=path)

    def display(self):
        return TwoByTwoDisplay(self.summaryset, '_freq_', conflev=self.conflev)

    def go(self, summaryset, conflev=None):
        self.summaryset = summaryset
        self.conflev = conflev
