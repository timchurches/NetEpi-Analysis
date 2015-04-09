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

# ToDo: add confidence interval methods for recurring events (eg hospital
# admission) as suggested in:
#       http://www.doh.wa.gov/Data/Guidelines/ConfIntguide.htm

# Standard Python libraries
import math
import time
import sys

# http://sourceforge.net/projects/numpy
import Numeric, MA
sumaxis = MA.add.reduce

# SOOM
from SOOMv0.common import *
from SOOMv0.CrossTab import CrossTab, shape_union, dims
from SOOMv0.Soom import soom

__all__ = (
    'calc_directly_std_rates', 
    'calc_stratified_rates',
    'calc_indirectly_std_ratios',
)

class Vars:
    "Debugging aid"
    def __init__(self, vars):
        self.__dict__.update(vars)

def just_freq_tables(crosstab):
    for table in crosstab.tables():
        name = table.name
        if name == '_freq_':
            yield table, name, '', ''
        elif name.startswith('freq_wgtd_by'):
            yield (table, name, name[len('freq'):], 
                   crosstab[name].label[len('Frequency'):])


def get_alpha(conflev):
    if conflev is None:
        return None
    if 0.0 < conflev < 1.0:
        return 1.0 - conflev
    raise Error("conflev must be greater than 0 and less than 1")


