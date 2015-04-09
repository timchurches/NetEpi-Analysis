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
# $Id: PopRate.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/sandbox/PopRate.py,v $

import Numeric
import CrossTab

def calc_directly_std_rates(summset, popset, stdpopset, conflevel=0.95, basepop = 100000, ci_method='dobson', popset_popcol='_freq_', stdpopset_popcol='_stdpop_'):
    """
    Calculate Standardised Population Rates
    """
    from rpy import r
    sumaxis = Numeric.add.reduce

    stdtab= CrossTab.CrossTab(stdpopset)
    summtab = CrossTab.CrossTab(summset, shaped_like=stdtab)
    stdtab.replicate_axes(summtab.get_shape())
    poptab = CrossTab.CrossTab(popset, shaped_like=summtab)
    poptab.collapse_axes(summtab.get_shape())
    popfreq = poptab.tables[popset_popcol].astype(Numeric.Float64)
    stdpop = stdtab.tables[stdpopset_popcol].astype(Numeric.Float64)
    sum_stdpop = sumaxis(stdpop)
    stdwgts = stdpop / sum_stdpop
    stdpop_sq = stdpop**2
    sum_stdpop_sq = sum_stdpop**2
    
    zv = r.qnorm(0.5*(1+conflevel))
    alpha = 1.0 - conflevel
    axis = 0
    basepop = float(basepop)
        
    for name, tab in summtab.tables.items():
        colname = None
        if name == '_freq_': 
            colname = '_rate_'
            collabel = 'Rate'
            wgtcolname = '_rate_by_stdwgt_'
            wgtcollabel = 'Rate multiplied by Std Wgt'
        elif name.startswith('freq_wgtd_by'):
            colname = 'rate_' + name[5:]
            label = summset[name].label[len('Frequency'):]
            wgtcolname = 'rate_by_stdwgt_' + name[5:]
            collabel = 'Rate' + label
            wgtcollabel = 'Rate multiplied by Std Wgt (' + label
        print 'shapes', name, tab.shape, popfreq.shape, stdwgts.shape
        if colname:
            summfreq = tab.astype(Numeric.Float64)
            rate = summfreq / popfreq
            wgtrate = rate * stdwgts

            # Crude rate
            cr = sumaxis(summfreq, axis) / sumaxis(popfreq, axis)

            # Directly standardised rate
            dsr = sumaxis(wgtrate, axis)*basepop

            # Calculations for CI per Dobson et al.
            se_wgtrate = summfreq*((stdwgts/(popfreq/basepop))**2)
            stderr = stdpop_sq * rate * (1.0 - rate)
            se_rate = sumaxis(se_wgtrate, axis)
            sumsei = sumaxis(stderr, axis)
            total_freq = sumaxis(summfreq, axis) 
            if total_freq == 0:
                import math
                u_lam = -math.log10(1 - conflevel)
                l_lam = 0.0
            else:
                l_lam = r.qgamma((1 - conflevel)/2.0, total_freq, scale = 1.)
                u_lam = r.qgamma((1 + conflevel)/2.0, total_freq + 1, scale = 1.)
            dsr_ll = dsr + (((se_rate/total_freq)**0.5)*(l_lam - total_freq))
            dsr_ul = dsr + (((se_rate/total_freq)**0.5)*(u_lam - total_freq))

            # Calculations for CI per Selvin/Epitools
            # dsr_var = sumaxis((stdwgts**2) * (summfreq / (popfreq**2)), axis)
            # x2divvar = (dsr**2) / dsr_var
            # lcf = r.qgamma(alpha/2., shape = x2divvar, scale = 1.) / x2divvar
            # ucf = r.qgamma(1. - alpha/2., shape = x2divvar+1., scale = 1.) / x2divvar
            # dsr_ll = dsr * lcf
            # dsr_ul = dsr * ucf

            print name, "Sex-specific CR=", cr*basepop
            print name, "Sex-specific DSR and Dobson limits:", dsr, dsr_ll, dsr_ul
    return summset


if __name__ == '__main__':
    from SOOMv0 import datasets, soom, SummaryStats

    path = '../SOOM_objects'
    # path = None
    ds = datasets.dsload('nhds', path=path)
    pop = datasets.dsload('nhds97pop', path=path)
    wp = datasets.dsload("worldpop_p", path=path)
    print wp
    s = ds.summ('agegrp', 'sex', SummaryStats.freq(), filterexpr='year=1997',)
    p = calc_directly_std_rates(s, pop, wp)
    
