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
# $Id: PlotRegistry.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/PlotRegistry.py,v $

class _PlotMethod(object):
    def __init__(self, name):
        self.name = name
        self._method = None

    def get_method(self):
        if self._method is None:
            # Demand load - rpy import is slow
            import SOOMv0.Plot.plotmethods
            self._method = getattr(SOOMv0.Plot.plotmethods, self.name)
        return self._method
    method = property(get_method)

    def __cmp__(self, other):
        return cmp(self.method.label, other.method.label)

class _PlotRegistry(object):
    def __init__(self):
        self.methods = {}

    def get_output(self):
        # Demand load - rpy import is slow
        import SOOMv0.Plot._output
        return SOOMv0.Plot._output.output
    output = property(get_output)

    def register(self, *args):
        method = _PlotMethod(*args)
        self.methods[method.name] = method

    def _display_hook(self):
        methods = self.methods.values()
        methods.sort()
        for method in methods:
            print '%-20s %s' % (method.name, method.method.label)

    def __getattr__(self, name):
        try:
            return self.methods[name].method
        except KeyError:
            raise AttributeError(name)


plot = _PlotRegistry()
plot.register('scatterplot')
plot.register('scattermatrix')
plot.register('boxplot')
plot.register('histogram')
plot.register('densityplot')
plot.register('lineplot')
plot.register('barchart')
plot.register('dotchart')
plot.register('fourfold')