def calc_directly_std_rates(summset, popset, stdpopset=None, 
                            conflev=0.95, basepop = 100000, 
                            timeinterval='years',
                            ci_method='dobson', popset_popcol='_freq_', 
                            stdpopset_popcol='_stdpop_',
                            axis = 0,
                            debug=False):

    """
    Calculate Directly Standardised Population Rates

    summset     is a summary dataset of counts of events for the
                population-of-interest being compared to the standard
                population.  
    popset      is the stratified population counts for the
                population-of-interest
    stdpopset   is the stratified population counts for the standard
                population
    """
    from rpy import r, get_default_mode, set_default_mode, BASIC_CONVERSION

    alpha = get_alpha(conflev)

    if ci_method not in ('dobson','ff'):
        raise Error('Only Dobson et al. (dobson) and Fay-Feuer (ff) methods '
                    'for confidence intervals currently implemented')
    if not popset.has_column(popset_popcol):
        raise Error('Denominator population dataset %r does not have a '
                    '%r column' % (popset.label or popset.name, popset_popcol))
    if stdpopset is not None and not stdpopset.has_column(stdpopset_popcol):
        raise Error('Standard population dataset %r does not have a '
                    '%r column' % (stdpopset.label or stdpopset.name, stdpopset_popcol))

    st = time.time()
    r_mode = get_default_mode()
    try:
        set_default_mode(BASIC_CONVERSION)

        # We turn the summset into an Ncondcols-dimensional matrix
        summtab = CrossTab.from_summset(summset)

        if stdpopset is not None:
            # Then attempt to do the same to the stdpop data, summing any
            # axes not required and replicate any missing until we have an
            # array the same shape as the summtab array.
            stdtab = CrossTab.from_summset(stdpopset, shaped_like=summtab)
            stdtab.collapse_axes_not_in(summtab)
            stdtab.replicate_axes(summtab)
            stdpop = stdtab[stdpopset_popcol].data.astype(Numeric.Float64)

        # The population dataset must have at least as many dimensions as
        # summary dataset. Any additional axes are eliminated by summing.
        # any missing axes are created by replication.
        poptab = CrossTab.from_summset(popset, shaped_like=summtab)
        poptab.collapse_axes_not_in(summtab)
        poptab.replicate_axes(summtab)
        popfreq = poptab[popset_popcol].data.astype(Numeric.Float64)

        # Manufacture a CrossTab for the result, with one less axis (the first)
        result = summtab.empty_copy()
        del result.axes[axis]

        if stdpopset is not None:
            sum_stdpop = sumaxis(stdpop)
            stdwgts = stdpop / sum_stdpop
            stdpop_sq = stdpop**2
            sum_stdpop_sq = sum_stdpop**2
            ffwi = stdwgts / popfreq
            ffwm = MA.maximum(MA.ravel(ffwi))

        basepop = float(basepop)

        for table, name, n_add, l_add in just_freq_tables(summtab):

            # avoid integer overflows...
            summfreq = table.data.astype(Numeric.Float64)
            strata_rate = summfreq / popfreq

            result.add_table('summfreq'+n_add, 
                     data=sumaxis(summfreq, axis),
                     label='Total events'+l_add)
            result.add_table('popfreq'+n_add, 
                     data=sumaxis(popfreq, axis),
                     label='Total person-'+timeinterval+' at risk'+l_add)

            if stdpopset is not None:
                std_strata_summfreq = summfreq * Numeric.where(MA.getmask(stdwgts),0.,1.)
                wgtrate = strata_rate * stdwgts
                result.add_table('std_strata_summfreq'+n_add, 
                         data=sumaxis(std_strata_summfreq, axis),
                         label="Total events in standard strata"+l_add)

            # Crude rate
            cr = sumaxis(summfreq, axis) / sumaxis(popfreq, axis) * basepop
            result.add_table('cr'+n_add, data=cr,
                            label='Crude Rate per '+'%d' % basepop +' person-'+timeinterval+l_add)

            if alpha is not None:
                # CIs for crude rate
                count = sumaxis(summfreq, axis)
                count_shape = count.shape
                count_flat = MA.ravel(count)
                totpop = sumaxis(popfreq, axis)
                assert totpop.shape == count.shape
                totpop_flat = MA.ravel(totpop)

                cr_ll = Numeric.empty(len(count_flat), typecode=Numeric.Float64)
                cr_ul = Numeric.empty(len(count_flat), typecode=Numeric.Float64)
                cr_ll_mask = Numeric.zeros(len(count_flat), typecode=Numeric.Int8)
                cr_ul_mask = Numeric.zeros(len(count_flat), typecode=Numeric.Int8)

                for i, v in enumerate(count_flat):
                    try:
                        if v == 0:
                            cr_ll[i] = 0.0
                        else:
                            cr_ll[i] = ((r.qchisq(alpha/2., df=2.0*v)/2.0) / totpop_flat[i]) * basepop
                        cr_ul[i] = ((r.qchisq(1. - alpha/2., df=2.0*(v + 1))/2.0) / totpop_flat[i]) * basepop
                    except:
                        cr_ll[i] = 0.0
                        cr_ul[i] = 0.0
                        cr_ll_mask[i] = 1
                        cr_ul_mask[i] = 1

                cr_ll = MA.array(cr_ll, mask=cr_ll_mask, typecode=MA.Float64)
                cr_ul = MA.array(cr_ul, mask=cr_ul_mask, typecode=MA.Float64)
                cr_ll.shape = count_shape
                cr_ul.shape = count_shape

                cr_base = 'Crude rate %d%%' % (100.0*conflev)
                result.add_table('cr_ll'+n_add, data=cr_ll,
                                label=cr_base+' lower confidence limit '+l_add)
                result.add_table('cr_ul'+n_add, data=cr_ul,
                                label=cr_base+' upper confidence limit '+l_add)

            if stdpopset is not None:

                # Directly Standardised Rate
                dsr = sumaxis(wgtrate, axis)
                result.add_table('dsr'+n_add, data=dsr*basepop,
                                label='Directly Standardised Rate per '+'%d' % basepop +' person-'+timeinterval+l_add)

                # Confidence Intervals
                if alpha is None or name != '_freq_':
                    # Can only calculate confidence intervals on freq cols
                    continue

                if ci_method == 'dobson':
                    # Dobson et al method
                    # see: Dobson A, Kuulasmaa K, Eberle E, Schere J. Confidence intervals for weighted sums 
                    # of Poisson parameters, Statistics in Medicine, Vol. 10, 1991, pp. 457-62.
                    # se_wgtrate = summfreq*((stdwgts/(popfreq/basepop))**2)
                    se_wgtrate = summfreq*((stdwgts/(popfreq))**2)
                    stderr = stdpop_sq * strata_rate * (1.0 - strata_rate)
                    se_rate = sumaxis(se_wgtrate, axis)
                    sumsei = sumaxis(stderr, axis)
                    total_freq = sumaxis(std_strata_summfreq, axis) 
                    # get shape of total_freq
                    total_freq_shape = total_freq.shape

                    total_freq_flat = MA.ravel(total_freq)

                    # flat arrays to hold results and associated masks
                    l_lam = Numeric.empty(len(total_freq_flat), typecode=Numeric.Float64)
                    u_lam = Numeric.empty(len(total_freq_flat), typecode=Numeric.Float64)
                    l_lam_mask = Numeric.zeros(len(total_freq_flat), typecode=Numeric.Int8)
                    u_lam_mask = Numeric.zeros(len(total_freq_flat), typecode=Numeric.Int8)

                    conflev_l = (1 - conflev) / 2.0
                    conflev_u = (1 + conflev) / 2.0

                    for i, v in enumerate(total_freq_flat):
                        try:
                            if v == 0.:            	    
                                u_lam[i] = -math.log(1 - conflev)
                                l_lam[i] = 0.0
                            else:
                                l_lam[i] = r.qgamma(conflev_l, v, scale = 1.)
                                u_lam[i] = r.qgamma(conflev_u, v + 1., scale = 1.)
                        except:
                            l_lam[i] = 0.0
                            u_lam[i] = 0.0
                            l_lam_mask[i] = 1
                            u_lam_mask[i] = 1

                    l_lam = MA.array(l_lam, mask=l_lam_mask, typecode=MA.Float64)
                    u_lam = MA.array(u_lam, mask=u_lam_mask, typecode=MA.Float64)
                    l_lam.shape = total_freq_shape
                    u_lam.shape = total_freq_shape
                    dsr_ll = dsr + (((se_rate/total_freq)**0.5)*(l_lam - total_freq))
                    dsr_ul = dsr + (((se_rate/total_freq)**0.5)*(u_lam - total_freq))

                elif ci_method == 'ff':
                    # Fay and Feuer method
                    # see: Fay MP, Feuer EJ. Confidence intervals for directly standardized rates:
                    # a method based on the gamma distribution. Statistics in Medicine 1997 Apr 15;16(7):791-801.

                    ffvari = summfreq * ffwi**2.0
                    ffvar = sumaxis(ffvari,axis)

                    dsr_flat = Numeric.ravel(MA.filled(dsr,0))
                    dsr_shape = dsr.shape

                    ffvar_flat = Numeric.ravel(MA.filled(ffvar,0))

                    # flat arrays to hold results and associated masks
                    dsr_ll = Numeric.empty(len(dsr_flat), typecode=Numeric.Float64)
                    dsr_ul = Numeric.empty(len(dsr_flat), typecode=Numeric.Float64)
                    dsr_ll_mask = Numeric.zeros(len(dsr_flat), typecode=Numeric.Int8)
                    dsr_ul_mask = Numeric.zeros(len(dsr_flat), typecode=Numeric.Int8)

                    for i, y in enumerate(dsr_flat):
                        try:
                            dsr_ll[i] = (ffvar_flat[i] / (2.0*y)) * r.qchisq(alpha/2., df= (2.0*(y**2.)/ffvar_flat[i]))
                            dsr_ul[i] = ((ffvar_flat[i] + (ffwm**2.0))/ (2.0*(y + ffwm))) * r.qchisq(1. - alpha/2., df = ((2.0*((y + ffwm)**2.0))/(ffvar_flat[i] + ffwm**2.0))) 
                        except:
                            dsr_ll[i] = 0.0
                            dsr_ul[i] = 0.0
                            dsr_ll_mask[i] = 1
                            dsr_ul_mask[i] = 1
                    dsr_ll = MA.array(dsr_ll,mask=dsr_ll_mask,typecode=MA.Float64)
                    dsr_ul = MA.array(dsr_ul,mask=dsr_ul_mask,typecode=MA.Float64)
                    dsr_ll.shape = dsr_shape
                    dsr_ul.shape = dsr_shape

                result.add_table('dsr_ll'+n_add, data=dsr_ll*basepop,
                                label='DSR '+ '%d' % (100.0*conflev)+'% lower confidence limit'+l_add)
                result.add_table('dsr_ul'+n_add, data=dsr_ul*basepop,
                                label='DSR '+ '%d' % (100.0*conflev)+'% upper confidence limit'+l_add)

    finally:
        set_default_mode(r_mode)
    soom.info('calc_directly_std_rates took %.03f' % (time.time() - st))
    if stdpopset is not None:
        name = 'dir_std_rates_' + summset.name
        label = 'Directly Standardised Rates for '+(summset.label or summset.name)
    else:
        name = 'crude_rates_' + summset.name
        label = 'Crude Rates for '+(summset.label or summset.name)
    if conflev:
        label += ' (%g%% conf. limits)' % (conflev * 100)
    if debug:
        global vars
        vars = Vars(locals())
    return result.to_summset(name, label=label)


def calc_stratified_rates(summset, popset,
                          conflev=0.95, basepop = 100000, 
                          timeinterval='years',
                          ci_method='dobson', popset_popcol='_freq_', 
                          debug=False):

    """
    Calculate stratified population rates

    summset     is a straified summary dataset of counts of events for
                the population-of-interest
    popset      is the stratified population counts for the
                population-of-interest
    """
    from rpy import r, get_default_mode, set_default_mode, BASIC_CONVERSION

    alpha = get_alpha(conflev)

    if ci_method not in  ('dobson','ff'):
        raise Error('Only Dobson et al. (dobson) and Fay-Feuer (ff) '
                    'methods for confidence intervals currently '
                    'implemented')
    if not popset.has_column(popset_popcol):
        raise Error('Denominator population dataset %r does not have a '
                    '%r column' % (popset.label or popset.name, popset_popcol))

    st = time.time()
    r_mode = get_default_mode()
    try:
        set_default_mode(BASIC_CONVERSION)

        # We turn the summset into an Ncondcols-dimensional matrix
        summtab = CrossTab.from_summset(summset)

        # The population dataset must have at least as many dimensions as
        # summary dataset. Any additional axes are eliminated by summing.
        # any missing axes are created by replication.
        poptab = CrossTab.from_summset(popset, shaped_like=summtab)
        poptab.collapse_axes_not_in(summtab)
        poptab.replicate_axes(summtab)
        popfreq = poptab[popset_popcol].data.astype(Numeric.Float64)

        # Manufacture a CrossTab for the result
        result = summtab.empty_copy()

        basepop = float(basepop)

        for table, name, n_add, l_add in just_freq_tables(summtab):
            # avoid integer overflows...
            summfreq = table.data.astype(Numeric.Float64)

            strata_rate = summfreq / popfreq

            result.add_table('summfreq'+n_add, 
                     data=summfreq,
                     label='Events'+l_add)
            result.add_table('popfreq'+n_add, 
                     data=popfreq,
                     label='Person-'+timeinterval+' at risk'+l_add)
            result.add_table('sr'+n_add, 
                     data=strata_rate * basepop,
                     label='Strata-specific Rate per '+'%d' % basepop +' person-'+timeinterval+l_add)

            if alpha is not None:
                # CIs for stratified rates
                summfreq_shape = summfreq.shape
                summfreq_flat = MA.ravel(summfreq)
                assert popfreq.shape == summfreq.shape
                popfreq_flat = MA.ravel(popfreq)

                sr_ll = Numeric.empty(len(summfreq_flat), typecode=Numeric.Float64)
                sr_ul = Numeric.empty(len(summfreq_flat), typecode=Numeric.Float64)
                sr_ll_mask = Numeric.zeros(len(summfreq_flat), typecode=Numeric.Int8)
                sr_ul_mask = Numeric.zeros(len(summfreq_flat), typecode=Numeric.Int8)

                for i, v in enumerate(summfreq_flat):
                    try:
                        if v == 0:
                            sr_ll[i] = 0.0
                        else:
                            sr_ll[i] = ((r.qchisq(alpha/2., df=2.0*v)/2.0) / popfreq_flat[i]) * basepop
                        sr_ul[i] = ((r.qchisq(1. - alpha/2., df=2.0*(v + 1))/2.0) / popfreq_flat[i]) * basepop
                    except:
                        sr_ll[i] = 0.0
                        sr_ul[i] = 0.0
                        sr_ll_mask[i] = 1
                        sr_ul_mask[i] = 1

                sr_ll = MA.array(sr_ll, mask=sr_ll_mask, typecode=MA.Float64)
                sr_ul = MA.array(sr_ul, mask=sr_ul_mask, typecode=MA.Float64)
                sr_ll.shape = summfreq_shape
                sr_ul.shape = summfreq_shape

                sr_base = 'Stratified rate %s%%' % (100.0*conflev)
                result.add_table('sr_ll'+n_add, data=sr_ll,
                                label=sr_base+' lower confidence limit '+l_add)
                result.add_table('sr_ul'+n_add, data=sr_ul,
                                label=sr_base+' upper confidence limit '+l_add)

    finally:
        set_default_mode(r_mode)
    soom.info('calc_stratified_rates took %.03f' % (time.time() - st))
    name = 'stratified_rates_' + summset.name
    label = 'Stratified Rates for '+(summset.label or summset.name)
    if conflev:
        label += ' (%g%% conf. limits)' % (conflev * 100)
    if debug:
        global vars
        vars = Vars(locals())
    return result.to_summset(name, label=label)


def calc_indirectly_std_ratios(summset, popset, stdsummset, stdpopset,
                            conflev=0.95, baseratio = 100, timeinterval='years',
                            popset_popcol='_freq_', stdpopset_popcol='_stdpop_', ci_method='daly', debug=False):

    """
    Calculate Indirectly Standardised Population Event Ratios

    - summset is a summary dataset of counts of events for the
      population-of-interest being compared to the standard population.
    - popset is the stratified population counts for the
      population-of-interest
    - stdsummset is a summary dataset of counts of events for the
      standard population
    - stdpopset is the stratified population counts for the standard
      population
    """
    from rpy import r, get_default_mode, set_default_mode, BASIC_CONVERSION

    alpha = get_alpha(conflev)

    if ci_method != 'daly':
        raise Error("Only Daly method for confidence intervals "
                         "currently implemented")
    if not popset.has_column(popset_popcol):
        raise Error('Denominator population dataset %r does not have a '
                    '%r column' % (popset.label or popset.name, popset_popcol))
    if not stdpopset.has_column(stdpopset_popcol):
        raise Error('Standard population dataset %r does not have a '
                    '%r column' % (stdpopset.label or stdpopset.name, stdpopset_popcol))

    st = time.time()
    r_mode = get_default_mode()
    try:
        set_default_mode(BASIC_CONVERSION)

        shape = shape_union(stdsummset, summset)

        summtab = CrossTab.from_summset(summset, shaped_like=shape)

        stdsummtab = CrossTab.from_summset(stdsummset, shaped_like=shape)

        stdpoptab = CrossTab.from_summset(stdpopset, shaped_like=shape)
        stdpoptab.collapse_axes_not_in(stdsummtab)

        stdsummtab.replicate_axes(shape)
        stdpoptab.replicate_axes(shape)

        poptab = CrossTab.from_summset(popset, shaped_like=shape)
        poptab.collapse_axes_not_in(shape)
        if poptab.get_shape() != stdsummtab.get_shape():
            raise Error('Observed population does not have all the required columns')
        popfreq = poptab[popset_popcol].data.astype(MA.Float64)

        result = stdsummtab.empty_copy()
        result.add_table('popfreq', data=popfreq,
                         label='Total person-'+timeinterval+' at risk')

        expected_cols = []
        for table, name, n_add, l_add in just_freq_tables(stdsummtab):
            stdsummfreq = stdsummtab[name].data.astype(MA.Float64)
            stdpopfreq = stdpoptab[stdpopset_popcol].data.astype(MA.Float64)
            std_strata_rates = stdsummfreq / stdpopfreq
            strata_expected_freq = std_strata_rates * popfreq
#            print stdsummfreq[0,0,0], stdpopfreq[0,0,0], popfreq[0,0,0]
            result.add_table('expected'+n_add, data=strata_expected_freq,
                             label='Expected events'+l_add)
            expected_cols.append('expected'+n_add)

        result.collapse_axes_not_in(summtab)

        axis = 0
        baseratio = float(baseratio)

        for table, name, n_add, l_add in just_freq_tables(summtab):
            observed = table.data.astype(Numeric.Float64)
            result.add_table('observed'+n_add, 
                             data=observed,
                             label='Observed events'+l_add)

            expected = result['expected'+n_add].data

            isr = observed / expected
            result.add_table('isr'+n_add, data=isr*baseratio,
                            label='Indirectly Standardised Event Ratio')

            # Confidence Intervals
            if alpha is None or name != '_freq_':
                # Can only calculate confidence intervals on freq cols
                continue

            conflev_l = (1 - conflev) / 2.0
            conflev_u = (1 + conflev) / 2.0

            # get shape of observed
            observed_shape = observed.shape
            # flattened version 
            observed_flat = MA.ravel(observed)


            # sanity check on shapes - should be the same!
            assert expected.shape == observed.shape

            # flattened version of expecetd
            expected_flat = MA.ravel(expected)

            # lists to hold results
            isr_ll = Numeric.empty(len(observed_flat), typecode=Numeric.Float64)
            isr_ul = Numeric.empty(len(observed_flat), typecode=Numeric.Float64)
            isr_ll_mask = Numeric.zeros(len(observed_flat), typecode=Numeric.Int8)
            isr_ul_mask = Numeric.zeros(len(observed_flat), typecode=Numeric.Int8)

            obs_mask = MA.getmaskarray(observed_flat)
            exp_mask = MA.getmaskarray(expected_flat)

            for i, v in enumerate(observed_flat):
                if obs_mask[i] or exp_mask[i]:
                    isr_ll[i] = 0.0
                    isr_ul[i] = 0.0
                    isr_ll_mask[i] = 1
                    isr_ul_mask[i] = 1
                else:
                    if v == 0.:            	    
                        obs_ll = 0.0
                        obs_ul = -math.log(1 - conflev)
                    else:
                        obs_ll = r.qgamma(conflev_l, v, scale = 1.)
                        obs_ul = r.qgamma(conflev_u, v + 1., scale = 1.)
                    isr_ll[i] = obs_ll / expected_flat[i]
                    isr_ul[i] = obs_ul / expected_flat[i]

            isr_ll = MA.array(isr_ll, typecode=MA.Float64, mask=isr_ll_mask)
            isr_ul = MA.array(isr_ul, typecode=MA.Float64, mask=isr_ul_mask)
            isr_ll.shape = observed_shape
            isr_ul.shape = observed_shape

            isr_base = 'ISR %d%%' % (100.0*conflev)
            result.add_table('isr_ll'+n_add, data=isr_ll*baseratio,
                            label=isr_base+' lower confidence limit'+l_add)
            result.add_table('isr_ul'+n_add, data=isr_ul*baseratio,
                            label=isr_base+' upper confidence limit'+l_add)
    finally:
        set_default_mode(r_mode)
    soom.info('calc_indirectly_std_ratios took %.03f' % (time.time() - st))
    name = 'indir_std_ratios_' + summset.name
    label = 'Indirectly Standardised Ratios for '+(summset.label or summset.name)
    if conflev:
        label += ' (%g%% conf. limits)' % (conflev * 100)

    if debug:
        global vars
        vars = Vars(locals())
    return result.to_summset(name, label=label)

if __name__ == '__main__':
    from SOOMv0 import datasets, soom, SummaryStats, plot

    soom.messages = False
    path = '../SOOM_objects'

    ds = datasets.dsload('syndeath', path=path)
    pop = datasets.dsload('synpop', path=path)
    stdpop_mf = datasets.dsload("aus01stdpop_mf", path=path)
    stdpop = datasets.dsload("aus01stdpop", path=path)

    if 1:
        print "Directly Age-Standardised Rates by Sex for 1997"
        print
        s = ds.summ('agegrp', 'sex', SummaryStats.freq(), filterexpr='year=1997', zeros=1)
        p = calc_directly_std_rates(s, pop, stdpopset=stdpop, popset_popcol='pop', 
                                stdpopset_popcol='pop')
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Crude Rates by Sex for 1997"
        print
        s = ds.summ('agegrp', 'sex', SummaryStats.freq(), filterexpr='year=1997', zeros=1)
        p = calc_directly_std_rates(s, pop, popset_popcol='pop')
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Age-specific Rates by Sex for 1997"
        print
        s = ds.summ('agegrp', 'sex', SummaryStats.freq(), filterexpr='year=1997', zeros=1)
        p = calc_stratified_rates(s, pop, popset_popcol='pop')
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Region-specific Rates by Sex for 1997"
        print
        s = ds.summ('region', 'sex', SummaryStats.freq(), filterexpr='year=1997', zeros=1)
        p = calc_stratified_rates(s, pop, popset_popcol='pop')
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Directly Age/sex-Standardised Rates by Year by Sex"
        print
        s = ds.summ('agegrp', 'sex', 'year', SummaryStats.freq(), zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop_mf, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99)
        print p
        print
        plot.lineplot(p, 'year', 'sex', measure='dsr', xlabelrotate=45)
        raw_input('See graph - hit <ENTER> to continue')

    if 1:
        print "Directly Age/sex-Standardised Rates by Year by Sex"
        print
        s = ds.summ('agegrp', 'year', 'sex', SummaryStats.freq(), zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop_mf, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99)
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Directly Age/sex-Standardised Rates by Sex by Year (Dobson CI method)"
        print
        s = ds.summ('agegrp', 'sex', 'year', SummaryStats.freq(), zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop_mf, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99,ci_method='dobson')
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Directly Age/sex-Standardised Rates by Sex by Year (Fay-Feuer CI method)"
        print
        s = ds.summ('agegrp', 'sex', 'year', SummaryStats.freq(), zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop_mf, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99,ci_method='ff')
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Directly Age-Standardised Rates by Sex by Year"
        print
        s = ds.summ('agegrp', 'sex', 'year', SummaryStats.freq(), zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99)
        print p
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Directly Age/sex-Standardised Rates by Sex by Region"
        print
        s = ds.summ('agegrp', 'sex', 'region', SummaryStats.freq(), zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop_mf, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99)
        print p
        print
        plot.dotchart(p, 'region', 'sex', measure='dsr',horizontal=True)
        raw_input('See graph - hit <ENTER> to continue')

    if 1:
        print "Directly Age/sex-Standardised Rates by Year by Region by Sex"
        print "First 15 lines only:"
        print
        s = ds.summ('agegrp', 'sex', 'year', 'region', SummaryStats.freq(), zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop_mf, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99,ci_method='dobson')
        print p[:15]
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Directly Age-Standardised Rates"
        print
        s = ds.summ('agegrp', 'year', SummaryStats.freq(), zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99)
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Directly Age-Standardised Rates by Year by Cause-of-death"
        print
        s = ds.summ('agegrp', 'year', 'causeofdeath', SummaryStats.freq(),filterexpr='causeofdeath in (1,2,3,4)', zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99,debug=True)
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Directly Age-Standardised Rates by Cause-of-death by Year"
        print
        s = ds.summ('agegrp', 'causeofdeath', 'year', SummaryStats.freq(),filterexpr='causeofdeath in (1,2,3,4)', zeros=1)
        p=calc_directly_std_rates(s, pop, stdpopset=stdpop, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99,debug=True)
        print p
        print
        raw_input('Hit <ENTER> to continue')

    if 1:
        print "Indirectly Age-Standardised Mortality Ratios by Region"
        print
        s = ds.summ('agegrp', 'sex', SummaryStats.freq(), zeros=1)
        t = ds.summ('sex', 'region', SummaryStats.freq(), zeros=1)
        stdpop = pop.summ('agegrp','sex',SummaryStats.asum('pop'))
        #pop2 = pop.summ('agegrp','sex','region',SummaryStats.asum('pop'))
        #p=calc_indirectly_std_ratios(t, pop2, s, stdpop, popset_popcol='sum_of_pop', stdpopset_popcol='sum_of_pop',conflev=0.99,debug=True)
        p=calc_indirectly_std_ratios(t, pop, s, pop, popset_popcol='pop', stdpopset_popcol='pop',conflev=0.99,debug=True)
        print p
        print
        raw_input('Hit <ENTER> to continue')

